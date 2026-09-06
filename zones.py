from math import hypot

from vision.zones import Zone, ZoneManager, bottom_center


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
        return hypot(p2[0] - p1[0], p2[1] - p1[1])

    def score(self, person_center, forklift_center, person_velocity=None, forklift_velocity=None, is_approaching=False, duration=0.0, distance=None):
        if distance is None:
            distance = self._distance(person_center, forklift_center)

        person_velocity = tuple(person_velocity or (0.0, 0.0))
        forklift_velocity = tuple(forklift_velocity or (0.0, 0.0))

        proximity_score = max(0.0, 100.0 - (distance / self.proximity_threshold) * 100.0)
        zone_score = 30.0 if self.zone.contains_point(person_center) or self.zone.contains_point(forklift_center) else 0.0

        relative_speed = hypot(
            forklift_velocity[0] - person_velocity[0],
            forklift_velocity[1] - person_velocity[1],
        )
        speed_score = min(20.0, relative_speed / 10.0)

        direction_score = 25.0 if is_approaching else 0.0
        duration_score = min(20.0, duration * 8.0)

        total = proximity_score + zone_score + direction_score + speed_score + duration_score
        return round(min(100.0, total), 1)


__all__ = ["Zone", "ZoneManager", "bottom_center", "SafetyZone", "RiskScorer"]
