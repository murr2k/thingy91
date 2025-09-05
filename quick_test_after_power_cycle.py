#!/usr/bin/env python3
"""
Quick test script to run immediately after power cycling Thingy91
Attempts to connect and send AT commands before USB disconnects
"""
import serial
import time
import sys

def quick_test(port):
    """Quickly test AT commands"""
    try:
        print(f"Attempting to connect to {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=1,  # Short timeout
            write_timeout=1
        )
        
        print(f"[OK] Connected to {port}")
        
        # Quick AT test
        ser.write(b"AT\r\n")
        time.sleep(0.2)
        response = ser.read(100)
        if response:
            print(f"AT Response: {response.decode('utf-8', errors='ignore')}")
        
        # Check SIM status quickly
        ser.write(b"AT%XSIM?\r\n")
        time.sleep(0.2)
        response = ser.read(200)
        if response:
            print(f"SIM Status: {response.decode('utf-8', errors='ignore')}")
        
        # Check modem info
        ser.write(b"AT+CGMR\r\n")
        time.sleep(0.2)
        response = ser.read(200)
        if response:
            print(f"Modem Version: {response.decode('utf-8', errors='ignore')}")
            
        # Try to check for SoftSIM support
        ser.write(b"AT%SOFTSIM?\r\n")
        time.sleep(0.2)
        response = ser.read(200)
        if response:
            print(f"SoftSIM Command: {response.decode('utf-8', errors='ignore')}")
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"[ERROR] Serial error on {port}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("POWER CYCLE THE THINGY91 NOW!")
    print("Waiting 2 seconds...")
    print("="*60 + "\n")
    
    time.sleep(2)
    
    # Try both ports quickly
    for port in ["COM10", "COM11"]:
        print(f"\nTrying {port}...")
        if quick_test(port):
            print(f"[SUCCESS] Got response from {port}")
            break
        else:
            print(f"[SKIP] No response from {port}")
    
    print("\nTest complete!")