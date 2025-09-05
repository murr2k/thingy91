#!/usr/bin/env python3
"""
Test HTTP connectivity over cellular
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

def test_http():
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=10)
        print("🌐 Testing HTTP Connectivity\n")
        
        # Check connection status first
        print("=== Connection Status ===")
        send_at_command(ser, "AT+CEREG?")
        send_at_command(ser, "AT+CGPADDR")
        
        # Try DNS resolution
        print("\n=== DNS Test ===")
        dns_response = send_at_command(ser, 'AT+CDNSGIP="httpbin.org"', timeout=30)
        if "+CDNSGIP:" in dns_response:
            print("✅ DNS resolution working")
        
        # HTTP GET test
        print("\n=== HTTP GET Test ===")
        
        # Configure HTTP
        send_at_command(ser, "AT+HTTPINIT")
        send_at_command(ser, 'AT+HTTPPARA="CID",0')
        send_at_command(ser, 'AT+HTTPPARA="URL","http://httpbin.org/ip"')
        
        # Perform HTTP GET
        http_response = send_at_command(ser, "AT+HTTPACTION=0", timeout=30)
        if "OK" in http_response:
            print("✅ HTTP request sent")
            time.sleep(3)
            
            # Read HTTP response
            send_at_command(ser, "AT+HTTPREAD")
        
        # Terminate HTTP
        send_at_command(ser, "AT+HTTPTERM")
        
        # Alternative test - try Nordic-specific socket commands
        print("\n=== Socket Test ===")
        socket_response = send_at_command(ser, 'AT#NSLOOKUP="httpbin.org"', timeout=20)
        if "OK" in socket_response or "#NSLOOKUP:" in socket_response:
            print("✅ Socket DNS lookup working")
        
        ser.close()
        print("\n🎉 HTTP test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_http()