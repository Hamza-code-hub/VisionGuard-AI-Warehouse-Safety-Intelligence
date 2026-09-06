from collections import deque
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import json
import time

import cv2


class EventRecorder:

    def __init__(
        self,
        output_dir,
        fps,
        frame_size,
        pre_seconds=5,
        post_seconds=5,
        cooldown_seconds=5,
    ):

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.fps = max(
            1.0,
            float(fps),
        )

        self.frame_size = (
            int(
                frame_size[0]
            ),
            int(
                frame_size[1]
            ),
        )

        self.pre_frames = int(
            self.fps
            * pre_seconds
        )

        self.post_frames = int(
            self.fps
            * post_seconds
        )

        self.buffer = deque(
            maxlen=self.pre_frames
        )

        self.active = None

        self.cooldown_seconds = (
            cooldown_seconds
        )

        self.last_event_end = 0

    def capture(
        self,
        frame,
    ):

        frame_copy = (
            frame.copy()
        )

        self.buffer.append(
            frame_copy
        )

        if self.active is None:
            return

        self.active[
            "frames"
        ].append(
            frame_copy
        )

        self.active[
            "remaining"
        ] -= 1

        if (
            self.active[
                "remaining"
            ]
            <= 0
        ):
            self._finalize()

    def trigger(
        self,
        metadata,
        snapshot_frame,
    ):

        if self.active is not None:
            return None

        if (
            time.time()
            - self.last_event_end
            <
            self.cooldown_seconds
        ):
            return None

        event_id = (
            datetime.now(
                timezone.utc
            )
            .strftime(
                "EVT-%Y%m%d-%H%M%S-%f"
            )
        )

        event_directory = (
            self.output_dir
            /
            event_id
        )

        event_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        snapshot_path = (
            event_directory
            /
            "snapshot.jpg"
        )

        cv2.imwrite(
            str(
                snapshot_path
            ),
            snapshot_frame,
        )

        metadata = dict(
            metadata
        )

        metadata[
            "event_id"
        ] = event_id

        metadata[
            "created_at_utc"
        ] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        self.active = {

            "event_id":
                event_id,

            "directory":
                event_directory,

            "metadata":
                metadata,

            "frames": [
                frame.copy()
                for frame
                in self.buffer
            ],

            "remaining":
                self.post_frames,
        }

        print(
            f"[EVENT] Triggered {event_id}"
        )

        return event_id

    def _finalize(
        self,
    ):

        if self.active is None:
            return

        event = self.active

        video_path = (
            event[
                "directory"
            ]
            /
            "event.mp4"
        )

        writer = (
            cv2.VideoWriter(
                str(
                    video_path
                ),

                cv2.VideoWriter_fourcc(
                    *"mp4v"
                ),

                self.fps,

                self.frame_size,
            )
        )

        for frame in event[
            "frames"
        ]:

            if (
                frame.shape[1],
                frame.shape[0],
            ) != self.frame_size:

                frame = cv2.resize(
                    frame,
                    self.frame_size,
                )

            writer.write(
                frame
            )

        writer.release()

        metadata_path = (
            event[
                "directory"
            ]
            /
            "event.json"
        )

        metadata_path.write_text(
            json.dumps(
                event[
                    "metadata"
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[EVENT] Saved {video_path}"
        )

        self.active = None

        self.last_event_end = (
            time.time()
        )

    def close(
        self,
    ):

        if self.active:
            self._finalize()