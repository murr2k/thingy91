#!/usr/bin/env python3
"""
Test cellular data connectivity
"""
import serial
import time

def send_at_command(ser, command, timeout=10):
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

def test_connectivity():
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=5)
        print("🔗 Testing Cellular Connectivity\n")
        
        # Check current status
        print("=== Registration Status ===")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+COPS?")
        
        # Check signal quality
        print("\n=== Signal Quality ===")
        send_at_command(ser, "AT+CSQ")
        send_at_command(ser, "AT+CESQ")
        
        # Check attachment
        print("\n=== Network Attachment ===")
        send_at_command(ser, "AT+CGATT?")
        
        # Try to attach if not attached
        response = send_at_command(ser, "AT+CGATT=1", timeout=30)
        if "OK" in response:
            print("✅ Attachment successful")
            time.sleep(3)
            send_at_command(ser, "AT+CGATT?")
        
        # Check PDP context
        print("\n=== PDP Context ===")
        send_at_command(ser, "AT+CGDCONT?")
        
        # Activate PDP context
        response = send_at_command(ser, "AT+CGACT=1,1", timeout=30)
        if "OK" in response:
            print("✅ PDP context activated")
        
        # Check if we got an IP address
        print("\n=== IP Address ===")
        send_at_command(ser, "AT+CGPADDR")
        
        # Test basic connectivity with ping
        print("\n=== Connectivity Test ===")
        ping_response = send_at_command(ser, 'AT+NPING="8.8.8.8",32,5000,1', timeout=15)
        if "OK" in ping_response or "+NPING:" in ping_response:
            print("✅ Ping test initiated")
        
        # Check final status
        print("\n=== Final Status ===")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+CGATT?")
        send_at_command(ser, "AT+CGACT?")
        
        ser.close()
        print("\n🎉 Connectivity test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_connectivity()