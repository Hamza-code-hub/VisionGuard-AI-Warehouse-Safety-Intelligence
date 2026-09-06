import json

from pathlib import Path

import cv2
import numpy as np


class GroundPlaneCalibration:

    def __init__(
        self,
        image_points,
        ground_points,
    ):

        image_points = (
            np.asarray(
                image_points,
                dtype=np.float32,
            )
        )

        ground_points = (
            np.asarray(
                ground_points,
                dtype=np.float32,
            )
        )

        if (
            len(image_points)
            < 4
        ):
            raise ValueError(
                "Minimum 4 calibration points required."
            )

        if (
            len(image_points)
            != len(
                ground_points
            )
        ):
            raise ValueError(
                "Image and ground points must match."
            )

        (
            self.homography,
            _
        ) = cv2.findHomography(
            image_points,
            ground_points,
            method=0,
        )

        if (
            self.homography
            is None
        ):
            raise RuntimeError(
                "Could not calculate homography."
            )

    @classmethod
    def from_json(
        cls,
        path,
    ):

        data = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        return cls(
            image_points=data[
                "image_points_px"
            ],
            ground_points=data[
                "ground_points_m"
            ],
        )

    def image_to_ground(
        self,
        point,
    ):

        point = np.array(
            [
                [
                    [
                        float(
                            point[0]
                        ),
                        float(
                            point[1]
                        ),
                    ]
                ]
            ],
            dtype=np.float32,
        )

        transformed = (
            cv2.perspectiveTransform(
                point,
                self.homography,
            )[0][0]
        )

        return (
            float(
                transformed[0]
            ),
            float(
                transformed[1]
            ),
        )

    def distance_m(
        self,
        point_a,
        point_b,
    ):

        a = np.array(
            self.image_to_ground(
                point_a
            ),
            dtype=float,
        )

        b = np.array(
            self.image_to_ground(
                point_b
            ),
            dtype=float,
        )

        return float(
            np.linalg.norm(
                a - b
            )
        )