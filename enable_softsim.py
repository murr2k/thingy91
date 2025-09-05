#!/usr/bin/env python3
"""
Enable SoftSIM functionality on Nordic Thingy91
"""
import serial
import time
import json

def send_at_command(ser, command, timeout=10):
    """Send AT command and return response"""
    print(f"Sending: {command}")
    
    ser.flushInput()
    ser.flushOutput()
    ser.write(f"{command}\r\n".encode())
    
    response = ""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += data
            
            if ("OK" in response or "ERROR" in response or 
                "+CME ERROR" in response or "+CMS ERROR" in response):
                break
        
        time.sleep(0.1)
    
    print(f"Response: {response.strip()}")
    return response.strip()

def enable_softsim():
    """Enable SoftSIM and configure modem"""
    
    # Load credentials
    with open('/home/murr2k/projects/thingy91/profiles/my_thingy91_profile.json', 'r') as f:
        profile = json.load(f)
    
    creds = profile['credentials']
    
    try:
        ser = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=115200,
            timeout=5
        )
        
        print("Connected to Thingy91")
        time.sleep(1)
        
        # Test basic communication
        send_at_command(ser, "AT")
        
        print("\n=== Current Status ===")
        send_at_command(ser, "AT+CFUN?")      # Current functionality
        send_at_command(ser, "AT%XSIM?")      # SIM status
        
        print("\n=== Enabling Full Functionality ===")
        response = send_at_command(ser, "AT+CFUN=1", timeout=30)
        if "OK" in response:
            print("✅ Full functionality enabled")
            time.sleep(5)  # Wait for modem to initialize
        else:
            print("❌ Failed to enable full functionality")
            
        print("\n=== Checking Modem Status After Enable ===")
        send_at_command(ser, "AT+CFUN?")
        send_at_command(ser, "AT%XSIM?")
        
        # Try Nordic-specific SoftSIM commands
        print("\n=== Nordic SoftSIM Commands ===")
        
        # Check if SoftSIM is supported/available
        send_at_command(ser, "AT%XICCID")     # Nordic ICCID command
        send_at_command(ser, "AT%XIMSI")      # Nordic IMSI command
        
        # Try to configure IMSI and ICCID directly (Nordic specific)
        print(f"\n=== Configuring SoftSIM Credentials ===")
        
        # Some Nordic devices support direct SoftSIM credential configuration
        imsi_cmd = f"AT%XIMSI=\"{creds['imsi']}\""
        response = send_at_command(ser, imsi_cmd)
        if "OK" in response:
            print("✅ IMSI configured")
        else:
            print("❌ IMSI configuration failed or not supported")
        
        iccid_cmd = f"AT%XICCID=\"{creds['iccid']}\""
        response = send_at_command(ser, iccid_cmd)
        if "OK" in response:
            print("✅ ICCID configured")
        else:
            print("❌ ICCID configuration failed or not supported")
        
        print("\n=== Checking Signal and Registration ===")
        send_at_command(ser, "AT+CSQ")        # Signal quality
        send_at_command(ser, "AT+CEREG?")     # Registration status
        
        # Try network attachment again
        print("\n=== Attempting Network Attachment ===")
        response = send_at_command(ser, "AT+CGATT=1", timeout=30)
        if "OK" in response:
            print("✅ Attachment command successful")
        else:
            print("❌ Attachment failed")
            
        # Check final status
        print("\n=== Final Status ===")
        send_at_command(ser, "AT+CGATT?")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+CSQ")
        
        # If still no SIM, this might be a hardware limitation
        response = send_at_command(ser, "AT%XSIM?")
        if "%XSIM: 0" in response:
            print("\n⚠️  Warning: Device reports no SIM card detected.")
            print("This Nordic Thingy91 may require:")
            print("1. A physical SIM card slot with Onomondo SIM")
            print("2. Different firmware that supports embedded SoftSIM")
            print("3. eSIM provisioning through Nordic's tools")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ SoftSIM enable failed: {e}")
        return False

if __name__ == "__main__":
    print("Enabling SoftSIM on Nordic Thingy91...")
    print("=" * 60)
    
    enable_softsim()