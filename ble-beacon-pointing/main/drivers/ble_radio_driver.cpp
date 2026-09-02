#include "ble_radio_driver.hpp"
#include <esp_bt.h>
#include <esp_bt_main.h>
#include <nvs_flash.h>
#include <esp_log.h>
#include <string.h>

static const char* TAG = "BleRadioDriver";
static BleRadioDriver* active_driver = nullptr;

static void gap_event_handler(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t* param) {
    if (active_driver) {
        active_driver->on_gap_event(event, param);
    }
}

BleRadioDriver::BleRadioDriver()
    : is_initialized(false),
      is_adv_data_ready(false),
      is_scan_response_ready(false),
      is_advertising(false),
      has_pending_adv_params(false),
      pending_adv_params{} {}

BleRadioDriver::~BleRadioDriver() {
    if (is_initialized) {
        esp_ble_gap_stop_advertising();
        esp_bluedroid_disable();
        esp_bluedroid_deinit();
        esp_bt_controller_disable();
        esp_bt_controller_deinit();
    }
    if (active_driver == this) {
        active_driver = nullptr;
    }
}

void BleRadioDriver::init() {
    // Initialize NVS (required by BT controller)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    #pragma GCC diagnostic push
    #pragma GCC diagnostic ignored "-Wmissing-field-initializers"
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    #pragma GCC diagnostic pop
    ret = esp_bt_controller_init(&bt_cfg);
    if (ret) {
        ESP_LOGE(TAG, "BT controller init failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_bt_controller_enable(ESP_BT_MODE_BLE);
    if (ret) {
        ESP_LOGE(TAG, "BT controller enable failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_bluedroid_init();
    if (ret) {
        ESP_LOGE(TAG, "Bluedroid init failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = esp_bluedroid_enable();
    if (ret) {
        ESP_LOGE(TAG, "Bluedroid enable failed: %s", esp_err_to_name(ret));
        return;
    }

    active_driver = this;
    ret = esp_ble_gap_register_callback(gap_event_handler);
    if (ret) {
        ESP_LOGE(TAG, "GAP callback register failed: %s", esp_err_to_name(ret));
        return;
    }
    
    // Set max TX power for better range
    esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_P9);

    is_initialized = true;
    ESP_LOGI(TAG, "BLE Radio initialized successfully");
}

void BleRadioDriver::set_raw_advertising_data(const uint8_t* raw_data, uint32_t raw_data_len) {
    if (!is_initialized) return;
    is_adv_data_ready = false;
    esp_err_t ret = esp_ble_gap_config_adv_data_raw(const_cast<uint8_t*>(raw_data), raw_data_len);
    if (ret) {
        ESP_LOGE(TAG, "Advertising data config failed: %s", esp_err_to_name(ret));
    }
}

void BleRadioDriver::set_raw_scan_response_data(const uint8_t* raw_data, uint32_t raw_data_len) {
    if (!is_initialized) return;
    is_scan_response_ready = false;
    esp_err_t ret = esp_ble_gap_config_scan_rsp_data_raw(const_cast<uint8_t*>(raw_data), raw_data_len);
    if (ret) {
        ESP_LOGE(TAG, "Scan response config failed: %s", esp_err_to_name(ret));
    }
}

void BleRadioDriver::set_device_name(const char* device_name) {
    if (!is_initialized) return;
    esp_err_t ret = esp_ble_gap_set_device_name(device_name);
    if (ret) {
        ESP_LOGE(TAG, "Device name config failed: %s", esp_err_to_name(ret));
    }
}

void BleRadioDriver::start_advertising(esp_ble_adv_params_t* adv_params) {
    if (!is_initialized) return;
    memcpy(&pending_adv_params, adv_params, sizeof(esp_ble_adv_params_t));
    has_pending_adv_params = true;
    try_start_pending_advertising();
}

void BleRadioDriver::stop_advertising() {
    if (!is_initialized) return;
    esp_ble_gap_stop_advertising();
    is_advertising = false;
    ESP_LOGI(TAG, "BLE Advertising stopped");
}

void BleRadioDriver::on_gap_event(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t* param) {
    switch (event) {
        case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT:
            if (param->adv_data_raw_cmpl.status == ESP_BT_STATUS_SUCCESS) {
                is_adv_data_ready = true;
                ESP_LOGI(TAG, "Advertising data configured");
                try_start_pending_advertising();
            } else {
                ESP_LOGE(TAG, "Advertising data rejected: %d", param->adv_data_raw_cmpl.status);
            }
            break;

        case ESP_GAP_BLE_SCAN_RSP_DATA_RAW_SET_COMPLETE_EVT:
            if (param->scan_rsp_data_raw_cmpl.status == ESP_BT_STATUS_SUCCESS) {
                is_scan_response_ready = true;
                ESP_LOGI(TAG, "Scan response configured");
                try_start_pending_advertising();
            } else {
                ESP_LOGE(TAG, "Scan response rejected: %d", param->scan_rsp_data_raw_cmpl.status);
            }
            break;

        case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
            if (param->adv_start_cmpl.status == ESP_BT_STATUS_SUCCESS) {
                is_advertising = true;
                ESP_LOGI(TAG, "BLE Advertising started");
            } else {
                ESP_LOGE(TAG, "Advertising start failed: %d", param->adv_start_cmpl.status);
            }
            break;

        case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
            is_advertising = false;
            break;

        default:
            break;
    }
}

void BleRadioDriver::try_start_pending_advertising() {
    if (!has_pending_adv_params || is_advertising || !is_adv_data_ready || !is_scan_response_ready) {
        return;
    }

    esp_err_t ret = esp_ble_gap_start_advertising(&pending_adv_params);
    if (ret) {
        ESP_LOGE(TAG, "Advertising start request failed: %s", esp_err_to_name(ret));
        return;
    }

    has_pending_adv_params = false;
}
