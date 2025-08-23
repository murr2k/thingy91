#!/usr/bin/env python3
"""
Onomondo SoftSIM Provisioning Tool for Nordic Thingy91
Copyright (c) 2025 Nordic Thingy91 Demo
"""

import serial
import base64
import json
import time
import sys
import argparse
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoftSIMState(Enum):
    """SoftSIM provisioning states"""
    UNPROVISIONED = "UNPROVISIONED"
    PROVISIONING = "PROVISIONING"
    PROVISIONED = "PROVISIONED"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"


@dataclass
class SoftSIMProfile:
    """SoftSIM profile data structure"""
    imsi: str
    iccid: str
    ki: str
    opc: str
    profile_id: str
    apn: str = "onomondo"
    version: str = "1.0.0"
    
    def to_json(self) -> str:
        """Convert profile to JSON string"""
        return json.dumps({
            "profile_version": self.version,
            "network_provider": "onomondo",
            "credentials": {
                "imsi": self.imsi,
                "iccid": self.iccid,
                "ki": self.ki,
                "opc": self.opc
            },
            "network_config": {
                "apn": self.apn,
                "preferred_plmn": ["26201", "26202"],
                "rat_priority": ["LTE-M", "NB-IoT"]
            },
            "security": {
                "algorithm": "AES",
                "key_size": 128
            },
            "profile_id": self.profile_id
        })
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'SoftSIMProfile':
        """Load profile from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(
            imsi=data['credentials']['imsi'],
            iccid=data['credentials']['iccid'],
            ki=data['credentials']['ki'],
            opc=data['credentials']['opc'],
            profile_id=data.get('profile_id', 'ONOMONDO_PROFILE'),
            apn=data.get('network_config', {}).get('apn', 'onomondo'),
            version=data.get('profile_version', '1.0.0')
        )


class SoftSIMProvisioner:
    """SoftSIM provisioning manager for Thingy91"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 10):
        """
        Initialize provisioner
        
        Args:
            port: Serial port path (e.g., /dev/ttyACM0 or COM3)
            baudrate: Serial baudrate (default 115200)
            timeout: Command timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """Connect to device via serial port"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Clear any pending data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            
            # Test connection with AT command
            response = self.send_at_command("AT")
            if "OK" in response:
                logger.info("Device communication verified")
                return True
            else:
                logger.error("Device not responding to AT commands")
                return False
                
        except serial.SerialException as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Disconnected from device")
    
    def send_at_command(self, cmd: str, wait_time: float = 1.0) -> str:
        """
        Send AT command and return response
        
        Args:
            cmd: AT command to send
            wait_time: Time to wait for response
            
        Returns:
            Response string
        """
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port not connected")
        
        # Clear buffers
        self.ser.reset_input_buffer()
        
        # Send command
        cmd_bytes = f"{cmd}\r\n".encode('utf-8')
        self.ser.write(cmd_bytes)
        logger.debug(f"Sent: {cmd}")
        
        # Wait for response
        time.sleep(wait_time)
        
        # Read response
        response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
        logger.debug(f"Received: {response}")
        
        return response
    
    def get_status(self) -> SoftSIMState:
        """Get current SoftSIM status"""
        response = self.send_at_command("AT+OSIMSTAT")
        
        for state in SoftSIMState:
            if state.value in response:
                return state
        
        return SoftSIMState.ERROR
    
    def provision_profile(self, profile: SoftSIMProfile) -> bool:
        """
        Provision SoftSIM profile to device
        
        Args:
            profile: SoftSIM profile to provision
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting SoftSIM provisioning...")
        
        # Check current status
        status = self.get_status()
        logger.info(f"Current status: {status.value}")
        
        if status == SoftSIMState.ACTIVE:
            logger.warning("SoftSIM already active, removing existing profile...")
            if not self.remove_profile():
                logger.error("Failed to remove existing profile")
                return False
        
        # Encode profile to base64
        profile_json = profile.to_json()
        profile_b64 = base64.b64encode(profile_json.encode()).decode()
        logger.debug(f"Profile encoded: {len(profile_b64)} bytes")
        
        # Send provisioning command
        logger.info("Sending provisioning command...")
        response = self.send_at_command(f"AT+OSIMPROV={profile_b64}", wait_time=5)
        
        if "OK" not in response:
            logger.error(f"Provisioning failed: {response}")
            return False
        
        logger.info("✓ Profile provisioned successfully")
        
        # Verify provisioning
        status = self.get_status()
        if status != SoftSIMState.PROVISIONED:
            logger.error(f"Unexpected status after provisioning: {status.value}")
            return False
        
        return True
    
    def activate(self) -> bool:
        """Activate SoftSIM"""
        logger.info("Activating SoftSIM...")
        
        response = self.send_at_command("AT+OSIMACT", wait_time=3)
        
        if "OK" not in response:
            logger.error(f"Activation failed: {response}")
            return False
        
        logger.info("✓ SoftSIM activated")
        return True
    
    def remove_profile(self) -> bool:
        """Remove existing SoftSIM profile"""
        logger.info("Removing SoftSIM profile...")
        
        response = self.send_at_command("AT+OSIMREM", wait_time=2)
        
        if "OK" not in response:
            logger.error(f"Profile removal failed: {response}")
            return False
        
        logger.info("✓ Profile removed")
        return True
    
    def wait_for_registration(self, timeout: int = 60) -> bool:
        """
        Wait for network registration
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if registered, False if timeout
        """
        logger.info("Waiting for network registration...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.send_at_command("AT+CEREG?")
            
            # Check for registered states (1=home, 5=roaming)
            if "+CEREG: 0,1" in response or "+CEREG: 0,5" in response:
                logger.info("✓ Registered on network")
                
                # Get operator info
                operator = self.send_at_command("AT+COPS?")
                if "+COPS:" in operator:
                    logger.info(f"Network operator: {operator.split('+COPS:')[1].strip()}")
                
                # Get signal strength
                signal = self.send_at_command("AT+CSQ")
                if "+CSQ:" in signal:
                    logger.info(f"Signal strength: {signal.split('+CSQ:')[1].strip()}")
                
                return True
            
            print(".", end="", flush=True)
            time.sleep(2)
        
        print()
        logger.error("Network registration timeout")
        return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive SoftSIM and network information"""
        info = {}
        
        # Get SoftSIM status
        info['status'] = self.get_status().value
        
        # Get IMSI
        response = self.send_at_command("AT+CIMI")
        if response and not "ERROR" in response:
            lines = response.strip().split('\n')
            for line in lines:
                if line and not "AT+" in line and not "OK" in line:
                    info['imsi'] = line.strip()
                    break
        
        # Get network registration
        response = self.send_at_command("AT+CEREG?")
        if "+CEREG:" in response:
            info['registration'] = response.split('+CEREG:')[1].strip()
        
        # Get operator
        response = self.send_at_command("AT+COPS?")
        if "+COPS:" in response:
            info['operator'] = response.split('+COPS:')[1].strip()
        
        # Get signal strength
        response = self.send_at_command("AT+CSQ")
        if "+CSQ:" in response:
            csq_str = response.split('+CSQ:')[1].split(',')[0].strip()
            try:
                csq = int(csq_str)
                if csq != 99:
                    # Convert to dBm
                    dbm = -113 + (csq * 2)
                    info['signal_strength'] = f"{csq} ({dbm} dBm)"
                else:
                    info['signal_strength'] = "Unknown"
            except:
                info['signal_strength'] = csq_str
        
        # Get custom SoftSIM info
        response = self.send_at_command("AT+OSIMINFO")
        if "+OSIMINFO:" in response:
            info['softsim_info'] = response.split('+OSIMINFO:')[1].strip()
        
        return info
    
    def run_diagnostics(self) -> bool:
        """Run comprehensive diagnostics"""
        logger.info("Running SoftSIM diagnostics...")
        
        tests = [
            ("Modem communication", "AT", "OK"),
            ("Modem information", "ATI", "nRF9160"),
            ("SIM status", "AT+OSIMSTAT", "OSIMSTAT:"),
            ("Network registration", "AT+CEREG?", "+CEREG:"),
            ("Signal quality", "AT+CSQ", "+CSQ:"),
            ("Operator selection", "AT+COPS?", "+COPS:"),
            ("PDP context", "AT+CGDCONT?", "+CGDCONT:"),
            ("Network attach", "AT+CGATT?", "+CGATT:"),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, command, expected in tests:
            response = self.send_at_command(command)
            if expected in response:
                logger.info(f"✓ {test_name}: PASS")
                passed += 1
            else:
                logger.error(f"✗ {test_name}: FAIL")
                logger.debug(f"  Response: {response}")
                failed += 1
        
        logger.info(f"\nDiagnostics complete: {passed} passed, {failed} failed")
        return failed == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Onomondo SoftSIM Provisioning Tool')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyACM0 or COM3)')
    parser.add_argument('--profile', '-p', help='JSON profile file to provision')
    parser.add_argument('--baudrate', '-b', type=int, default=115200, help='Serial baudrate')
    parser.add_argument('--activate', '-a', action='store_true', help='Activate after provisioning')
    parser.add_argument('--info', '-i', action='store_true', help='Get device information')
    parser.add_argument('--remove', '-r', action='store_true', help='Remove existing profile')
    parser.add_argument('--diagnostics', '-d', action='store_true', help='Run diagnostics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create provisioner
    provisioner = SoftSIMProvisioner(args.port, args.baudrate)
    
    try:
        # Connect to device
        if not provisioner.connect():
            logger.error("Failed to connect to device")
            return 1
        
        # Handle different operations
        if args.remove:
            if provisioner.remove_profile():
                logger.info("Profile removed successfully")
                return 0
            else:
                return 1
        
        if args.diagnostics:
            if provisioner.run_diagnostics():
                return 0
            else:
                return 1
        
        if args.info:
            info = provisioner.get_info()
            print("\n=== Device Information ===")
            for key, value in info.items():
                print(f"{key}: {value}")
            return 0
        
        if args.profile:
            # Load and provision profile
            profile = SoftSIMProfile.from_json_file(args.profile)
            
            if not provisioner.provision_profile(profile):
                logger.error("Provisioning failed")
                return 1
            
            if args.activate:
                if not provisioner.activate():
                    logger.error("Activation failed")
                    return 1
                
                if not provisioner.wait_for_registration():
                    logger.warning("Network registration timeout")
                
                # Show final info
                info = provisioner.get_info()
                print("\n=== Final Status ===")
                for key, value in info.items():
                    print(f"{key}: {value}")
        
        else:
            # Just show status
            status = provisioner.get_status()
            logger.info(f"SoftSIM status: {status.value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    finally:
        provisioner.disconnect()


if __name__ == "__main__":
    sys.exit(main())