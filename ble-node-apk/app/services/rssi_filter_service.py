from __future__ import annotations

from app.utils import constants


class RssiFilterService:
    """Per-anchor Exponential Moving Average filter."""

    def __init__(self, alpha: float = constants.RSSI_EMA_ALPHA) -> None:
        self._alpha = alpha
        self._values: dict[str, float] = {}
        self._sample_counts: dict[str, int] = {}

    def clear(self) -> None:
        self._values.clear()
        self._sample_counts.clear()

    def update(self, anchor_id: str, rssi: int | None) -> float | None:
        if rssi is None:
            return self._values.get(anchor_id)

        previous = self._values.get(anchor_id)
        filtered = float(rssi) if previous is None else (self._alpha * rssi) + ((1.0 - self._alpha) * previous)
        self._values[anchor_id] = filtered
        self._sample_counts[anchor_id] = self._sample_counts.get(anchor_id, 0) + 1
        return filtered

    def sample_count(self, anchor_id: str) -> int:
        return self._sample_counts.get(anchor_id, 0)
