/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "button_handler.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <dk_buttons_and_leds.h>

LOG_MODULE_REGISTER(button_handler, CONFIG_LOG_DEFAULT_LEVEL);

/* Button configuration */
static struct button_config config = {
    .long_press_time_ms = 2000,
    .double_press_time_ms = 500,
    .debounce_time_ms = 50,
    .enable_repeat = false,
    .repeat_interval_ms = 200
};

/* Button state tracking */
struct button_state {
    bool is_pressed;
    bool last_state;
    uint64_t press_time;
    uint64_t release_time;
    uint32_t press_count;
    uint8_t consecutive_presses;
    bool long_press_triggered;
    bool debounce_active;
};

static struct button_state buttons[BUTTON_MAX];
static button_callback_t event_callback = NULL;
static bool handler_enabled = true;

/* Work items for button processing */
static struct k_work_delayable button_work[BUTTON_MAX];
static struct k_work_delayable double_press_work[BUTTON_MAX];

/* Forward declarations */
static void button_work_handler(struct k_work *work);
static void double_press_work_handler(struct k_work *work);
static void dk_button_callback(uint32_t button_state, uint32_t has_changed);
static void process_button_event(enum button_id button, bool pressed);
static void trigger_button_event(enum button_id button, enum button_event event);

static void button_work_handler(struct k_work *work)
{
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);
    enum button_id button = dwork - button_work;
    
    if (button >= BUTTON_MAX) {
        return;
    }
    
    struct button_state *state = &buttons[button];
    uint64_t current_time = k_uptime_get();
    
    /* Check for long press */
    if (state->is_pressed && !state->long_press_triggered) {
        if (current_time - state->press_time >= config.long_press_time_ms) {
            state->long_press_triggered = true;
            trigger_button_event(button, BUTTON_EVENT_LONG_PRESS);
            LOG_DBG("Button %d long press detected", button);
        } else {
            /* Reschedule to check again */
            k_work_reschedule(&button_work[button], 
                             K_MSEC(config.long_press_time_ms - (current_time - state->press_time)));
        }
    }
    
    /* Handle key repeat if enabled */
    if (config.enable_repeat && state->is_pressed && state->long_press_triggered) {
        trigger_button_event(button, BUTTON_EVENT_PRESS);
        k_work_reschedule(&button_work[button], K_MSEC(config.repeat_interval_ms));
    }
}

static void double_press_work_handler(struct k_work *work)
{
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);
    enum button_id button = dwork - double_press_work;
    
    if (button >= BUTTON_MAX) {
        return;
    }
    
    struct button_state *state = &buttons[button];
    
    /* Process accumulated presses */
    if (state->consecutive_presses == 1) {
        trigger_button_event(button, BUTTON_EVENT_PRESS);
    } else if (state->consecutive_presses == 2) {
        trigger_button_event(button, BUTTON_EVENT_DOUBLE_PRESS);
    } else if (state->consecutive_presses >= 3) {
        trigger_button_event(button, BUTTON_EVENT_TRIPLE_PRESS);
    }
    
    state->consecutive_presses = 0;
}

static void dk_button_callback(uint32_t button_state, uint32_t has_changed)
{
    if (!handler_enabled) {
        return;
    }
    
    /* Process each button */
    for (int i = 0; i < BUTTON_MAX && i < 4; i++) {  /* DK supports up to 4 buttons */
        uint32_t button_mask = BIT(i);
        
        if (has_changed & button_mask) {
            bool pressed = (button_state & button_mask) != 0;
            process_button_event((enum button_id)i, pressed);
        }
    }
}

static void process_button_event(enum button_id button, bool pressed)
{
    if (button >= BUTTON_MAX) {
        return;
    }
    
    struct button_state *state = &buttons[button];
    uint64_t current_time = k_uptime_get();
    
    /* Debounce check */
    if (state->debounce_active && 
        current_time - state->release_time < config.debounce_time_ms) {
        return;
    }
    
    state->debounce_active = false;
    
    if (pressed && !state->last_state) {
        /* Button press detected */
        state->is_pressed = true;
        state->press_time = current_time;
        state->press_count++;
        state->long_press_triggered = false;
        
        /* Cancel any pending double-press timeout */
        k_work_cancel_delayable(&double_press_work[button]);
        
        /* Count consecutive presses */
        if (current_time - state->release_time <= config.double_press_time_ms) {
            state->consecutive_presses++;
        } else {
            state->consecutive_presses = 1;
        }
        
        /* Start long press detection */
        k_work_schedule(&button_work[button], K_MSEC(config.long_press_time_ms));
        
        LOG_DBG("Button %d pressed (consecutive: %d)", button, state->consecutive_presses);
        
    } else if (!pressed && state->last_state) {
        /* Button release detected */
        state->is_pressed = false;
        state->release_time = current_time;
        state->debounce_active = true;
        
        /* Cancel long press detection */
        k_work_cancel_delayable(&button_work[button]);
        
        /* If it was a long press, don't process as normal press */
        if (!state->long_press_triggered) {
            /* Start double-press timeout */
            k_work_schedule(&double_press_work[button], K_MSEC(config.double_press_time_ms));
        }
        
        trigger_button_event(button, BUTTON_EVENT_RELEASE);
        LOG_DBG("Button %d released", button);
    }
    
    state->last_state = pressed;
}

static void trigger_button_event(enum button_id button, enum button_event event)
{
    if (event_callback) {
        event_callback(button, event);
    }
    
    LOG_DBG("Button %d event: %d", button, event);
}

int button_handler_init(void)
{
    LOG_INF("Initializing button handler");
    
    /* Initialize button states */
    for (int i = 0; i < BUTTON_MAX; i++) {
        memset(&buttons[i], 0, sizeof(buttons[i]));
        k_work_init_delayable(&button_work[i], button_work_handler);
        k_work_init_delayable(&double_press_work[i], double_press_work_handler);
    }
    
    /* Initialize DK buttons */
    int ret = dk_buttons_init(dk_button_callback);
    if (ret) {
        LOG_ERR("Failed to initialize DK buttons: %d", ret);
        return ret;
    }
    
    handler_enabled = true;
    
    LOG_INF("Button handler initialized successfully");
    return 0;
}

int button_handler_configure(const struct button_config *new_config)
{
    if (!new_config) {
        return -EINVAL;
    }
    
    memcpy(&config, new_config, sizeof(config));
    
    LOG_INF("Button handler configured - Long press: %d ms, Double press: %d ms, "
            "Debounce: %d ms, Repeat: %s",
            config.long_press_time_ms, config.double_press_time_ms, 
            config.debounce_time_ms, config.enable_repeat ? "enabled" : "disabled");
    
    return 0;
}

int button_handler_register_callback(button_callback_t callback)
{
    event_callback = callback;
    LOG_INF("Button callback registered");
    return 0;
}

int button_handler_enable(bool enable)
{
    handler_enabled = enable;
    
    if (!enable) {
        /* Cancel all pending work */
        for (int i = 0; i < BUTTON_MAX; i++) {
            k_work_cancel_delayable(&button_work[i]);
            k_work_cancel_delayable(&double_press_work[i]);
        }
        
        /* Reset button states */
        for (int i = 0; i < BUTTON_MAX; i++) {
            buttons[i].is_pressed = false;
            buttons[i].last_state = false;
            buttons[i].consecutive_presses = 0;
            buttons[i].long_press_triggered = false;
            buttons[i].debounce_active = false;
        }
    }
    
    LOG_INF("Button handler %s", enable ? "enabled" : "disabled");
    return 0;
}

bool button_handler_is_pressed(enum button_id button)
{
    if (button >= BUTTON_MAX) {
        return false;
    }
    
    return buttons[button].is_pressed;
}

uint32_t button_handler_get_press_count(enum button_id button)
{
    if (button >= BUTTON_MAX) {
        return 0;
    }
    
    return buttons[button].press_count;
}

int button_handler_reset_press_count(enum button_id button)
{
    if (button >= BUTTON_MAX) {
        return -EINVAL;
    }
    
    buttons[button].press_count = 0;
    LOG_DBG("Button %d press count reset", button);
    return 0;
}

int button_handler_test(void)
{
    LOG_INF("Button handler test - Press buttons to see events");
    LOG_INF("Button 1: Trigger sensor reading");
    LOG_INF("Button 2: Toggle power mode");
    LOG_INF("Button 3: LED test");
    LOG_INF("Button 4: System info");
    
    /* Test callback */
    static bool test_active = false;
    
    if (!test_active) {
        test_active = true;
        
        /* Register test callback */
        button_callback_t original_callback = event_callback;
        
        event_callback = [](enum button_id button, enum button_event event) {
            LOG_INF("TEST: Button %d, Event %d", button, event);
        };
        
        /* Wait for button presses */
        k_msleep(10000);  /* 10 second test window */
        
        /* Restore original callback */
        event_callback = original_callback;
        test_active = false;
        
        LOG_INF("Button handler test completed");
    }
    
    return 0;
}