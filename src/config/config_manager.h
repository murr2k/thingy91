/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef CONFIG_MANAGER_H_
#define CONFIG_MANAGER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Application configuration structure
 */
struct app_config {
    /* Device identification */
    char device_id[32];
    char firmware_version[16];
    char hardware_version[16];
    
    /* Sensor configuration */
    uint32_t sensor_read_interval_ms;
    bool enable_environmental_sensors;
    bool enable_motion_sensors;
    uint8_t sensor_data_quality_threshold;
    
    /* Connectivity configuration */
    char cellular_apn[64];
    char cellular_network_mode[16];
    bool cellular_power_saving_enabled;
    
    /* MQTT configuration */
    char mqtt_broker_hostname[64];
    uint16_t mqtt_broker_port;
    char mqtt_client_id[32];
    char mqtt_username[32];
    char mqtt_password[64];
    char mqtt_publish_topic[64];
    char mqtt_subscribe_topic[64];
    uint16_t mqtt_keepalive_sec;
    bool mqtt_tls_enabled;
    
    /* Data processing configuration */
    bool enable_data_filtering;
    uint8_t data_smoothing_factor;
    bool enable_data_compression;
    uint32_t data_buffer_size;
    uint32_t data_retention_hours;
    
    /* Power management configuration */
    bool auto_sleep_enabled;
    uint32_t idle_timeout_minutes;
    float low_battery_threshold_v;
    bool battery_monitoring_enabled;
    
    /* LED configuration */
    bool led_enabled;
    uint8_t led_brightness;
    bool led_animations_enabled;
    
    /* Logging configuration */
    uint8_t log_level;
    bool log_to_flash_enabled;
    
    /* Configuration metadata */
    uint32_t config_version;
    uint32_t config_crc;
    uint64_t last_modified_timestamp;
};

/**
 * @brief Configuration defaults
 */
extern const struct app_config default_config;

/**
 * @brief Initialize configuration manager
 * 
 * @return 0 on success, negative errno on failure
 */
int config_manager_init(void);

/**
 * @brief Load configuration from storage
 * 
 * @return 0 on success, negative errno on failure
 */
int config_manager_load(void);

/**
 * @brief Save current configuration to storage
 * 
 * @return 0 on success, negative errno on failure
 */
int config_manager_save(void);

/**
 * @brief Get current configuration
 * 
 * @return Pointer to current configuration
 */
const struct app_config *config_manager_get(void);

/**
 * @brief Set configuration
 * 
 * @param config Pointer to new configuration
 * @return 0 on success, negative errno on failure
 */
int config_manager_set(const struct app_config *config);

/**
 * @brief Update a single configuration parameter
 * 
 * @param key Configuration parameter name
 * @param value Pointer to new value
 * @param value_size Size of new value
 * @return 0 on success, negative errno on failure
 */
int config_manager_set_parameter(const char *key, const void *value, size_t value_size);

/**
 * @brief Get a single configuration parameter
 * 
 * @param key Configuration parameter name
 * @param value Pointer to buffer for value
 * @param value_size Size of value buffer
 * @return 0 on success, negative errno on failure
 */
int config_manager_get_parameter(const char *key, void *value, size_t value_size);

/**
 * @brief Reset configuration to defaults
 * 
 * @return 0 on success, negative errno on failure
 */
int config_manager_reset_to_defaults(void);

/**
 * @brief Validate configuration integrity
 * 
 * @param config Configuration to validate (NULL for current)
 * @return 0 if valid, negative errno if invalid
 */
int config_manager_validate(const struct app_config *config);

/**
 * @brief Export configuration as JSON
 * 
 * @param json_buffer Output JSON buffer
 * @param buffer_size Size of JSON buffer
 * @return Length of JSON string on success, negative errno on failure
 */
int config_manager_export_json(char *json_buffer, size_t buffer_size);

/**
 * @brief Import configuration from JSON
 * 
 * @param json_string JSON configuration string
 * @return 0 on success, negative errno on failure
 */
int config_manager_import_json(const char *json_string);

/**
 * @brief Get configuration file path
 * 
 * @return Configuration file path
 */
const char *config_manager_get_file_path(void);

/**
 * @brief Check if configuration has been modified
 * 
 * @return True if modified, false otherwise
 */
bool config_manager_is_modified(void);

/**
 * @brief Mark configuration as clean (not modified)
 * 
 * @return 0 on success, negative errno on failure
 */
int config_manager_mark_clean(void);

#ifdef __cplusplus
}
#endif

#endif /* CONFIG_MANAGER_H_ */