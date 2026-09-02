from __future__ import annotations

from dataclasses import dataclass, field

from app.models.anchor import Anchor
from app.models.position import Position


@dataclass(frozen=True)
class ScanSnapshot:
    anchors: list[Anchor] = field(default_factory=list)
    position: Position | None = None
    scan_state: str = "idle"
    permission_state: str = "unknown"
    bluetooth_enabled: bool = False
    raw_ble_packets: int = 0
    accepted_esp_packets: int = 0
    rejected_packets: int = 0
    missing_rssi_packets: int = 0
    last_error: str | None = None
