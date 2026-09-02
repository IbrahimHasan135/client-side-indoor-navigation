#pragma once

#include "drivers/ble_radio_driver.hpp"

class BeaconService {
public:
    /**
     * @brief Construct a new Beacon Service object via dependency injection
     * @param driver Pointer to the BLE Radio Driver
     */
    BeaconService(BleRadioDriver* driver);
    
    /**
     * @brief Setup beacon payload and start broadcasting
     */
    void start_broadcasting();

    /**
     * @brief Derive a stable per-board iBeacon minor from the ESP BLE MAC.
     */
    uint16_t get_beacon_minor() const;

private:
    BleRadioDriver* ble_driver;
    
    /**
     * @brief Helper to construct iBeacon packet
     */
    void build_ibeacon_payload(uint8_t* payload_buffer);

    /**
     * @brief Helper to construct scan response with device name
     */
    uint8_t build_scan_response_payload(uint8_t* payload_buffer, uint8_t buffer_len);
};
