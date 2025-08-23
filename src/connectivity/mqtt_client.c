/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "mqtt_client.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/mqtt.h>
#include <zephyr/random/random.h>
#include <zephyr/sys/printk.h>

LOG_MODULE_REGISTER(mqtt_client, CONFIG_LOG_DEFAULT_LEVEL);

/* MQTT client configuration */
static struct mqtt_config mqtt_cfg = {
    .broker_hostname = "broker.hivemq.com",
    .broker_port = 8883,
    .client_id = "thingy91_demo",
    .use_tls = true,
    .keepalive = CONFIG_THINGY91_DEMO_MQTT_KEEPALIVE,
    .publish_topic = "thingy91/demo/sensor_data",
    .subscribe_topic = "thingy91/demo/commands"
};

/* MQTT client state */
static struct mqtt_client client;
static struct sockaddr_storage broker;
static enum mqtt_status current_status = MQTT_STATUS_DISCONNECTED;
static mqtt_event_cb_t event_callback = NULL;
static mqtt_message_cb_t message_callback = NULL;

/* MQTT buffers */
static uint8_t rx_buffer[512];
static uint8_t tx_buffer[512];
static uint8_t payload_buf[1024];

/* Statistics */
static uint32_t messages_sent = 0;
static uint32_t messages_received = 0;
static uint32_t bytes_sent = 0;
static uint32_t bytes_received = 0;

/* Work items */
static struct k_work_delayable keepalive_work;
static struct k_work mqtt_work;

/* Forward declarations */
static void mqtt_evt_handler(struct mqtt_client *const client,
                            const struct mqtt_evt *evt);
static void keepalive_work_handler(struct k_work *work);
static void mqtt_work_handler(struct k_work *work);
static int broker_init(void);
static void generate_client_id(void);
static void update_status(enum mqtt_status new_status);

static void mqtt_evt_handler(struct mqtt_client *const client,
                            const struct mqtt_evt *evt)
{
    switch (evt->type) {
    case MQTT_EVT_CONNACK:
        if (evt->result != 0) {
            LOG_ERR("MQTT connect failed: %d", evt->result);
            update_status(MQTT_STATUS_ERROR);
        } else {
            LOG_INF("MQTT client connected");
            update_status(MQTT_STATUS_CONNECTED);
            
            /* Subscribe to command topic */
            struct mqtt_subscription_list subscription_list = {
                .list = (struct mqtt_topic[]) {
                    {
                        .topic = {
                            .utf8 = mqtt_cfg.subscribe_topic,
                            .size = strlen(mqtt_cfg.subscribe_topic)
                        },
                        .qos = MQTT_QOS_1_AT_LEAST_ONCE
                    }
                },
                .list_count = 1,
                .message_id = sys_rand32_get()
            };
            
            int ret = mqtt_subscribe(client, &subscription_list);
            if (ret) {
                LOG_WRN("Failed to subscribe to command topic: %d", ret);
            } else {
                LOG_INF("Subscribed to topic: %s", mqtt_cfg.subscribe_topic);
            }
        }
        break;
        
    case MQTT_EVT_DISCONNECT:
        LOG_INF("MQTT client disconnected: %d", evt->result);
        update_status(MQTT_STATUS_DISCONNECTED);
        break;
        
    case MQTT_EVT_SUBACK:
        if (evt->result != 0) {
            LOG_ERR("MQTT subscribe failed: %d", evt->result);
        } else {
            LOG_INF("MQTT subscribe successful");
        }
        break;
        
    case MQTT_EVT_PUBACK:
        if (evt->result != 0) {
            LOG_ERR("MQTT publish failed: %d", evt->result);
        } else {
            LOG_DBG("MQTT publish successful");
        }
        break;
        
    case MQTT_EVT_PUBLISH:
        {
            struct mqtt_message msg;
            int len;
            
            len = MIN(evt->param.publish.message.payload.len, 
                     sizeof(payload_buf) - 1);
            
            /* Extract topic */
            len = MIN(evt->param.publish.message.topic.len, sizeof(msg.topic) - 1);
            memcpy(msg.topic, evt->param.publish.message.topic.utf8, len);
            msg.topic[len] = '\0';
            
            /* Extract payload */
            len = MIN(evt->param.publish.message.payload.len, sizeof(msg.payload) - 1);
            memcpy(msg.payload, evt->param.publish.message.payload.data, len);
            msg.payload[len] = '\0';
            msg.payload_len = len;
            
            msg.qos = evt->param.publish.message.topic.qos;
            msg.retain = evt->param.publish.message.payload.retain;
            
            LOG_INF("Received MQTT message on topic '%s': %s", msg.topic, msg.payload);
            
            messages_received++;
            bytes_received += msg.payload_len;
            
            if (message_callback) {
                message_callback(&msg);
            }
            
            /* Send PUBACK for QoS 1 messages */
            if (msg.qos == MQTT_QOS_1_AT_LEAST_ONCE) {
                struct mqtt_puback_param puback = {
                    .message_id = evt->param.publish.message_id
                };
                mqtt_publish_qos1_ack(&client, &puback);
            }
        }
        break;
        
    default:
        LOG_DBG("Unhandled MQTT event: %d", evt->type);
        break;
    }
}

static void keepalive_work_handler(struct k_work *work)
{
    int ret;
    
    if (current_status != MQTT_STATUS_CONNECTED) {
        return;
    }
    
    ret = mqtt_ping(&client);
    if (ret) {
        LOG_ERR("Failed to send MQTT ping: %d", ret);
        update_status(MQTT_STATUS_ERROR);
    } else {
        LOG_DBG("MQTT ping sent");
        /* Schedule next keepalive */
        k_work_schedule(&keepalive_work, K_SECONDS(mqtt_cfg.keepalive));
    }
}

static void mqtt_work_handler(struct k_work *work)
{
    int ret;
    
    if (current_status != MQTT_STATUS_CONNECTED) {
        return;
    }
    
    ret = mqtt_input(&client);
    if (ret < 0) {
        LOG_ERR("MQTT input error: %d", ret);
        update_status(MQTT_STATUS_ERROR);
    }
    
    ret = mqtt_live(&client);
    if (ret < 0 && ret != -EAGAIN) {
        LOG_ERR("MQTT live error: %d", ret);
        update_status(MQTT_STATUS_ERROR);
    }
    
    /* Reschedule work if still connected */
    if (current_status == MQTT_STATUS_CONNECTED) {
        k_work_submit(&mqtt_work);
    }
}

static int broker_init(void)
{
    struct sockaddr_in *broker4 = (struct sockaddr_in *)&broker;
    
    broker4->sin_family = AF_INET;
    broker4->sin_port = htons(mqtt_cfg.broker_port);
    
    /* Resolve hostname to IP address */
    struct zsock_addrinfo hints = {
        .ai_family = AF_INET,
        .ai_socktype = SOCK_STREAM
    };
    struct zsock_addrinfo *result;
    
    int ret = zsock_getaddrinfo(mqtt_cfg.broker_hostname, NULL, &hints, &result);
    if (ret == 0) {
        struct sockaddr_in *addr_in = (struct sockaddr_in *)result->ai_addr;
        broker4->sin_addr = addr_in->sin_addr;
        zsock_freeaddrinfo(result);
        
        char addr_str[INET_ADDRSTRLEN];
        zsock_inet_ntop(AF_INET, &broker4->sin_addr, addr_str, sizeof(addr_str));
        LOG_INF("Resolved %s to %s", mqtt_cfg.broker_hostname, addr_str);
    } else {
        LOG_ERR("Failed to resolve hostname %s: %d", mqtt_cfg.broker_hostname, ret);
        return -EHOSTUNREACH;
    }
    
    return 0;
}

static void generate_client_id(void)
{
    uint32_t random_id = sys_rand32_get();
    snprintf(mqtt_cfg.client_id, sizeof(mqtt_cfg.client_id), 
             "thingy91_%08x", random_id);
}

static void update_status(enum mqtt_status new_status)
{
    if (new_status != current_status) {
        current_status = new_status;
        LOG_INF("MQTT status changed to: %d", current_status);
        
        if (event_callback) {
            event_callback(current_status);
        }
        
        /* Handle status-specific actions */
        switch (current_status) {
        case MQTT_STATUS_CONNECTED:
            k_work_schedule(&keepalive_work, K_SECONDS(mqtt_cfg.keepalive));
            k_work_submit(&mqtt_work);
            break;
            
        case MQTT_STATUS_DISCONNECTED:
        case MQTT_STATUS_ERROR:
            k_work_cancel_delayable(&keepalive_work);
            k_work_cancel(&mqtt_work);
            break;
            
        default:
            break;
        }
    }
}

int mqtt_client_init(void)
{
    LOG_INF("Initializing MQTT client");
    
    /* Generate unique client ID */
    generate_client_id();
    
    /* Initialize MQTT client */
    mqtt_client_init(&client);
    
    client.broker = &broker;
    client.evt_cb = mqtt_evt_handler;
    client.client_id.utf8 = (uint8_t *)mqtt_cfg.client_id;
    client.client_id.size = strlen(mqtt_cfg.client_id);
    client.password = NULL;
    client.user_name = NULL;
    client.protocol_version = MQTT_VERSION_3_1_1;
    
    /* Setup buffers */
    client.rx_buf = rx_buffer;
    client.rx_buf_size = sizeof(rx_buffer);
    client.tx_buf = tx_buffer;
    client.tx_buf_size = sizeof(tx_buffer);
    
    /* Configure transport */
    client.transport.type = MQTT_TRANSPORT_NON_SECURE;
    if (mqtt_cfg.use_tls) {
        client.transport.type = MQTT_TRANSPORT_SECURE;
    }
    
    /* Initialize work items */
    k_work_init_delayable(&keepalive_work, keepalive_work_handler);
    k_work_init(&mqtt_work, mqtt_work_handler);
    
    LOG_INF("MQTT client initialized with ID: %s", mqtt_cfg.client_id);
    return 0;
}

int mqtt_client_configure(const struct mqtt_config *config)
{
    if (!config) {
        return -EINVAL;
    }
    
    memcpy(&mqtt_cfg, config, sizeof(mqtt_cfg));
    
    /* Update client configuration */
    client.client_id.utf8 = (uint8_t *)mqtt_cfg.client_id;
    client.client_id.size = strlen(mqtt_cfg.client_id);
    
    if (strlen(mqtt_cfg.username) > 0) {
        client.user_name = (struct mqtt_utf8 *)&(struct mqtt_utf8){
            .utf8 = (uint8_t *)mqtt_cfg.username,
            .size = strlen(mqtt_cfg.username)
        };
    }
    
    if (strlen(mqtt_cfg.password) > 0) {
        client.password = (struct mqtt_utf8 *)&(struct mqtt_utf8){
            .utf8 = (uint8_t *)mqtt_cfg.password,
            .size = strlen(mqtt_cfg.password)
        };
    }
    
    client.transport.type = mqtt_cfg.use_tls ? MQTT_TRANSPORT_SECURE : MQTT_TRANSPORT_NON_SECURE;
    
    LOG_INF("MQTT client configured for broker: %s:%d", 
            mqtt_cfg.broker_hostname, mqtt_cfg.broker_port);
    
    return 0;
}

int mqtt_client_connect(void)
{
    int ret;
    
    if (current_status == MQTT_STATUS_CONNECTED) {
        return 0; /* Already connected */
    }
    
    LOG_INF("Connecting to MQTT broker %s:%d", 
            mqtt_cfg.broker_hostname, mqtt_cfg.broker_port);
    
    update_status(MQTT_STATUS_CONNECTING);
    
    /* Initialize broker address */
    ret = broker_init();
    if (ret) {
        LOG_ERR("Failed to initialize broker address: %d", ret);
        update_status(MQTT_STATUS_ERROR);
        return ret;
    }
    
    /* Connect to broker */
    ret = mqtt_connect(&client);
    if (ret) {
        LOG_ERR("Failed to connect to MQTT broker: %d", ret);
        update_status(MQTT_STATUS_ERROR);
        return ret;
    }
    
    return 0;
}

int mqtt_client_disconnect(void)
{
    int ret;
    
    if (current_status == MQTT_STATUS_DISCONNECTED) {
        return 0; /* Already disconnected */
    }
    
    LOG_INF("Disconnecting from MQTT broker");
    
    ret = mqtt_disconnect(&client);
    if (ret) {
        LOG_ERR("Failed to disconnect from MQTT broker: %d", ret);
        return ret;
    }
    
    update_status(MQTT_STATUS_DISCONNECTED);
    return 0;
}

bool mqtt_client_is_connected(void)
{
    return current_status == MQTT_STATUS_CONNECTED;
}

bool mqtt_client_has_error(void)
{
    return current_status == MQTT_STATUS_ERROR;
}

int mqtt_client_publish_data(const char *data)
{
    return mqtt_client_publish(mqtt_cfg.publish_topic, data, strlen(data), 
                              MQTT_QOS_1_AT_LEAST_ONCE, false);
}

int mqtt_client_publish(const char *topic, const char *payload, 
                       size_t payload_len, uint8_t qos, bool retain)
{
    int ret;
    
    if (current_status != MQTT_STATUS_CONNECTED) {
        LOG_WRN("MQTT client not connected, cannot publish");
        return -ENOTCONN;
    }
    
    struct mqtt_publish_param param = {
        .message.topic.topic.utf8 = (uint8_t *)topic,
        .message.topic.topic.size = strlen(topic),
        .message.topic.qos = qos,
        .message.payload.data = payload,
        .message.payload.len = payload_len,
        .message_id = sys_rand32_get(),
        .dup_flag = 0,
        .retain_flag = retain ? 1 : 0
    };
    
    ret = mqtt_publish(&client, &param);
    if (ret) {
        LOG_ERR("Failed to publish MQTT message: %d", ret);
        return ret;
    }
    
    messages_sent++;
    bytes_sent += payload_len;
    
    LOG_DBG("Published to topic '%s': %.*s", topic, (int)payload_len, payload);
    return 0;
}

int mqtt_client_subscribe(const char *topic, uint8_t qos)
{
    if (current_status != MQTT_STATUS_CONNECTED) {
        return -ENOTCONN;
    }
    
    struct mqtt_subscription_list subscription_list = {
        .list = (struct mqtt_topic[]) {
            {
                .topic = {
                    .utf8 = (uint8_t *)topic,
                    .size = strlen(topic)
                },
                .qos = qos
            }
        },
        .list_count = 1,
        .message_id = sys_rand32_get()
    };
    
    int ret = mqtt_subscribe(&client, &subscription_list);
    if (ret) {
        LOG_ERR("Failed to subscribe to topic '%s': %d", topic, ret);
        return ret;
    }
    
    LOG_INF("Subscribed to topic: %s", topic);
    return 0;
}

int mqtt_client_unsubscribe(const char *topic)
{
    if (current_status != MQTT_STATUS_CONNECTED) {
        return -ENOTCONN;
    }
    
    struct mqtt_subscription_list subscription_list = {
        .list = (struct mqtt_topic[]) {
            {
                .topic = {
                    .utf8 = (uint8_t *)topic,
                    .size = strlen(topic)
                }
            }
        },
        .list_count = 1,
        .message_id = sys_rand32_get()
    };
    
    int ret = mqtt_unsubscribe(&client, &subscription_list);
    if (ret) {
        LOG_ERR("Failed to unsubscribe from topic '%s': %d", topic, ret);
        return ret;
    }
    
    LOG_INF("Unsubscribed from topic: %s", topic);
    return 0;
}

int mqtt_client_set_event_callback(mqtt_event_cb_t callback)
{
    event_callback = callback;
    return 0;
}

int mqtt_client_set_message_callback(mqtt_message_cb_t callback)
{
    message_callback = callback;
    return 0;
}

int mqtt_client_get_stats(uint32_t *msg_sent, uint32_t *msg_received,
                         uint32_t *bytes_sent_out, uint32_t *bytes_received_in)
{
    if (msg_sent) *msg_sent = messages_sent;
    if (msg_received) *msg_received = messages_received;
    if (bytes_sent_out) *bytes_sent_out = bytes_sent;
    if (bytes_received_in) *bytes_received_in = bytes_received;
    
    return 0;
}