/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef LED_CONTROLLER_H_
#define LED_CONTROLLER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief LED states for visual feedback
 */
enum led_state {
    LED_STATE_OFF,
    LED_STATE_INITIALIZING,
    LED_STATE_CONNECTING,
    LED_STATE_CONNECTED,
    LED_STATE_TRANSMITTING,
    LED_STATE_BUFFERING,
    LED_STATE_ERROR,
    LED_STATE_LOW_POWER,
    LED_STATE_CUSTOM
};

/**
 * @brief LED color structure
 */
struct led_color {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
};

/**
 * @brief LED pattern configuration
 */
struct led_pattern {
    enum led_state state;
    struct led_color color;
    uint16_t on_time_ms;        /* LED on duration */
    uint16_t off_time_ms;       /* LED off duration */
    uint8_t repeat_count;       /* Number of repeats, 0 = infinite */
    bool fade_enable;           /* Enable fade effects */
};

/**
 * @brief Initialize LED controller
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_init(void);

/**
 * @brief Set LED to indicate initialization
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_initializing(void);

/**
 * @brief Set LED to indicate connecting state
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_connecting(void);

/**
 * @brief Set LED to indicate connected state
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_connected(void);

/**
 * @brief Indicate data transmission with LED
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_indicate_transmission(void);

/**
 * @brief Indicate data buffering with LED
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_indicate_buffering(void);

/**
 * @brief Set LED to indicate error state
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_error(void);

/**
 * @brief Set LED to indicate low power mode
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_low_power(void);

/**
 * @brief Turn off all LEDs
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_off(void);

/**
 * @brief Set custom LED pattern
 * 
 * @param pattern LED pattern configuration
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_pattern(const struct led_pattern *pattern);

/**
 * @brief Set LED color directly
 * 
 * @param color LED color
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_color(const struct led_color *color);

/**
 * @brief Set LED brightness
 * 
 * @param brightness Brightness level (0-255)
 * @return 0 on success, negative errno on failure
 */
int led_controller_set_brightness(uint8_t brightness);

/**
 * @brief Enable or disable LED controller
 * 
 * @param enable True to enable, false to disable
 * @return 0 on success, negative errno on failure
 */
int led_controller_enable(bool enable);

/**
 * @brief Get current LED state
 * 
 * @return Current LED state
 */
enum led_state led_controller_get_state(void);

/**
 * @brief Test LED functionality
 * 
 * @return 0 on success, negative errno on failure
 */
int led_controller_test(void);

#ifdef __cplusplus
}
#endif

#endif /* LED_CONTROLLER_H_ */