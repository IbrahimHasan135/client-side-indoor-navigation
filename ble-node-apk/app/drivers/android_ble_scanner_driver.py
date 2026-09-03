from __future__ import annotations

from time import monotonic

from kivy.utils import platform

from app.models.ble_advertisement import BleAdvertisement


class AndroidBleScannerDriver:
    """Android BLE scanner driver through a tiny Java ScanCallback bridge."""

    def __init__(self, bluetooth_adapter_driver) -> None:
        self._bluetooth_adapter_driver = bluetooth_adapter_driver
        self._advertisement_callback = None
        self._error_callback = None
        self._scan_callback = None
        self._bridge = None
        self._is_scanning = False

    def set_advertisement_callback(self, callback) -> None:
        self._advertisement_callback = callback

    def set_error_callback(self, callback) -> None:
        self._error_callback = callback

    def start_scan(self) -> None:
        if self._is_scanning:
            return

        if platform != "android":
            self._emit_error("BLE scan hanya tersedia saat APK berjalan di Android.")
            return

        if not self._bluetooth_adapter_driver.is_supported():
            self._emit_error("Bluetooth adapter tidak tersedia.")
            return

        if not self._bluetooth_adapter_driver.is_enabled():
            self._emit_error("Bluetooth Android belum aktif.")
            return

        self._scan_callback = self._create_scan_listener()
        self._bridge = self._create_bridge(self._scan_callback)
        self._bridge.start()
        self._is_scanning = True

    def stop_scan(self) -> None:
        if self._bridge and self._is_scanning:
            try:
                self._bridge.stop()
            except Exception as exc:
                self._emit_error(f"Android BLE stop ignored: {exc}")

        self._is_scanning = False

    def _create_bridge(self, listener):
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        BleScanBridge = autoclass("org.indoor.navigation.BleScanBridge")
        return BleScanBridge(PythonActivity.mActivity.getApplicationContext(), listener)

    def _create_scan_listener(self):
        from jnius import PythonJavaClass, java_method

        outer = self

        class BleAdvertisementListener(PythonJavaClass):
            __javainterfaces__ = ["org/indoor/navigation/BleAdvertisementListener"]
            __javacontext__ = "app"

            @java_method("(Ljava/lang/String;Ljava/lang/String;II[I[[B)V")
            def onAdvertisement(self, address, name, rssi, tx_power, manufacturer_ids, manufacturer_payloads):
                try:
                    outer._handle_scan_result(address, name, rssi, tx_power, manufacturer_ids, manufacturer_payloads)
                except Exception as exc:
                    outer._emit_error(f"BLE callback parse error: {exc}")

            @java_method("(I)V")
            def onScanFailed(self, error_code):
                outer._emit_error(f"Android BLE scan failed, error_code={error_code}")

        return BleAdvertisementListener()

    def _handle_scan_result(self, address, name, rssi, tx_power, manufacturer_ids, manufacturer_payloads) -> None:
        if not self._advertisement_callback:
            return

        advertisement = BleAdvertisement(
            address=str(address or ""),
            name=str(name) if name else None,
            rssi=int(rssi),
            tx_power=None if int(tx_power) == -2147483648 else int(tx_power),
            manufacturer_data=self._get_manufacturer_data(manufacturer_ids, manufacturer_payloads),
            service_data={},
            timestamp_ms=int(monotonic() * 1000),
        )
        self._advertisement_callback(advertisement)

    def _get_manufacturer_data(self, manufacturer_ids, manufacturer_payloads) -> dict[int, bytes]:
        data = {}
        if manufacturer_ids is None or manufacturer_payloads is None:
            return data

        count = min(len(manufacturer_ids), len(manufacturer_payloads))
        for index in range(count):
            data[int(manufacturer_ids[index])] = self._java_bytes_to_python(manufacturer_payloads[index])
        return data

    def _java_bytes_to_python(self, java_bytes) -> bytes:
        if java_bytes is None:
            return b""

        return bytes((int(byte) + 256) % 256 for byte in java_bytes)

    def _emit_error(self, message: str) -> None:
        if self._error_callback:
            self._error_callback(message)
