from __future__ import annotations

from kivy.clock import Clock

from app.utils import constants


class ScanController:
    """Bridge UI actions to BLE scan services."""

    def __init__(
        self,
        permission_controller,
        bluetooth_adapter_driver,
        beacon_scan_service,
        logger,
    ) -> None:
        self._permission_controller = permission_controller
        self._bluetooth_adapter_driver = bluetooth_adapter_driver
        self._beacon_scan_service = beacon_scan_service
        self._logger = logger
        self._ui_update_callback = None
        self._refresh_event = None

    def set_ui_update_callback(self, callback) -> None:
        self._ui_update_callback = callback

    def start_scan(self) -> None:
        self._push_snapshot("Meminta permission")
        self._permission_controller.ensure_permissions(self._start_after_permission)

    def stop_scan(self) -> None:
        self._beacon_scan_service.stop()
        self._stop_refresh()
        self._push_snapshot("Scan dihentikan")

    def snapshot(self):
        bluetooth_enabled = self._bluetooth_adapter_driver.is_enabled()
        self._beacon_scan_service.set_bluetooth_enabled(bluetooth_enabled)
        self._beacon_scan_service.set_permission_state(self._permission_controller.state)
        return self._beacon_scan_service.snapshot()

    def _start_after_permission(self, granted: bool) -> None:
        if not granted:
            self._beacon_scan_service.set_permission_state("denied")
            self._push_snapshot("Permission ditolak")
            return

        self._beacon_scan_service.set_permission_state("granted")
        self._beacon_scan_service.set_bluetooth_enabled(self._bluetooth_adapter_driver.is_enabled())
        self._beacon_scan_service.start()
        self._start_refresh()
        self._push_snapshot("Scanning")

    def _start_refresh(self) -> None:
        self._stop_refresh()
        self._refresh_event = Clock.schedule_interval(
            lambda _dt: self._push_snapshot(),
            constants.UI_REFRESH_INTERVAL_SEC,
        )

    def _stop_refresh(self) -> None:
        if self._refresh_event:
            self._refresh_event.cancel()
            self._refresh_event = None

    def _push_snapshot(self, status_message: str | None = None) -> None:
        if not self._ui_update_callback:
            return

        self._ui_update_callback(self.snapshot(), status_message)
