# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(thingy91_demo)

# Source files
target_sources(app PRIVATE
    src/main.c
    src/sensors/sensor_manager.c
    src/sensors/environmental_sensor.c
    src/sensors/motion_sensor.c
    src/connectivity/cellular_manager.c
    src/connectivity/mqtt_client.c
    src/data/data_processor.c
    src/data/data_buffer.c
    src/ui/led_controller.c
    src/ui/button_handler.c
    src/power/power_manager.c
    src/config/config_manager.c
)

# Include directories
target_include_directories(app PRIVATE
    src/
    src/sensors/
    src/connectivity/
    src/data/
    src/ui/
    src/power/
    src/config/
)

# Add compiler definitions
target_compile_definitions(app PRIVATE
    -DCONFIG_THINGY91_DEMO=1
)