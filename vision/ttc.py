import math

import numpy as np


def time_to_closest_approach(
    position_a,
    velocity_a,
    position_b,
    velocity_b,
    safety_radius_m=1.5,
):

    position_a = np.asarray(
        position_a,
        dtype=float,
    )

    position_b = np.asarray(
        position_b,
        dtype=float,
    )

    velocity_a = np.asarray(
        velocity_a,
        dtype=float,
    )

    velocity_b = np.asarray(
        velocity_b,
        dtype=float,
    )

    relative_position = (
        position_b
        - position_a
    )

    relative_velocity = (
        velocity_b
        - velocity_a
    )

    velocity_squared = float(
        np.dot(
            relative_velocity,
            relative_velocity,
        )
    )

    current_distance = float(
        np.linalg.norm(
            relative_position
        )
    )

    if velocity_squared < 1e-8:

        return {
            "ttc_s":
                math.inf,

            "time_to_closest_s":
                math.inf,

            "closest_distance_m":
                current_distance,

            "predicted_breach":
                False,
        }

    time_to_closest = (
        -float(
            np.dot(
                relative_position,
                relative_velocity,
            )
        )
        / velocity_squared
    )

    if time_to_closest <= 0:

        return {
            "ttc_s":
                math.inf,

            "time_to_closest_s":
                time_to_closest,

            "closest_distance_m":
                current_distance,

            "predicted_breach":
                False,
        }

    closest_vector = (
        relative_position
        +
        relative_velocity
        * time_to_closest
    )

    closest_distance = float(
        np.linalg.norm(
            closest_vector
        )
    )

    predicted_breach = (
        closest_distance
        <= safety_radius_m
    )

    if predicted_breach:

        ttc = (
            time_to_closest
        )

    else:

        ttc = math.inf

    return {
        "ttc_s":
            float(ttc),

        "time_to_closest_s":
            float(
                time_to_closest
            ),

        "closest_distance_m":
            closest_distance,

        "predicted_breach":
            predicted_breach,
    }