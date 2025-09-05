#!/usr/bin/env python3
"""
Quick test for SoftSIM status on Thingy91
"""
import serial
import time

def send_at_command(ser, command, timeout=3):
    """Send AT command and return response"""
    print(f">>> {command}")
    ser.write(f"{command}\r\n".encode())
    
    time.sleep(0.5)
    response = ""
    start = time.time()
    
    while time.time() - start < timeout:
        if ser.in_waiting:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            if "OK" in response or "ERROR" in response:
                break
        time.sleep(0.1)
    
    print(f"<<< {response.strip()}\n")
    return response

def test_softsim():
    try:
        ser = serial.Serial('COM11', 115200, timeout=2)
        print("Connected to COM11\n")
        
        # Basic test
        send_at_command(ser, "AT")
        
        # Check SIM status
        print("=== SIM Status ===")
        send_at_command(ser, "AT%XSIM?")
        
        # Check IMSI
        send_at_command(ser, "AT+CIMI")
        
        # Check registration
        send_at_command(ser, "AT+CEREG?")
        
        # Check modem version
        send_at_command(ser, "AT+CGMR")
        
        # Try SoftSIM specific commands
        print("=== Testing SoftSIM Commands ===")
        send_at_command(ser, "AT%SOFTSIM?")
        send_at_command(ser, "AT%SOFTSIM=?")
        send_at_command(ser, "AT%SOFTSIM=1")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_softsim()