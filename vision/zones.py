import json

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


def bottom_center(
    bbox,
):
    """
    Ground contact point.

    Better than bounding-box center
    when working with floor zones.
    """

    x1, y1, x2, y2 = bbox

    return (
        float(
            (x1 + x2)
            / 2
        ),
        float(y2),
    )


class SafetyZone:
    def __init__(self, name, points):
        self.name = name
        self.points = [(float(x), float(y)) for x, y in points]

    def contains_point(self, point):
        x, y = point
        inside = False
        n = len(self.points)
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % n]
            if ((y1 > y) != (y2 > y)) and (
                x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
            ):
                inside = not inside
        return inside

    def __repr__(self):
        return f"SafetyZone(name={self.name!r}, points={self.points})"


class RiskScorer:
    def __init__(self, zone, proximity_threshold=150.0):
        self.zone = zone
        self.proximity_threshold = proximity_threshold

    def _distance(self, p1, p2):
        import math
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def score(self, person_center, forklift_center, person_velocity=None, forklift_velocity=None, is_approaching=False, duration=0.0, distance=None):
        if distance is None:
            distance = self._distance(person_center, forklift_center)

        person_velocity = tuple(person_velocity or (0.0, 0.0))
        forklift_velocity = tuple(forklift_velocity or (0.0, 0.0))

        proximity_score = max(0.0, 100.0 - (distance / self.proximity_threshold) * 100.0)
        zone_score = 30.0 if self.zone.contains_point(person_center) or self.zone.contains_point(forklift_center) else 0.0

        relative_speed = math.hypot(
            forklift_velocity[0] - person_velocity[0],
            forklift_velocity[1] - person_velocity[1],
        )
        speed_score = min(20.0, relative_speed / 10.0)

        direction_score = 25.0 if is_approaching else 0.0
        duration_score = min(20.0, duration * 8.0)

        total = proximity_score + zone_score + direction_score + speed_score + duration_score
        return round(min(100.0, total), 1)


@dataclass
class Zone:

    name: str
    zone_type: str
    polygon: np.ndarray
    risk_weight: float = 1.0

    def contains(
        self,
        point,
    ):

        x, y = point

        result = (
            cv2.pointPolygonTest(
                self.polygon.astype(
                    np.float32
                ),
                (
                    float(x),
                    float(y),
                ),
                False,
            )
        )

        return result >= 0


class ZoneManager:

    def __init__(
        self,
        zones,
    ):

        self.zones = zones

    @classmethod
    def from_json(
        cls,
        path,
    ):

        path = Path(path)

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        zones = []

        for item in data[
            "zones"
        ]:

            polygon = np.array(
                item["points"],
                dtype=np.int32,
            )

            zone = Zone(
                name=item[
                    "name"
                ],

                zone_type=item.get(
                    "type",
                    "danger",
                ),

                polygon=polygon,

                risk_weight=float(
                    item.get(
                        "risk_weight",
                        1.0,
                    )
                ),
            )

            zones.append(
                zone
            )

        return cls(
            zones
        )

    def zones_for_point(
        self,
        point,
    ):

        return [
            zone
            for zone
            in self.zones
            if zone.contains(
                point
            )
        ]

    def shared_zones(
        self,
        point_a,
        point_b,
    ):

        zones_a = {
            zone.name: zone
            for zone
            in self.zones_for_point(
                point_a
            )
        }

        zones_b = {
            zone.name: zone
            for zone
            in self.zones_for_point(
                point_b
            )
        }

        shared_names = (
            zones_a.keys()
            &
            zones_b.keys()
        )

        return [
            zones_a[name]
            for name
            in shared_names
        ]

    def draw(
        self,
        frame,
    ):

        overlay = (
            frame.copy()
        )

        for zone in self.zones:

            points = (
                zone.polygon.reshape(
                    (-1, 1, 2)
                )
            )

            cv2.fillPoly(
                overlay,
                [points],
                (0, 0, 255),
            )

            cv2.polylines(
                frame,
                [points],
                True,
                (0, 0, 255),
                2,
            )

            x, y = (
                zone.polygon[0]
            )

            cv2.putText(
                frame,
                zone.name,
                (
                    int(x),
                    max(
                        30,
                        int(y) - 10,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.addWeighted(
            overlay,
            0.10,
            frame,
            0.90,
            0,
            frame,
        )

        return frame