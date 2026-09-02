from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BleAdvertisement:
    address: str
    name: str | None
    rssi: int | None
    tx_power: int | None
    manufacturer_data: dict[int, bytes] = field(default_factory=dict)
    service_data: dict[str, bytes] = field(default_factory=dict)
    timestamp_ms: int = 0
