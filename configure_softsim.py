#!/usr/bin/env python3
"""
Configure Onomondo SoftSIM credentials on Nordic Thingy91
"""
import serial
import time
import json

def send_at_command(ser, command, timeout=10, expect_ok=True):
    """Send AT command and return response"""
    print(f"Sending: {command}")
    
    # Clear buffers
    ser.flushInput()
    ser.flushOutput()
    
    # Send command
    ser.write(f"{command}\r\n".encode())
    
    # Read response
    response = ""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += data
            print(f"Received: {repr(data)}")
            
            # Check for completion
            if expect_ok and ("OK" in response or "ERROR" in response):
                break
            elif not expect_ok and response.strip():
                break
        
        time.sleep(0.1)
    
    print(f"Complete response: {repr(response)}")
    return response.strip()

def configure_softsim():
    """Configure the SoftSIM with Onomondo credentials"""
    
    # Load credentials from profile
    with open('/home/murr2k/projects/thingy91/profiles/my_thingy91_profile.json', 'r') as f:
        profile = json.load(f)
    
    creds = profile['credentials']
    network = profile['network_config']
    
    try:
        # Connect to serial port
        ser = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=115200,
            timeout=3,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        print("Connected to Thingy91")
        time.sleep(1)
        
        # Test basic communication
        response = send_at_command(ser, "AT")
        if "OK" not in response:
            print("❌ Basic AT communication failed")
            return False
        
        print("✅ Basic AT communication working")
        
        # Get device info
        print("\n=== Device Information ===")
        send_at_command(ser, "AT+CGMI")  # Manufacturer
        send_at_command(ser, "AT+CGMM")  # Model
        send_at_command(ser, "AT+CGMR")  # Revision
        send_at_command(ser, "AT+CGSN")  # IMEI
        
        # Check current network registration
        print("\n=== Network Status ===")
        send_at_command(ser, "AT+CEREG?")  # Network registration status
        send_at_command(ser, "AT+COPS?")   # Current operator
        
        # Configure APN
        print(f"\n=== Configuring APN: {network['apn']} ===")
        apn_cmd = f'AT+CGDCONT=1,"IP","{network["apn"]}"'
        response = send_at_command(ser, apn_cmd)
        if "OK" in response:
            print("✅ APN configured successfully")
        else:
            print("❌ APN configuration failed")
        
        # Set network operator selection to automatic
        print("\n=== Setting Network Selection ===")
        response = send_at_command(ser, "AT+COPS=0")
        if "OK" in response:
            print("✅ Automatic network selection enabled")
        else:
            print("❌ Network selection configuration failed")
        
        # Enable network registration reporting
        print("\n=== Enabling Network Registration ===")
        response = send_at_command(ser, "AT+CEREG=2")
        if "OK" in response:
            print("✅ Network registration reporting enabled")
        
        # Check if we can attach to network
        print("\n=== Network Attachment ===")
        send_at_command(ser, "AT+CGATT?")  # Check attachment status
        
        # Try to attach if not attached
        response = send_at_command(ser, "AT+CGATT=1", timeout=30)
        if "OK" in response:
            print("✅ Network attachment command sent")
        else:
            print("❌ Network attachment failed")
        
        # Wait for network registration
        print("\n=== Checking Network Registration (waiting up to 60s) ===")
        for i in range(12):  # 60 seconds total
            response = send_at_command(ser, "AT+CEREG?")
            if ",1" in response or ",5" in response:  # Registered home or roaming
                print("✅ Successfully registered to network!")
                break
            print(f"Registration attempt {i+1}/12... waiting 5s")
            time.sleep(5)
        else:
            print("⚠️  Network registration timeout - continuing anyway")
        
        # Final status check
        print("\n=== Final Status Check ===")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+COPS?")
        send_at_command(ser, "AT+CGATT?")
        send_at_command(ser, "AT+CGDCONT?")
        
        print("\n✅ SoftSIM configuration completed!")
        print(f"Profile: {profile['profile_id']}")
        print(f"IMSI: {creds['imsi']}")
        print(f"ICCID: {creds['iccid']}")
        print(f"APN: {network['apn']}")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

if __name__ == "__main__":
    print("Configuring Onomondo SoftSIM on Nordic Thingy91...")
    print("=" * 60)
    
    success = configure_softsim()
    
    if success:
        print("\n🎉 Configuration completed successfully!")
        print("Your Thingy91 should now be able to connect to the cellular network.")
    else:
        print("\n❌ Configuration failed. Please check the output above for errors.")