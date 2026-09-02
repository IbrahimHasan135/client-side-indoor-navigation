#pragma once

#include <stdint.h>
#include <esp_gap_ble_api.h>

class BleRadioDriver {
public:
    BleRadioDriver();
    ~BleRadioDriver();

    /**
     * @brief Initialize Bluetooth controller and Bluedroid stack
     */
    void init();

    /**
     * @brief Configure raw advertising data
     * @param raw_data Pointer to raw payload bytes
     * @param raw_data_len Length of the payload
     */
    void set_raw_advertising_data(const uint8_t* raw_data, uint32_t raw_data_len);

    /**
     * @brief Configure raw scan response data
     * @param raw_data Pointer to raw scan response bytes
     * @param raw_data_len Length of the payload
     */
    void set_raw_scan_response_data(const uint8_t* raw_data, uint32_t raw_data_len);

    /**
     * @brief Set BLE device name used by scanners and scan responses
     */
    void set_device_name(const char* device_name);

    /**
     * @brief Start advertising with given parameters
     * @param adv_params Pointer to advertising parameters struct
     */
    void start_advertising(esp_ble_adv_params_t* adv_params);

    /**
     * @brief Stop advertising
     */
    void stop_advertising();

    void on_gap_event(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t* param);

private:
    void try_start_pending_advertising();

    bool is_initialized;
    bool is_adv_data_ready;
    bool is_scan_response_ready;
    bool is_advertising;
    bool has_pending_adv_params;
    esp_ble_adv_params_t pending_adv_params;
};
