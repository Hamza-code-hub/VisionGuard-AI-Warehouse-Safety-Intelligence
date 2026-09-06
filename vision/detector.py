from ultralytics import YOLO


class YOLOTracker:

    def __init__(
        self,
        model_path,
        confidence=0.40,
    ):

        self.model = YOLO(
            model_path
        )

        self.confidence = (
            confidence
        )

    def track(
        self,
        frame,
    ):

        result = self.model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=self.confidence,
            verbose=False,
        )[0]

        tracks = []

        if result.boxes is None:
            return tracks

        if result.boxes.id is None:
            return tracks

        boxes = (
            result.boxes.xyxy
            .cpu()
            .tolist()
        )

        classes = (
            result.boxes.cls
            .cpu()
            .tolist()
        )

        confidences = (
            result.boxes.conf
            .cpu()
            .tolist()
        )

        track_ids = (
            result.boxes.id
            .int()
            .cpu()
            .tolist()
        )

        names = result.names

        for (
            box,
            class_id,
            confidence,
            track_id,
        ) in zip(
            boxes,
            classes,
            confidences,
            track_ids,
        ):

            class_id = int(
                class_id
            )

            class_name = (
                str(
                    names[
                        class_id
                    ]
                )
                .lower()
                .strip()
            )

            tracks.append(
                {
                    "track_id":
                        int(track_id),

                    "class_id":
                        class_id,

                    "class_name":
                        class_name,

                    "confidence":
                        float(
                            confidence
                        ),

                    "bbox": [
                        float(value)
                        for value
                        in box
                    ],
                }
            )

        return tracks