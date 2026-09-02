from __future__ import annotations

from kivy.utils import platform


class AndroidBluetoothAdapterDriver:
    """Thin wrapper around Android BluetoothAdapter."""

    def __init__(self) -> None:
        self._is_android = platform == "android"
        self._adapter = self._load_adapter() if self._is_android else None

    def is_supported(self) -> bool:
        return self._adapter is not None

    def is_enabled(self) -> bool:
        try:
            return bool(self._adapter and self._adapter.isEnabled())
        except Exception:
            return False

    def get_ble_scanner(self):
        if not self._adapter:
            return None

        try:
            return self._adapter.getBluetoothLeScanner()
        except Exception:
            return None

    def _load_adapter(self):
        from jnius import autoclass

        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        return BluetoothAdapter.getDefaultAdapter()
