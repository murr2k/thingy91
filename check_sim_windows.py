#!/usr/bin/env python3
"""
Check SIM status and diagnose network registration issues on Windows
"""
import serial
import time
import sys

def send_at_command(ser, command, timeout=10):
    """Send AT command and return response"""
    print(f"Sending: {command}")
    
    # Clear buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
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
    print("-" * 40)
    return response.strip()

def check_sim_status(port):
    """Check SIM and network status in detail"""
    
    try:
        # Connect to serial port
        print(f"Connecting to {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=5,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"Connected to {port}")
        time.sleep(2)  # Give device time to settle
        
        # Test basic communication
        response = send_at_command(ser, "AT")
        if "OK" not in response:
            print(f"[WARNING] No AT response from {port}, trying anyway...")
        
        print("\n=== SIM Status ===")
        send_at_command(ser, "AT+CPIN?")      # SIM PIN status
        send_at_command(ser, "AT+CCID")       # SIM ICCID
        send_at_command(ser, "AT+CIMI")       # SIM IMSI
        
        print("\n=== Nordic Specific SIM Commands ===")
        send_at_command(ser, "AT%XSIM?")      # Nordic SIM slot status
        send_at_command(ser, "AT%XSIM=1")     # Enable SIM interface
        send_at_command(ser, "AT%XSIM?")      # Check again
        
        print("\n=== Network Registration ===")
        send_at_command(ser, "AT+CEREG=2")    # Enable network registration with location
        send_at_command(ser, "AT+CEREG?")     # EPS registration status
        send_at_command(ser, "AT+CREG?")      # Network registration status
        send_at_command(ser, "AT+CGREG?")     # GPRS registration status
        
        print("\n=== Signal Quality ===")
        send_at_command(ser, "AT+CSQ")        # Signal quality
        send_at_command(ser, "AT+CESQ")       # Extended signal quality
        
        print("\n=== Current Operator ===")
        send_at_command(ser, "AT+COPS?")      # Current operator
        
        print("\n=== APN Configuration ===")
        send_at_command(ser, "AT+CGDCONT?")   # PDP context
        
        print("\n=== SoftSIM Specific Commands ===")
        # Try to check if SoftSIM is available
        send_at_command(ser, "AT%SOFTSIM?")   # Check SoftSIM status (if supported)
        send_at_command(ser, "AT%SOFTSIM=1")  # Try to enable SoftSIM
        
        print("\n=== Attach Status ===")
        send_at_command(ser, "AT+CGATT?")     # Attach status
        
        print("\n=== Modem Functionality ===")
        send_at_command(ser, "AT+CFUN?")      # Functionality level
        
        print("\n=== Network Errors ===")
        send_at_command(ser, "AT+CEER")       # Extended error report
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"[ERROR] Serial port error on {port}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Status check failed on {port}: {e}")
        return False

if __name__ == "__main__":
    print("Checking SIM and Network Status on Windows COM ports...")
    print("=" * 60)
    
    # Try both COM ports
    ports = ["COM10", "COM11"]
    
    for port in ports:
        print(f"\n{'='*60}")
        print(f"Testing {port}")
        print('='*60)
        
        if check_sim_status(port):
            print(f"\n[SUCCESS] Completed check on {port}")
            break  # Stop if we found a working port
        else:
            print(f"\n[FAILED] Could not check status on {port}")