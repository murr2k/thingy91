#!/usr/bin/env python3
"""
Check SIM status and diagnose network registration issues
"""
import serial
import time

def send_at_command(ser, command, timeout=10):
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
            
            # Check for completion
            if ("OK" in response or "ERROR" in response or 
                "+CME ERROR" in response or "+CMS ERROR" in response):
                break
        
        time.sleep(0.1)
    
    print(f"Response: {response.strip()}")
    return response.strip()

def check_sim_status():
    """Check SIM and network status in detail"""
    
    try:
        # Connect to serial port
        ser = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=115200,
            timeout=5
        )
        
        print("Connected to Thingy91")
        time.sleep(1)
        
        # Test basic communication
        send_at_command(ser, "AT")
        
        print("\n=== SIM Status ===")
        send_at_command(ser, "AT+CPIN?")      # SIM PIN status
        send_at_command(ser, "AT+CCID")       # SIM ICCID
        send_at_command(ser, "AT+CIMI")       # SIM IMSI
        
        print("\n=== Network Registration Detail ===")
        send_at_command(ser, "AT+CEREG?")     # EPS registration status
        send_at_command(ser, "AT+CREG?")      # Network registration status
        send_at_command(ser, "AT+CGREG?")     # GPRS registration status
        
        print("\n=== Signal Quality ===")
        send_at_command(ser, "AT+CSQ")        # Signal quality
        send_at_command(ser, "AT+CESQ")       # Extended signal quality
        
        print("\n=== Available Networks ===")
        send_at_command(ser, "AT+COPS=?", timeout=60)  # Scan for networks (can take time)
        
        print("\n=== Current Operator ===")
        send_at_command(ser, "AT+COPS?")      # Current operator
        
        print("\n=== APN Configuration ===")
        send_at_command(ser, "AT+CGDCONT?")   # PDP context
        
        print("\n=== Attach Status ===")
        send_at_command(ser, "AT+CGATT?")     # Attach status
        
        print("\n=== Modem Functionality ===")
        send_at_command(ser, "AT+CFUN?")      # Functionality level
        
        print("\n=== Network Errors ===")
        send_at_command(ser, "AT+CEER")       # Extended error report
        
        # Try to get more detailed network info
        print("\n=== Detailed Network Info ===")
        send_at_command(ser, "AT%XCBAND?")    # Band configuration (Nordic specific)
        send_at_command(ser, "AT%XSIM?")      # SIM slot status (Nordic specific)
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

if __name__ == "__main__":
    print("Checking SIM and Network Status...")
    print("=" * 60)
    
    check_sim_status()