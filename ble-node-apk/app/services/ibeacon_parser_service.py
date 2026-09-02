from __future__ import annotations

from dataclasses import dataclass

from app.models.ble_advertisement import BleAdvertisement
from app.utils import constants


@dataclass(frozen=True)
class IBeaconPacket:
    major: int
    minor: int
    tx_power: int
    anchor_id: str


class IBeaconParserService:
    """Decode iBeacon manufacturer data from raw BLE advertisements."""

    def parse(self, advertisement: BleAdvertisement) -> IBeaconPacket | None:
        payload = advertisement.manufacturer_data.get(constants.IBEACON_COMPANY_ID)
        if not payload:
            return None

        offset = payload.find(b"\x02\x15" + constants.IBEACON_UUID)
        if offset < 0 or len(payload) < offset + 23:
            return None

        major = int.from_bytes(payload[offset + 18 : offset + 20], "big")
        minor = int.from_bytes(payload[offset + 20 : offset + 22], "big")
        tx_power_raw = payload[offset + 22]
        tx_power = tx_power_raw - 256 if tx_power_raw > 127 else tx_power_raw
        return IBeaconPacket(
            major=major,
            minor=minor,
            tx_power=tx_power,
            anchor_id=f"{major}:{minor}",
        )

    def is_project_beacon(self, advertisement: BleAdvertisement) -> bool:
        if self.parse(advertisement):
            return True

        return bool(advertisement.name and advertisement.name.startswith(constants.DEVICE_NAME_PREFIX))
