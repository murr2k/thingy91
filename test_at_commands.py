#!/usr/bin/env python3
import serial
import time
import sys

def test_at_communication(port):
    try:
        # Try to open the serial port
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=3,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        print(f"Connected to {port}")
        
        # Clear any existing data
        ser.flushInput()
        ser.flushOutput()
        
        # Send AT command
        command = "AT\r\n"
        print(f"Sending: {repr(command)}")
        ser.write(command.encode())
        
        # Wait for response
        time.sleep(0.5)
        
        # Read response
        response = b""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting)
            time.sleep(0.1)
        
        if response:
            print(f"Response: {repr(response)}")
            print(f"Decoded: {response.decode('utf-8', errors='ignore')}")
            return True
        else:
            print("No response received")
            return False
            
    except Exception as e:
        print(f"Error with {port}: {e}")
        return False
    finally:
        try:
            ser.close()
        except:
            pass

if __name__ == "__main__":
    ports = ["/dev/ttyACM0", "/dev/ttyACM1"]
    
    for port in ports:
        print(f"\n=== Testing {port} ===")
        if test_at_communication(port):
            print(f"✓ {port} responded to AT command")
        else:
            print(f"✗ {port} did not respond")