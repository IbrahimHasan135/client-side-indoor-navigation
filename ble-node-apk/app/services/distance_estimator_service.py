from __future__ import annotations

from app.utils import constants


class DistanceEstimatorService:
    """Convert RSSI into a rough distance estimate for POC navigation."""

    def __init__(self, path_loss_exponent: float = constants.PATH_LOSS_EXPONENT) -> None:
        self._path_loss_exponent = path_loss_exponent

    def estimate(self, rssi: float | int | None, tx_power: int | None = None) -> float | None:
        if rssi is None:
            return None

        measured_power = tx_power if tx_power is not None else constants.DEFAULT_TX_POWER_DBM
        distance = 10 ** ((measured_power - float(rssi)) / (10.0 * self._path_loss_exponent))
        return round(distance, 2)
