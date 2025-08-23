/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <dk_buttons_and_leds.h>

#include "sensors/sensor_manager.h"
#include "connectivity/cellular_manager.h"
#include "connectivity/mqtt_client.h"
#include "data/data_processor.h"
#include "ui/led_controller.h"
#include "ui/button_handler.h"
#include "power/power_manager.h"
#include "config/config_manager.h"

LOG_MODULE_REGISTER(main, CONFIG_LOG_DEFAULT_LEVEL);

/* Application states */
enum app_state {
    APP_STATE_INIT,
    APP_STATE_CELLULAR_CONNECTING,
    APP_STATE_MQTT_CONNECTING,
    APP_STATE_RUNNING,
    APP_STATE_ERROR,
    APP_STATE_SLEEP
};

static enum app_state current_state = APP_STATE_INIT;
static struct k_work_delayable main_work;
static struct k_work_delayable sensor_work;

/* Forward declarations */
static void main_work_handler(struct k_work *work);
static void sensor_work_handler(struct k_work *work);
static void state_machine_update(void);
static void handle_sensor_data(const struct sensor_data *data);

/* Work handlers */
static void main_work_handler(struct k_work *work)
{
    state_machine_update();
    
    /* Schedule next state machine update */
    k_work_schedule(&main_work, K_SECONDS(1));
}

static void sensor_work_handler(struct k_work *work)
{
    struct sensor_data data;
    int ret;
    
    if (current_state != APP_STATE_RUNNING) {
        goto schedule_next;
    }
    
    /* Read sensor data */
    ret = sensor_manager_read_all(&data);
    if (ret == 0) {
        handle_sensor_data(&data);
    } else {
        LOG_WRN("Failed to read sensor data: %d", ret);
        led_controller_set_error();
    }

schedule_next:
    /* Schedule next sensor reading */
    k_work_schedule(&sensor_work, K_MSEC(CONFIG_THINGY91_DEMO_SENSOR_INTERVAL_MS));
}

static void handle_sensor_data(const struct sensor_data *data)
{
    char json_buffer[512];
    int ret;
    
    LOG_INF("Sensor data - Temp: %.2f°C, Humidity: %.2f%%, Pressure: %.2f hPa",
            data->temperature, data->humidity, data->pressure);
    LOG_INF("Motion - X: %.2f, Y: %.2f, Z: %.2f", 
            data->accel_x, data->accel_y, data->accel_z);
    
    /* Process and format data */
    ret = data_processor_format_json(data, json_buffer, sizeof(json_buffer));
    if (ret < 0) {
        LOG_ERR("Failed to format sensor data as JSON: %d", ret);
        return;
    }
    
    /* Buffer data for transmission */
    ret = data_processor_buffer_data(json_buffer);
    if (ret < 0) {
        LOG_ERR("Failed to buffer data: %d", ret);
        return;
    }
    
    /* Attempt to transmit if connected */
    if (mqtt_client_is_connected()) {
        ret = mqtt_client_publish_data(json_buffer);
        if (ret == 0) {
            led_controller_indicate_transmission();
            LOG_INF("Data transmitted successfully");
        } else {
            LOG_WRN("Failed to transmit data: %d", ret);
        }
    } else {
        LOG_INF("MQTT not connected, data buffered");
        led_controller_indicate_buffering();
    }
}

static void state_machine_update(void)
{
    enum app_state next_state = current_state;
    
    switch (current_state) {
    case APP_STATE_INIT:
        if (cellular_manager_is_ready()) {
            next_state = APP_STATE_CELLULAR_CONNECTING;
            led_controller_set_connecting();
        }
        break;
        
    case APP_STATE_CELLULAR_CONNECTING:
        if (cellular_manager_is_connected()) {
            next_state = APP_STATE_MQTT_CONNECTING;
        } else if (cellular_manager_has_error()) {
            next_state = APP_STATE_ERROR;
            led_controller_set_error();
        }
        break;
        
    case APP_STATE_MQTT_CONNECTING:
        if (mqtt_client_is_connected()) {
            next_state = APP_STATE_RUNNING;
            led_controller_set_connected();
            LOG_INF("Application ready - starting sensor readings");
        } else if (mqtt_client_has_error()) {
            next_state = APP_STATE_ERROR;
            led_controller_set_error();
        }
        break;
        
    case APP_STATE_RUNNING:
        if (!cellular_manager_is_connected()) {
            next_state = APP_STATE_CELLULAR_CONNECTING;
            led_controller_set_connecting();
        } else if (!mqtt_client_is_connected()) {
            next_state = APP_STATE_MQTT_CONNECTING;
        }
        break;
        
    case APP_STATE_ERROR:
        /* Stay in error state until manual reset */
        break;
        
    case APP_STATE_SLEEP:
        /* Wake up handling would be implemented here */
        break;
    }
    
    if (next_state != current_state) {
        LOG_INF("State transition: %d -> %d", current_state, next_state);
        current_state = next_state;
    }
}

static void button_callback(uint32_t button_state, uint32_t has_changed)
{
    if (has_changed & DK_BTN1_MSK) {
        if (button_state & DK_BTN1_MSK) {
            LOG_INF("Button 1 pressed - triggering immediate sensor reading");
            k_work_reschedule(&sensor_work, K_NO_WAIT);
        }
    }
    
    if (has_changed & DK_BTN2_MSK) {
        if (button_state & DK_BTN2_MSK) {
            LOG_INF("Button 2 pressed - toggling power mode");
            power_manager_toggle_power_mode();
        }
    }
}

int main(void)
{
    int ret;
    
    LOG_INF("Nordic Thingy91 Demo Application Starting");
    LOG_INF("Build time: " __DATE__ " " __TIME__);
    
    /* Initialize DK library for buttons and LEDs */
    ret = dk_buttons_init(button_callback);
    if (ret) {
        LOG_ERR("Failed to initialize buttons: %d", ret);
        return ret;
    }
    
    ret = dk_leds_init();
    if (ret) {
        LOG_ERR("Failed to initialize LEDs: %d", ret);
        return ret;
    }
    
    /* Initialize application modules */
    ret = config_manager_init();
    if (ret) {
        LOG_ERR("Failed to initialize config manager: %d", ret);
        return ret;
    }
    
    ret = power_manager_init();
    if (ret) {
        LOG_ERR("Failed to initialize power manager: %d", ret);
        return ret;
    }
    
    ret = led_controller_init();
    if (ret) {
        LOG_ERR("Failed to initialize LED controller: %d", ret);
        return ret;
    }
    
    ret = data_processor_init();
    if (ret) {
        LOG_ERR("Failed to initialize data processor: %d", ret);
        return ret;
    }
    
    ret = sensor_manager_init();
    if (ret) {
        LOG_ERR("Failed to initialize sensor manager: %d", ret);
        return ret;
    }
    
    ret = cellular_manager_init();
    if (ret) {
        LOG_ERR("Failed to initialize cellular manager: %d", ret);
        return ret;
    }
    
    ret = mqtt_client_init();
    if (ret) {
        LOG_ERR("Failed to initialize MQTT client: %d", ret);
        return ret;
    }
    
    /* Initialize work items */
    k_work_init_delayable(&main_work, main_work_handler);
    k_work_init_delayable(&sensor_work, sensor_work_handler);
    
    /* Start the application */
    led_controller_set_initializing();
    LOG_INF("Application initialized successfully");
    
    /* Start main state machine */
    k_work_schedule(&main_work, K_SECONDS(1));
    
    /* Start sensor readings */
    k_work_schedule(&sensor_work, K_SECONDS(5));
    
    return 0;
}