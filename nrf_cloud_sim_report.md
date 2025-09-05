# nRF Cloud & iBasis SIM Report

## 📋 Account Information

### nRF Cloud Account
- **Team Name**: Murray SST
- **Tenant ID**: 4bbfdb3e-8857-4aef-9d00-06950ed00fc5
- **User ID**: 0727a568-64f5-44e8-9b51-56a76624a137
- **Role**: Owner
- **Plan**: DEVELOPER

### Plan Limits
- **Devices**: 10
- **Monthly Location Service Requests**: 500
- **Monthly FOTA Job Executions**: 50
- **Message Routing Service Destinations**: 1
- **Monthly Stored Device Messages**: 3,000

## 📱 Your Thingy91 Device

### Device Details
- **Device ID**: nrf-352656101402322
- **Name**: nrf-352656101402322
- **Tag**: Murray1
- **Type**: Generic
- **Created**: April 1, 2021
- **Last Updated**: November 4, 2022
- **Status**: Currently disconnected

### Firmware Information
- **App**: asset_tracker v0.0.0-development
- **Modem Firmware**: mfw_nrf9160_1.2.3 (older than current 1.3.2)
- **Supports**: BOOT, MODEM, APP updates

## 📶 SIM & Network Details

### SIM Information
- **ICCID**: 8931080019073552599
- **IMSI**: 204080813556798 ✅ (matches current device reading)
- **UICC Mode**: 1 (Standard SIM)

### Last Known Network Status (from nRF Cloud)
- **Carrier**: 302220 (Telus - Canada)
- **Network Mode**: LTE-M GPS
- **Current Band**: 12
- **Supported Bands**: (2,3,4,8,12,13,20,28)
- **Area Code**: 11010
- **Cell ID**: 28309772
- **IP Address**: 10.165.173.224 (previous connection)
- **RSRP**: -95 dBm
- **UE Mode**: 2

### Current vs Historical Comparison
| Parameter | nRF Cloud (Historical) | Live Device (Current) |
|-----------|----------------------|----------------------|
| **IMSI** | 204080813556798 | 204080813556798 ✅ |
| **Carrier** | 302220 (Telus) | 302720 (Rogers) |
| **IP Address** | 10.165.173.224 | 10.165.235.227 |
| **Network** | LTE-M GPS | LTE (roaming) |
| **Band** | 12 | 12 ✅ |

## 🔄 Device Status

### Connection Status
- **Current**: Disconnected from nRF Cloud
- **Last Disconnect**: November 4, 2022
- **Disconnect Reason**: MQTT_KEEP_ALIVE_TIMEOUT
- **MQTT Enabled**: No

### Configuration
- **GPS**: Disabled
- **Active Mode**: Enabled
- **GNSS Timeout**: 60s
- **Movement Detection**: Enabled (threshold: 10, timeout: 3600s)

## ⚠️ Findings & Recommendations

### Key Observations
1. **SIM Working**: The same IMSI (204080813556798) is active on both nRF Cloud records and current live device ✅
2. **Network Change**: Device roamed from Telus (302220) to Rogers (302720)
3. **Firmware Updated**: Live device shows mfw_nrf9160_1.3.2 vs nRF Cloud's 1.2.3
4. **nRF Cloud Disconnected**: Device hasn't connected to nRF Cloud since Nov 2022

### iBasis Network Details
- **Provider**: iBasis (global IoT connectivity provider)
- **APN**: ibasis.iot
- **Roaming**: Active across Canadian carriers (Telus ↔ Rogers)
- **IP Range**: 10.165.x.x (private iBasis network)

### Next Steps
1. **Reconnect to nRF Cloud**: Update device firmware to re-establish nRF Cloud connection
2. **Monitor Usage**: Current nRF Cloud API doesn't expose detailed usage/billing data
3. **iBasis Portal**: May need direct iBasis portal access for detailed usage metrics

## 📊 Summary

Your iBasis SIM through nRF Cloud is **fully operational**:
- ✅ SIM active and registered
- ✅ Data connection working
- ✅ Roaming between Canadian carriers
- ✅ Device firmware updated and functional
- ⚠️ nRF Cloud connection needs restoration for cloud features