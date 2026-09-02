from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Anchor:
    anchor_id: str
    major: int | None
    minor: int | None
    address: str
    name: str | None
    raw_rssi: int | None
    filtered_rssi: float | None
    distance_m: float | None
    sample_count: int
    last_seen_ms: int
    stale: bool
