from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    x: float | None
    y: float | None
    quality: str
    anchor_count: int
