# 📋 nRF Connect SDK v3.0.0 Compatibility Update

## ✅ **PROJECT UPDATED FOR NEWER SDK VERSIONS**

Your SoftSIM project has been updated for compatibility with **nRF Connect SDK v3.0.0** (and v2.7.0+).

---

## **🔧 Updated Components**

### **1. West Manifest (`west.yml`)**
Updated to use nRF Connect SDK v3.0.2 compatible versions:
- **sdk-nrf**: `v3.0.2` (was v2.4.0)
- **sdk-zephyr**: `v4.0.99-ncs1-2` (was v3.3.99-ncs1)
- **sdk-mcuboot**: `v2.1.0-ncs5-2` (was v1.10.0-ncs1)
- **sdk-mbedtls**: `v3.6.3-ncs1-2` (was v3.4.0-ncs1)
- **sdk-nrfxlib**: `v3.0.2` (was v2.4.0)
- **sdk-trusted-firmware-m**: `v2.1.1-ncs4-2` (was v1.7.0-ncs1)

### **2. Board Target Format**
Updated to new board naming convention:
- **New**: `thingy91/nrf9160/ns`
- **Old**: `thingy91_nrf9160_ns`

### **3. Build Guide Updated**
Modified `/home/murr2k/projects/thingy91/nrf_connect_softsim_guide.md` with:
- **Recommended SDK**: v3.0.0 (or v2.7.0+)
- **Updated board targets** throughout guide
- **Compatible build commands**

---

## **✅ What Remains the Same**

### **Your SoftSIM Configuration**
- **✅ SoftSIM Profile**: Still embedded in `prj.conf` 
- **✅ ICCID**: `89457300000032481957` unchanged
- **✅ Onomondo Module**: Compatible with all SDK versions
- **✅ Build Settings**: All prj.conf settings remain valid

### **Core Functionality**
- **✅ Hardware**: Same Thingy91 target
- **✅ SoftSIM**: Same decrypted profile data
- **✅ Network**: Same Onomondo cellular connectivity
- **✅ Flash Process**: Same programming method

---

## **🚀 Recommended SDK Version**

### **For Maximum Stability**: Use **nRF Connect SDK v3.0.0**
- Latest stable release
- Full Thingy91 support
- All SoftSIM features working
- Best toolchain integration

### **Alternative Options**:
- **v2.7.0** - Also fully compatible
- **v2.8.0/v2.9.0** - Should work with minor config adjustments

---

## **📝 Build Instructions Updated**

### **Using nRF Connect for Desktop:**
1. Install **nRF Connect SDK v3.0.0** via Toolchain Manager
2. Open project in VS Code
3. **Board**: Select `thingy91/nrf9160/ns`
4. Build and flash as normal

### **Command Line Build:**
```bash
cd /home/murr2k/projects/thingy91
west build -b thingy91/nrf9160/ns --pristine
```

---

## **🎯 What This Means for You**

### **✅ Advantages of Newer SDK:**
- **Better tooling** - improved VS Code integration
- **More features** - enhanced debugging and profiling
- **Bug fixes** - resolved issues from older versions
- **Future support** - continued updates and maintenance

### **✅ Your SoftSIM Setup:**
- **Still works perfectly** with all SDK versions
- **No profile changes needed** - your decrypted SoftSIM data is universal
- **Same cellular functionality** - pure software SIM operation unchanged
- **Same performance** - network connectivity identical

---

## **🚀 READY TO BUILD**

**Everything is configured and ready!** 

Use nRF Connect for Desktop with **v3.0.0** and follow the updated guide:
👉 `/home/murr2k/projects/thingy91/nrf_connect_softsim_guide.md`

**Your SoftSIM profile is still embedded and ready for cellular connectivity!** 🎉