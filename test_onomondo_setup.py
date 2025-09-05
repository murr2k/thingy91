#!/usr/bin/env python3
"""
Test Onomondo SoftSIM setup with Thingy91
"""

import sys
import json
from pathlib import Path

def check_credentials():
    """Check if Onomondo credentials are properly set up"""
    print("🔍 Checking Onomondo Setup...")
    
    # Check secrets GUI storage
    secrets_file = Path("secrets_gui/.env.onomondo.encrypted")
    if secrets_file.exists():
        print("✅ Onomondo credentials stored in secrets GUI")
    else:
        print("❌ No encrypted credentials found")
    
    # Check profile file
    profile_file = Path("profiles/my_thingy91_profile.json")
    if profile_file.exists():
        print("✅ Thingy91 profile created")
        with open(profile_file) as f:
            profile = json.load(f)
            print(f"   - IMSI: {profile['credentials']['imsi']}")
            print(f"   - ICCID: {profile['credentials']['iccid']}")
            print(f"   - APN: {profile['network_config']['apn']}")
    else:
        print("❌ No Thingy91 profile found")

def check_device_connection():
    """Check if Thingy91 is connected"""
    print("\n📱 Checking Device Connection...")
    
    import glob
    devices = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    
    if devices:
        print(f"✅ Found USB devices: {devices}")
        return devices[0]
    else:
        print("❌ No Thingy91 device found")
        print("   Connect your Thingy91 via USB and try again")
        return None

def test_device_communication(port):
    """Test basic AT communication with device"""
    print(f"\n💬 Testing communication on {port}...")
    
    try:
        from scripts.provision_softsim import SoftSIMProvisioner
        
        provisioner = SoftSIMProvisioner(port)
        if provisioner.connect():
            print("✅ Connected to device")
            
            # Run basic diagnostics
            print("\n🔧 Running diagnostics...")
            provisioner.run_diagnostics()
            
            # Get device info
            print("\n📋 Device Information:")
            info = provisioner.get_info()
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            provisioner.disconnect()
            return True
        else:
            print("❌ Failed to connect to device")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def simulate_provisioning():
    """Show what the provisioning process would look like"""
    print("\n🔄 SoftSIM Provisioning Process:")
    print("   1. Connect to device via serial")
    print("   2. Check current SoftSIM status")
    print("   3. Configure APN settings (onomondo)")
    print("   4. Set network preferences (LTE-M/NB-IoT)")
    print("   5. Test network registration")
    print("   6. Verify data connectivity")
    
    print("\n📝 Commands that would be executed:")
    print("   AT+CGDCONT=1,\"IP\",\"onomondo\"")
    print("   AT+COPS=0,0,\"23450\"")
    print("   AT+CEREG=1")
    print("   AT+CGATT=1")

def show_next_steps():
    """Show what to do next"""
    print("\n🚀 Next Steps:")
    print("1. Connect your Thingy91 to this computer via USB")
    print("2. Run: python3 scripts/provision_softsim.py /dev/ttyACM0 --info")
    print("3. Run: python3 scripts/provision_softsim.py /dev/ttyACM0 --profile profiles/my_thingy91_profile.json")
    print("4. Monitor status at: http://localhost:5000")
    
    print("\n📚 Your SoftSIM Details:")
    print("   - Status: Online (already working!)")
    print("   - IMSI: 234502102769985")
    print("   - ICCID: 89457300000032481957")
    print("   - Current IP: 100.106.249.62")
    print("   - APN: onomondo")
    
    print("\n💡 Since your SoftSIM is already online, you may just need to:")
    print("   - Configure the Thingy91 to use APN 'onomondo'")
    print("   - Set network to LTE-M or NB-IoT")
    print("   - Test connectivity")

def main():
    print("=" * 60)
    print("🌐 Onomondo SoftSIM Setup Test")
    print("=" * 60)
    
    # Check credentials setup
    check_credentials()
    
    # Check device connection
    device = check_device_connection()
    
    if device:
        # Test communication
        test_device_communication(device)
    else:
        # Show what would happen
        simulate_provisioning()
    
    # Show next steps
    show_next_steps()
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())