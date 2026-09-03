from __future__ import annotations

DEVICE_NAME_PREFIX = "BLE-NAV-ESP32"
IBEACON_COMPANY_ID = 0x004C
IBEACON_UUID = bytes(
    [
        0xFD,
        0xA5,
        0x06,
        0x93,
        0xA4,
        0xE2,
        0x4F,
        0xB1,
        0xAF,
        0xCF,
        0xC6,
        0xEB,
        0x07,
        0x64,
        0x78,
        0x25,
    ]
)

RSSI_EMA_ALPHA = 0.25
MEASURED_POWER_AT_1M_DBM = -42
PATH_LOSS_EXPONENT = 3.0
ANCHOR_STALE_AFTER_MS = 3500
UI_REFRESH_INTERVAL_SEC = 0.25

ANCHOR_POSITIONS_M = {
    "1:1": (0.0, 0.0),
}
