# 🚀 nRF Connect for Desktop - SoftSIM Build Guide

## ✅ **READY TO BUILD:** Your Onomondo SoftSIM Firmware!

All files are prepared and ready. Follow these steps to build and flash your SoftSIM firmware:

---

## **Step 1: Launch nRF Connect for Desktop**

```bash
# From your terminal, run:
~/nrfconnect.AppImage
```

Or double-click the AppImage file from your file manager.

---

## **Step 2: Install Required Apps**

Once nRF Connect for Desktop opens:

1. **Click "Install" on these apps:**
   - **Programmer** (for flashing firmware)
   - **nRF Connect SDK Toolchain Manager** (for building firmware)

2. **Wait for installations to complete**

---

## **Step 3: Set Up Build Environment**

### **Option A: Using Toolchain Manager (Recommended)**

1. Open **nRF Connect SDK Toolchain Manager**
2. Install **v3.0.0** (or v2.7.0+ - project updated for compatibility)
3. Click **"Open VS Code"** when installation completes

### **Option B: Direct Build**

1. Open **VS Code with nRF Connect extension**
2. File → Open Folder → Select `/home/murr2k/projects/thingy91`

---

## **Step 4: Configure Your SoftSIM Project**

Your project is **already configured** with:

✅ **Target Board**: `thingy91/nrf9160/ns`  
✅ **SoftSIM Profile**: Your decrypted Onomondo profile  
✅ **Build Configuration**: `prj.conf` with all settings  
✅ **SoftSIM Module**: Onomondo library included  

### **Key Files Ready:**
- `/home/murr2k/projects/thingy91/prj.conf` - **Contains your real SoftSIM profile**
- `/home/murr2k/projects/thingy91/modules/lib/onomondo-softsim/` - **SoftSIM library**
- `/home/murr2k/projects/thingy91/CMakeLists.txt` - **Build configuration**

---

## **Step 5: Build Firmware**

### **In VS Code with nRF Connect:**

1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Type**: `nRF Connect: Add Build Configuration`
3. **Select Board**: `thingy91/nrf9160/ns` 
4. **Click "Build Configuration"**
5. **Wait for build to complete**

### **Alternative - Terminal Build:**

```bash
cd /home/murr2k/projects/thingy91
west build -b thingy91/nrf9160/ns
```

---

## **Step 6: Flash to Your Thingy91**

### **Using nRF Connect Programmer:**

1. **Connect your Thingy91 via USB**
2. **Open Programmer app in nRF Connect**
3. **Select your device** (should show as Nordic device)
4. **Click "Add file"** → Select `build/zephyr/merged.hex`
5. **Click "Erase & write"**
6. **Wait for flash completion** ✅

### **Alternative - Command Line:**

```bash
nrfjprog --family NRF91 --program build/zephyr/merged.hex --chiperase --verify --reset
```

---

## **Step 7: Verify SoftSIM Operation**

### **Connect to Device:**
```bash
# Use your favorite serial terminal (screen, minicom, etc.)
screen /dev/ttyACM0 115200

# Or
sudo minicom -D /dev/ttyACM0 -b 115200
```

### **Expected SoftSIM Boot Messages:**
```
[00:00:00.123,000] <inf> softsim: SoftSIM initialized
[00:00:00.456,000] <inf> softsim: Using static profile: 89457300000032481957
[00:00:01.789,000] <inf> lte: LTE Link Connecting...
[00:00:05.012,000] <inf> lte: Network registration status: 1 (home network)
```

### **Test Connectivity:**
The device should automatically connect to the Onomondo network using your SoftSIM profile!

---

## **🎯 YOUR SOFTSIM PROFILE IS EMBEDDED!**

### **Profile Details:**
- **ICCID**: `89457300000032481957`
- **Network**: Onomondo (roaming on local carriers)
- **Profile Type**: Static (embedded in firmware)
- **Status**: ✅ **Ready for cellular connectivity**

---

## **🚀 FINAL NOTES**

### **What You've Accomplished:**
1. ✅ **Hardware recovered** and USB functional  
2. ✅ **SoftSIM profile retrieved** and decrypted  
3. ✅ **Firmware configured** with your real profile  
4. ✅ **Build environment ready** with nRF Connect  

### **Next Steps:**
- Flash the firmware and test cellular connectivity
- Your Thingy91 will have **pure software SIM functionality**
- No physical SIM card required ever again! 🎉

---

## **💡 Troubleshooting**

### **Build Issues:**
- Ensure nRF Connect SDK v2.4.0 is installed
- Check that all modules are properly downloaded
- Verify `/home/murr2k/projects/thingy91/modules/lib/onomondo-softsim/` exists

### **Flash Issues:**
- Use J-Link if USB programming fails
- Try recovery mode if device doesn't respond
- Ensure latest nRF Command Line Tools are installed

### **Connection Issues:**
- Check antenna connection on Thingy91
- Verify SoftSIM profile in logs matches ICCID `89457300000032481957`
- Contact Onomondo support if network registration fails

---

**🎉 CONGRATULATIONS! Your Nordic Thingy91 is ready for SoftSIM cellular connectivity!**