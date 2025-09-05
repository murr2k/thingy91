# 🚀 VS Code + nRF Connect SDK Installation Guide

## **You're on the right track!** 

The page that opened is Nordic's official installation guide. Here's what to do:

---

## **Step 1: Follow the Installation Process**

### **On the Nordic documentation page:**

1. **Choose your platform**: Select **Linux** (since you're on WSL/Ubuntu)

2. **Install prerequisites** (if not already installed):
   ```bash
   # Update package list
   sudo apt update
   
   # Install required packages
   sudo apt install git cmake ninja-build gperf ccache dfu-util device-tree-compiler wget python3-dev python3-pip python3-setuptools python3-tk python3-wheel xz-utils file make gcc gcc-multilib g++-multilib libsdl2-dev
   ```

3. **Install VS Code** (if not already installed):
   ```bash
   # Download and install VS Code
   wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
   sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
   sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
   sudo apt update
   sudo apt install code
   ```

---

## **Step 2: Install nRF Connect Extension**

### **In VS Code:**
1. **Open VS Code**: `code`
2. **Go to Extensions** (Ctrl+Shift+X)
3. **Search for**: `nRF Connect for VS Code`
4. **Click "Install"** on the official Nordic extension

---

## **Step 3: Initialize nRF Connect SDK**

### **Using the extension:**
1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Type**: `nRF Connect: Install SDK`
3. **Select version**: `v3.0.0`
4. **Choose installation directory** (e.g., `~/ncs/v3.0.0`)
5. **Wait for installation** (this will take several minutes)

---

## **Step 4: Open Your SoftSIM Project**

### **Once SDK is installed:**
1. **Open your project**: File → Open Folder
2. **Navigate to**: `/home/murr2k/projects/thingy91`
3. **VS Code will recognize** it as an nRF Connect project
4. **The extension will show** SoftSIM configuration ready

---

## **🎯 What You'll See After Installation**

### **VS Code Interface:**
- **nRF Connect sidebar** with project tools
- **Board selection** dropdown (select `thingy91/nrf9160/ns`)
- **Build/Flash buttons** in the status bar
- **Your SoftSIM files** with syntax highlighting

### **Your Project Status:**
- ✅ **SoftSIM Profile**: Already embedded in `prj.conf`
- ✅ **Target Board**: Updated to `thingy91/nrf9160/ns`
- ✅ **Onomondo Module**: Ready in `modules/lib/onomondo-softsim/`
- ✅ **ICCID**: `89457300000032481957` configured

---

## **⚡ Quick Commands After Setup**

### **To build your SoftSIM firmware:**
```bash
# In VS Code terminal or external terminal
cd /home/murr2k/projects/thingy91
west build -b thingy91/nrf9160/ns --pristine
```

### **Or use VS Code GUI:**
1. **Command Palette**: `Ctrl+Shift+P`
2. **Type**: `nRF Connect: Build`
3. **Select board**: `thingy91/nrf9160/ns`
4. **Click Build**

---

## **🚀 You're Almost There!**

**Follow the Nordic documentation page for the detailed installation steps, then:**

1. Install the SDK via VS Code extension
2. Open your SoftSIM project folder
3. Build with board `thingy91/nrf9160/ns`
4. Flash to your Thingy91
5. **Enjoy pure software SIM connectivity!** 🎉

Your SoftSIM profile is ready and waiting!