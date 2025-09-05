#!/usr/bin/env python3
"""
Test physical SIM card functionality
"""
import serial
import time

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
            print(f"  Received: {repr(data)}")
            
            if ("OK" in response or "ERROR" in response or 
                "+CME ERROR" in response or "+CMS ERROR" in response):
                break
        
        time.sleep(0.1)
    
    print(f"Complete response: {repr(response.strip())}")
    return response.strip()

def test_physical_sim():
    """Test physical SIM functionality with full reset"""
    
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
        
        print("\n=== Modem Reset and Initialization ===")
        # Reset modem functionality
        response = send_at_command(ser, "AT+CFUN=0", timeout=10)
        if "OK" in response:
            print("✅ Modem disabled")
            time.sleep(3)
        
        # Re-enable with full reset
        response = send_at_command(ser, "AT+CFUN=1,1", timeout=30)  # Full reset
        if "OK" in response:
            print("✅ Modem reset and enabled")
            time.sleep(10)  # Wait for full initialization
        
        print("\n=== Post-Reset Status ===")
        send_at_command(ser, "AT+CFUN?")
        send_at_command(ser, "AT%XSIM?")
        
        print("\n=== SIM Detection Attempts ===")
        
        # Try different SIM status commands
        for cmd in ["AT+CPIN?", "AT+CCID", "AT+CIMI", "AT%XICCID", "AT%XIMSI"]:
            response = send_at_command(ser, cmd, timeout=5)
            if "OK" in response and not "ERROR" in response:
                print(f"✅ {cmd} successful")
            else:
                print(f"❌ {cmd} failed")
        
        print("\n=== Signal Quality ===")
        send_at_command(ser, "AT+CSQ")
        
        print("\n=== Network Scan ===")
        response = send_at_command(ser, "AT+COPS=?", timeout=120)  # Long timeout for network scan
        if "+COPS:" in response:
            print("✅ Networks found")
        
        print("\n=== Registration Status ===")
        send_at_command(ser, "AT+CEREG?")
        
        # Try manual network registration if automatic failed
        print("\n=== Manual Network Registration ===")
        # Try to register to first available network
        response = send_at_command(ser, "AT+COPS=1,2,\"23450\"", timeout=60)  # Onomondo network
        if "OK" in response:
            print("✅ Manual registration to 23450 (Onomondo) attempted")
        else:
            print("❌ Manual registration failed, trying automatic")
            send_at_command(ser, "AT+COPS=0", timeout=30)
        
        print("\n=== Final Status Check ===")
        send_at_command(ser, "AT+COPS?")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+CGATT?")
        
        # Try network attachment
        print("\n=== Network Attachment ===")
        response = send_at_command(ser, "AT+CGATT=1", timeout=60)
        if "OK" in response:
            print("✅ Attachment attempted")
            time.sleep(5)
            send_at_command(ser, "AT+CGATT?")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Physical SIM Card...")
    print("=" * 60)
    
    test_physical_sim()