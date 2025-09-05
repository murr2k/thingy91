#!/usr/bin/env python3
"""
Set up Onomondo credentials in the secrets GUI
"""

import requests
import json
import base64

# Secrets GUI endpoint
GUI_URL = "http://localhost:5000"

# Onomondo credentials
ONOMONDO_CREDS = {
    'ONOMONDO_API_KEY': 'onok_d90a23b7.lp5n7QzS8inO4Jf0pKRSJdMR4WF0Qxtqn3eMZCyPJPwswMCvt/2Ez+YN',
    'ONOMONDO_IMSI': '234502102769985',
    'ONOMONDO_ICCID': '89457300000032481957', 
    'ONOMONDO_MSISDN': '882360027454443'
}

def login_to_gui():
    """Login to the secrets GUI"""
    session = requests.Session()
    
    # Get login page to get session
    response = session.get(f"{GUI_URL}/login")
    
    # Login with default credentials
    login_data = {
        'username': 'admin',
        'password': 'changeme'
    }
    
    response = session.post(f"{GUI_URL}/login", data=login_data, allow_redirects=True)
    
    if response.status_code == 200 and "dashboard" in response.text.lower():
        print("✓ Logged into secrets GUI")
        return session
    else:
        print(f"✗ Failed to login to secrets GUI - Status: {response.status_code}")
        return None

def configure_onomondo(session):
    """Configure Onomondo service in the GUI"""
    
    config_data = {
        'password': 'onomondo-encryption-key-123',  # Encryption password
        'secrets': ONOMONDO_CREDS
    }
    
    response = session.post(
        f"{GUI_URL}/api/service/onomondo/configure",
        json=config_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✓ Onomondo credentials configured successfully")
        return True
    else:
        print(f"✗ Failed to configure Onomondo: {response.text}")
        return False

def test_onomondo(session):
    """Test Onomondo connection"""
    
    response = session.post(f"{GUI_URL}/api/service/onomondo/test")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Onomondo connection test: {result.get('status', 'unknown')}")
        print(f"  Message: {result.get('message', 'No message')}")
        return True
    else:
        print(f"✗ Connection test failed: {response.text}")
        return False

def main():
    print("Setting up Onomondo credentials in Secrets GUI...")
    
    # Login to GUI
    session = login_to_gui()
    if not session:
        return 1
    
    # Configure Onomondo
    if not configure_onomondo(session):
        return 1
    
    # Test connection
    test_onomondo(session)
    
    print("\n=== Setup Complete ===")
    print("Your Onomondo credentials are now stored securely in the GUI.")
    print("Visit http://localhost:5000 to view the dashboard.")
    
    return 0

if __name__ == "__main__":
    exit(main())