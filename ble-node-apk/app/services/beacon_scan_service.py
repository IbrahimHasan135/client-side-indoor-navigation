from __future__ import annotations

from app.models.ble_advertisement import BleAdvertisement
from app.models.scan_snapshot import ScanSnapshot
from app.services.anchor_registry_service import AnchorRegistryService
from app.services.ibeacon_parser_service import IBeaconParserService
from app.services.position_estimator_service import PositionEstimatorService
from app.utils.logger import AppLogger


class BeaconScanService:
    """Coordinate passive BLE scan and domain processing."""

    def __init__(
        self,
        ble_scanner_driver,
        ibeacon_parser: IBeaconParserService,
        anchor_registry: AnchorRegistryService,
        position_estimator: PositionEstimatorService,
        logger: AppLogger,
    ) -> None:
        self._ble_scanner_driver = ble_scanner_driver
        self._ibeacon_parser = ibeacon_parser
        self._anchor_registry = anchor_registry
        self._position_estimator = position_estimator
        self._logger = logger
        self._scan_state = "idle"
        self._permission_state = "unknown"
        self._bluetooth_enabled = False
        self._raw_ble_packets = 0
        self._accepted_esp_packets = 0
        self._rejected_packets = 0
        self._missing_rssi_packets = 0
        self._last_error: str | None = None

    def start(self) -> None:
        self._anchor_registry.clear()
        self._raw_ble_packets = 0
        self._accepted_esp_packets = 0
        self._rejected_packets = 0
        self._missing_rssi_packets = 0
        self._last_error = None
        self._scan_state = "starting"
        self._ble_scanner_driver.set_advertisement_callback(self._handle_advertisement)
        self._ble_scanner_driver.set_error_callback(self._handle_scan_error)
        self._ble_scanner_driver.start_scan()
        self._scan_state = "scanning"
        self._logger.info("BLE", "scan started")

    def stop(self) -> None:
        self._ble_scanner_driver.stop_scan()
        self._scan_state = "stopped"
        self._logger.info("BLE", "scan stopped")

    def set_permission_state(self, state: str) -> None:
        self._permission_state = state

    def set_bluetooth_enabled(self, enabled: bool) -> None:
        self._bluetooth_enabled = enabled

    def snapshot(self) -> ScanSnapshot:
        anchors = self._anchor_registry.snapshot()
        return ScanSnapshot(
            anchors=anchors,
            position=self._position_estimator.estimate(anchors),
            scan_state=self._scan_state,
            permission_state=self._permission_state,
            bluetooth_enabled=self._bluetooth_enabled,
            raw_ble_packets=self._raw_ble_packets,
            accepted_esp_packets=self._accepted_esp_packets,
            rejected_packets=self._rejected_packets,
            missing_rssi_packets=self._missing_rssi_packets,
            last_error=self._last_error,
        )

    def _handle_advertisement(self, advertisement: BleAdvertisement) -> None:
        self._raw_ble_packets += 1
        if advertisement.rssi is None:
            self._missing_rssi_packets += 1

        packet = self._ibeacon_parser.parse(advertisement)
        if not packet and not self._ibeacon_parser.is_project_beacon(advertisement):
            self._rejected_packets += 1
            return

        self._accepted_esp_packets += 1
        anchor = self._anchor_registry.update(advertisement, packet)
        self._logger.info("BLE", f"accepted anchor={anchor.anchor_id} rssi={anchor.raw_rssi}")

    def _handle_scan_error(self, message: str) -> None:
        self._scan_state = "error"
        self._last_error = message
        self._logger.error("BLE", message)
