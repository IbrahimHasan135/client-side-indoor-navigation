idf_component_register(
    SRCS "main.cpp"
         "drivers/ble_radio_driver.cpp"
         "services/beacon_service.cpp"
    INCLUDE_DIRS "."
    REQUIRES bt nvs_flash
)
