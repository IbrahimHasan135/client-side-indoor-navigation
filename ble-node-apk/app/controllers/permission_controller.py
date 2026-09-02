from __future__ import annotations


class PermissionController:
    """Coordinate Android permission flow for scan features."""

    def __init__(self, permission_driver, logger) -> None:
        self._permission_driver = permission_driver
        self._logger = logger
        self.state = "unknown"

    def ensure_permissions(self, callback) -> None:
        if self._permission_driver.has_required_permissions():
            self.state = "granted"
            callback(True)
            return

        self.state = "requesting"
        self._logger.info("Permission", "requesting Android BLE/location permissions")

        def on_result(granted: bool) -> None:
            self.state = "granted" if granted else "denied"
            self._logger.info("Permission", self.state)
            callback(granted)

        self._permission_driver.request_required_permissions(on_result)
