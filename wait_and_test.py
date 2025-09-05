#!/usr/bin/env python3
"""
Wait for COM ports to appear after power cycle, then test immediately
"""
import serial
import serial.tools.list_ports
import time
import sys

def wait_for_ports(timeout=10):
    """Wait for COM10 or COM11 to appear"""
    print("Waiting for COM ports to appear...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if "COM10" in ports or "COM11" in ports:
            print(f"Found ports: {[p for p in ports if 'COM' in p]}")
            return True
        time.sleep(0.5)
        print(".", end="", flush=True)
    
    print("\n[TIMEOUT] No COM10/COM11 found")
    return False

def test_port(port):
    """Test a COM port"""
    try:
        print(f"\nTesting {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=2,
            write_timeout=2
        )
        
        print(f"[OK] Connected to {port}")
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Test AT command
        print("Sending AT...")
        ser.write(b"AT\r\n")
        time.sleep(0.5)
        response = ser.read(ser.in_waiting or 100)
        
        if response:
            print(f"Response: {response.decode('utf-8', errors='ignore').strip()}")
            
            # If we got a response, try more commands
            commands = [
                ("AT+CGMR", "Modem Version"),
                ("AT%XSIM?", "SIM Status"),
                ("AT+CIMI", "IMSI"),
                ("AT+CFUN?", "Functionality"),
                ("AT%SOFTSIM?", "SoftSIM Support")
            ]
            
            for cmd, desc in commands:
                print(f"\nChecking {desc}...")
                ser.write(f"{cmd}\r\n".encode())
                time.sleep(0.5)
                response = ser.read(ser.in_waiting or 200)
                if response:
                    print(f"{desc}: {response.decode('utf-8', errors='ignore').strip()}")
        else:
            print("No response to AT command")
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("\n" + "="*60)
    print("NORDIC THINGY91 COM PORT TESTER")
    print("="*60)
    print("\n1. POWER CYCLE THE THINGY91 NOW!")
    print("2. Script will wait for COM ports to appear...")
    print("3. Then test communication immediately\n")
    
    # Wait for ports to appear
    if wait_for_ports(timeout=15):
        # List all available ports
        print("\nAvailable COM ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  - {port.device}: {port.description}")
        
        # Test COM10 and COM11
        tested = False
        for port in ["COM10", "COM11"]:
            try:
                ports = [p.device for p in serial.tools.list_ports.comports()]
                if port in ports:
                    if test_port(port):
                        tested = True
                        print(f"\n[SUCCESS] Communication established on {port}")
                        break
            except Exception as e:
                print(f"[ERROR] Failed to test {port}: {e}")
        
        if not tested:
            print("\n[FAILED] Could not communicate with any port")
    else:
        print("\n[FAILED] COM ports did not appear after power cycle")
        print("\nTroubleshooting:")
        print("1. Make sure Thingy91 is connected via USB")
        print("2. Try installing Nordic USB drivers")
        print("3. Check if device appears in Device Manager")
        print("4. May need to reflash firmware via J-Link")

if __name__ == "__main__":
    main()