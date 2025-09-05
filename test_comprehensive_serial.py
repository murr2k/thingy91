#!/usr/bin/env python3
import serial
import time
import sys

def test_serial_port(port, baudrate, timeout=2):
    """Test serial communication with various configurations"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"Testing {port} at {baudrate} baud...")
        
        # Clear buffers
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.1)
        
        # Try different AT command formats
        commands = [
            "AT\r\n",
            "AT\r",
            "AT\n",
            "at\r\n",
            "+++",  # Escape sequence
        ]
        
        for cmd in commands:
            print(f"  Trying: {repr(cmd)}")
            ser.write(cmd.encode())
            time.sleep(0.5)
            
            response = b""
            start_time = time.time()
            while time.time() - start_time < 1:
                if ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting)
                time.sleep(0.1)
            
            if response:
                print(f"  ✓ Response: {repr(response)}")
                print(f"  ✓ Decoded: {response.decode('utf-8', errors='ignore').strip()}")
                return True, baudrate
            else:
                print(f"  ✗ No response")
        
        ser.close()
        return False, baudrate
        
    except Exception as e:
        print(f"  Error: {e}")
        return False, baudrate

def main():
    ports = ["/dev/ttyACM0", "/dev/ttyACM1"]
    baudrates = [115200, 9600, 38400, 57600, 19200, 1200]
    
    working_configs = []
    
    for port in ports:
        print(f"\n{'='*50}")
        print(f"Testing port: {port}")
        print(f"{'='*50}")
        
        for baudrate in baudrates:
            success, baud = test_serial_port(port, baudrate)
            if success:
                working_configs.append((port, baud))
                print(f"✓ WORKING CONFIG: {port} at {baud} baud")
                break  # Found working config for this port
        
        if not any(config[0] == port for config in working_configs):
            print(f"✗ No working config found for {port}")
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    if working_configs:
        print("Working configurations:")
        for port, baud in working_configs:
            print(f"  {port}: {baud} baud")
    else:
        print("No working serial configurations found.")
        print("Device may need:")
        print("  1. Hardware reset")
        print("  2. Different firmware") 
        print("  3. Special initialization sequence")

if __name__ == "__main__":
    main()