from __future__ import annotations

from app.utils import constants


class DistanceEstimatorService:
    """Convert RSSI into a rough distance estimate for POC navigation."""

    def __init__(
        self,
        measured_power_at_1m: int = constants.MEASURED_POWER_AT_1M_DBM,
        path_loss_exponent: float = constants.PATH_LOSS_EXPONENT,
    ) -> None:
        self._measured_power_at_1m = measured_power_at_1m
        self._path_loss_exponent = path_loss_exponent

    def estimate(self, rssi: float | int | None, tx_power: int | None = None) -> float | None:
        if rssi is None:
            return None

        measured_power = self._measured_power_at_1m
        distance = 10 ** ((measured_power - float(rssi)) / (10.0 * self._path_loss_exponent))
        return round(distance, 2)
