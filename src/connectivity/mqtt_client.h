/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef MQTT_CLIENT_H_
#define MQTT_CLIENT_H_

#include <zephyr/kernel.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief MQTT connection status
 */
enum mqtt_status {
    MQTT_STATUS_DISCONNECTED,
    MQTT_STATUS_CONNECTING,
    MQTT_STATUS_CONNECTED,
    MQTT_STATUS_ERROR
};

/**
 * @brief MQTT configuration structure
 */
struct mqtt_config {
    char broker_hostname[64];
    uint16_t broker_port;
    char client_id[32];
    char username[32];
    char password[64];
    bool use_tls;
    uint16_t keepalive;
    char publish_topic[64];
    char subscribe_topic[64];
};

/**
 * @brief MQTT message structure
 */
struct mqtt_message {
    char topic[64];
    char payload[512];
    uint16_t payload_len;
    uint8_t qos;
    bool retain;
};

/**
 * @brief MQTT event callback function type
 */
typedef void (*mqtt_event_cb_t)(enum mqtt_status status);

/**
 * @brief MQTT message callback function type
 */
typedef void (*mqtt_message_cb_t)(const struct mqtt_message *message);

/**
 * @brief Initialize MQTT client
 * 
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_init(void);

/**
 * @brief Configure MQTT client
 * 
 * @param config MQTT configuration
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_configure(const struct mqtt_config *config);

/**
 * @brief Connect to MQTT broker
 * 
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_connect(void);

/**
 * @brief Disconnect from MQTT broker
 * 
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_disconnect(void);

/**
 * @brief Check if MQTT client is connected
 * 
 * @return true if connected, false otherwise
 */
bool mqtt_client_is_connected(void);

/**
 * @brief Check if MQTT client has error
 * 
 * @return true if error, false otherwise
 */
bool mqtt_client_has_error(void);

/**
 * @brief Publish data to MQTT broker
 * 
 * @param data Data to publish (JSON string)
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_publish_data(const char *data);

/**
 * @brief Publish message to MQTT broker
 * 
 * @param topic Topic to publish to
 * @param payload Message payload
 * @param payload_len Length of payload
 * @param qos Quality of Service (0, 1, or 2)
 * @param retain Retain flag
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_publish(const char *topic, const char *payload, 
                       size_t payload_len, uint8_t qos, bool retain);

/**
 * @brief Subscribe to MQTT topic
 * 
 * @param topic Topic to subscribe to
 * @param qos Quality of Service (0, 1, or 2)
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_subscribe(const char *topic, uint8_t qos);

/**
 * @brief Unsubscribe from MQTT topic
 * 
 * @param topic Topic to unsubscribe from
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_unsubscribe(const char *topic);

/**
 * @brief Set MQTT event callback
 * 
 * @param callback Callback function for MQTT events
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_set_event_callback(mqtt_event_cb_t callback);

/**
 * @brief Set MQTT message callback
 * 
 * @param callback Callback function for received messages
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_set_message_callback(mqtt_message_cb_t callback);

/**
 * @brief Get MQTT connection statistics
 * 
 * @param messages_sent Number of messages sent
 * @param messages_received Number of messages received
 * @param bytes_sent Number of bytes sent
 * @param bytes_received Number of bytes received
 * @return 0 on success, negative errno on failure
 */
int mqtt_client_get_stats(uint32_t *messages_sent, uint32_t *messages_received,
                         uint32_t *bytes_sent, uint32_t *bytes_received);

#ifdef __cplusplus
}
#endif

#endif /* MQTT_CLIENT_H_ */