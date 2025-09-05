#!/usr/bin/env python3
"""
Check the status of services in the Secrets Manager GUI.
"""

import requests
import json
from datetime import datetime

def check_gui_status():
    """Check service status from the GUI API"""
    
    print("=" * 60)
    print("🔍 Checking Secrets Manager GUI Service Status")
    print("=" * 60)
    
    # The API requires authentication, so we'll check the login page first
    try:
        # Check if GUI is running
        response = requests.get("http://localhost:5000/login", timeout=5)
        if response.status_code == 200:
            print("✅ GUI is running at http://localhost:5000")
        else:
            print(f"❌ GUI returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to GUI: {e}")
        return
    
    print("\n📊 Service Status Check:")
    print("-" * 40)
    
    # Try to get status (may require auth)
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            statuses = response.json()
            
            # Focus on Fly.io
            if 'flyio' in statuses:
                flyio_status = statuses['flyio']
                print(f"\n🚀 Fly.io Service:")
                print(f"   Status: {flyio_status.get('status', 'unknown')}")
                print(f"   Message: {flyio_status.get('message', 'N/A')}")
                if 'timestamp' in flyio_status:
                    print(f"   Last checked: {flyio_status['timestamp']}")
                if 'response_time' in flyio_status:
                    print(f"   Response time: {flyio_status['response_time']:.2f}s")
            else:
                print("\n⚠️  Fly.io service not found in status response")
            
            # Show other services briefly
            print("\n📦 Other Services:")
            for service_id, status in statuses.items():
                if service_id != 'flyio':
                    status_emoji = {
                        'healthy': '✅',
                        'degraded': '⚠️',
                        'unhealthy': '❌',
                        'unconfigured': '⚪',
                        'unknown': '❓'
                    }.get(status.get('status', 'unknown'), '❓')
                    print(f"   {status_emoji} {service_id}: {status.get('status', 'unknown')}")
                    
        elif response.status_code == 401:
            print("⚠️  API requires authentication")
            print("\nTo view status in the GUI:")
            print("1. Open http://localhost:5000")
            print("2. Login with admin/changeme")
            print("3. Check the dashboard for service status indicators")
        else:
            print(f"❌ API returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
    
    print("\n" + "=" * 60)
    print("💡 Access the GUI at: http://localhost:5000")
    print("   Username: admin")
    print("   Password: changeme")
    print("=" * 60)

if __name__ == "__main__":
    check_gui_status()