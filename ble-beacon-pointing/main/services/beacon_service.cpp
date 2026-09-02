#include "beacon_service.hpp"
#include "utils/constants.hpp"
#include <string.h>
#include <algorithm>
#include <esp_mac.h>

BeaconService::BeaconService(BleRadioDriver* driver) : ble_driver(driver) {}

uint16_t BeaconService::get_beacon_minor() const {
    uint8_t ble_mac[6] = {};
    if (esp_read_mac(ble_mac, ESP_MAC_BT) != ESP_OK) {
        return Constants::BEACON_MINOR;
    }

    return (static_cast<uint16_t>(ble_mac[4]) << 8) | ble_mac[5];
}

void BeaconService::build_ibeacon_payload(uint8_t* payload_buffer) {
    // iBeacon Packet Structure (30 bytes total, 31 max)
    const uint16_t beacon_minor = get_beacon_minor();
    
    // BLE Advertising Header
    payload_buffer[0] = 0x02; // Length of Flags
    payload_buffer[1] = 0x01; // Type = Flags
    payload_buffer[2] = 0x06; // LE General Discoverable Mode, BR/EDR Not Supported

    // iBeacon specific data
    payload_buffer[3] = 0x1A; // Length of following data (26 bytes)
    payload_buffer[4] = 0xFF; // Manufacturer Specific Data Type

    // Company ID (Apple = 0x004C)
    payload_buffer[5] = (Constants::IBEACON_COMPANY_ID & 0xFF);
    payload_buffer[6] = (Constants::IBEACON_COMPANY_ID >> 8);

    // iBeacon Type (0x02) and Length (0x15 = 21 bytes)
    payload_buffer[7] = 0x02;
    payload_buffer[8] = 0x15;

    // Proximity UUID (16 bytes)
    memcpy(&payload_buffer[9], Constants::IBEACON_PROXIMITY_UUID, 16);

    // Major (2 bytes, Big Endian)
    payload_buffer[25] = (Constants::BEACON_MAJOR >> 8);
    payload_buffer[26] = (Constants::BEACON_MAJOR & 0xFF);

    // Minor (2 bytes, Big Endian)
    payload_buffer[27] = (beacon_minor >> 8);
    payload_buffer[28] = (beacon_minor & 0xFF);

    // Tx Power (Measured Power at 1m)
    payload_buffer[29] = Constants::MEASURED_POWER;
}

uint8_t BeaconService::build_scan_response_payload(uint8_t* payload_buffer, uint8_t buffer_len) {
    const size_t name_len = strlen(Constants::DEVICE_NAME);
    const uint8_t max_name_len = buffer_len > 2 ? buffer_len - 2 : 0;
    const uint8_t used_name_len = std::min(static_cast<uint8_t>(name_len), max_name_len);

    payload_buffer[0] = used_name_len + 1;
    payload_buffer[1] = 0x09; // Complete Local Name
    memcpy(&payload_buffer[2], Constants::DEVICE_NAME, used_name_len);

    return used_name_len + 2;
}

void BeaconService::start_broadcasting() {
    if (!ble_driver) return;

    // 1. Build Payload
    uint8_t raw_adv_data[30];
    build_ibeacon_payload(raw_adv_data);

    uint8_t raw_scan_response[31];
    const uint8_t scan_response_len = build_scan_response_payload(raw_scan_response, sizeof(raw_scan_response));

    // 2. Set raw data to driver
    ble_driver->set_device_name(Constants::DEVICE_NAME);
    ble_driver->set_raw_advertising_data(raw_adv_data, sizeof(raw_adv_data));
    ble_driver->set_raw_scan_response_data(raw_scan_response, scan_response_len);

    // 3. Configure advertising parameters
    esp_ble_adv_params_t adv_params = {};
    adv_params.adv_int_min       = Constants::ADV_INTERVAL_MIN;
    adv_params.adv_int_max       = Constants::ADV_INTERVAL_MAX;
    adv_params.adv_type          = ADV_TYPE_NONCONN_IND; // Passive iBeacon advertising, no GATT connection
    adv_params.own_addr_type     = BLE_ADDR_TYPE_PUBLIC;
    adv_params.channel_map       = ADV_CHNL_ALL;
    adv_params.adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY;

    // 4. Instruct driver to start
    ble_driver->start_advertising(&adv_params);
}
