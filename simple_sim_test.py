#!/usr/bin/env python3
"""
Simple SIM test - check if physical SIM is detected
"""
import serial
import time

def send_at_command(ser, command, timeout=5):
    print(f"→ {command}")
    ser.flushInput()
    ser.flushOutput()
    ser.write(f"{command}\r\n".encode())
    
    response = ""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += data
            if "OK" in response or "ERROR" in response or "+CME ERROR" in response:
                break
        time.sleep(0.1)
    
    clean_response = response.strip().replace('\r\n', ' | ')
    print(f"← {clean_response}")
    return response.strip()

def main():
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=3)
        print("Connected to Thingy91\n")
        
        # Basic test
        send_at_command(ser, "AT")
        
        # Check current functionality
        print("\n=== Current Status ===")
        send_at_command(ser, "AT+CFUN?")
        send_at_command(ser, "AT%XSIM?")
        
        # SIM PIN status
        print("\n=== SIM Tests ===")
        send_at_command(ser, "AT+CPIN?")
        send_at_command(ser, "AT+CCID")
        send_at_command(ser, "AT+CIMI")
        
        # Network status
        print("\n=== Network ===")
        send_at_command(ser, "AT+CSQ")
        send_at_command(ser, "AT+CEREG?")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()