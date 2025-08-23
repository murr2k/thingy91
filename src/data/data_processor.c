/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "data_processor.h"
#include "data_buffer.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/crc.h>
#include <zephyr/data/json.h>
#include <stdio.h>
#include <math.h>

LOG_MODULE_REGISTER(data_processor, CONFIG_LOG_DEFAULT_LEVEL);

/* Processing statistics */
static struct data_stats stats = {0};

/* Filter configuration */
static struct data_filter_config filter_config = {
    .enable_smoothing = true,
    .smoothing_factor = 3,
    .enable_outlier_detection = true,
    .outlier_threshold = 3.0f,
    .enable_delta_compression = false,
    .delta_threshold = 0.1f
};

/* Historical data for filtering */
static struct sensor_data history[10];
static uint8_t history_index = 0;
static uint8_t history_count = 0;

/* Timing tracking */
static uint64_t processing_start_time = 0;
static uint64_t transmission_start_time = 0;

/* Forward declarations */
static int apply_smoothing_filter(struct sensor_data *data);
static int detect_outliers(const struct sensor_data *data);
static float calculate_moving_average(float new_value, float *history, 
                                    uint8_t history_size, uint8_t factor);
static float calculate_standard_deviation(float *values, uint8_t count);
static void update_processing_stats(uint64_t processing_time);
static void add_to_history(const struct sensor_data *data);

static int apply_smoothing_filter(struct sensor_data *data)
{
    if (!filter_config.enable_smoothing || history_count == 0) {
        return 0;
    }
    
    /* Create arrays for moving average calculation */
    float temp_history[10] = {0};
    float humidity_history[10] = {0};
    float pressure_history[10] = {0};
    float accel_x_history[10] = {0};
    float accel_y_history[10] = {0};
    float accel_z_history[10] = {0};
    
    /* Fill history arrays */
    for (int i = 0; i < history_count; i++) {
        temp_history[i] = history[i].temperature;
        humidity_history[i] = history[i].humidity;
        pressure_history[i] = history[i].pressure;
        accel_x_history[i] = history[i].accel_x;
        accel_y_history[i] = history[i].accel_y;
        accel_z_history[i] = history[i].accel_z;
    }
    
    /* Apply smoothing */
    data->temperature = calculate_moving_average(data->temperature, temp_history,
                                               history_count, filter_config.smoothing_factor);
    data->humidity = calculate_moving_average(data->humidity, humidity_history,
                                            history_count, filter_config.smoothing_factor);
    data->pressure = calculate_moving_average(data->pressure, pressure_history,
                                            history_count, filter_config.smoothing_factor);
    data->accel_x = calculate_moving_average(data->accel_x, accel_x_history,
                                           history_count, filter_config.smoothing_factor);
    data->accel_y = calculate_moving_average(data->accel_y, accel_y_history,
                                           history_count, filter_config.smoothing_factor);
    data->accel_z = calculate_moving_average(data->accel_z, accel_z_history,
                                           history_count, filter_config.smoothing_factor);
    
    return 0;
}

static int detect_outliers(const struct sensor_data *data)
{
    if (!filter_config.enable_outlier_detection || history_count < 3) {
        return 0; /* Not enough data or detection disabled */
    }
    
    /* Check temperature outlier */
    float temp_values[10];
    for (int i = 0; i < history_count; i++) {
        temp_values[i] = history[i].temperature;
    }
    float temp_std = calculate_standard_deviation(temp_values, history_count);
    float temp_avg = 0;
    for (int i = 0; i < history_count; i++) {
        temp_avg += temp_values[i];
    }
    temp_avg /= history_count;
    
    if (fabsf(data->temperature - temp_avg) > (filter_config.outlier_threshold * temp_std)) {
        LOG_WRN("Temperature outlier detected: %.2f (avg: %.2f, std: %.2f)",
                data->temperature, temp_avg, temp_std);
        return 1; /* Outlier detected */
    }
    
    return 0; /* No outliers */
}

static float calculate_moving_average(float new_value, float *history, 
                                    uint8_t history_size, uint8_t factor)
{
    if (history_size == 0) {
        return new_value;
    }
    
    float sum = new_value * factor;
    uint8_t weight_sum = factor;
    
    for (int i = 0; i < history_size && i < 5; i++) {
        uint8_t weight = factor - i;
        if (weight < 1) weight = 1;
        sum += history[history_size - 1 - i] * weight;
        weight_sum += weight;
    }
    
    return sum / weight_sum;
}

static float calculate_standard_deviation(float *values, uint8_t count)
{
    if (count < 2) {
        return 0.0f;
    }
    
    float mean = 0.0f;
    for (int i = 0; i < count; i++) {
        mean += values[i];
    }
    mean /= count;
    
    float variance = 0.0f;
    for (int i = 0; i < count; i++) {
        float diff = values[i] - mean;
        variance += diff * diff;
    }
    variance /= (count - 1);
    
    return sqrtf(variance);
}

static void update_processing_stats(uint64_t processing_time)
{
    stats.processed_samples++;
    
    /* Update average processing time */
    if (stats.processed_samples == 1) {
        stats.avg_processing_time_ms = (float)processing_time / 1000.0f;
    } else {
        float alpha = 0.1f; /* Smoothing factor */
        stats.avg_processing_time_ms = (1.0f - alpha) * stats.avg_processing_time_ms +
                                      alpha * (float)processing_time / 1000.0f;
    }
}

static void add_to_history(const struct sensor_data *data)
{
    history[history_index] = *data;
    history_index = (history_index + 1) % ARRAY_SIZE(history);
    if (history_count < ARRAY_SIZE(history)) {
        history_count++;
    }
}

int data_processor_init(void)
{
    LOG_INF("Initializing data processor");
    
    /* Initialize data buffer */
    int ret = data_buffer_init();
    if (ret) {
        LOG_ERR("Failed to initialize data buffer: %d", ret);
        return ret;
    }
    
    /* Reset statistics */
    memset(&stats, 0, sizeof(stats));
    
    /* Clear history */
    memset(history, 0, sizeof(history));
    history_index = 0;
    history_count = 0;
    
    LOG_INF("Data processor initialized successfully");
    return 0;
}

int data_processor_process(const struct sensor_data *raw_data, 
                          struct sensor_data *processed_data)
{
    if (!raw_data || !processed_data) {
        return -EINVAL;
    }
    
    processing_start_time = k_uptime_get();
    stats.total_samples++;
    
    /* Copy raw data to processed data */
    memcpy(processed_data, raw_data, sizeof(*processed_data));
    
    /* Apply filters if configured */
    if (filter_config.enable_smoothing) {
        int ret = apply_smoothing_filter(processed_data);
        if (ret) {
            LOG_WRN("Smoothing filter failed: %d", ret);
        }
    }
    
    /* Detect outliers */
    if (filter_config.enable_outlier_detection) {
        int ret = detect_outliers(processed_data);
        if (ret > 0) {
            LOG_WRN("Outlier detected, using previous value");
            if (history_count > 0) {
                uint8_t prev_idx = (history_index - 1 + ARRAY_SIZE(history)) % ARRAY_SIZE(history);
                memcpy(processed_data, &history[prev_idx], sizeof(*processed_data));
                processed_data->timestamp = raw_data->timestamp;
            }
        }
    }
    
    /* Add to history for future filtering */
    add_to_history(processed_data);
    
    /* Update statistics */
    uint64_t processing_time = k_uptime_get() - processing_start_time;
    update_processing_stats(processing_time);
    
    LOG_DBG("Processed sensor data in %llu us", processing_time);
    return 0;
}

int data_processor_format_json(const struct sensor_data *data, 
                              char *json_buffer, size_t buffer_size)
{
    if (!data || !json_buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    /* Create JSON string */
    int ret = snprintf(json_buffer, buffer_size,
        "{"
        "\"timestamp\":%llu,"
        "\"device_id\":\"thingy91_demo\","
        "\"environmental\":{"
            "\"temperature\":%.2f,"
            "\"humidity\":%.2f,"
            "\"pressure\":%.2f,"
            "\"gas_resistance\":%.0f"
        "},"
        "\"motion\":{"
            "\"accel_x\":%.3f,"
            "\"accel_y\":%.3f,"
            "\"accel_z\":%.3f,"
            "\"gyro_x\":%.3f,"
            "\"gyro_y\":%.3f,"
            "\"gyro_z\":%.3f"
        "},"
        "\"metadata\":{"
            "\"data_quality\":%d,"
            "\"valid\":%s"
        "}"
        "}",
        data->timestamp,
        data->temperature,
        data->humidity,
        data->pressure,
        data->gas_resistance,
        data->accel_x,
        data->accel_y,
        data->accel_z,
        data->gyro_x,
        data->gyro_y,
        data->gyro_z,
        data->data_quality,
        data->valid ? "true" : "false"
    );
    
    if (ret < 0 || ret >= buffer_size) {
        LOG_ERR("JSON formatting failed or buffer too small: %d", ret);
        return -ENOBUFS;
    }
    
    return ret;
}

int data_processor_format_binary(const struct sensor_data *data,
                                uint8_t *binary_buffer, size_t buffer_size)
{
    if (!data || !binary_buffer || buffer_size < sizeof(*data)) {
        return -EINVAL;
    }
    
    /* Simple binary format - just copy the structure */
    memcpy(binary_buffer, data, sizeof(*data));
    
    /* Add CRC for integrity */
    if (buffer_size >= sizeof(*data) + sizeof(uint16_t)) {
        uint16_t crc = crc16_ccitt(0, binary_buffer, sizeof(*data));
        memcpy(binary_buffer + sizeof(*data), &crc, sizeof(crc));
        return sizeof(*data) + sizeof(uint16_t);
    }
    
    return sizeof(*data);
}

int data_processor_buffer_data(const char *json_data)
{
    if (!json_data) {
        return -EINVAL;
    }
    
    int ret = data_buffer_add(json_data);
    if (ret == 0) {
        stats.buffered_samples++;
    } else if (ret == -ENOSPC) {
        stats.buffer_full_count++;
        stats.dropped_samples++;
    }
    
    return ret;
}

int data_processor_get_buffered_data(char *json_buffer, size_t buffer_size)
{
    if (!json_buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    int ret = data_buffer_get(json_buffer, buffer_size);
    if (ret > 0) {
        stats.transmitted_samples++;
    }
    
    return ret;
}

int data_processor_clear_buffer(void)
{
    int cleared = data_buffer_clear();
    LOG_INF("Cleared %d buffered data entries", cleared);
    return cleared;
}

int data_processor_get_stats(struct data_stats *stats_out)
{
    if (!stats_out) {
        return -EINVAL;
    }
    
    memcpy(stats_out, &stats, sizeof(*stats_out));
    return 0;
}

int data_processor_configure_filter(const struct data_filter_config *config)
{
    if (!config) {
        return -EINVAL;
    }
    
    memcpy(&filter_config, config, sizeof(filter_config));
    
    LOG_INF("Data filter configured - Smoothing: %s (factor: %d), "
            "Outlier detection: %s (threshold: %.2f), "
            "Delta compression: %s (threshold: %.3f)",
            filter_config.enable_smoothing ? "enabled" : "disabled",
            filter_config.smoothing_factor,
            filter_config.enable_outlier_detection ? "enabled" : "disabled",
            filter_config.outlier_threshold,
            filter_config.enable_delta_compression ? "enabled" : "disabled",
            filter_config.delta_threshold);
    
    return 0;
}

int data_processor_reset_stats(void)
{
    memset(&stats, 0, sizeof(stats));
    LOG_INF("Data processing statistics reset");
    return 0;
}

int data_processor_compress(const uint8_t *input, size_t input_len,
                           uint8_t *output, size_t output_size)
{
    if (!input || !output || input_len == 0 || output_size == 0) {
        return -EINVAL;
    }
    
    /* Simple RLE compression for demonstration */
    size_t output_pos = 0;
    size_t input_pos = 0;
    
    while (input_pos < input_len && output_pos < output_size - 1) {
        uint8_t current_byte = input[input_pos];
        uint8_t count = 1;
        
        /* Count consecutive identical bytes */
        while (input_pos + count < input_len && 
               input[input_pos + count] == current_byte && 
               count < 255) {
            count++;
        }
        
        if (count > 3 || current_byte == 0) {
            /* Use RLE encoding */
            if (output_pos + 2 >= output_size) break;
            output[output_pos++] = 0; /* RLE marker */
            output[output_pos++] = count;
            output[output_pos++] = current_byte;
        } else {
            /* Copy bytes directly */
            for (int i = 0; i < count && output_pos < output_size; i++) {
                if (input[input_pos + i] == 0) {
                    /* Escape zero bytes */
                    if (output_pos + 1 >= output_size) break;
                    output[output_pos++] = 0;
                    output[output_pos++] = 1;
                    output[output_pos++] = 0;
                } else {
                    output[output_pos++] = input[input_pos + i];
                }
            }
        }
        
        input_pos += count;
    }
    
    return output_pos;
}

int data_processor_decompress(const uint8_t *input, size_t input_len,
                             uint8_t *output, size_t output_size)
{
    if (!input || !output || input_len == 0 || output_size == 0) {
        return -EINVAL;
    }
    
    /* Simple RLE decompression */
    size_t output_pos = 0;
    size_t input_pos = 0;
    
    while (input_pos < input_len && output_pos < output_size) {
        if (input[input_pos] == 0 && input_pos + 1 < input_len) {
            /* RLE sequence */
            uint8_t count = input[input_pos + 1];
            if (count == 1 && input_pos + 2 < input_len && input[input_pos + 2] == 0) {
                /* Escaped zero */
                output[output_pos++] = 0;
                input_pos += 3;
            } else if (input_pos + 2 < input_len) {
                /* RLE sequence */
                uint8_t value = input[input_pos + 2];
                for (int i = 0; i < count && output_pos < output_size; i++) {
                    output[output_pos++] = value;
                }
                input_pos += 3;
            } else {
                break; /* Invalid sequence */
            }
        } else {
            /* Direct copy */
            output[output_pos++] = input[input_pos++];
        }
    }
    
    return output_pos;
}