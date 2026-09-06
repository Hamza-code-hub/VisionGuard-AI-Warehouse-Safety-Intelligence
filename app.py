import argparse
import math

import cv2

from vision.calibration import GroundPlaneCalibration
from vision.detector import YOLOTracker
from vision.drawing import (
    draw_alert,
    draw_connection,
    draw_fps,
    draw_tracks,
)
from vision.events import EventRecorder
from vision.motion import MotionTracker
from vision.risk import RiskEngine
from vision.ttc import time_to_closest_approach
from vision.zones import ZoneManager, bottom_center


def parse_args():
    parser = argparse.ArgumentParser(
        description="VisionGuard Warehouse Safety Prototype"
    )

    parser.add_argument(
        "--model",
        default="models/best.pt",
        help="YOLO model path",
    )

    parser.add_argument(
        "--video",
        default="videos/demo.mp4",
        help="Input video path",
    )

    parser.add_argument(
        "--zones",
        default="config/zones.json",
    )

    parser.add_argument(
        "--calibration",
        default="config/calibration.json",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.40,
    )

    parser.add_argument(
        "--critical-risk",
        type=int,
        default=80,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    detector = YOLOTracker(
        model_path=args.model,
        confidence=args.confidence,
    )

    zone_manager = ZoneManager.from_json(
        args.zones
    )

    calibration = GroundPlaneCalibration.from_json(
        args.calibration
    )

    motion = MotionTracker(
        history_size=12
    )

    risk_engine = RiskEngine()

    cap = cv2.VideoCapture(
        args.video
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {args.video}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 25.0

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    recorder = EventRecorder(
        output_dir="output/events",
        fps=fps,
        frame_size=(width, height),
        pre_seconds=5,
        post_seconds=5,
        cooldown_seconds=5,
    )

    frame_index = 0

    exposure_started = {}

    while True:
        success, frame = cap.read()

        if not success:
            break

        frame_index += 1

        timestamp_s = (
            frame_index / fps
        )

        recorder.capture(frame)

        tracks = detector.track(
            frame
        )

        persons = []
        forklifts = []

        # ----------------------------------
        # Prepare detections
        # ----------------------------------

        for track in tracks:

            if track["class_name"] not in {
                "person",
                "forklift",
            }:
                continue

            anchor_px = bottom_center(
                track["bbox"]
            )

            ground_position = (
                calibration.image_to_ground(
                    anchor_px
                )
            )

            track["anchor_px"] = (
                anchor_px
            )

            track["ground_xy"] = (
                ground_position
            )

            motion.update(
                track_id=track["track_id"],
                position_m=ground_position,
                timestamp_s=timestamp_s,
            )

            if (
                track["class_name"]
                == "person"
            ):
                persons.append(track)

            elif (
                track["class_name"]
                == "forklift"
            ):
                forklifts.append(
                    track
                )

        best_event = None

        # ----------------------------------
        # Person ↔ Forklift analysis
        # ----------------------------------

        for person in persons:

            for forklift in forklifts:

                pair_key = (
                    person["track_id"],
                    forklift["track_id"],
                )

                distance_m = (
                    calibration.distance_m(
                        person["anchor_px"],
                        forklift["anchor_px"],
                    )
                )

                shared_zones = (
                    zone_manager.shared_zones(
                        person["anchor_px"],
                        forklift["anchor_px"],
                    )
                )

                same_danger_zone = (
                    len(shared_zones) > 0
                )

                person_velocity = (
                    motion.velocity(
                        person["track_id"]
                    )
                )

                forklift_velocity = (
                    motion.velocity(
                        forklift["track_id"]
                    )
                )

                closing_speed = (
                    motion.closing_speed_mps(
                        person["track_id"],
                        person["ground_xy"],
                        forklift["track_id"],
                        forklift["ground_xy"],
                    )
                )

                ttc_data = (
                    time_to_closest_approach(
                        person["ground_xy"],
                        person_velocity,
                        forklift["ground_xy"],
                        forklift_velocity,
                        safety_radius_m=1.5,
                    )
                )

                # ----------------------------------
                # Exposure duration
                # ----------------------------------

                risky_condition = (
                    distance_m < 4.0
                    or same_danger_zone
                )

                if risky_condition:

                    if (
                        pair_key
                        not in exposure_started
                    ):
                        exposure_started[
                            pair_key
                        ] = timestamp_s

                    exposure_duration = (
                        timestamp_s
                        - exposure_started[
                            pair_key
                        ]
                    )

                else:

                    exposure_started.pop(
                        pair_key,
                        None,
                    )

                    exposure_duration = 0.0

                detection_confidence = min(
                    person["confidence"],
                    forklift["confidence"],
                )

                risk = (
                    risk_engine.evaluate(
                        distance_m=distance_m,
                        ttc_s=ttc_data[
                            "ttc_s"
                        ],
                        same_danger_zone=(
                            same_danger_zone
                        ),
                        closing_speed_mps=(
                            closing_speed
                        ),
                        exposure_duration_s=(
                            exposure_duration
                        ),
                        detection_confidence=(
                            detection_confidence
                        ),
                    )
                )

                event = {
                    "person": person,
                    "forklift": forklift,

                    "person_id": (
                        person["track_id"]
                    ),

                    "forklift_id": (
                        forklift["track_id"]
                    ),

                    "distance_m": (
                        distance_m
                    ),

                    "closing_speed_mps": (
                        closing_speed
                    ),

                    "ttc_s": (
                        ttc_data["ttc_s"]
                    ),

                    "predicted_closest_distance_m":
                        ttc_data[
                            "closest_distance_m"
                        ],

                    "shared_zones": [
                        zone.name
                        for zone in shared_zones
                    ],

                    "exposure_duration_s":
                        exposure_duration,

                    "risk": risk,
                }

                if (
                    best_event is None
                    or risk["risk_score"]
                    >
                    best_event[
                        "risk"
                    ][
                        "risk_score"
                    ]
                ):
                    best_event = event

        # ----------------------------------
        # Draw UI
        # ----------------------------------

        zone_manager.draw(
            frame
        )

        draw_tracks(
            frame,
            tracks,
        )

        if best_event:

            draw_connection(
                frame,
                best_event["person"],
                best_event["forklift"],
                best_event["distance_m"],
            )

            draw_alert(
                frame,
                best_event,
            )

        draw_fps(
            frame,
            fps,
        )

        # ----------------------------------
        # Create event
        # ----------------------------------

        if (
            best_event
            and
            best_event[
                "risk"
            ][
                "risk_score"
            ]
            >= args.critical_risk
        ):

            ttc = best_event[
                "ttc_s"
            ]

            metadata = {

                "event_type":
                    "forklift_pedestrian_proximity",

                "person_id":
                    best_event[
                        "person_id"
                    ],

                "forklift_id":
                    best_event[
                        "forklift_id"
                    ],

                "closest_distance_m":
                    round(
                        best_event[
                            "distance_m"
                        ],
                        3,
                    ),

                "closing_speed_mps":
                    round(
                        best_event[
                            "closing_speed_mps"
                        ],
                        3,
                    ),

                "ttc_s":
                    None
                    if math.isinf(ttc)
                    else round(
                        ttc,
                        3,
                    ),

                "shared_zones":
                    best_event[
                        "shared_zones"
                    ],

                "exposure_duration_s":
                    round(
                        best_event[
                            "exposure_duration_s"
                        ],
                        3,
                    ),

                **best_event[
                    "risk"
                ],
            }

            recorder.trigger(
                metadata=metadata,
                snapshot_frame=frame,
            )

        cv2.imshow(
            "VisionGuard",
            frame,
        )

        key = (
            cv2.waitKey(1)
            & 0xFF
        )

        if key == ord("q"):
            break

    recorder.close()

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()