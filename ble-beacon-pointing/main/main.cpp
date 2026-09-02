#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "drivers/ble_radio_driver.hpp"
#include "services/beacon_service.hpp"
#include "utils/constants.hpp"
#include <esp_log.h>

static const char* TAG = "Controller";

// Objects instantiated in global scope (or could be in app_main)
BleRadioDriver* bleDriver = nullptr;
BeaconService* beaconService = nullptr;

/**
 * @brief Task specifically handling beacon broadcasting logic
 */
void beacon_task(void* pvParameters) {
    ESP_LOGI(TAG, "Beacon Task Started.");

    // The service instructs the driver to start broadcasting
    beaconService->start_broadcasting();

    // Loop infinitely since FreeRTOS tasks must not return unless deleted
    while (1) {
        // Since advertising is handled by the BT controller in the background,
        // this task can simply delay to free up CPU time, or could be used
        // to dynamically update Major/Minor values if needed in the future.
        ESP_LOGI(TAG, "Beacon alive. iBeacon major=%u minor=%u", Constants::BEACON_MAJOR, beaconService->get_beacon_minor());
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}

extern "C" void app_main() {
    ESP_LOGI(TAG, "Booting BLE Beacon...");

    // 1. Instantiate and Initialize Driver
    bleDriver = new BleRadioDriver();
    bleDriver->init();

    // 2. Instantiate Service with Dependency Injection
    beaconService = new BeaconService(bleDriver);

    // 3. Create FreeRTOS Task to handle the Beacon logic
    // Assigning 2048 bytes of stack and a normal priority of 5
    xTaskCreate(
        beacon_task,        // Task function
        "BeaconTask",       // Task name
        2048,               // Stack size
        NULL,               // Parameters
        5,                  // Priority
        NULL                // Task Handle
    );

    ESP_LOGI(TAG, "Controller setup complete. Relinquishing main thread.");
}
