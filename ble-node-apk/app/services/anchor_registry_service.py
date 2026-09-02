from __future__ import annotations

from time import monotonic

from app.models.anchor import Anchor
from app.models.ble_advertisement import BleAdvertisement
from app.services.distance_estimator_service import DistanceEstimatorService
from app.services.ibeacon_parser_service import IBeaconPacket
from app.services.rssi_filter_service import RssiFilterService
from app.utils import constants


class AnchorRegistryService:
    """Store latest RSSI state per anchor."""

    def __init__(
        self,
        rssi_filter: RssiFilterService,
        distance_estimator: DistanceEstimatorService,
        stale_after_ms: int = constants.ANCHOR_STALE_AFTER_MS,
    ) -> None:
        self._rssi_filter = rssi_filter
        self._distance_estimator = distance_estimator
        self._stale_after_ms = stale_after_ms
        self._anchors: dict[str, Anchor] = {}

    def clear(self) -> None:
        self._anchors.clear()
        self._rssi_filter.clear()

    def update(self, advertisement: BleAdvertisement, packet: IBeaconPacket | None) -> Anchor:
        anchor_id = packet.anchor_id if packet else advertisement.address
        filtered_rssi = self._rssi_filter.update(anchor_id, advertisement.rssi)
        distance_m = self._distance_estimator.estimate(
            filtered_rssi if filtered_rssi is not None else advertisement.rssi,
            packet.tx_power if packet else advertisement.tx_power,
        )
        anchor = Anchor(
            anchor_id=anchor_id,
            major=packet.major if packet else None,
            minor=packet.minor if packet else None,
            address=advertisement.address,
            name=advertisement.name,
            raw_rssi=advertisement.rssi,
            filtered_rssi=round(filtered_rssi, 1) if filtered_rssi is not None else None,
            distance_m=distance_m,
            sample_count=self._rssi_filter.sample_count(anchor_id),
            last_seen_ms=advertisement.timestamp_ms or self._now_ms(),
            stale=False,
        )
        self._anchors[anchor_id] = anchor
        return anchor

    def snapshot(self) -> list[Anchor]:
        now_ms = self._now_ms()
        anchors = []
        for anchor in self._anchors.values():
            stale = now_ms - anchor.last_seen_ms > self._stale_after_ms
            anchors.append(
                Anchor(
                    anchor_id=anchor.anchor_id,
                    major=anchor.major,
                    minor=anchor.minor,
                    address=anchor.address,
                    name=anchor.name,
                    raw_rssi=anchor.raw_rssi,
                    filtered_rssi=anchor.filtered_rssi,
                    distance_m=anchor.distance_m,
                    sample_count=anchor.sample_count,
                    last_seen_ms=anchor.last_seen_ms,
                    stale=stale,
                )
            )

        return sorted(anchors, key=lambda item: item.filtered_rssi if item.filtered_rssi is not None else -999, reverse=True)

    def _now_ms(self) -> int:
        return int(monotonic() * 1000)
