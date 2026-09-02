from __future__ import annotations

from kivy.utils import platform


class AndroidPermissionDriver:
    """Request Android runtime permissions without touching UI widgets."""

    def __init__(self) -> None:
        self._is_android = platform == "android"
        self._permissions = self._load_permissions()

    def required_permissions(self) -> list[str]:
        if not self._is_android:
            return []

        return [
            self._permission_value("BLUETOOTH_SCAN", "android.permission.BLUETOOTH_SCAN"),
            self._permission_value("BLUETOOTH_CONNECT", "android.permission.BLUETOOTH_CONNECT"),
            self._permission_value("ACCESS_FINE_LOCATION", "android.permission.ACCESS_FINE_LOCATION"),
            self._permission_value("ACCESS_COARSE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"),
        ]

    def has_required_permissions(self) -> bool:
        if not self._is_android:
            return False

        from android.permissions import check_permission

        return all(check_permission(permission) for permission in self.required_permissions())

    def request_required_permissions(self, callback) -> None:
        if not self._is_android:
            callback(False)
            return

        from android.permissions import request_permissions

        permissions = self.required_permissions()

        def on_result(_permissions, grants):
            callback(all(grants))

        request_permissions(permissions, on_result)

    def _load_permissions(self):
        if not self._is_android:
            return None

        from android.permissions import Permission

        return Permission

    def _permission_value(self, name: str, fallback: str) -> str:
        return getattr(self._permissions, name, fallback)
