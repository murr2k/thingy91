@echo off
REM Flash Nordic Thingy91 with Serial LTE Modem firmware
REM This will restore USB CDC functionality

echo ============================================================
echo NORDIC THINGY91 FIRMWARE FLASHER
echo ============================================================
echo.
echo This script will flash:
echo 1. Serial LTE Modem to nRF9160 (for AT commands)
echo 2. Connectivity bridge to nRF52840 (for USB CDC)
echo.
echo IMPORTANT: Make sure J-Link is connected to Thingy91 SWD port
echo.
pause

set JLINK="C:\Program Files\SEGGER\JLink\JLink.exe"

echo.
echo Step 1: Download firmware files if needed...
echo Please download from: https://www.nordicsemi.com/Products/Development-hardware/Nordic-Thingy-91/Download
echo.
echo Required files:
echo - mfw_nrf9160_1.3.x.zip (Serial LTE Modem)
echo - connectivity_bridge_nrf52840.hex
echo.
echo Place the hex files in the current directory.
echo.
pause

REM Check if J-Link is available
if not exist %JLINK% (
    echo ERROR: J-Link not found at %JLINK%
    echo Please install J-Link from: https://www.segger.com/downloads/jlink/
    pause
    exit /b 1
)

echo.
echo Step 2: Flash nRF9160 (Serial LTE Modem)
echo ============================================

REM Create J-Link script for nRF9160
echo device nRF9160_xxAA > flash_nrf9160.jlink
echo si SWD >> flash_nrf9160.jlink
echo speed 4000 >> flash_nrf9160.jlink
echo connect >> flash_nrf9160.jlink
echo erase >> flash_nrf9160.jlink
echo loadfile mfw_nrf9160_1.3.4_uart.hex >> flash_nrf9160.jlink
echo r >> flash_nrf9160.jlink
echo g >> flash_nrf9160.jlink
echo exit >> flash_nrf9160.jlink

%JLINK% -CommandFile flash_nrf9160.jlink

echo.
echo Step 3: Flash nRF52840 (Connectivity Bridge)
echo ============================================

REM Create J-Link script for nRF52840
echo device nRF52840_xxAA > flash_nrf52840.jlink
echo si SWD >> flash_nrf52840.jlink
echo speed 4000 >> flash_nrf52840.jlink
echo connect >> flash_nrf52840.jlink
echo erase >> flash_nrf52840.jlink
echo loadfile connectivity_bridge_2023.hex >> flash_nrf52840.jlink
echo r >> flash_nrf52840.jlink
echo g >> flash_nrf52840.jlink
echo exit >> flash_nrf52840.jlink

%JLINK% -CommandFile flash_nrf52840.jlink

echo.
echo ============================================================
echo FLASHING COMPLETE!
echo ============================================================
echo.
echo Please:
echo 1. Disconnect J-Link
echo 2. Power cycle the Thingy91
echo 3. Check Device Manager for COM ports
echo 4. Run: python wait_and_test.py
echo.
pause