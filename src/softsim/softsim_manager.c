/*
 * Copyright (c) 2025 Nordic Thingy91 Demo
 * SPDX-License-Identifier: MIT
 */

#include "softsim_manager.h"
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <modem/nrf_modem_lib.h>
#include <modem/at_cmd.h>
#include <modem/at_monitor.h>
#include <nrf_modem_at.h>
#include <string.h>
#include <stdio.h>

LOG_MODULE_REGISTER(softsim_manager, CONFIG_SOFTSIM_DEBUG ? LOG_LEVEL_DBG : LOG_LEVEL_INF);

/* SoftSIM manager state */
static enum softsim_state current_state = SOFTSIM_STATE_UNPROVISIONED;
static struct softsim_profile active_profile;
static struct k_mutex softsim_mutex;

/* Settings subsystem for profile persistence */
#define SOFTSIM_SETTINGS_KEY "softsim"
#define SOFTSIM_PROFILE_KEY "softsim/profile"
#define SOFTSIM_STATE_KEY "softsim/state"

/* AT command response buffer */
#define AT_RESPONSE_MAX_LEN 256
static char at_response[AT_RESPONSE_MAX_LEN];

/* KMU slot configuration */
#define KMU_SLOT_SOFTSIM CONFIG_SOFTSIM_PROFILE_STORAGE

/* Forward declarations */
static int store_profile_to_kmu(const struct softsim_profile *profile);
static int load_profile_from_kmu(struct softsim_profile *profile);
static int store_profile_to_nvs(const struct softsim_profile *profile);
static int load_profile_from_nvs(struct softsim_profile *profile);

/**
 * @brief Settings load handler
 */
static int softsim_settings_load(const char *name, size_t len,
                                 settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
    int rc;

    if (settings_name_steq(name, "profile", &next) && !next) {
        rc = read_cb(cb_arg, &active_profile, sizeof(active_profile));
        if (rc >= 0) {
            LOG_INF("Loaded SoftSIM profile from NVS");
            current_state = SOFTSIM_STATE_PROVISIONED;
            return 0;
        }
    }

    if (settings_name_steq(name, "state", &next) && !next) {
        rc = read_cb(cb_arg, &current_state, sizeof(current_state));
        if (rc >= 0) {
            LOG_INF("Loaded SoftSIM state: %d", current_state);
            return 0;
        }
    }

    return -ENOENT;
}

static struct settings_handler softsim_settings = {
    .name = SOFTSIM_SETTINGS_KEY,
    .h_set = softsim_settings_load,
};

/**
 * @brief Initialize SoftSIM manager
 */
int softsim_manager_init(void)
{
    int err;

    LOG_INF("Initializing SoftSIM manager");

    /* Initialize mutex */
    k_mutex_init(&softsim_mutex);

    /* Register settings handler */
    err = settings_subsys_init();
    if (err) {
        LOG_ERR("Failed to initialize settings subsystem: %d", err);
        return err;
    }

    err = settings_register(&softsim_settings);
    if (err) {
        LOG_ERR("Failed to register settings handler: %d", err);
        return err;
    }

    /* Load saved profile if exists */
    err = settings_load_subtree(SOFTSIM_SETTINGS_KEY);
    if (err) {
        LOG_WRN("No saved SoftSIM profile found");
    }

    /* Check if profile exists in KMU */
    if (current_state == SOFTSIM_STATE_PROVISIONED) {
        struct softsim_profile kmu_profile;
        err = load_profile_from_kmu(&kmu_profile);
        if (err == 0) {
            memcpy(&active_profile, &kmu_profile, sizeof(active_profile));
            LOG_INF("SoftSIM profile loaded from KMU");
        } else {
            LOG_WRN("Failed to load profile from KMU, using NVS backup");
        }
    }

    /* Initialize modem if not already done */
    if (!nrf_modem_is_initialized()) {
        err = nrf_modem_lib_init();
        if (err) {
            LOG_ERR("Failed to initialize modem: %d", err);
            current_state = SOFTSIM_STATE_ERROR;
            return err;
        }
    }

    LOG_INF("SoftSIM manager initialized, state: %d", current_state);
    return 0;
}

/**
 * @brief Provision SoftSIM profile
 */
int softsim_provision_profile(const struct softsim_profile *profile)
{
    int err;

    if (!profile) {
        return -EINVAL;
    }

    k_mutex_lock(&softsim_mutex, K_FOREVER);

    LOG_INF("Provisioning SoftSIM profile");
    current_state = SOFTSIM_STATE_PROVISIONING;

    /* Validate profile */
    if (profile->version == 0) {
        LOG_ERR("Invalid profile version");
        current_state = SOFTSIM_STATE_ERROR;
        k_mutex_unlock(&softsim_mutex);
        return -EINVAL;
    }

    /* Store profile in active memory */
    memcpy(&active_profile, profile, sizeof(active_profile));

    /* Store profile in KMU (secure storage) */
    err = store_profile_to_kmu(profile);
    if (err) {
        LOG_ERR("Failed to store profile in KMU: %d", err);
        current_state = SOFTSIM_STATE_ERROR;
        k_mutex_unlock(&softsim_mutex);
        return err;
    }

    /* Backup profile to NVS */
    err = store_profile_to_nvs(profile);
    if (err) {
        LOG_WRN("Failed to backup profile to NVS: %d", err);
        /* Continue anyway, KMU storage succeeded */
    }

    /* Configure modem with SoftSIM credentials */
    err = configure_modem_softsim();
    if (err) {
        LOG_ERR("Failed to configure modem: %d", err);
        current_state = SOFTSIM_STATE_ERROR;
        k_mutex_unlock(&softsim_mutex);
        return err;
    }

    current_state = SOFTSIM_STATE_PROVISIONED;
    
    /* Save state */
    settings_save_one(SOFTSIM_STATE_KEY, &current_state, sizeof(current_state));

    LOG_INF("SoftSIM profile provisioned successfully");
    LOG_DBG("IMSI: %.15s", profile->imsi);
    LOG_DBG("ICCID: %.20s", profile->iccid);
    LOG_DBG("Profile ID: %.16s", profile->profile_id);

    k_mutex_unlock(&softsim_mutex);
    return 0;
}

/**
 * @brief Configure modem with SoftSIM credentials
 */
static int configure_modem_softsim(void)
{
    int err;
    char cmd[256];

    LOG_INF("Configuring modem with SoftSIM credentials");

    /* Disable auto-connect while configuring */
    err = nrf_modem_at_printf("AT+CFUN=4");
    if (err) {
        LOG_ERR("Failed to set modem to offline mode: %d", err);
        return err;
    }

    /* Configure IMSI */
    snprintf(cmd, sizeof(cmd), "AT%%SIMDF=\"%s\"", active_profile.imsi);
    err = nrf_modem_at_printf(cmd);
    if (err) {
        LOG_ERR("Failed to configure IMSI: %d", err);
        return err;
    }

    /* Configure authentication keys */
    /* Note: Actual implementation would use secure AT commands */
    /* This is a simplified example */
    
    /* Configure APN */
    snprintf(cmd, sizeof(cmd), "AT+CGDCONT=0,\"IP\",\"%s\"", CONFIG_SOFTSIM_APN);
    err = nrf_modem_at_printf(cmd);
    if (err) {
        LOG_ERR("Failed to configure APN: %d", err);
        return err;
    }

    /* Enable roaming */
    err = nrf_modem_at_printf("AT+CRSM=214,28589,0,0,2,\"0001\"");
    if (err) {
        LOG_WRN("Failed to enable roaming: %d", err);
    }

    LOG_INF("Modem configured with SoftSIM");
    return 0;
}

/**
 * @brief Activate SoftSIM
 */
int softsim_activate(void)
{
    int err;

    k_mutex_lock(&softsim_mutex, K_FOREVER);

    if (current_state != SOFTSIM_STATE_PROVISIONED) {
        LOG_ERR("Cannot activate - SoftSIM not provisioned");
        k_mutex_unlock(&softsim_mutex);
        return -EINVAL;
    }

    LOG_INF("Activating SoftSIM");

    /* Enable modem and connect */
    err = nrf_modem_at_printf("AT+CFUN=1");
    if (err) {
        LOG_ERR("Failed to activate modem: %d", err);
        k_mutex_unlock(&softsim_mutex);
        return err;
    }

    /* Wait for network registration */
    k_sleep(K_SECONDS(2));

    /* Check registration status */
    err = nrf_modem_at_scanf("AT+CEREG?", "+CEREG: %*d,%d", &err);
    if (err == 1 || err == 5) {
        LOG_INF("SoftSIM activated and registered on network");
        current_state = SOFTSIM_STATE_ACTIVE;
        settings_save_one(SOFTSIM_STATE_KEY, &current_state, sizeof(current_state));
    } else {
        LOG_WRN("SoftSIM activated but not yet registered");
        current_state = SOFTSIM_STATE_PROVISIONED;
    }

    k_mutex_unlock(&softsim_mutex);
    return 0;
}

/**
 * @brief Get current SoftSIM state
 */
enum softsim_state softsim_get_state(void)
{
    return current_state;
}

/**
 * @brief Verify SoftSIM profile
 */
int softsim_verify_profile(void)
{
    int err;
    char imsi[16];

    k_mutex_lock(&softsim_mutex, K_FOREVER);

    if (current_state < SOFTSIM_STATE_PROVISIONED) {
        LOG_ERR("No profile to verify");
        k_mutex_unlock(&softsim_mutex);
        return -ENOENT;
    }

    /* Query IMSI from modem */
    err = nrf_modem_at_scanf("AT+CIMI", "%15s", imsi);
    if (err < 0) {
        LOG_ERR("Failed to query IMSI: %d", err);
        k_mutex_unlock(&softsim_mutex);
        return err;
    }

    /* Compare with provisioned IMSI */
    if (strncmp(imsi, (char *)active_profile.imsi, 15) == 0) {
        LOG_INF("SoftSIM profile verified successfully");
        k_mutex_unlock(&softsim_mutex);
        return 0;
    } else {
        LOG_ERR("SoftSIM profile verification failed");
        LOG_DBG("Expected IMSI: %.15s", active_profile.imsi);
        LOG_DBG("Actual IMSI: %s", imsi);
        k_mutex_unlock(&softsim_mutex);
        return -EINVAL;
    }
}

/**
 * @brief Remove SoftSIM profile
 */
int softsim_remove_profile(void)
{
    int err;

    k_mutex_lock(&softsim_mutex, K_FOREVER);

    LOG_INF("Removing SoftSIM profile");

    /* Deactivate modem */
    err = nrf_modem_at_printf("AT+CFUN=0");
    if (err) {
        LOG_WRN("Failed to deactivate modem: %d", err);
    }

    /* Clear profile from memory */
    memset(&active_profile, 0, sizeof(active_profile));

    /* Clear profile from KMU */
    /* Note: Actual implementation would clear KMU slot */

    /* Clear profile from NVS */
    settings_delete(SOFTSIM_PROFILE_KEY);
    
    current_state = SOFTSIM_STATE_UNPROVISIONED;
    settings_save_one(SOFTSIM_STATE_KEY, &current_state, sizeof(current_state));

    LOG_INF("SoftSIM profile removed");

    k_mutex_unlock(&softsim_mutex);
    return 0;
}

/**
 * @brief Store profile to KMU (stub implementation)
 */
static int store_profile_to_kmu(const struct softsim_profile *profile)
{
    /* This would interface with actual KMU hardware */
    /* For now, just log the action */
    LOG_INF("Storing profile to KMU slot %d", KMU_SLOT_SOFTSIM);
    return 0;
}

/**
 * @brief Load profile from KMU (stub implementation)
 */
static int load_profile_from_kmu(struct softsim_profile *profile)
{
    /* This would interface with actual KMU hardware */
    /* For now, just log the action */
    LOG_INF("Loading profile from KMU slot %d", KMU_SLOT_SOFTSIM);
    return 0;
}

/**
 * @brief Store profile to NVS
 */
static int store_profile_to_nvs(const struct softsim_profile *profile)
{
    return settings_save_one(SOFTSIM_PROFILE_KEY, profile, sizeof(*profile));
}

/**
 * @brief Load profile from NVS
 */
static int load_profile_from_nvs(struct softsim_profile *profile)
{
    return settings_load_subtree(SOFTSIM_SETTINGS_KEY);
}