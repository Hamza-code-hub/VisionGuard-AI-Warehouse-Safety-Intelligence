import math

import cv2


def draw_tracks(
    frame,
    tracks,
):

    for track in tracks:

        if (
            track[
                "class_name"
            ]
            not in {
                "person",
                "forklift",
            }
        ):
            continue

        x1, y1, x2, y2 = map(
            int,
            track["bbox"],
        )

        if (
            track[
                "class_name"
            ]
            == "person"
        ):

            color = (
                0,
                220,
                0,
            )

        else:

            color = (
                0,
                220,
                255,
            )

        label = (
            f'{track["class_name"].upper()} '
            f'#{track["track_id"]} '
            f'{track["confidence"]:.2f}'
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2,
        )

        cv2.putText(
            frame,
            label,
            (
                x1,
                max(
                    25,
                    y1 - 10,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )


def draw_connection(
    frame,
    person,
    forklift,
    distance_m,
):

    person_point = tuple(
        map(
            int,
            person[
                "anchor_px"
            ],
        )
    )

    forklift_point = tuple(
        map(
            int,
            forklift[
                "anchor_px"
            ],
        )
    )

    cv2.line(
        frame,
        person_point,
        forklift_point,
        (0, 0, 255),
        2,
    )

    midpoint = (

        int(
            (
                person_point[0]
                +
                forklift_point[0]
            )
            / 2
        ),

        int(
            (
                person_point[1]
                +
                forklift_point[1]
            )
            / 2
        ),
    )

    cv2.putText(
        frame,
        f"{distance_m:.2f} m",
        midpoint,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def draw_alert(
    frame,
    event,
):

    if not event:
        return

    risk = event[
        "risk"
    ]

    score = risk[
        "risk_score"
    ]

    severity = (
        risk[
            "severity"
        ]
        .upper()
    )

    distance = event[
        "distance_m"
    ]

    ttc = event[
        "ttc_s"
    ]

    x = 20
    y = 20

    width = 470
    height = 190

    cv2.rectangle(
        frame,
        (x, y),
        (
            x + width,
            y + height,
        ),
        (20, 20, 20),
        -1,
    )

    if severity == "CRITICAL":

        border = (
            0,
            0,
            255,
        )

    elif severity == "HIGH":

        border = (
            0,
            140,
            255,
        )

    else:

        border = (
            0,
            220,
            255,
        )

    cv2.rectangle(
        frame,
        (x, y),
        (
            x + width,
            y + height,
        ),
        border,
        2,
    )

    if math.isinf(
        ttc
    ):

        ttc_text = (
            "No predicted breach"
        )

    else:

        ttc_text = (
            f"{ttc:.2f} sec"
        )

    texts = [

        f"RISK: {severity}",

        f"Risk Score: {score}/100",

        f"Distance: {distance:.2f} m",

        f"TTC: {ttc_text}",
    ]

    text_y = y + 40

    for index, text in enumerate(
        texts
    ):

        color = (
            border
            if index == 0
            else (
                255,
                255,
                255,
            )
        )

        cv2.putText(
            frame,
            text,
            (
                x + 15,
                text_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
            cv2.LINE_AA,
        )

        text_y += 38


def draw_fps(
    frame,
    fps,
):

    cv2.putText(
        frame,
        f"Source FPS: {fps:.1f}",
        (
            frame.shape[1] - 190,
            30,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )