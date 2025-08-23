/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "cellular_manager.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <modem/lte_lc.h>
#include <modem/modem_info.h>
#include <modem/nrf_modem_lib.h>

LOG_MODULE_REGISTER(cellular_manager, CONFIG_LOG_DEFAULT_LEVEL);

/* Cellular manager state */
static enum cellular_status current_status = CELLULAR_STATUS_DISCONNECTED;
static cellular_event_cb_t event_callback = NULL;
static struct cellular_info cellular_info;
static struct k_work_delayable status_work;
static bool initialized = false;

/* Forward declarations */
static void lte_handler(const struct lte_lc_evt *const evt);
static void status_work_handler(struct k_work *work);
static void update_cellular_info(void);

static void lte_handler(const struct lte_lc_evt *const evt)
{
    enum cellular_status new_status = current_status;
    
    switch (evt->type) {
    case LTE_LC_EVT_NW_REG_STATUS:
        switch (evt->nw_reg_status) {
        case LTE_LC_NW_REG_REGISTERED_HOME:
        case LTE_LC_NW_REG_REGISTERED_ROAMING:
            new_status = CELLULAR_STATUS_CONNECTED;
            cellular_info.roaming = (evt->nw_reg_status == LTE_LC_NW_REG_REGISTERED_ROAMING);
            LOG_INF("Network registration successful (roaming: %s)", 
                    cellular_info.roaming ? "yes" : "no");
            break;
        case LTE_LC_NW_REG_SEARCHING:
            new_status = CELLULAR_STATUS_CONNECTING;
            LOG_INF("Searching for network");
            break;
        case LTE_LC_NW_REG_NOT_REGISTERED:
        case LTE_LC_NW_REG_REGISTRATION_DENIED:
        case LTE_LC_NW_REG_UNKNOWN:
        default:
            new_status = CELLULAR_STATUS_DISCONNECTED;
            LOG_WRN("Network registration failed: %d", evt->nw_reg_status);
            break;
        }
        break;
        
    case LTE_LC_EVT_PSM_UPDATE:
        LOG_INF("PSM parameter update: TAU=%d, Active=%d", 
                evt->psm_cfg.tau, evt->psm_cfg.active_time);
        break;
        
    case LTE_LC_EVT_EDRX_UPDATE:
        LOG_INF("eDRX parameter update: mode=%d, edrx=%.2f", 
                evt->edrx_cfg.mode, evt->edrx_cfg.edrx);
        break;
        
    case LTE_LC_EVT_RRC_UPDATE:
        LOG_DBG("RRC mode: %s", 
                evt->rrc_mode == LTE_LC_RRC_MODE_CONNECTED ? "connected" : "idle");
        break;
        
    case LTE_LC_EVT_CELL_UPDATE:
        cellular_info.cell_id = evt->cell.id;
        cellular_info.area_code = evt->cell.tac;
        LOG_INF("Cell update: ID=0x%08x, TAC=0x%04x", evt->cell.id, evt->cell.tac);
        break;
        
    default:
        LOG_DBG("LTE event: %d", evt->type);
        break;
    }
    
    /* Update status and notify callback */
    if (new_status != current_status) {
        current_status = new_status;
        cellular_info.status = current_status;
        
        LOG_INF("Cellular status changed to: %d", current_status);
        
        if (event_callback) {
            event_callback(current_status);
        }
        
        /* Update cellular info when status changes */
        k_work_reschedule(&status_work, K_SECONDS(1));
    }
}

static void status_work_handler(struct k_work *work)
{
    update_cellular_info();
    
    /* Schedule periodic updates when connected */
    if (current_status == CELLULAR_STATUS_CONNECTED) {
        k_work_reschedule(&status_work, K_SECONDS(30));
    }
}

static void update_cellular_info(void)
{
    int ret;
    
    /* Update signal strength */
    ret = modem_info_short_get(MODEM_INFO_RSRP, &cellular_info.signal_strength);
    if (ret < 0) {
        cellular_info.signal_strength = INT8_MIN;
    }
    
    /* Calculate signal quality from RSRP */
    if (cellular_info.signal_strength != INT8_MIN) {
        if (cellular_info.signal_strength >= -80) {
            cellular_info.signal_quality = 100;
        } else if (cellular_info.signal_strength >= -90) {
            cellular_info.signal_quality = 80;
        } else if (cellular_info.signal_strength >= -100) {
            cellular_info.signal_quality = 60;
        } else if (cellular_info.signal_strength >= -110) {
            cellular_info.signal_quality = 40;
        } else if (cellular_info.signal_strength >= -120) {
            cellular_info.signal_quality = 20;
        } else {
            cellular_info.signal_quality = 0;
        }
    }
    
    /* Update operator name */
    ret = modem_info_string_get(MODEM_INFO_OPERATOR, cellular_info.operator_name,
                               sizeof(cellular_info.operator_name));
    if (ret < 0) {
        strcpy(cellular_info.operator_name, "Unknown");
    }
    
    /* Update IMEI */
    ret = modem_info_string_get(MODEM_INFO_IMEI, cellular_info.imei,
                               sizeof(cellular_info.imei));
    if (ret < 0) {
        strcpy(cellular_info.imei, "Unknown");
    }
    
    /* Update firmware version */
    ret = modem_info_string_get(MODEM_INFO_FW_VERSION, cellular_info.firmware_version,
                               sizeof(cellular_info.firmware_version));
    if (ret < 0) {
        strcpy(cellular_info.firmware_version, "Unknown");
    }
    
    LOG_DBG("Cellular info updated - RSRP: %d dBm, Quality: %d%%, Operator: %s",
            cellular_info.signal_strength, cellular_info.signal_quality,
            cellular_info.operator_name);
}

int cellular_manager_init(void)
{
    int ret;
    
    LOG_INF("Initializing cellular manager");
    
    /* Initialize cellular info structure */
    memset(&cellular_info, 0, sizeof(cellular_info));
    cellular_info.status = CELLULAR_STATUS_DISCONNECTED;
    strcpy(cellular_info.network_mode, "LTE-M");
    
    /* Initialize modem library */
    ret = nrf_modem_lib_init();
    if (ret) {
        LOG_ERR("Failed to initialize modem library: %d", ret);
        return ret;
    }
    
    /* Initialize modem info */
    ret = modem_info_init();
    if (ret) {
        LOG_ERR("Failed to initialize modem info: %d", ret);
        return ret;
    }
    
    /* Register LTE handler */
    lte_lc_register_handler(lte_handler);
    
    /* Initialize work item */
    k_work_init_delayable(&status_work, status_work_handler);
    
    /* Get initial modem information */
    update_cellular_info();
    
    initialized = true;
    LOG_INF("Cellular manager initialized successfully");
    LOG_INF("IMEI: %s, Firmware: %s", cellular_info.imei, cellular_info.firmware_version);
    
    return 0;
}

int cellular_manager_connect(void)
{
    int ret;
    
    if (!initialized) {
        return -ENODEV;
    }
    
    if (current_status == CELLULAR_STATUS_CONNECTED) {
        return 0; /* Already connected */
    }
    
    LOG_INF("Connecting to cellular network");
    current_status = CELLULAR_STATUS_CONNECTING;
    cellular_info.status = current_status;
    
    /* Start LTE connection */
    ret = lte_lc_init_and_connect_async(lte_handler);
    if (ret) {
        LOG_ERR("Failed to start LTE connection: %d", ret);
        current_status = CELLULAR_STATUS_ERROR;
        cellular_info.status = current_status;
        return ret;
    }
    
    /* Start status monitoring */
    k_work_reschedule(&status_work, K_SECONDS(5));
    
    return 0;
}

int cellular_manager_disconnect(void)
{
    int ret;
    
    if (!initialized) {
        return -ENODEV;
    }
    
    if (current_status == CELLULAR_STATUS_DISCONNECTED) {
        return 0; /* Already disconnected */
    }
    
    LOG_INF("Disconnecting from cellular network");
    
    ret = lte_lc_offline();
    if (ret) {
        LOG_ERR("Failed to disconnect LTE: %d", ret);
        return ret;
    }
    
    current_status = CELLULAR_STATUS_DISCONNECTED;
    cellular_info.status = current_status;
    
    /* Cancel status monitoring */
    k_work_cancel_delayable(&status_work);
    
    return 0;
}

bool cellular_manager_is_ready(void)
{
    return initialized;
}

bool cellular_manager_is_connected(void)
{
    return current_status == CELLULAR_STATUS_CONNECTED;
}

bool cellular_manager_has_error(void)
{
    return current_status == CELLULAR_STATUS_ERROR;
}

int cellular_manager_get_info(struct cellular_info *info)
{
    if (!info) {
        return -EINVAL;
    }
    
    memcpy(info, &cellular_info, sizeof(*info));
    return 0;
}

int cellular_manager_set_event_callback(cellular_event_cb_t callback)
{
    event_callback = callback;
    return 0;
}

int8_t cellular_manager_get_signal_strength(void)
{
    return cellular_info.signal_strength;
}

int cellular_manager_configure(const char *apn, const char *network_mode)
{
    int ret;
    
    if (!initialized) {
        return -ENODEV;
    }
    
    LOG_INF("Configuring cellular: APN=%s, Mode=%s", 
            apn ? apn : "default", network_mode);
    
    /* Configure APN if provided */
    if (apn) {
        ret = lte_lc_apn_set(apn);
        if (ret) {
            LOG_WRN("Failed to set APN: %d", ret);
            return ret;
        }
    }
    
    /* Configure network mode */
    if (network_mode && strcmp(network_mode, "NB-IoT") == 0) {
        ret = lte_lc_system_mode_set(LTE_LC_SYSTEM_MODE_NBIOT, LTE_LC_SYSTEM_MODE_PREFER_AUTO);
        strcpy(cellular_info.network_mode, "NB-IoT");
    } else {
        ret = lte_lc_system_mode_set(LTE_LC_SYSTEM_MODE_LTEM, LTE_LC_SYSTEM_MODE_PREFER_AUTO);
        strcpy(cellular_info.network_mode, "LTE-M");
    }
    
    if (ret) {
        LOG_ERR("Failed to set system mode: %d", ret);
        return ret;
    }
    
    LOG_INF("Cellular configuration completed");
    return 0;
}

int cellular_manager_set_power_saving(bool enable)
{
    int ret;
    
    if (!initialized) {
        return -ENODEV;
    }
    
    LOG_INF("Setting cellular power saving: %s", enable ? "enabled" : "disabled");
    
    if (enable) {
        /* Enable PSM (Power Saving Mode) */
        ret = lte_lc_psm_req(true);
        if (ret) {
            LOG_WRN("Failed to enable PSM: %d", ret);
        }
        
        /* Enable eDRX (Extended Discontinuous Reception) */
        ret = lte_lc_edrx_req(true);
        if (ret) {
            LOG_WRN("Failed to enable eDRX: %d", ret);
        }
    } else {
        /* Disable PSM */
        ret = lte_lc_psm_req(false);
        if (ret) {
            LOG_WRN("Failed to disable PSM: %d", ret);
        }
        
        /* Disable eDRX */
        ret = lte_lc_edrx_req(false);
        if (ret) {
            LOG_WRN("Failed to disable eDRX: %d", ret);
        }
    }
    
    return 0;
}