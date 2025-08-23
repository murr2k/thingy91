/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef BUTTON_HANDLER_H_
#define BUTTON_HANDLER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Button events
 */
enum button_event {
    BUTTON_EVENT_NONE,
    BUTTON_EVENT_PRESS,
    BUTTON_EVENT_RELEASE,
    BUTTON_EVENT_LONG_PRESS,
    BUTTON_EVENT_DOUBLE_PRESS,
    BUTTON_EVENT_TRIPLE_PRESS
};

/**
 * @brief Button IDs
 */
enum button_id {
    BUTTON_1 = 0,
    BUTTON_2,
    BUTTON_3,
    BUTTON_4,
    BUTTON_MAX
};

/**
 * @brief Button configuration
 */
struct button_config {
    uint32_t long_press_time_ms;    /* Long press threshold */
    uint32_t double_press_time_ms;  /* Double press window */
    uint32_t debounce_time_ms;      /* Debounce time */
    bool enable_repeat;             /* Enable key repeat */
    uint32_t repeat_interval_ms;    /* Key repeat interval */
};

/**
 * @brief Button callback function type
 */
typedef void (*button_callback_t)(enum button_id button, enum button_event event);

/**
 * @brief Initialize button handler
 * 
 * @return 0 on success, negative errno on failure
 */
int button_handler_init(void);

/**
 * @brief Configure button behavior
 * 
 * @param config Button configuration
 * @return 0 on success, negative errno on failure
 */
int button_handler_configure(const struct button_config *config);

/**
 * @brief Register button callback
 * 
 * @param callback Callback function for button events
 * @return 0 on success, negative errno on failure
 */
int button_handler_register_callback(button_callback_t callback);

/**
 * @brief Enable or disable button processing
 * 
 * @param enable True to enable, false to disable
 * @return 0 on success, negative errno on failure
 */
int button_handler_enable(bool enable);

/**
 * @brief Get current button state
 * 
 * @param button Button ID
 * @return True if button is pressed, false otherwise
 */
bool button_handler_is_pressed(enum button_id button);

/**
 * @brief Get button press count since last reset
 * 
 * @param button Button ID
 * @return Number of presses
 */
uint32_t button_handler_get_press_count(enum button_id button);

/**
 * @brief Reset button press count
 * 
 * @param button Button ID
 * @return 0 on success, negative errno on failure
 */
int button_handler_reset_press_count(enum button_id button);

/**
 * @brief Test button functionality
 * 
 * @return 0 on success, negative errno on failure
 */
int button_handler_test(void);

#ifdef __cplusplus
}
#endif

#endif /* BUTTON_HANDLER_H_ */