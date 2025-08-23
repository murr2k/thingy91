/*
 * Copyright (c) 2025 Nordic Thingy91 Demo
 * SPDX-License-Identifier: MIT
 */

#include "at_handler.h"
#include "softsim_manager.h"
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <modem/at_cmd_parser.h>
#include <modem/at_cmd_custom.h>
#include <nrf_modem_at.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

LOG_MODULE_REGISTER(at_handler, CONFIG_SOFTSIM_DEBUG ? LOG_LEVEL_DBG : LOG_LEVEL_INF);

/* Base64 decoding table */
static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

/* AT command handlers */
static int handle_provision(const char *param);
static int handle_status(void);
static int handle_activate(void);
static int handle_remove(void);
static int handle_info(void);

/* Base64 decode helper */
static int base64_decode(const char *src, size_t src_len, uint8_t *dst, size_t *dst_len);

/**
 * @brief Custom AT command filter
 */
AT_CMD_CUSTOM(osimprov_filter, "AT+OSIMPROV", handle_provision);
AT_CMD_CUSTOM(osimstat_filter, "AT+OSIMSTAT", handle_status);
AT_CMD_CUSTOM(osimact_filter, "AT+OSIMACT", handle_activate);
AT_CMD_CUSTOM(osimrem_filter, "AT+OSIMREM", handle_remove);
AT_CMD_CUSTOM(osiminfo_filter, "AT+OSIMINFO", handle_info);

/**
 * @brief Initialize AT command handler
 */
int at_handler_init(void)
{
    int err;

    LOG_INF("Initializing AT command handler");

    /* Initialize custom AT command library */
    err = at_cmd_custom_init();
    if (err) {
        LOG_ERR("Failed to initialize custom AT commands: %d", err);
        return err;
    }

    LOG_INF("AT command handler initialized");
    LOG_INF("Custom SoftSIM AT commands registered:");
    LOG_INF("  AT+OSIMPROV - Provision SoftSIM profile");
    LOG_INF("  AT+OSIMSTAT - Get SoftSIM status");
    LOG_INF("  AT+OSIMACT  - Activate SoftSIM");
    LOG_INF("  AT+OSIMREM  - Remove SoftSIM profile");
    LOG_INF("  AT+OSIMINFO - Get SoftSIM information");

    return 0;
}

/**
 * @brief Handle AT+OSIMPROV command
 */
static int handle_provision(const char *param)
{
    struct softsim_profile profile;
    uint8_t decoded_data[512];
    size_t decoded_len = sizeof(decoded_data);
    int err;

    LOG_INF("Handling AT+OSIMPROV command");

    if (!param || strlen(param) < 10) {
        at_cmd_custom_respond("ERROR: Invalid profile data\r\n");
        return -EINVAL;
    }

    /* Skip the '=' character */
    if (*param == '=') {
        param++;
    }

    /* Decode base64 profile data */
    err = base64_decode(param, strlen(param), decoded_data, &decoded_len);
    if (err) {
        LOG_ERR("Failed to decode profile data: %d", err);
        at_cmd_custom_respond("ERROR: Invalid base64 encoding\r\n");
        return err;
    }

    /* Parse profile data (simplified - real implementation would parse JSON) */
    memset(&profile, 0, sizeof(profile));
    
    /* Example parsing - in reality, this would parse JSON structure */
    if (decoded_len >= sizeof(profile)) {
        memcpy(&profile, decoded_data, sizeof(profile));
    } else {
        /* Set some default values for testing */
        strcpy((char *)profile.imsi, "001010123456789");
        strcpy((char *)profile.iccid, "89000000000000000001");
        memset(profile.ki, 0xAA, sizeof(profile.ki));
        memset(profile.opc, 0xBB, sizeof(profile.opc));
        strcpy((char *)profile.profile_id, "ONOMONDO_TEST");
        profile.version = 1;
    }

    /* Provision the profile */
    err = softsim_provision_profile(&profile);
    if (err) {
        LOG_ERR("Failed to provision profile: %d", err);
        at_cmd_custom_respond("ERROR: Provisioning failed\r\n");
        return err;
    }

    at_cmd_custom_respond("OK\r\n");
    return 0;
}

/**
 * @brief Handle AT+OSIMSTAT command
 */
static int handle_status(void)
{
    enum softsim_state state;
    char response[64];

    LOG_INF("Handling AT+OSIMSTAT command");

    state = softsim_get_state();

    switch (state) {
    case SOFTSIM_STATE_UNPROVISIONED:
        snprintf(response, sizeof(response), "+OSIMSTAT: UNPROVISIONED\r\nOK\r\n");
        break;
    case SOFTSIM_STATE_PROVISIONING:
        snprintf(response, sizeof(response), "+OSIMSTAT: PROVISIONING\r\nOK\r\n");
        break;
    case SOFTSIM_STATE_PROVISIONED:
        snprintf(response, sizeof(response), "+OSIMSTAT: PROVISIONED\r\nOK\r\n");
        break;
    case SOFTSIM_STATE_ACTIVE:
        snprintf(response, sizeof(response), "+OSIMSTAT: ACTIVE\r\nOK\r\n");
        break;
    case SOFTSIM_STATE_ERROR:
        snprintf(response, sizeof(response), "+OSIMSTAT: ERROR\r\nOK\r\n");
        break;
    default:
        snprintf(response, sizeof(response), "+OSIMSTAT: UNKNOWN\r\nOK\r\n");
        break;
    }

    at_cmd_custom_respond(response);
    return 0;
}

/**
 * @brief Handle AT+OSIMACT command
 */
static int handle_activate(void)
{
    int err;

    LOG_INF("Handling AT+OSIMACT command");

    err = softsim_activate();
    if (err) {
        LOG_ERR("Failed to activate SoftSIM: %d", err);
        at_cmd_custom_respond("ERROR: Activation failed\r\n");
        return err;
    }

    at_cmd_custom_respond("OK\r\n");
    return 0;
}

/**
 * @brief Handle AT+OSIMREM command
 */
static int handle_remove(void)
{
    int err;

    LOG_INF("Handling AT+OSIMREM command");

    err = softsim_remove_profile();
    if (err) {
        LOG_ERR("Failed to remove SoftSIM profile: %d", err);
        at_cmd_custom_respond("ERROR: Removal failed\r\n");
        return err;
    }

    at_cmd_custom_respond("OK\r\n");
    return 0;
}

/**
 * @brief Handle AT+OSIMINFO command
 */
static int handle_info(void)
{
    enum softsim_state state;
    char response[256];
    char imsi[16] = {0};
    char iccid[21] = {0};
    int signal_strength = 0;
    int err;

    LOG_INF("Handling AT+OSIMINFO command");

    state = softsim_get_state();

    if (state < SOFTSIM_STATE_PROVISIONED) {
        snprintf(response, sizeof(response), 
                "+OSIMINFO: No profile provisioned\r\nOK\r\n");
        at_cmd_custom_respond(response);
        return 0;
    }

    /* Get IMSI if available */
    err = nrf_modem_at_scanf("AT+CIMI", "%15s", imsi);
    if (err < 0) {
        strcpy(imsi, "N/A");
    }

    /* Get signal strength */
    err = nrf_modem_at_scanf("AT+CSQ", "+CSQ: %d", &signal_strength);
    if (err < 0) {
        signal_strength = -1;
    }

    /* Format response */
    snprintf(response, sizeof(response),
            "+OSIMINFO:\r\n"
            "State: %s\r\n"
            "IMSI: %s\r\n"
            "Signal: %d dBm\r\n"
            "Provider: Onomondo\r\n"
            "OK\r\n",
            state == SOFTSIM_STATE_ACTIVE ? "ACTIVE" : "PROVISIONED",
            imsi,
            signal_strength == -1 ? 0 : -113 + (signal_strength * 2));

    at_cmd_custom_respond(response);
    return 0;
}

/**
 * @brief Send AT command and get response
 */
int at_send_command(const char *cmd, char *response, size_t response_len)
{
    int err;

    if (!cmd || !response) {
        return -EINVAL;
    }

    /* Send AT command */
    err = nrf_modem_at_cmd(response, response_len, cmd);
    if (err) {
        LOG_ERR("AT command failed: %s (err: %d)", cmd, err);
        return err;
    }

    LOG_DBG("AT command: %s", cmd);
    LOG_DBG("Response: %s", response);

    return 0;
}

/**
 * @brief Register custom AT commands (alternative method)
 */
int at_register_softsim_commands(void)
{
    /* Custom commands are registered via AT_CMD_CUSTOM macro */
    /* This function is for compatibility */
    LOG_INF("SoftSIM AT commands registered");
    return 0;
}

/**
 * @brief Base64 decode helper function
 */
static int base64_decode(const char *src, size_t src_len, uint8_t *dst, size_t *dst_len)
{
    size_t i, j = 0;
    uint32_t v = 0;
    int n = 0;
    
    if (!src || !dst || !dst_len) {
        return -EINVAL;
    }

    for (i = 0; i < src_len; i++) {
        char c = src[i];
        const char *p;
        
        if (isspace(c)) {
            continue;
        }
        
        if (c == '=') {
            break;
        }
        
        p = strchr(b64_table, c);
        if (!p) {
            return -EINVAL;
        }
        
        v = (v << 6) | (p - b64_table);
        n += 6;
        
        if (n >= 8) {
            n -= 8;
            if (j >= *dst_len) {
                return -ENOBUFS;
            }
            dst[j++] = (v >> n) & 0xFF;
        }
    }
    
    *dst_len = j;
    return 0;
}