import cv2


VIDEO_PATH = (
    "videos/demo.mp4"
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
            f"Calibration point {len(points)}: [{x}, {y}]"
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
        "Could not load video."
    )


cv2.namedWindow(
    "Calibration Picker"
)


cv2.setMouseCallback(
    "Calibration Picker",
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
            8,
            (255, 0, 255),
            -1,
        )

        cv2.putText(
            display,
            str(
                index + 1
            ),
            (
                point[0] + 10,
                point[1] - 10,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

    cv2.putText(
        display,
        "Select known floor reference points | R reset | Q quit",
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
        "Calibration Picker",
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


cv2.destroyAllWindows()


print(
    "\nUse these pixel coordinates:"
)

print(
    points
)