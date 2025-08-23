/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "led_controller.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>
#include <dk_buttons_and_leds.h>

LOG_MODULE_REGISTER(led_controller, CONFIG_LOG_DEFAULT_LEVEL);

/* LED state management */
static enum led_state current_state = LED_STATE_OFF;
static bool controller_enabled = true;
static uint8_t current_brightness = 255;

/* LED patterns for different states */
static const struct led_pattern default_patterns[] = {
    [LED_STATE_OFF] = {
        .state = LED_STATE_OFF,
        .color = {0, 0, 0},
        .on_time_ms = 0,
        .off_time_ms = 0,
        .repeat_count = 0,
        .fade_enable = false
    },
    [LED_STATE_INITIALIZING] = {
        .state = LED_STATE_INITIALIZING,
        .color = {255, 255, 0},  /* Yellow */
        .on_time_ms = 500,
        .off_time_ms = 500,
        .repeat_count = 0,       /* Continuous */
        .fade_enable = true
    },
    [LED_STATE_CONNECTING] = {
        .state = LED_STATE_CONNECTING,
        .color = {0, 0, 255},    /* Blue */
        .on_time_ms = 200,
        .off_time_ms = 800,
        .repeat_count = 0,       /* Continuous */
        .fade_enable = false
    },
    [LED_STATE_CONNECTED] = {
        .state = LED_STATE_CONNECTED,
        .color = {0, 255, 0},    /* Green */
        .on_time_ms = 1000,
        .off_time_ms = 0,
        .repeat_count = 1,       /* Solid */
        .fade_enable = false
    },
    [LED_STATE_TRANSMITTING] = {
        .state = LED_STATE_TRANSMITTING,
        .color = {0, 255, 255},  /* Cyan */
        .on_time_ms = 100,
        .off_time_ms = 0,
        .repeat_count = 1,       /* Brief flash */
        .fade_enable = false
    },
    [LED_STATE_BUFFERING] = {
        .state = LED_STATE_BUFFERING,
        .color = {255, 165, 0},  /* Orange */
        .on_time_ms = 250,
        .off_time_ms = 250,
        .repeat_count = 2,       /* Two blinks */
        .fade_enable = false
    },
    [LED_STATE_ERROR] = {
        .state = LED_STATE_ERROR,
        .color = {255, 0, 0},    /* Red */
        .on_time_ms = 100,
        .off_time_ms = 100,
        .repeat_count = 0,       /* Continuous fast blink */
        .fade_enable = false
    },
    [LED_STATE_LOW_POWER] = {
        .state = LED_STATE_LOW_POWER,
        .color = {100, 0, 100},  /* Dim purple */
        .on_time_ms = 2000,
        .off_time_ms = 8000,
        .repeat_count = 0,       /* Slow blink */
        .fade_enable = true
    }
};

/* Current pattern and animation state */
static struct led_pattern current_pattern;
static struct k_work_delayable led_work;
static uint8_t animation_step = 0;
static uint8_t repeat_counter = 0;
static bool animation_active = false;

/* Forward declarations */
static void led_work_handler(struct k_work *work);
static int set_led_color_internal(const struct led_color *color);
static int apply_brightness(struct led_color *color, uint8_t brightness);
static void start_animation(const struct led_pattern *pattern);
static void stop_animation(void);

static void led_work_handler(struct k_work *work)
{
    if (!controller_enabled || !animation_active) {
        return;
    }
    
    int delay_ms = 0;
    
    switch (animation_step) {
    case 0: /* LED on phase */
        if (current_pattern.on_time_ms > 0) {
            struct led_color adjusted_color = current_pattern.color;
            apply_brightness(&adjusted_color, current_brightness);
            set_led_color_internal(&adjusted_color);
            delay_ms = current_pattern.on_time_ms;
            animation_step = 1;
        } else {
            /* Solid color, no animation needed */
            struct led_color adjusted_color = current_pattern.color;
            apply_brightness(&adjusted_color, current_brightness);
            set_led_color_internal(&adjusted_color);
            animation_active = false;
            return;
        }
        break;
        
    case 1: /* LED off phase */
        if (current_pattern.off_time_ms > 0) {
            struct led_color off_color = {0, 0, 0};
            set_led_color_internal(&off_color);
            delay_ms = current_pattern.off_time_ms;
        } else {
            delay_ms = 100; /* Small delay for next cycle */
        }
        
        animation_step = 0;
        repeat_counter++;
        
        /* Check if animation should stop */
        if (current_pattern.repeat_count > 0 && 
            repeat_counter >= current_pattern.repeat_count) {
            animation_active = false;
            return;
        }
        break;
        
    default:
        animation_step = 0;
        break;
    }
    
    /* Schedule next animation step */
    if (animation_active) {
        k_work_schedule(&led_work, K_MSEC(delay_ms));
    }
}

static int set_led_color_internal(const struct led_color *color)
{
    if (!color) {
        return -EINVAL;
    }
    
    /* Use DK LED functions for basic LED control */
    /* For RGB LEDs, this would need to be adapted to PWM control */
    
    if (color->red > 0 || color->green > 0 || color->blue > 0) {
        /* Turn on LED 1 for any color */
        dk_set_led(DK_LED1, 1);
        
        /* Use LED 2 for different states */
        if (color->red > color->green && color->red > color->blue) {
            /* Red dominant - use LED 2 */
            dk_set_led(DK_LED2, 1);
            dk_set_led(DK_LED3, 0);
            dk_set_led(DK_LED4, 0);
        } else if (color->green > color->red && color->green > color->blue) {
            /* Green dominant - use LED 3 */
            dk_set_led(DK_LED2, 0);
            dk_set_led(DK_LED3, 1);
            dk_set_led(DK_LED4, 0);
        } else if (color->blue > color->red && color->blue > color->green) {
            /* Blue dominant - use LED 4 */
            dk_set_led(DK_LED2, 0);
            dk_set_led(DK_LED3, 0);
            dk_set_led(DK_LED4, 1);
        } else {
            /* Mixed colors - use multiple LEDs */
            dk_set_led(DK_LED2, color->red > 128 ? 1 : 0);
            dk_set_led(DK_LED3, color->green > 128 ? 1 : 0);
            dk_set_led(DK_LED4, color->blue > 128 ? 1 : 0);
        }
    } else {
        /* Turn off all LEDs */
        dk_set_led(DK_LED1, 0);
        dk_set_led(DK_LED2, 0);
        dk_set_led(DK_LED3, 0);
        dk_set_led(DK_LED4, 0);
    }
    
    return 0;
}

static int apply_brightness(struct led_color *color, uint8_t brightness)
{
    if (!color) {
        return -EINVAL;
    }
    
    color->red = (color->red * brightness) / 255;
    color->green = (color->green * brightness) / 255;
    color->blue = (color->blue * brightness) / 255;
    
    return 0;
}

static void start_animation(const struct led_pattern *pattern)
{
    if (!pattern) {
        return;
    }
    
    /* Stop any current animation */
    stop_animation();
    
    /* Copy pattern and start new animation */
    memcpy(&current_pattern, pattern, sizeof(current_pattern));
    animation_step = 0;
    repeat_counter = 0;
    animation_active = true;
    
    /* Start the animation work */
    k_work_schedule(&led_work, K_NO_WAIT);
}

static void stop_animation(void)
{
    animation_active = false;
    k_work_cancel_delayable(&led_work);
}

int led_controller_init(void)
{
    LOG_INF("Initializing LED controller");
    
    /* Initialize DK LEDs */
    int ret = dk_leds_init();
    if (ret) {
        LOG_ERR("Failed to initialize DK LEDs: %d", ret);
        return ret;
    }
    
    /* Initialize LED work item */
    k_work_init_delayable(&led_work, led_work_handler);
    
    /* Set initial state */
    current_state = LED_STATE_OFF;
    controller_enabled = true;
    current_brightness = 255;
    
    /* Turn off all LEDs initially */
    led_controller_set_off();
    
    LOG_INF("LED controller initialized successfully");
    return 0;
}

int led_controller_set_initializing(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_INITIALIZING;
    start_animation(&default_patterns[LED_STATE_INITIALIZING]);
    
    LOG_DBG("LED set to initializing state");
    return 0;
}

int led_controller_set_connecting(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_CONNECTING;
    start_animation(&default_patterns[LED_STATE_CONNECTING]);
    
    LOG_DBG("LED set to connecting state");
    return 0;
}

int led_controller_set_connected(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_CONNECTED;
    start_animation(&default_patterns[LED_STATE_CONNECTED]);
    
    LOG_DBG("LED set to connected state");
    return 0;
}

int led_controller_indicate_transmission(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    /* Brief indication without changing main state */
    struct led_pattern temp_pattern = default_patterns[LED_STATE_TRANSMITTING];
    start_animation(&temp_pattern);
    
    LOG_DBG("LED indicating transmission");
    return 0;
}

int led_controller_indicate_buffering(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    /* Brief indication without changing main state */
    struct led_pattern temp_pattern = default_patterns[LED_STATE_BUFFERING];
    start_animation(&temp_pattern);
    
    LOG_DBG("LED indicating buffering");
    return 0;
}

int led_controller_set_error(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_ERROR;
    start_animation(&default_patterns[LED_STATE_ERROR]);
    
    LOG_DBG("LED set to error state");
    return 0;
}

int led_controller_set_low_power(void)
{
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_LOW_POWER;
    start_animation(&default_patterns[LED_STATE_LOW_POWER]);
    
    LOG_DBG("LED set to low power state");
    return 0;
}

int led_controller_set_off(void)
{
    current_state = LED_STATE_OFF;
    stop_animation();
    
    struct led_color off_color = {0, 0, 0};
    set_led_color_internal(&off_color);
    
    LOG_DBG("LED set to off state");
    return 0;
}

int led_controller_set_pattern(const struct led_pattern *pattern)
{
    if (!pattern) {
        return -EINVAL;
    }
    
    if (!controller_enabled) {
        return 0;
    }
    
    current_state = LED_STATE_CUSTOM;
    start_animation(pattern);
    
    LOG_DBG("LED set to custom pattern");
    return 0;
}

int led_controller_set_color(const struct led_color *color)
{
    if (!color) {
        return -EINVAL;
    }
    
    if (!controller_enabled) {
        return 0;
    }
    
    stop_animation();
    
    struct led_color adjusted_color = *color;
    apply_brightness(&adjusted_color, current_brightness);
    set_led_color_internal(&adjusted_color);
    
    LOG_DBG("LED color set to RGB(%d, %d, %d)", color->red, color->green, color->blue);
    return 0;
}

int led_controller_set_brightness(uint8_t brightness)
{
    current_brightness = brightness;
    
    /* If currently showing a solid color, update it with new brightness */
    if (current_state == LED_STATE_CONNECTED && !animation_active) {
        struct led_color adjusted_color = default_patterns[LED_STATE_CONNECTED].color;
        apply_brightness(&adjusted_color, current_brightness);
        set_led_color_internal(&adjusted_color);
    }
    
    LOG_DBG("LED brightness set to %d", brightness);
    return 0;
}

int led_controller_enable(bool enable)
{
    controller_enabled = enable;
    
    if (!enable) {
        stop_animation();
        struct led_color off_color = {0, 0, 0};
        set_led_color_internal(&off_color);
    }
    
    LOG_INF("LED controller %s", enable ? "enabled" : "disabled");
    return 0;
}

enum led_state led_controller_get_state(void)
{
    return current_state;
}

int led_controller_test(void)
{
    LOG_INF("Starting LED controller test");
    
    /* Test sequence: Red -> Green -> Blue -> Off */
    struct led_color colors[] = {
        {255, 0, 0},    /* Red */
        {0, 255, 0},    /* Green */
        {0, 0, 255},    /* Blue */
        {255, 255, 0},  /* Yellow */
        {255, 0, 255},  /* Magenta */
        {0, 255, 255},  /* Cyan */
        {255, 255, 255}, /* White */
        {0, 0, 0}       /* Off */
    };
    
    for (int i = 0; i < ARRAY_SIZE(colors); i++) {
        led_controller_set_color(&colors[i]);
        k_msleep(500);
    }
    
    LOG_INF("LED controller test completed");
    return 0;
}