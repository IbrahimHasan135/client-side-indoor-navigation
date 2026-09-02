from __future__ import annotations

from app.controllers.permission_controller import PermissionController
from app.controllers.scan_controller import ScanController
from app.drivers.android_ble_scanner_driver import AndroidBleScannerDriver
from app.drivers.android_bluetooth_adapter_driver import AndroidBluetoothAdapterDriver
from app.drivers.android_permission_driver import AndroidPermissionDriver
from app.services.anchor_registry_service import AnchorRegistryService
from app.services.beacon_scan_service import BeaconScanService
from app.services.distance_estimator_service import DistanceEstimatorService
from app.services.ibeacon_parser_service import IBeaconParserService
from app.services.position_estimator_service import PositionEstimatorService
from app.services.rssi_filter_service import RssiFilterService
from app.utils.logger import AppLogger


class AppController:
    """Application composition root."""

    def __init__(self) -> None:
        self.logger = AppLogger()

        self.permission_driver = AndroidPermissionDriver()
        self.bluetooth_adapter_driver = AndroidBluetoothAdapterDriver()
        self.ble_scanner_driver = AndroidBleScannerDriver(self.bluetooth_adapter_driver)

        self.ibeacon_parser = IBeaconParserService()
        self.rssi_filter = RssiFilterService()
        self.distance_estimator = DistanceEstimatorService()
        self.position_estimator = PositionEstimatorService()
        self.anchor_registry = AnchorRegistryService(self.rssi_filter, self.distance_estimator)

        self.beacon_scan_service = BeaconScanService(
            self.ble_scanner_driver,
            self.ibeacon_parser,
            self.anchor_registry,
            self.position_estimator,
            self.logger,
        )
        self.permission_controller = PermissionController(self.permission_driver, self.logger)
        self.scan_controller = ScanController(
            self.permission_controller,
            self.bluetooth_adapter_driver,
            self.beacon_scan_service,
            self.logger,
        )
