/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef DATA_BUFFER_H_
#define DATA_BUFFER_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Data buffer configuration
 */
struct data_buffer_config {
    size_t max_entries;         /* Maximum number of buffered entries */
    size_t max_entry_size;      /* Maximum size of each entry */
    bool enable_persistence;    /* Enable flash storage persistence */
    bool enable_compression;    /* Enable data compression */
    uint32_t retention_time_ms; /* Data retention time in milliseconds */
};

/**
 * @brief Data buffer status
 */
struct data_buffer_status {
    size_t total_entries;       /* Total number of entries */
    size_t available_space;     /* Available space in entries */
    size_t oldest_timestamp;    /* Timestamp of oldest entry */
    size_t newest_timestamp;    /* Timestamp of newest entry */
    size_t total_bytes_stored;  /* Total bytes stored */
    bool is_full;              /* Buffer full indicator */
};

/**
 * @brief Initialize data buffer
 * 
 * @return 0 on success, negative errno on failure
 */
int data_buffer_init(void);

/**
 * @brief Configure data buffer
 * 
 * @param config Buffer configuration
 * @return 0 on success, negative errno on failure
 */
int data_buffer_configure(const struct data_buffer_config *config);

/**
 * @brief Add data to buffer
 * 
 * @param data Data to add (null-terminated string)
 * @return 0 on success, negative errno on failure
 */
int data_buffer_add(const char *data);

/**
 * @brief Add binary data to buffer
 * 
 * @param data Binary data to add
 * @param data_len Length of binary data
 * @return 0 on success, negative errno on failure
 */
int data_buffer_add_binary(const uint8_t *data, size_t data_len);

/**
 * @brief Get next data entry from buffer
 * 
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @return Length of data on success, 0 if no data, negative errno on failure
 */
int data_buffer_get(char *buffer, size_t buffer_size);

/**
 * @brief Get next binary data entry from buffer
 * 
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @return Length of data on success, 0 if no data, negative errno on failure
 */
int data_buffer_get_binary(uint8_t *buffer, size_t buffer_size);

/**
 * @brief Peek at next data entry without removing it
 * 
 * @param buffer Output buffer
 * @param buffer_size Size of output buffer
 * @return Length of data on success, 0 if no data, negative errno on failure
 */
int data_buffer_peek(char *buffer, size_t buffer_size);

/**
 * @brief Remove oldest entry from buffer
 * 
 * @return 0 on success, negative errno on failure
 */
int data_buffer_remove_oldest(void);

/**
 * @brief Clear all buffered data
 * 
 * @return Number of entries cleared
 */
int data_buffer_clear(void);

/**
 * @brief Get buffer status information
 * 
 * @param status Pointer to status structure to fill
 * @return 0 on success, negative errno on failure
 */
int data_buffer_get_status(struct data_buffer_status *status);

/**
 * @brief Check if buffer is empty
 * 
 * @return true if empty, false otherwise
 */
bool data_buffer_is_empty(void);

/**
 * @brief Check if buffer is full
 * 
 * @return true if full, false otherwise
 */
bool data_buffer_is_full(void);

/**
 * @brief Get number of entries in buffer
 * 
 * @return Number of entries
 */
size_t data_buffer_get_count(void);

/**
 * @brief Save buffer to persistent storage
 * 
 * @return 0 on success, negative errno on failure
 */
int data_buffer_save_to_flash(void);

/**
 * @brief Load buffer from persistent storage
 * 
 * @return 0 on success, negative errno on failure
 */
int data_buffer_load_from_flash(void);

/**
 * @brief Remove expired entries based on retention time
 * 
 * @return Number of entries removed
 */
int data_buffer_cleanup_expired(void);

#ifdef __cplusplus
}
#endif

#endif /* DATA_BUFFER_H_ */