/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "data_buffer.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/fs/nvs.h>
#include <string.h>

LOG_MODULE_REGISTER(data_buffer, CONFIG_LOG_DEFAULT_LEVEL);

/* Buffer configuration defaults */
static struct data_buffer_config config = {
    .max_entries = CONFIG_THINGY91_DEMO_DATA_BUFFER_SIZE,
    .max_entry_size = 512,
    .enable_persistence = false,
    .enable_compression = false,
    .retention_time_ms = 24 * 60 * 60 * 1000  /* 24 hours */
};

/* Buffer entry structure */
struct buffer_entry {
    uint64_t timestamp;
    uint16_t data_len;
    uint8_t data[512];  /* Maximum entry size */
};

/* Ring buffer for data storage */
static struct buffer_entry *buffer_entries;
static size_t buffer_head = 0;
static size_t buffer_tail = 0;
static size_t buffer_count = 0;
static bool buffer_initialized = false;

/* NVS file system for persistence */
static struct nvs_fs nvs;
static bool nvs_initialized = false;

/* Mutex for thread safety */
static struct k_mutex buffer_mutex;

/* Forward declarations */
static int init_nvs_storage(void);
static uint16_t get_nvs_id(size_t index);
static int save_entry_to_nvs(size_t index, const struct buffer_entry *entry);
static int load_entry_from_nvs(size_t index, struct buffer_entry *entry);
static bool is_buffer_full_internal(void);
static size_t get_next_index(size_t current);

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
    nvs.sector_count = 8;  /* Use 8 sectors for data buffer */
    
    ret = nvs_mount(&nvs);
    if (ret) {
        LOG_ERR("Failed to mount NVS: %d", ret);
        return ret;
    }
    
    nvs_initialized = true;
    LOG_INF("NVS storage initialized for data buffer persistence");
    return 0;
#else
    LOG_WRN("NVS not configured, persistence disabled");
    return -ENOSYS;
#endif
}

static uint16_t get_nvs_id(size_t index)
{
    /* NVS IDs for buffer entries start from 1000 */
    return 1000 + (uint16_t)index;
}

static int save_entry_to_nvs(size_t index, const struct buffer_entry *entry)
{
#ifdef CONFIG_NVS
    if (!nvs_initialized || !config.enable_persistence) {
        return 0;  /* No-op if persistence disabled */
    }
    
    uint16_t id = get_nvs_id(index);
    size_t entry_size = sizeof(entry->timestamp) + sizeof(entry->data_len) + entry->data_len;
    
    ssize_t ret = nvs_write(&nvs, id, entry, entry_size);
    if (ret < 0) {
        LOG_ERR("Failed to save entry %zu to NVS: %d", index, (int)ret);
        return (int)ret;
    }
    
    return 0;
#else
    return -ENOSYS;
#endif
}

static int load_entry_from_nvs(size_t index, struct buffer_entry *entry)
{
#ifdef CONFIG_NVS
    if (!nvs_initialized || !config.enable_persistence) {
        return -ENOENT;
    }
    
    uint16_t id = get_nvs_id(index);
    
    ssize_t ret = nvs_read(&nvs, id, entry, sizeof(*entry));
    if (ret < 0) {
        if (ret != -ENOENT) {
            LOG_ERR("Failed to load entry %zu from NVS: %d", index, (int)ret);
        }
        return (int)ret;
    }
    
    return 0;
#else
    return -ENOSYS;
#endif
}

static bool is_buffer_full_internal(void)
{
    return buffer_count >= config.max_entries;
}

static size_t get_next_index(size_t current)
{
    return (current + 1) % config.max_entries;
}

int data_buffer_init(void)
{
    int ret;
    
    LOG_INF("Initializing data buffer with %zu entries", config.max_entries);
    
    /* Allocate buffer memory */
    buffer_entries = k_malloc(config.max_entries * sizeof(struct buffer_entry));
    if (!buffer_entries) {
        LOG_ERR("Failed to allocate buffer memory");
        return -ENOMEM;
    }
    
    /* Initialize buffer state */
    buffer_head = 0;
    buffer_tail = 0;
    buffer_count = 0;
    
    /* Initialize mutex */
    ret = k_mutex_init(&buffer_mutex);
    if (ret) {
        LOG_ERR("Failed to initialize buffer mutex: %d", ret);
        k_free(buffer_entries);
        return ret;
    }
    
    /* Initialize NVS storage if persistence is enabled */
    if (config.enable_persistence) {
        ret = init_nvs_storage();
        if (ret) {
            LOG_WRN("NVS initialization failed, persistence disabled: %d", ret);
            config.enable_persistence = false;
        }
    }
    
    buffer_initialized = true;
    LOG_INF("Data buffer initialized successfully");
    
    return 0;
}

int data_buffer_configure(const struct data_buffer_config *new_config)
{
    if (!new_config) {
        return -EINVAL;
    }
    
    if (buffer_initialized && new_config->max_entries != config.max_entries) {
        LOG_WRN("Cannot change buffer size after initialization");
        return -EINVAL;
    }
    
    memcpy(&config, new_config, sizeof(config));
    
    LOG_INF("Data buffer configured: %zu entries, %zu bytes per entry, "
            "persistence: %s, compression: %s",
            config.max_entries, config.max_entry_size,
            config.enable_persistence ? "enabled" : "disabled",
            config.enable_compression ? "enabled" : "disabled");
    
    return 0;
}

int data_buffer_add(const char *data)
{
    if (!data) {
        return -EINVAL;
    }
    
    size_t data_len = strlen(data);
    return data_buffer_add_binary((const uint8_t *)data, data_len);
}

int data_buffer_add_binary(const uint8_t *data, size_t data_len)
{
    int ret;
    
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    if (!data || data_len == 0 || data_len > config.max_entry_size) {
        return -EINVAL;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    /* Check if buffer is full */
    if (is_buffer_full_internal()) {
        /* Remove oldest entry to make space */
        buffer_tail = get_next_index(buffer_tail);
        buffer_count--;
    }
    
    /* Add new entry */
    struct buffer_entry *entry = &buffer_entries[buffer_head];
    entry->timestamp = k_uptime_get();
    entry->data_len = data_len;
    memcpy(entry->data, data, data_len);
    
    /* Save to persistent storage if enabled */
    if (config.enable_persistence) {
        ret = save_entry_to_nvs(buffer_head, entry);
        if (ret) {
            LOG_WRN("Failed to persist buffer entry: %d", ret);
        }
    }
    
    buffer_head = get_next_index(buffer_head);
    buffer_count++;
    
    k_mutex_unlock(&buffer_mutex);
    
    LOG_DBG("Added %zu bytes to buffer (count: %zu)", data_len, buffer_count);
    return 0;
}

int data_buffer_get(char *buffer, size_t buffer_size)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    if (!buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    if (buffer_count == 0) {
        k_mutex_unlock(&buffer_mutex);
        return 0;  /* No data available */
    }
    
    struct buffer_entry *entry = &buffer_entries[buffer_tail];
    
    /* Check if buffer is large enough */
    if (buffer_size <= entry->data_len) {
        k_mutex_unlock(&buffer_mutex);
        return -ENOBUFS;
    }
    
    /* Copy data to output buffer */
    memcpy(buffer, entry->data, entry->data_len);
    buffer[entry->data_len] = '\0';  /* Null terminate for string data */
    
    /* Remove entry from buffer */
    buffer_tail = get_next_index(buffer_tail);
    buffer_count--;
    
    k_mutex_unlock(&buffer_mutex);
    
    LOG_DBG("Retrieved %d bytes from buffer (count: %zu)", entry->data_len, buffer_count);
    return entry->data_len;
}

int data_buffer_get_binary(uint8_t *buffer, size_t buffer_size)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    if (!buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    if (buffer_count == 0) {
        k_mutex_unlock(&buffer_mutex);
        return 0;  /* No data available */
    }
    
    struct buffer_entry *entry = &buffer_entries[buffer_tail];
    
    /* Check if buffer is large enough */
    if (buffer_size < entry->data_len) {
        k_mutex_unlock(&buffer_mutex);
        return -ENOBUFS;
    }
    
    /* Copy data to output buffer */
    memcpy(buffer, entry->data, entry->data_len);
    
    /* Remove entry from buffer */
    buffer_tail = get_next_index(buffer_tail);
    buffer_count--;
    
    k_mutex_unlock(&buffer_mutex);
    
    return entry->data_len;
}

int data_buffer_peek(char *buffer, size_t buffer_size)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    if (!buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    if (buffer_count == 0) {
        k_mutex_unlock(&buffer_mutex);
        return 0;  /* No data available */
    }
    
    struct buffer_entry *entry = &buffer_entries[buffer_tail];
    
    /* Check if buffer is large enough */
    if (buffer_size <= entry->data_len) {
        k_mutex_unlock(&buffer_mutex);
        return -ENOBUFS;
    }
    
    /* Copy data to output buffer without removing entry */
    memcpy(buffer, entry->data, entry->data_len);
    buffer[entry->data_len] = '\0';  /* Null terminate for string data */
    
    k_mutex_unlock(&buffer_mutex);
    
    return entry->data_len;
}

int data_buffer_remove_oldest(void)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    if (buffer_count == 0) {
        k_mutex_unlock(&buffer_mutex);
        return -ENOENT;
    }
    
    buffer_tail = get_next_index(buffer_tail);
    buffer_count--;
    
    k_mutex_unlock(&buffer_mutex);
    
    return 0;
}

int data_buffer_clear(void)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    int cleared = buffer_count;
    buffer_head = 0;
    buffer_tail = 0;
    buffer_count = 0;
    
    k_mutex_unlock(&buffer_mutex);
    
    return cleared;
}

int data_buffer_get_status(struct data_buffer_status *status)
{
    if (!buffer_initialized || !status) {
        return -EINVAL;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    status->total_entries = buffer_count;
    status->available_space = config.max_entries - buffer_count;
    status->is_full = is_buffer_full_internal();
    status->total_bytes_stored = 0;
    status->oldest_timestamp = 0;
    status->newest_timestamp = 0;
    
    if (buffer_count > 0) {
        /* Find oldest and newest timestamps, calculate total bytes */
        for (size_t i = 0; i < buffer_count; i++) {
            size_t idx = (buffer_tail + i) % config.max_entries;
            struct buffer_entry *entry = &buffer_entries[idx];
            
            status->total_bytes_stored += entry->data_len;
            
            if (i == 0) {
                status->oldest_timestamp = entry->timestamp;
            }
            if (i == buffer_count - 1) {
                status->newest_timestamp = entry->timestamp;
            }
        }
    }
    
    k_mutex_unlock(&buffer_mutex);
    
    return 0;
}

bool data_buffer_is_empty(void)
{
    if (!buffer_initialized) {
        return true;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    bool empty = (buffer_count == 0);
    k_mutex_unlock(&buffer_mutex);
    
    return empty;
}

bool data_buffer_is_full(void)
{
    if (!buffer_initialized) {
        return false;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    bool full = is_buffer_full_internal();
    k_mutex_unlock(&buffer_mutex);
    
    return full;
}

size_t data_buffer_get_count(void)
{
    if (!buffer_initialized) {
        return 0;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    size_t count = buffer_count;
    k_mutex_unlock(&buffer_mutex);
    
    return count;
}

int data_buffer_save_to_flash(void)
{
    if (!buffer_initialized || !config.enable_persistence) {
        return -ENODEV;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    int saved = 0;
    for (size_t i = 0; i < buffer_count; i++) {
        size_t idx = (buffer_tail + i) % config.max_entries;
        int ret = save_entry_to_nvs(idx, &buffer_entries[idx]);
        if (ret == 0) {
            saved++;
        }
    }
    
    k_mutex_unlock(&buffer_mutex);
    
    LOG_INF("Saved %d buffer entries to flash", saved);
    return saved;
}

int data_buffer_load_from_flash(void)
{
    if (!buffer_initialized || !config.enable_persistence) {
        return -ENODEV;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    int loaded = 0;
    for (size_t i = 0; i < config.max_entries; i++) {
        struct buffer_entry entry;
        int ret = load_entry_from_nvs(i, &entry);
        if (ret == 0) {
            memcpy(&buffer_entries[buffer_head], &entry, sizeof(entry));
            buffer_head = get_next_index(buffer_head);
            buffer_count++;
            loaded++;
            
            if (buffer_count >= config.max_entries) {
                break;
            }
        }
    }
    
    k_mutex_unlock(&buffer_mutex);
    
    LOG_INF("Loaded %d buffer entries from flash", loaded);
    return loaded;
}

int data_buffer_cleanup_expired(void)
{
    if (!buffer_initialized) {
        return -ENODEV;
    }
    
    k_mutex_lock(&buffer_mutex, K_FOREVER);
    
    uint64_t current_time = k_uptime_get();
    int removed = 0;
    
    while (buffer_count > 0) {
        struct buffer_entry *entry = &buffer_entries[buffer_tail];
        
        /* Check if entry has expired */
        if (current_time - entry->timestamp > config.retention_time_ms) {
            buffer_tail = get_next_index(buffer_tail);
            buffer_count--;
            removed++;
        } else {
            break;  /* Entries are ordered by time, so no more expired entries */
        }
    }
    
    k_mutex_unlock(&buffer_mutex);
    
    if (removed > 0) {
        LOG_INF("Removed %d expired buffer entries", removed);
    }
    
    return removed;
}