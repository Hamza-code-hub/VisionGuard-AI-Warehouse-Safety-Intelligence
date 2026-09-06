from collections import (
    defaultdict,
    deque,
)

import numpy as np


class MotionTracker:

    def __init__(
        self,
        history_size=12,
    ):

        self.history = (
            defaultdict(
                lambda: deque(
                    maxlen=history_size
                )
            )
        )

    def update(
        self,
        track_id,
        position_m,
        timestamp_s,
    ):

        self.history[
            int(track_id)
        ].append(
            (
                float(
                    timestamp_s
                ),

                np.asarray(
                    position_m,
                    dtype=float,
                ),
            )
        )

    def velocity(
        self,
        track_id,
    ):

        items = self.history.get(
            int(track_id)
        )

        if (
            not items
            or len(items) < 2
        ):
            return np.zeros(
                2,
                dtype=float,
            )

        t0, p0 = items[0]

        t1, p1 = items[-1]

        dt = t1 - t0

        if dt <= 0:
            return np.zeros(
                2,
                dtype=float,
            )

        velocity = (
            p1 - p0
        ) / dt

        return velocity

    def speed_mps(
        self,
        track_id,
    ):

        velocity = (
            self.velocity(
                track_id
            )
        )

        return float(
            np.linalg.norm(
                velocity
            )
        )

    def speed_kmh(
        self,
        track_id,
    ):

        return (
            self.speed_mps(
                track_id
            )
            * 3.6
        )

    def closing_speed_mps(
        self,
        id_a,
        pos_a,
        id_b,
        pos_b,
    ):

        a = np.asarray(
            pos_a,
            dtype=float,
        )

        b = np.asarray(
            pos_b,
            dtype=float,
        )

        relative_position = (
            b - a
        )

        distance = np.linalg.norm(
            relative_position
        )

        if distance <= 1e-6:
            return 0.0

        velocity_a = (
            self.velocity(
                id_a
            )
        )

        velocity_b = (
            self.velocity(
                id_b
            )
        )

        relative_velocity = (
            velocity_b
            - velocity_a
        )

        unit_direction = (
            relative_position
            / distance
        )

        distance_rate = np.dot(
            unit_direction,
            relative_velocity,
        )

        # Negative distance rate =
        # objects becoming closer.

        closing_speed = max(
            0.0,
            -float(
                distance_rate
            ),
        )

        return closing_speed