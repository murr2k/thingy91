# Nordic Thingy91 DK - Windows 11 Quick Start PowerShell Script
# Run this script as Administrator in PowerShell

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   Nordic Thingy91 DK - Windows 11 Quick Start Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[✓] Running as Administrator" -ForegroundColor Green

# Function to check if a program is installed
function Test-ProgramInstalled {
    param($programName)
    $installed = Get-Command $programName -ErrorAction SilentlyContinue
    return $installed -ne $null
}

# Install Windows Package Manager (winget) if not present
if (-not (Test-ProgramInstalled "winget")) {
    Write-Host "[!] Installing Windows Package Manager..." -ForegroundColor Yellow
    Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
}

# Install USBIPD for USB passthrough to WSL2
Write-Host "[*] Checking USBIPD installation..." -ForegroundColor Cyan
if (-not (Test-ProgramInstalled "usbipd")) {
    Write-Host "[*] Installing USBIPD..." -ForegroundColor Yellow
    winget install --exact --id Microsoft.USBPCIProxy --accept-package-agreements --accept-source-agreements
    Write-Host "[✓] USBIPD installed successfully" -ForegroundColor Green
} else {
    Write-Host "[✓] USBIPD already installed" -ForegroundColor Green
}

# Check if WSL2 is installed and running
Write-Host "[*] Checking WSL2 status..." -ForegroundColor Cyan
$wslStatus = wsl --status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] WSL2 is not installed. Installing..." -ForegroundColor Yellow
    wsl --install -d Ubuntu-22.04
    Write-Host "[✓] WSL2 with Ubuntu 22.04 installed" -ForegroundColor Green
    Write-Host "[!] Please restart your computer and run this script again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
} else {
    Write-Host "[✓] WSL2 is installed" -ForegroundColor Green
}

# Update WSL2
Write-Host "[*] Updating WSL2..." -ForegroundColor Cyan
wsl --update
Write-Host "[✓] WSL2 updated" -ForegroundColor Green

# Function to find Nordic devices
function Find-NordicDevice {
    Write-Host "[*] Searching for Nordic Thingy91 devices..." -ForegroundColor Cyan
    $devices = usbipd list 2>$null
    
    if ($devices) {
        Write-Host ""
        Write-Host "USB Devices found:" -ForegroundColor Yellow
        Write-Host $devices
        Write-Host ""
        
        # Try to find Nordic device automatically
        $nordicDevice = $devices | Select-String -Pattern "Nordic|Thingy|1915:9100|1915:910b|1915:910c"
        
        if ($nordicDevice) {
            Write-Host "[✓] Found Nordic device:" -ForegroundColor Green
            Write-Host $nordicDevice -ForegroundColor Cyan
            
            # Extract BUSID
            if ($nordicDevice -match "(\d+-\d+)") {
                $busId = $matches[1]
                return $busId
            }
        } else {
            Write-Host "[!] Nordic device not found automatically" -ForegroundColor Yellow
            Write-Host "Please connect your Thingy91 DK via USB" -ForegroundColor Yellow
        }
    }
    return $null
}

# Function to attach device to WSL
function Attach-DeviceToWSL {
    param($busId)
    
    if ($busId) {
        Write-Host "[*] Attempting to attach device $busId to WSL2..." -ForegroundColor Cyan
        
        # First, bind the device if not already bound
        usbipd bind --busid $busId 2>$null
        
        # Attach to WSL
        $result = usbipd attach --wsl --busid $busId 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] Device attached successfully to WSL2" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[!] Failed to attach device: $result" -ForegroundColor Red
            return $false
        }
    }
    return $false
}

# Main device detection and attachment
$busId = Find-NordicDevice

if ($busId) {
    Write-Host ""
    $response = Read-Host "Attach device $busId to WSL2? (Y/n)"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        if (Attach-DeviceToWSL $busId) {
            Write-Host ""
            Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
            Write-Host "Device is ready in WSL2!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next steps in WSL2 Ubuntu:" -ForegroundColor Yellow
            Write-Host "1. Open WSL2 Ubuntu terminal" -ForegroundColor White
            Write-Host "2. Run: lsusb  (to verify device is visible)" -ForegroundColor White
            Write-Host "3. Run: ls -la /dev/ttyACM* /dev/ttyUSB*  (to find serial port)" -ForegroundColor White
            Write-Host "4. Clone the project:" -ForegroundColor White
            Write-Host "   git clone https://github.com/murr2k/thingy91.git" -ForegroundColor Gray
            Write-Host "   cd thingy91" -ForegroundColor Gray
            Write-Host "5. Run the setup script:" -ForegroundColor White
            Write-Host "   ./scripts/setup_wsl.sh" -ForegroundColor Gray
            Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host ""
    Write-Host "[!] No Nordic device detected" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual steps required:" -ForegroundColor Yellow
    Write-Host "1. Connect your Thingy91 DK via USB" -ForegroundColor White
    Write-Host "2. Run: usbipd list" -ForegroundColor White
    Write-Host "3. Find your device's BUSID" -ForegroundColor White
    Write-Host "4. Run: usbipd bind --busid <BUSID>" -ForegroundColor White
    Write-Host "5. Run: usbipd attach --wsl --busid <BUSID>" -ForegroundColor White
}

# Create a batch file for easy device attachment
$batchContent = @"
@echo off
echo Listing USB devices...
usbipd list
echo.
echo Enter the BUSID of your Nordic Thingy91 (e.g., 2-4):
set /p busid=BUSID: 
echo.
echo Attaching device to WSL2...
usbipd attach --wsl --busid %busid%
echo.
echo Done! Check WSL2 with: lsusb
pause
"@

$batchPath = "$env:USERPROFILE\Desktop\attach_thingy91_to_wsl.bat"
$batchContent | Out-File -FilePath $batchPath -Encoding ASCII
Write-Host ""
Write-Host "[✓] Created helper batch file on Desktop: attach_thingy91_to_wsl.bat" -ForegroundColor Green

# Download nRF Connect for Desktop if not installed
Write-Host ""
Write-Host "[*] Checking nRF Connect for Desktop..." -ForegroundColor Cyan

$nrfConnectPath = "${env:ProgramFiles}\Nordic Semiconductor\nRF Connect for Desktop"
if (-not (Test-Path $nrfConnectPath)) {
    Write-Host "[!] nRF Connect for Desktop not found" -ForegroundColor Yellow
    $response = Read-Host "Download nRF Connect for Desktop? (Y/n)"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        Write-Host "[*] Opening download page..." -ForegroundColor Cyan
        Start-Process "https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-desktop/download"
        Write-Host "[!] Please install nRF Connect for Desktop manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] nRF Connect for Desktop is installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your Windows environment is ready for Thingy91 development!" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed instructions, see:" -ForegroundColor Yellow
Write-Host "https://github.com/murr2k/thingy91/blob/main/SETUP_WSL_WINDOWS.md" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"