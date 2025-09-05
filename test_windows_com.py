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
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"Connected to {port}")
        
        # Clear any existing data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
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
            
            # Try more commands
            print("\nTrying more AT commands...")
            
            # Check SIM status
            ser.write(b"AT+CIMI\r\n")
            time.sleep(0.5)
            sim_response = ser.read(ser.in_waiting)
            print(f"CIMI (IMSI): {sim_response.decode('utf-8', errors='ignore')}")
            
            # Check network registration
            ser.write(b"AT+CEREG?\r\n")
            time.sleep(0.5)
            reg_response = ser.read(ser.in_waiting)
            print(f"CEREG: {reg_response.decode('utf-8', errors='ignore')}")
            
            return True
        else:
            print("No response received")
            return False
            
    except Exception as e:
        print(f"Error with {port}: {e}")
        return False
    finally:
        try:
            if 'ser' in locals():
                ser.close()
        except:
            pass

if __name__ == "__main__":
    # Windows COM ports
    ports = ["COM10", "COM11"]
    
    for port in ports:
        print(f"\n{'='*50}")
        print(f"Testing {port}")
        print('='*50)
        if test_at_communication(port):
            print(f"[OK] {port} responded to AT command")
        else:
            print(f"[FAIL] {port} did not respond")