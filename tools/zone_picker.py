import json

import cv2


VIDEO_PATH = (
    "videos/demo.mp4"
)

OUTPUT_PATH = (
    "config/zones.json"
)


points = []


def mouse_callback(
    event,
    x,
    y,
    flags,
    param,
):

    if (
        event
        ==
        cv2.EVENT_LBUTTONDOWN
    ):

        points.append(
            [x, y]
        )

        print(
            f"Point added: {x}, {y}"
        )


cap = cv2.VideoCapture(
    VIDEO_PATH
)


success, frame = (
    cap.read()
)


cap.release()


if not success:

    raise RuntimeError(
        "Could not read video."
    )


cv2.namedWindow(
    "Zone Picker"
)


cv2.setMouseCallback(
    "Zone Picker",
    mouse_callback,
)


while True:

    display = (
        frame.copy()
    )

    for index, point in enumerate(
        points
    ):

        cv2.circle(
            display,
            tuple(point),
            6,
            (0, 255, 255),
            -1,
        )

        cv2.putText(
            display,
            str(index + 1),
            (
                point[0] + 8,
                point[1] - 8,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    if len(points) > 1:

        for index in range(
            len(points) - 1
        ):

            cv2.line(
                display,
                tuple(
                    points[index]
                ),
                tuple(
                    points[index + 1]
                ),
                (0, 255, 255),
                2,
            )

    if len(points) >= 3:

        cv2.line(
            display,
            tuple(
                points[-1]
            ),
            tuple(
                points[0]
            ),
            (0, 255, 255),
            2,
        )

    cv2.putText(
        display,
        "Left click: add point | S: save | R: reset | Q: quit",
        (
            20,
            35,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.imshow(
        "Zone Picker",
        display,
    )

    key = (
        cv2.waitKey(20)
        & 0xFF
    )

    if key == ord("q"):
        break

    if key == ord("r"):

        points.clear()

        print(
            "Points reset."
        )

    if key == ord("s"):

        if len(points) < 3:

            print(
                "Need at least 3 points."
            )

            continue

        config = {
            "zones": [
                {
                    "name":
                        "Forklift Danger Zone",

                    "type":
                        "danger",

                    "risk_weight":
                        1.0,

                    "points":
                        points,
                }
            ]
        }

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                config,
                file,
                indent=4,
            )

        print(
            f"Saved to {OUTPUT_PATH}"
        )

        break


cv2.destroyAllWindows()