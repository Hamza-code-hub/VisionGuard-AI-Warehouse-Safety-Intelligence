import unittest

from zones import SafetyZone, RiskScorer


class ZoneRiskTests(unittest.TestCase):
    def test_zone_contains_point(self):
        zone = SafetyZone(
            name="forklift_lane",
            points=[(100, 100), (300, 100), (300, 250), (100, 250)],
        )

        self.assertTrue(zone.contains_point((200, 150)))
        self.assertFalse(zone.contains_point((50, 150)))

    def test_risk_score_rises_for_close_zone_approach(self):
        zone = SafetyZone(
            name="danger_zone",
            points=[(100, 100), (300, 100), (300, 250), (100, 250)],
        )
        scorer = RiskScorer(zone)

        score = scorer.score(
            person_center=(200, 180),
            forklift_center=(210, 150),
            person_velocity=(10, 0),
            forklift_velocity=(15, 0),
            is_approaching=True,
            duration=2.5,
        )

        self.assertGreaterEqual(score, 60)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
