import math


def clamp(
    value,
    minimum=0.0,
    maximum=100.0,
):

    return max(
        minimum,
        min(
            maximum,
            float(value),
        ),
    )


def inverse_score(
    value,
    safe_value,
    critical_value,
):

    if value is None:
        return 0.0

    if math.isinf(value):
        return 0.0

    if (
        value
        <= critical_value
    ):
        return 100.0

    if (
        value
        >= safe_value
    ):
        return 0.0

    ratio = (
        safe_value
        - value
    ) / (
        safe_value
        - critical_value
    )

    return clamp(
        ratio
        * 100
    )


class RiskEngine:

    def evaluate(
        self,
        *,
        distance_m,
        ttc_s,
        same_danger_zone,
        closing_speed_mps,
        exposure_duration_s,
        detection_confidence,
    ):

        distance_score = (
            inverse_score(
                distance_m,
                safe_value=5.0,
                critical_value=1.0,
            )
        )

        ttc_score = (
            inverse_score(
                ttc_s,
                safe_value=5.0,
                critical_value=0.8,
            )
        )

        speed_score = clamp(
            (
                closing_speed_mps
                / 3.0
            )
            * 100
        )

        zone_score = (
            100.0
            if same_danger_zone
            else 0.0
        )

        duration_score = clamp(
            (
                exposure_duration_s
                / 5.0
            )
            * 100
        )

        confidence_score = clamp(
            detection_confidence
            * 100
        )

        components = {

            "distance":
                distance_score,

            "ttc":
                ttc_score,

            "closing_speed":
                speed_score,

            "shared_zone":
                zone_score,

            "duration":
                duration_score,

            "detection_confidence":
                confidence_score,
        }

        final_score = (

            distance_score
            * 0.30

            + ttc_score
            * 0.25

            + speed_score
            * 0.15

            + zone_score
            * 0.15

            + duration_score
            * 0.10

            + confidence_score
            * 0.05
        )

        final_score = int(
            round(
                clamp(
                    final_score
                )
            )
        )

        if final_score >= 80:

            severity = (
                "critical"
            )

        elif final_score >= 60:

            severity = (
                "high"
            )

        elif final_score >= 35:

            severity = (
                "medium"
            )

        else:

            severity = (
                "low"
            )

        reasons = []

        if distance_m < 2.0:

            reasons.append(
                "distance below 2 meters"
            )

        if same_danger_zone:

            reasons.append(
                "person and forklift share a danger zone"
            )

        if (
            closing_speed_mps
            >= 0.5
        ):

            reasons.append(
                "person and forklift are moving toward each other"
            )

        if (
            not math.isinf(
                ttc_s
            )
            and ttc_s <= 2.0
        ):

            reasons.append(
                "predicted collision risk below 2 seconds"
            )

        if (
            exposure_duration_s
            >= 2.0
        ):

            reasons.append(
                "dangerous condition persisted for more than 2 seconds"
            )

        return {

            "risk_score":
                final_score,

            "severity":
                severity,

            "components": {
                name:
                    round(
                        value,
                        2,
                    )
                for name, value
                in components.items()
            },

            "reasons":
                reasons,
        }