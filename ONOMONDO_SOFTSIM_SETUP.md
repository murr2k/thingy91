# Onomondo SoftSIM Integration Guide for Nordic Thingy91 DK

## Overview

This guide provides comprehensive instructions for provisioning the Nordic Thingy91 DK with Onomondo's SoftSIM solution, enabling global cellular connectivity without physical SIM cards.

## Prerequisites

### Hardware Requirements
- Nordic Thingy91 DK
- USB cable for programming
- PC with Windows 11 + WSL2 or Linux

### Software Requirements
- nRF Connect SDK v2.9.1 or later
- nRF9160 modem firmware v1.3.4 or later
- Zephyr RTOS
- PSA Certified Crypto API
- Trusted Firmware-M (TF-M)

### Onomondo Account
- Active Onomondo account (https://onomondo.com)
- SoftSIM profile credentials
- API access for provisioning

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           Application Layer              │
│         (Thingy91 Demo App)             │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         SoftSIM Manager Module          │
│   (Profile Management & Provisioning)   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          nRF9160 Modem Core            │
│     (AT Commands & Network Stack)       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Key Management Unit (KMU)          │
│    (Secure Credential Storage)          │
└─────────────────────────────────────────┘
```

## Step 1: Environment Setup

### 1.1 Initialize Onomondo-enabled SDK

```bash
# Create new workspace for Onomondo integration
mkdir -p ~/onomondo-workspace
cd ~/onomondo-workspace

# Initialize with Onomondo manifest
west init -m https://github.com/onomondo/nrf-softsim.git --mr main
west update

# Install Python dependencies
pip3 install --user -r nrf/scripts/requirements.txt
pip3 install --user -r zephyr/scripts/requirements.txt
```

### 1.2 Configure Build Environment

```bash
# Set environment variables
export ZEPHYR_BASE=~/onomondo-workspace/zephyr
export NRF_BASE=~/onomondo-workspace/nrf
export SOFTSIM_DIR=~/onomondo-workspace/modules/lib/onomondo-softsim
```

## Step 2: Project Configuration

### 2.1 Update CMakeLists.txt

Add Onomondo SoftSIM support to the project:

```cmake
# CMakeLists.txt additions
cmake_minimum_required(VERSION 3.20.0)

# Find Zephyr and Onomondo packages
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
find_package(Onomondo REQUIRED HINTS $ENV{SOFTSIM_DIR})

project(thingy91_softsim)

# Include Onomondo SoftSIM library
target_sources(app PRIVATE
    src/main.c
    src/softsim/softsim_manager.c
    src/softsim/profile_handler.c
    src/softsim/at_handler.c
)

# Link Onomondo libraries
target_link_libraries(app PRIVATE
    onomondo_softsim
    onomondo_kmu
    onomondo_profile
)
```

### 2.2 Kconfig Configuration

Create Kconfig options for SoftSIM:

```kconfig
# Kconfig.softsim
menuconfig ONOMONDO_SOFTSIM
    bool "Onomondo SoftSIM support"
    default y
    help
      Enable Onomondo SoftSIM functionality

if ONOMONDO_SOFTSIM

config SOFTSIM_AUTO_PROVISION
    bool "Automatic SoftSIM provisioning"
    default n
    help
      Automatically provision SoftSIM on first boot

config SOFTSIM_PROFILE_STORAGE
    int "SoftSIM profile storage slot"
    default 0
    range 0 3
    help
      KMU slot for storing SoftSIM profile

config SOFTSIM_APN
    string "Onomondo APN"
    default "onomondo"
    help
      Access Point Name for Onomondo network

config SOFTSIM_DEBUG
    bool "Enable SoftSIM debug logging"
    default y
    help
      Enable detailed logging for SoftSIM operations

endif # ONOMONDO_SOFTSIM
```

### 2.3 Project Configuration (prj.conf)

Update project configuration:

```conf
# prj.conf additions for SoftSIM

# Onomondo SoftSIM
CONFIG_ONOMONDO_SOFTSIM=y
CONFIG_SOFTSIM_AUTO_PROVISION=n
CONFIG_SOFTSIM_PROFILE_STORAGE=0
CONFIG_SOFTSIM_APN="onomondo"
CONFIG_SOFTSIM_DEBUG=y

# Security features
CONFIG_TRUSTED_EXECUTION_SECURE=y
CONFIG_TFM_PROFILE_TYPE_MEDIUM=y
CONFIG_TFM_CRYPTO=y
CONFIG_TFM_KEY_MANAGEMENT=y

# Modem configuration
CONFIG_NRF_MODEM_LIB=y
CONFIG_NRF_MODEM_LIB_SYS_INIT=y
CONFIG_MODEM_INFO=y
CONFIG_MODEM_KEY_MGMT=y

# AT command interface
CONFIG_AT_HOST_LIBRARY=y
CONFIG_AT_CMD_CUSTOM=y
CONFIG_AT_CMD_THREAD_STACK_SIZE=2048

# Network settings
CONFIG_LTE_LINK_CONTROL=y
CONFIG_LTE_NETWORK_MODE_LTE_M_GPS=y
CONFIG_LTE_AUTO_INIT_AND_CONNECT=n
CONFIG_LTE_PSM_ENABLE=y
CONFIG_LTE_EDRX_ENABLE=y

# Flash storage for profiles
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_NVS=y
CONFIG_SETTINGS=y
CONFIG_SETTINGS_NVS=y

# UART for profile transfer
CONFIG_UART_INTERRUPT_DRIVEN=y
CONFIG_UART_ASYNC_API=y
CONFIG_SERIAL=y
```

## Step 3: Implementation Files

### 3.1 Create SoftSIM Manager Module

```c
// src/softsim/softsim_manager.h
#ifndef SOFTSIM_MANAGER_H
#define SOFTSIM_MANAGER_H

#include <zephyr/kernel.h>
#include <modem/nrf_modem_lib.h>

/* SoftSIM states */
enum softsim_state {
    SOFTSIM_STATE_UNPROVISIONED,
    SOFTSIM_STATE_PROVISIONING,
    SOFTSIM_STATE_PROVISIONED,
    SOFTSIM_STATE_ACTIVE,
    SOFTSIM_STATE_ERROR
};

/* SoftSIM profile structure */
struct softsim_profile {
    uint8_t imsi[15];
    uint8_t iccid[20];
    uint8_t ki[16];
    uint8_t opc[16];
    uint8_t profile_id[16];
    uint32_t version;
};

/* Initialize SoftSIM manager */
int softsim_manager_init(void);

/* Provision SoftSIM profile */
int softsim_provision_profile(const struct softsim_profile *profile);

/* Activate SoftSIM */
int softsim_activate(void);

/* Get current SoftSIM state */
enum softsim_state softsim_get_state(void);

/* Verify SoftSIM profile */
int softsim_verify_profile(void);

/* Remove SoftSIM profile */
int softsim_remove_profile(void);

#endif /* SOFTSIM_MANAGER_H */
```

### 3.2 Create AT Command Handler

```c
// src/softsim/at_handler.h
#ifndef AT_HANDLER_H
#define AT_HANDLER_H

/* Custom AT commands for SoftSIM */
#define AT_SOFTSIM_PROVISION  "AT+OSIMPROV"
#define AT_SOFTSIM_STATUS     "AT+OSIMSTAT"
#define AT_SOFTSIM_ACTIVATE   "AT+OSIMACT"
#define AT_SOFTSIM_REMOVE     "AT+OSIMREM"
#define AT_SOFTSIM_INFO       "AT+OSIMINFO"

/* Initialize AT command handler */
int at_handler_init(void);

/* Send AT command and get response */
int at_send_command(const char *cmd, char *response, size_t response_len);

/* Register custom AT commands */
int at_register_softsim_commands(void);

#endif /* AT_HANDLER_H */
```

## Step 4: Provisioning Process

### 4.1 Manual Provisioning via UART

```bash
# Connect to device serial port
minicom -D /dev/ttyACM0 -b 115200

# Send provisioning command
AT+OSIMPROV=<base64_encoded_profile>

# Check status
AT+OSIMSTAT

# Activate SoftSIM
AT+OSIMACT

# Verify network registration
AT+CEREG?
```

### 4.2 Automated Provisioning Script

```python
#!/usr/bin/env python3
# scripts/provision_softsim.py

import serial
import base64
import json
import time
import sys

class SoftSIMProvisioner:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=10)
        
    def send_at_command(self, cmd, wait_time=1):
        """Send AT command and return response"""
        self.ser.write(f"{cmd}\r\n".encode())
        time.sleep(wait_time)
        response = self.ser.read(self.ser.in_waiting).decode()
        return response
    
    def provision_profile(self, profile_file):
        """Provision SoftSIM profile from JSON file"""
        with open(profile_file, 'r') as f:
            profile = json.load(f)
        
        # Encode profile to base64
        profile_data = json.dumps(profile).encode()
        profile_b64 = base64.b64encode(profile_data).decode()
        
        # Check current status
        print("Checking SoftSIM status...")
        status = self.send_at_command("AT+OSIMSTAT")
        print(f"Status: {status}")
        
        # Send provisioning command
        print("Provisioning SoftSIM profile...")
        response = self.send_at_command(f"AT+OSIMPROV={profile_b64}", wait_time=5)
        
        if "OK" in response:
            print("✓ Profile provisioned successfully")
            
            # Activate SoftSIM
            print("Activating SoftSIM...")
            response = self.send_at_command("AT+OSIMACT", wait_time=3)
            
            if "OK" in response:
                print("✓ SoftSIM activated")
                
                # Check network registration
                print("Checking network registration...")
                for i in range(30):
                    response = self.send_at_command("AT+CEREG?")
                    if "+CEREG: 0,1" in response or "+CEREG: 0,5" in response:
                        print("✓ Registered on network")
                        return True
                    time.sleep(2)
                    print(".", end="", flush=True)
                
                print("\n✗ Network registration timeout")
            else:
                print(f"✗ Activation failed: {response}")
        else:
            print(f"✗ Provisioning failed: {response}")
        
        return False
    
    def get_info(self):
        """Get SoftSIM information"""
        info = self.send_at_command("AT+OSIMINFO")
        return info
    
    def close(self):
        """Close serial connection"""
        self.ser.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: provision_softsim.py <serial_port> <profile.json>")
        sys.exit(1)
    
    port = sys.argv[1]
    profile_file = sys.argv[2]
    
    provisioner = SoftSIMProvisioner(port)
    
    try:
        success = provisioner.provision_profile(profile_file)
        if success:
            info = provisioner.get_info()
            print(f"\nSoftSIM Info:\n{info}")
            sys.exit(0)
        else:
            sys.exit(1)
    finally:
        provisioner.close()
```

### 4.3 Profile JSON Template

```json
{
    "profile_version": "1.0.0",
    "network_provider": "onomondo",
    "credentials": {
        "imsi": "YOUR_IMSI_HERE",
        "iccid": "YOUR_ICCID_HERE",
        "ki": "YOUR_KI_HERE",
        "opc": "YOUR_OPC_HERE"
    },
    "network_config": {
        "apn": "onomondo",
        "preferred_plmn": ["26201", "26202"],
        "rat_priority": ["LTE-M", "NB-IoT"]
    },
    "security": {
        "algorithm": "AES",
        "key_size": 128
    }
}
```

## Step 5: Testing and Validation

### 5.1 Verification Checklist

- [ ] Profile provisioned successfully
- [ ] SoftSIM activated
- [ ] Network registration successful
- [ ] Data connection established
- [ ] Profile persists after power cycle
- [ ] Onomondo dashboard shows device online
- [ ] Data transmission working

### 5.2 Test Script

```bash
#!/bin/bash
# scripts/test_softsim.sh

set -e

SERIAL_PORT="/dev/ttyACM0"

echo "Testing Onomondo SoftSIM Integration"
echo "====================================="

# Function to send AT command
send_at() {
    echo -e "$1\r" > $SERIAL_PORT
    sleep 1
    cat $SERIAL_PORT &
    sleep 2
    pkill -f "cat $SERIAL_PORT"
}

# Check SoftSIM status
echo "1. Checking SoftSIM status..."
send_at "AT+OSIMSTAT"

# Check network registration
echo "2. Checking network registration..."
send_at "AT+CEREG?"

# Check signal strength
echo "3. Checking signal strength..."
send_at "AT+CSQ"

# Check operator
echo "4. Checking network operator..."
send_at "AT+COPS?"

# Test data connection
echo "5. Testing data connection..."
send_at "AT+CGDCONT?"
send_at "AT+CGACT?"

echo "Test complete!"
```

## Step 6: Monitoring via Onomondo Platform

### 6.1 Dashboard Access

1. Log in to Onomondo platform: https://app.onomondo.com
2. Navigate to Devices section
3. Find your device by IMSI or ICCID
4. Monitor:
   - Connection status
   - Data usage
   - Network logs
   - Signaling information

### 6.2 Platform Features

- **Network Logs**: View registration attempts and handovers
- **Traffic Monitor**: Real-time data usage monitoring
- **Signaling Logs**: Detailed protocol-level debugging
- **Remote Actions**: Send SMS, change network settings
- **Alerts**: Configure notifications for events

## Step 7: Production Deployment

### 7.1 Batch Provisioning

```python
#!/usr/bin/env python3
# scripts/batch_provision.py

import csv
import json
from provision_softsim import SoftSIMProvisioner

def batch_provision(device_list_csv, profile_template):
    """Provision multiple devices from CSV"""
    
    with open(device_list_csv, 'r') as f:
        devices = csv.DictReader(f)
        
        for device in devices:
            print(f"\nProvisioning device: {device['serial_number']}")
            
            # Create device-specific profile
            profile = json.load(open(profile_template))
            profile['credentials']['imsi'] = device['imsi']
            profile['credentials']['iccid'] = device['iccid']
            profile['credentials']['ki'] = device['ki']
            profile['credentials']['opc'] = device['opc']
            
            # Save temporary profile
            temp_profile = f"/tmp/profile_{device['serial_number']}.json"
            with open(temp_profile, 'w') as f:
                json.dump(profile, f)
            
            # Provision device
            provisioner = SoftSIMProvisioner(device['port'])
            success = provisioner.provision_profile(temp_profile)
            provisioner.close()
            
            if success:
                print(f"✓ {device['serial_number']} provisioned")
            else:
                print(f"✗ {device['serial_number']} failed")
```

### 7.2 Remote Provisioning

For production deployments, implement secure remote provisioning:

1. Use HTTPS endpoint for profile delivery
2. Implement mutual TLS authentication
3. Encrypt profiles in transit
4. Validate device identity before provisioning
5. Log all provisioning attempts

## Troubleshooting

### Common Issues and Solutions

#### Profile Provisioning Fails
- Verify modem firmware version (≥1.3.4)
- Check profile format and encoding
- Ensure KMU is not locked
- Clear previous profiles with `AT+OSIMREM`

#### Network Registration Issues
- Verify APN settings
- Check network coverage
- Ensure profile credentials are valid
- Review Onomondo dashboard for errors

#### Data Connection Problems
- Verify data plan is active
- Check PDP context settings
- Ensure correct RAT (LTE-M/NB-IoT) selection
- Monitor signal strength

#### Profile Not Persistent
- Check flash storage configuration
- Verify NVS settings
- Ensure proper shutdown sequence
- Check KMU write permissions

## Security Considerations

1. **Credential Protection**
   - Never log sensitive credentials
   - Use secure storage (KMU)
   - Implement access controls

2. **Provisioning Security**
   - Use encrypted channels
   - Validate device identity
   - Implement rate limiting

3. **Runtime Security**
   - Monitor for anomalies
   - Implement secure boot
   - Regular security updates

## References

- [Onomondo SoftSIM Documentation](https://docs.onomondo.com/softsim)
- [Nordic nRF9160 Documentation](https://docs.nordicsemi.com/nrf9160)
- [Onomondo nrf-softsim Repository](https://github.com/onomondo/nrf-softsim)
- [nRF Connect SDK](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/index.html)

## Support

- Onomondo Support: support@onomondo.com
- Nordic DevZone: https://devzone.nordicsemi.com
- GitHub Issues: https://github.com/onomondo/nrf-softsim/issues