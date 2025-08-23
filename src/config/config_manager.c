/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "config_manager.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/fs/nvs.h>
#include <zephyr/sys/crc.h>
#include <zephyr/data/json.h>
#include <stdio.h>
#include <string.h>

LOG_MODULE_REGISTER(config_manager, CONFIG_LOG_DEFAULT_LEVEL);

/* Configuration version for migration */
#define CONFIG_VERSION 1
#define CONFIG_NVS_ID 1

/* Default configuration */
const struct app_config default_config = {
    .device_id = "thingy91_demo_device",
    .firmware_version = "1.0.0",
    .hardware_version = "1.0",
    
    .sensor_read_interval_ms = CONFIG_THINGY91_DEMO_SENSOR_INTERVAL_MS,
    .enable_environmental_sensors = true,
    .enable_motion_sensors = true,
    .sensor_data_quality_threshold = 80,
    
    .cellular_apn = "",
    .cellular_network_mode = "LTE-M",
    .cellular_power_saving_enabled = true,
    
    .mqtt_broker_hostname = "broker.hivemq.com",
    .mqtt_broker_port = 8883,
    .mqtt_client_id = "thingy91_demo",
    .mqtt_username = "",
    .mqtt_password = "",
    .mqtt_publish_topic = "thingy91/demo/sensor_data",
    .mqtt_subscribe_topic = "thingy91/demo/commands",
    .mqtt_keepalive_sec = CONFIG_THINGY91_DEMO_MQTT_KEEPALIVE,
    .mqtt_tls_enabled = true,
    
    .enable_data_filtering = true,
    .data_smoothing_factor = 3,
    .enable_data_compression = false,
    .data_buffer_size = CONFIG_THINGY91_DEMO_DATA_BUFFER_SIZE,
    .data_retention_hours = 24,
    
    .auto_sleep_enabled = true,
    .idle_timeout_minutes = 5,
    .low_battery_threshold_v = 3.2f,
    .battery_monitoring_enabled = true,
    
    .led_enabled = true,
    .led_brightness = 255,
    .led_animations_enabled = true,
    
    .log_level = CONFIG_LOG_DEFAULT_LEVEL,
    .log_to_flash_enabled = false,
    
    .config_version = CONFIG_VERSION,
    .config_crc = 0,
    .last_modified_timestamp = 0
};

/* Current configuration */
static struct app_config current_config;
static bool config_modified = false;
static bool config_loaded = false;

/* NVS file system for configuration storage */
static struct nvs_fs nvs;
static bool nvs_initialized = false;

/* Mutex for configuration access */
static struct k_mutex config_mutex;

/* Forward declarations */
static int init_nvs_storage(void);
static uint32_t calculate_config_crc(const struct app_config *config);
static int load_config_from_nvs(void);
static int save_config_to_nvs(void);
static int migrate_config_if_needed(struct app_config *config);
static int parse_json_config(const char *json_string, struct app_config *config);
static int format_json_config(const struct app_config *config, char *json_buffer, size_t buffer_size);

static int init_nvs_storage(void)
{
#ifdef CONFIG_NVS
    int ret;
    struct flash_pages_info info;
    
    /* Initialize NVS file system */
    nvs.flash_device = FLASH_AREA_DEVICE(storage);
    if (!device_is_ready(nvs.flash_device)) {
        LOG_ERR("Flash device not ready for NVS");
        return -ENODEV;
    }
    
    nvs.offset = FLASH_AREA_OFFSET(storage);
    ret = flash_get_page_info_by_offs(nvs.flash_device, nvs.offset, &info);
    if (ret) {
        LOG_ERR("Unable to get storage flash page info: %d", ret);
        return ret;
    }
    
    nvs.sector_size = info.size;
    nvs.sector_count = 4;  /* Use 4 sectors for configuration */
    
    ret = nvs_mount(&nvs);
    if (ret) {
        LOG_ERR("Failed to mount NVS: %d", ret);
        return ret;
    }
    
    nvs_initialized = true;
    LOG_INF("NVS storage initialized for configuration");
    return 0;
#else
    LOG_WRN("NVS not configured, configuration persistence disabled");
    return -ENOSYS;
#endif
}

static uint32_t calculate_config_crc(const struct app_config *config)
{
    if (!config) {
        return 0;
    }
    
    /* Calculate CRC excluding the CRC field itself */
    size_t crc_offset = offsetof(struct app_config, config_crc);
    size_t data_before_crc = crc_offset;
    size_t data_after_crc = sizeof(*config) - crc_offset - sizeof(config->config_crc);
    
    uint32_t crc = crc32_ieee_init();
    crc = crc32_ieee_update(crc, (const uint8_t*)config, data_before_crc);
    crc = crc32_ieee_update(crc, (const uint8_t*)config + crc_offset + sizeof(config->config_crc), data_after_crc);
    return crc32_ieee_finalize(crc);
}

static int load_config_from_nvs(void)
{
#ifdef CONFIG_NVS
    if (!nvs_initialized) {
        return -ENODEV;
    }
    
    ssize_t ret = nvs_read(&nvs, CONFIG_NVS_ID, &current_config, sizeof(current_config));
    if (ret < 0) {
        if (ret == -ENOENT) {
            LOG_INF("No stored configuration found, using defaults");
        } else {
            LOG_ERR("Failed to read configuration from NVS: %d", (int)ret);
        }
        return (int)ret;
    }
    
    /* Validate configuration */
    int validation_ret = config_manager_validate(&current_config);
    if (validation_ret != 0) {
        LOG_WRN("Stored configuration is invalid, using defaults");
        return validation_ret;
    }
    
    LOG_INF("Configuration loaded from storage");
    return 0;
#else
    return -ENOSYS;
#endif
}

static int save_config_to_nvs(void)
{
#ifdef CONFIG_NVS
    if (!nvs_initialized) {
        return -ENODEV;
    }
    
    /* Update CRC and timestamp before saving */
    current_config.config_crc = calculate_config_crc(&current_config);
    current_config.last_modified_timestamp = k_uptime_get();
    
    ssize_t ret = nvs_write(&nvs, CONFIG_NVS_ID, &current_config, sizeof(current_config));
    if (ret < 0) {
        LOG_ERR("Failed to save configuration to NVS: %d", (int)ret);
        return (int)ret;
    }
    
    config_modified = false;
    LOG_INF("Configuration saved to storage");
    return 0;
#else
    LOG_WRN("NVS not available, configuration not persisted");
    return -ENOSYS;
#endif
}

static int migrate_config_if_needed(struct app_config *config)
{
    if (!config) {
        return -EINVAL;
    }
    
    if (config->config_version == CONFIG_VERSION) {
        return 0;  /* No migration needed */
    }
    
    LOG_INF("Migrating configuration from version %d to %d", 
            config->config_version, CONFIG_VERSION);
    
    /* Perform version-specific migration */
    if (config->config_version == 0) {
        /* Migration from version 0 to 1 */
        /* Add any new fields with default values */
        config->sensor_data_quality_threshold = 80;
        config->data_retention_hours = 24;
    }
    
    config->config_version = CONFIG_VERSION;
    return 0;
}

static int parse_json_config(const char *json_string, struct app_config *config)
{
    if (!json_string || !config) {
        return -EINVAL;
    }
    
    /* This is a simplified JSON parser - in a real implementation,
     * you would use a proper JSON library */
    LOG_WRN("JSON configuration import not fully implemented");
    return -ENOSYS;
}

static int format_json_config(const struct app_config *config, char *json_buffer, size_t buffer_size)
{
    if (!config || !json_buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    int ret = snprintf(json_buffer, buffer_size,
        "{\n"
        "  \"device_id\": \"%s\",\n"
        "  \"firmware_version\": \"%s\",\n"
        "  \"hardware_version\": \"%s\",\n"
        "  \"sensor\": {\n"
        "    \"read_interval_ms\": %u,\n"
        "    \"enable_environmental\": %s,\n"
        "    \"enable_motion\": %s,\n"
        "    \"quality_threshold\": %u\n"
        "  },\n"
        "  \"cellular\": {\n"
        "    \"apn\": \"%s\",\n"
        "    \"network_mode\": \"%s\",\n"
        "    \"power_saving\": %s\n"
        "  },\n"
        "  \"mqtt\": {\n"
        "    \"broker_hostname\": \"%s\",\n"
        "    \"broker_port\": %u,\n"
        "    \"client_id\": \"%s\",\n"
        "    \"publish_topic\": \"%s\",\n"
        "    \"subscribe_topic\": \"%s\",\n"
        "    \"keepalive_sec\": %u,\n"
        "    \"tls_enabled\": %s\n"
        "  },\n"
        "  \"data_processing\": {\n"
        "    \"enable_filtering\": %s,\n"
        "    \"smoothing_factor\": %u,\n"
        "    \"enable_compression\": %s,\n"
        "    \"buffer_size\": %u,\n"
        "    \"retention_hours\": %u\n"
        "  },\n"
        "  \"power\": {\n"
        "    \"auto_sleep\": %s,\n"
        "    \"idle_timeout_minutes\": %u,\n"
        "    \"low_battery_threshold_v\": %.2f,\n"
        "    \"battery_monitoring\": %s\n"
        "  },\n"
        "  \"ui\": {\n"
        "    \"led_enabled\": %s,\n"
        "    \"led_brightness\": %u,\n"
        "    \"led_animations\": %s\n"
        "  },\n"
        "  \"logging\": {\n"
        "    \"log_level\": %u,\n"
        "    \"log_to_flash\": %s\n"
        "  },\n"
        "  \"metadata\": {\n"
        "    \"config_version\": %u,\n"
        "    \"last_modified\": %llu\n"
        "  }\n"
        "}",
        config->device_id,
        config->firmware_version,
        config->hardware_version,
        config->sensor_read_interval_ms,
        config->enable_environmental_sensors ? "true" : "false",
        config->enable_motion_sensors ? "true" : "false",
        config->sensor_data_quality_threshold,
        config->cellular_apn,
        config->cellular_network_mode,
        config->cellular_power_saving_enabled ? "true" : "false",
        config->mqtt_broker_hostname,
        config->mqtt_broker_port,
        config->mqtt_client_id,
        config->mqtt_publish_topic,
        config->mqtt_subscribe_topic,
        config->mqtt_keepalive_sec,
        config->mqtt_tls_enabled ? "true" : "false",
        config->enable_data_filtering ? "true" : "false",
        config->data_smoothing_factor,
        config->enable_data_compression ? "true" : "false",
        config->data_buffer_size,
        config->data_retention_hours,
        config->auto_sleep_enabled ? "true" : "false",
        config->idle_timeout_minutes,
        config->low_battery_threshold_v,
        config->battery_monitoring_enabled ? "true" : "false",
        config->led_enabled ? "true" : "false",
        config->led_brightness,
        config->led_animations_enabled ? "true" : "false",
        config->log_level,
        config->log_to_flash_enabled ? "true" : "false",
        config->config_version,
        config->last_modified_timestamp
    );
    
    if (ret < 0 || ret >= buffer_size) {
        LOG_ERR("JSON formatting failed or buffer too small: %d", ret);
        return -ENOBUFS;
    }
    
    return ret;
}

int config_manager_init(void)
{
    LOG_INF("Initializing configuration manager");
    
    /* Initialize mutex */
    int ret = k_mutex_init(&config_mutex);
    if (ret) {
        LOG_ERR("Failed to initialize config mutex: %d", ret);
        return ret;
    }
    
    /* Initialize NVS storage */
    ret = init_nvs_storage();
    if (ret && ret != -ENOSYS) {
        LOG_WRN("Failed to initialize NVS storage: %d", ret);
    }
    
    /* Load configuration from storage */
    memcpy(&current_config, &default_config, sizeof(current_config));
    
    ret = load_config_from_nvs();
    if (ret == 0) {
        /* Migrate configuration if needed */
        ret = migrate_config_if_needed(&current_config);
        if (ret) {
            LOG_WRN("Configuration migration failed: %d", ret);
            memcpy(&current_config, &default_config, sizeof(current_config));
        } else {
            config_loaded = true;
        }
    } else if (ret == -ENOENT || ret == -ENOSYS) {
        /* No stored configuration or NVS not available, use defaults */
        LOG_INF("Using default configuration");
        config_loaded = false;
    } else {
        LOG_ERR("Failed to load configuration: %d", ret);
        return ret;
    }
    
    /* Update CRC for current configuration */
    current_config.config_crc = calculate_config_crc(&current_config);
    config_modified = false;
    
    LOG_INF("Configuration manager initialized successfully");
    LOG_INF("Device ID: %s, Firmware: %s, Hardware: %s", 
            current_config.device_id, 
            current_config.firmware_version,
            current_config.hardware_version);
    
    return 0;
}

int config_manager_load(void)
{
    k_mutex_lock(&config_mutex, K_FOREVER);
    
    int ret = load_config_from_nvs();
    if (ret == 0) {
        ret = migrate_config_if_needed(&current_config);
        if (ret == 0) {
            current_config.config_crc = calculate_config_crc(&current_config);
            config_modified = false;
            config_loaded = true;
        }
    }
    
    k_mutex_unlock(&config_mutex);
    return ret;
}

int config_manager_save(void)
{
    k_mutex_lock(&config_mutex, K_FOREVER);
    int ret = save_config_to_nvs();
    k_mutex_unlock(&config_mutex);
    return ret;
}

const struct app_config *config_manager_get(void)
{
    return &current_config;
}

int config_manager_set(const struct app_config *config)
{
    if (!config) {
        return -EINVAL;
    }
    
    int ret = config_manager_validate(config);
    if (ret != 0) {
        return ret;
    }
    
    k_mutex_lock(&config_mutex, K_FOREVER);
    
    memcpy(&current_config, config, sizeof(current_config));
    current_config.config_crc = calculate_config_crc(&current_config);
    current_config.last_modified_timestamp = k_uptime_get();
    config_modified = true;
    
    k_mutex_unlock(&config_mutex);
    
    LOG_INF("Configuration updated");
    return 0;
}

int config_manager_set_parameter(const char *key, const void *value, size_t value_size)
{
    if (!key || !value) {
        return -EINVAL;
    }
    
    k_mutex_lock(&config_mutex, K_FOREVER);
    
    /* Simple parameter setting - in a real implementation, 
     * you would use a lookup table or reflection */
    int ret = -ENOENT;
    
    if (strcmp(key, "sensor_read_interval_ms") == 0 && value_size == sizeof(uint32_t)) {
        current_config.sensor_read_interval_ms = *(const uint32_t*)value;
        ret = 0;
    } else if (strcmp(key, "mqtt_broker_hostname") == 0 && value_size < sizeof(current_config.mqtt_broker_hostname)) {
        strncpy(current_config.mqtt_broker_hostname, (const char*)value, sizeof(current_config.mqtt_broker_hostname) - 1);
        current_config.mqtt_broker_hostname[sizeof(current_config.mqtt_broker_hostname) - 1] = '\0';
        ret = 0;
    } else if (strcmp(key, "led_brightness") == 0 && value_size == sizeof(uint8_t)) {
        current_config.led_brightness = *(const uint8_t*)value;
        ret = 0;
    }
    /* Add more parameters as needed */
    
    if (ret == 0) {
        config_modified = true;
        current_config.last_modified_timestamp = k_uptime_get();
        LOG_DBG("Parameter '%s' updated", key);
    }
    
    k_mutex_unlock(&config_mutex);
    return ret;
}

int config_manager_get_parameter(const char *key, void *value, size_t value_size)
{
    if (!key || !value) {
        return -EINVAL;
    }
    
    int ret = -ENOENT;
    
    if (strcmp(key, "sensor_read_interval_ms") == 0 && value_size >= sizeof(uint32_t)) {
        *(uint32_t*)value = current_config.sensor_read_interval_ms;
        ret = sizeof(uint32_t);
    } else if (strcmp(key, "mqtt_broker_hostname") == 0 && value_size >= strlen(current_config.mqtt_broker_hostname) + 1) {
        strcpy((char*)value, current_config.mqtt_broker_hostname);
        ret = strlen(current_config.mqtt_broker_hostname) + 1;
    } else if (strcmp(key, "led_brightness") == 0 && value_size >= sizeof(uint8_t)) {
        *(uint8_t*)value = current_config.led_brightness;
        ret = sizeof(uint8_t);
    }
    /* Add more parameters as needed */
    
    return ret;
}

int config_manager_reset_to_defaults(void)
{
    k_mutex_lock(&config_mutex, K_FOREVER);
    
    memcpy(&current_config, &default_config, sizeof(current_config));
    current_config.config_crc = calculate_config_crc(&current_config);
    current_config.last_modified_timestamp = k_uptime_get();
    config_modified = true;
    
    k_mutex_unlock(&config_mutex);
    
    LOG_INF("Configuration reset to defaults");
    return 0;
}

int config_manager_validate(const struct app_config *config)
{
    if (!config) {
        return -EINVAL;
    }
    
    /* Validate configuration version */
    if (config->config_version > CONFIG_VERSION) {
        LOG_ERR("Unsupported configuration version: %d", config->config_version);
        return -EINVAL;
    }
    
    /* Validate CRC if not zero */
    if (config->config_crc != 0) {
        uint32_t calculated_crc = calculate_config_crc(config);
        if (calculated_crc != config->config_crc) {
            LOG_ERR("Configuration CRC mismatch: calculated=0x%08x, stored=0x%08x", 
                    calculated_crc, config->config_crc);
            return -EINVAL;
        }
    }
    
    /* Validate sensor interval */
    if (config->sensor_read_interval_ms < 100 || config->sensor_read_interval_ms > 3600000) {
        LOG_ERR("Invalid sensor read interval: %d ms", config->sensor_read_interval_ms);
        return -EINVAL;
    }
    
    /* Validate MQTT configuration */
    if (strlen(config->mqtt_broker_hostname) == 0) {
        LOG_ERR("Empty MQTT broker hostname");
        return -EINVAL;
    }
    
    if (config->mqtt_broker_port == 0 || config->mqtt_broker_port > 65535) {
        LOG_ERR("Invalid MQTT broker port: %d", config->mqtt_broker_port);
        return -EINVAL;
    }
    
    /* Validate power configuration */
    if (config->low_battery_threshold_v < 2.0f || config->low_battery_threshold_v > 5.0f) {
        LOG_ERR("Invalid low battery threshold: %.2fV", config->low_battery_threshold_v);
        return -EINVAL;
    }
    
    return 0;
}

int config_manager_export_json(char *json_buffer, size_t buffer_size)
{
    if (!json_buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    return format_json_config(&current_config, json_buffer, buffer_size);
}

int config_manager_import_json(const char *json_string)
{
    if (!json_string) {
        return -EINVAL;
    }
    
    struct app_config temp_config;
    int ret = parse_json_config(json_string, &temp_config);
    if (ret != 0) {
        return ret;
    }
    
    return config_manager_set(&temp_config);
}

const char *config_manager_get_file_path(void)
{
    return "nvs://config";
}

bool config_manager_is_modified(void)
{
    return config_modified;
}

int config_manager_mark_clean(void)
{
    config_modified = false;
    return 0;
}