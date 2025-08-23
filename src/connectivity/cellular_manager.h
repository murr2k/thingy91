/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef CELLULAR_MANAGER_H_
#define CELLULAR_MANAGER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Cellular network status
 */
enum cellular_status {
    CELLULAR_STATUS_DISCONNECTED,
    CELLULAR_STATUS_CONNECTING,
    CELLULAR_STATUS_CONNECTED,
    CELLULAR_STATUS_ERROR
};

/**
 * @brief Cellular network information
 */
struct cellular_info {
    enum cellular_status status;
    char operator_name[32];
    char imei[32];
    int8_t signal_strength;     /* RSSI in dBm */
    uint8_t signal_quality;     /* Signal quality 0-100 */
    char network_mode[16];      /* LTE-M, NB-IoT, etc. */
    char firmware_version[32];
    bool roaming;
    uint32_t cell_id;
    uint16_t area_code;
};

/**
 * @brief Cellular event callback function type
 */
typedef void (*cellular_event_cb_t)(enum cellular_status status);

/**
 * @brief Initialize cellular manager
 * 
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_init(void);

/**
 * @brief Connect to cellular network
 * 
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_connect(void);

/**
 * @brief Disconnect from cellular network
 * 
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_disconnect(void);

/**
 * @brief Check if cellular connection is ready
 * 
 * @return true if ready, false otherwise
 */
bool cellular_manager_is_ready(void);

/**
 * @brief Check if cellular is connected
 * 
 * @return true if connected, false otherwise
 */
bool cellular_manager_is_connected(void);

/**
 * @brief Check if cellular has error
 * 
 * @return true if error, false otherwise
 */
bool cellular_manager_has_error(void);

/**
 * @brief Get cellular network information
 * 
 * @param info Pointer to cellular info structure to fill
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_get_info(struct cellular_info *info);

/**
 * @brief Set cellular event callback
 * 
 * @param callback Callback function for cellular events
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_set_event_callback(cellular_event_cb_t callback);

/**
 * @brief Get signal strength
 * 
 * @return Signal strength in dBm, or INT8_MIN on error
 */
int8_t cellular_manager_get_signal_strength(void);

/**
 * @brief Configure cellular parameters
 * 
 * @param apn Access Point Name
 * @param network_mode Network mode (LTE-M, NB-IoT, etc.)
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_configure(const char *apn, const char *network_mode);

/**
 * @brief Enable/disable power saving mode
 * 
 * @param enable True to enable power saving
 * @return 0 on success, negative errno on failure
 */
int cellular_manager_set_power_saving(bool enable);

#ifdef __cplusplus
}
#endif

#endif /* CELLULAR_MANAGER_H_ */