#pragma once

#include <stdint.h>

namespace Constants {
    constexpr const char* DEVICE_NAME = "BLE-NAV-ESP32-01";

    // Standard Apple iBeacon Prefix (Company ID: 0x004C, Type: 0x02, Length: 0x15)
    constexpr uint16_t IBEACON_COMPANY_ID = 0x004C; 
    
    // Default Proximity UUID (Example UUID: fda50693-a4e2-4fb1-afcf-c6eb07647825)
    constexpr uint8_t IBEACON_PROXIMITY_UUID[16] = {
        0xFD, 0xA5, 0x06, 0x93, 0xA4, 0xE2, 0x4F, 0xB1, 
        0xAF, 0xCF, 0xC6, 0xEB, 0x07, 0x64, 0x78, 0x25
    };
    
    // Beacon Identifier
    constexpr uint16_t BEACON_MAJOR = 1; // e.g., Floor 1
    constexpr uint16_t BEACON_MINOR = 1; // e.g., Room 1

    // Measured Tx Power at 1 meter (2's complement representation of dBm)
    constexpr int8_t MEASURED_POWER = -59;

    constexpr uint16_t ADV_INTERVAL_MIN = 0x00A0; // 100 ms
    constexpr uint16_t ADV_INTERVAL_MAX = 0x00A0; // 100 ms
}
