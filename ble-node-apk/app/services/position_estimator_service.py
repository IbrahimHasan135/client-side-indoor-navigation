from __future__ import annotations

from app.models.anchor import Anchor
from app.models.position import Position
from app.utils import constants


class PositionEstimatorService:
    """POC position estimator using weighted centroid."""

    def __init__(self, anchor_positions: dict[str, tuple[float, float]] | None = None) -> None:
        self._anchor_positions = anchor_positions or constants.ANCHOR_POSITIONS_M

    def estimate(self, anchors: list[Anchor]) -> Position:
        usable = [anchor for anchor in anchors if not anchor.stale and anchor.anchor_id in self._anchor_positions]
        if not usable:
            return Position(x=None, y=None, quality="Belum ada anchor dengan posisi terdaftar.", anchor_count=0)

        weighted_x = 0.0
        weighted_y = 0.0
        total_weight = 0.0
        for anchor in usable:
            distance = anchor.distance_m if anchor.distance_m and anchor.distance_m > 0 else 0.1
            weight = 1.0 / max(distance, 0.1)
            x, y = self._anchor_positions[anchor.anchor_id]
            weighted_x += x * weight
            weighted_y += y * weight
            total_weight += weight

        quality = "Baik" if len(usable) >= 3 else "POC. Tambah minimal 3 anchor untuk posisi lebih stabil."
        return Position(
            x=round(weighted_x / total_weight, 2),
            y=round(weighted_y / total_weight, 2),
            quality=quality,
            anchor_count=len(usable),
        )
