#!/usr/bin/env python3
"""
Universal Service Setup Script
Configures CLI tools and services using tokens from Secrets Manager
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app import EncryptedEnvFile
except ImportError:
    print("Warning: Could not import EncryptedEnvFile", file=sys.stderr)
    EncryptedEnvFile = None

class ServiceConfigurator:
    """Configures various services with stored credentials"""
    
    def __init__(self):
        self.services = {
            'github': self.setup_github,
            'flyio': self.setup_flyio,
            'npm': self.setup_npm,
            'terraform': self.setup_terraform,
            'slack': self.setup_slack_cli,
            'cloudflare': self.setup_cloudflare,
            'digikey': self.setup_digikey,
            'blynk': self.setup_blynk,
        }
    
    def get_token(self, service: str, key: str) -> Optional[str]:
        """Get token from environment or encrypted file"""
        # Try environment variable
        env_key = f"{service.upper()}_{key.upper()}"
        token = os.environ.get(env_key)
        if token:
            return token
        
        # Try encrypted file
        if EncryptedEnvFile:
            env_file = Path(f'.env.{service}')
            if not env_file.with_suffix('.encrypted').exists():
                env_file = Path(__file__).parent.parent / f'.env.{service}'
            
            if env_file.with_suffix('.encrypted').exists():
                try:
                    import getpass
                    password = getpass.getpass(f'Enter password for {service}: ')
                    ef = EncryptedEnvFile(str(env_file))
                    secrets = ef.decrypt_env(password.encode())
                    return secrets.get(env_key)
                except Exception as e:
                    print(f"Error decrypting: {e}", file=sys.stderr)
        
        return None
    
    def setup_github(self) -> bool:
        """Setup GitHub CLI"""
        print("🐙 Setting up GitHub CLI...")
        
        token = self.get_token('github', 'token')
        if not token:
            print("  ❌ No GitHub token found")
            return False
        
        try:
            # Check if gh is installed
            result = subprocess.run(['which', 'gh'], capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  GitHub CLI not installed. Install from: https://cli.github.com/")
                return False
            
            # Authenticate
            process = subprocess.Popen(
                ['gh', 'auth', 'login', '--with-token'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=token)
            
            if process.returncode == 0:
                print("  ✅ GitHub CLI authenticated")
                subprocess.run(['gh', 'auth', 'status'])
                return True
            else:
                print(f"  ❌ Failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_flyio(self) -> bool:
        """Setup Fly.io CLI"""
        print("🚀 Setting up Fly.io CLI...")
        
        token = self.get_token('flyio', 'api_token')
        if not token:
            print("  ❌ No Fly.io token found")
            return False
        
        try:
            # Check if flyctl is installed
            fly_cmd = 'fly'
            result = subprocess.run(['which', 'fly'], capture_output=True)
            if result.returncode != 0:
                fly_cmd = 'flyctl'
                result = subprocess.run(['which', 'flyctl'], capture_output=True)
                if result.returncode != 0:
                    print("  ⚠️  Fly.io CLI not installed. Install from: https://fly.io/docs/hands-on/install-flyctl/")
                    return False
            
            # Configure
            config_dir = Path.home() / '.fly'
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / 'config.yml'
            with open(config_file, 'w') as f:
                f.write(f'access_token: {token}\n')
            
            os.chmod(config_file, 0o600)
            
            # Verify
            result = subprocess.run([fly_cmd, 'auth', 'whoami'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Fly.io authenticated as: {result.stdout.strip()}")
                return True
            else:
                print(f"  ❌ Failed to authenticate")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_npm(self) -> bool:
        """Setup NPM authentication"""
        print("📦 Setting up NPM Registry...")
        
        token = self.get_token('npm', 'auth_token')
        if not token:
            print("  ❌ No NPM token found")
            return False
        
        try:
            # Check if npm is installed
            result = subprocess.run(['which', 'npm'], capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  npm not installed. Install Node.js from: https://nodejs.org/")
                return False
            
            # Configure
            subprocess.run(['npm', 'config', 'set', '//registry.npmjs.org/:_authToken', token])
            
            # Verify
            result = subprocess.run(['npm', 'whoami'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ NPM authenticated as: {result.stdout.strip()}")
                return True
            else:
                print(f"  ❌ Failed to authenticate")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_terraform(self) -> bool:
        """Setup Terraform Cloud"""
        print("🏗️  Setting up Terraform Cloud...")
        
        token = self.get_token('terraform', 'api_token')
        if not token:
            print("  ❌ No Terraform token found")
            return False
        
        try:
            # Check if terraform is installed
            result = subprocess.run(['which', 'terraform'], capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  Terraform not installed. Install from: https://www.terraform.io/downloads")
                return False
            
            # Create credentials file
            tf_dir = Path.home() / '.terraform.d'
            tf_dir.mkdir(exist_ok=True)
            
            credentials = {
                "credentials": {
                    "app.terraform.io": {
                        "token": token
                    }
                }
            }
            
            creds_file = tf_dir / 'credentials.tfrc.json'
            with open(creds_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            os.chmod(creds_file, 0o600)
            
            print(f"  ✅ Terraform Cloud credentials configured")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_slack_cli(self) -> bool:
        """Setup Slack CLI"""
        print("💬 Setting up Slack CLI...")
        
        token = self.get_token('slack', 'bot_token')
        if not token:
            print("  ❌ No Slack token found")
            return False
        
        try:
            # Check if slack-cli is installed
            result = subprocess.run(['which', 'slack'], capture_output=True)
            if result.returncode != 0:
                print("  ⚠️  Slack CLI not installed")
                print("     Install: curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash")
                return False
            
            # Export token for Slack CLI
            os.environ['SLACK_BOT_TOKEN'] = token
            
            # Test authentication
            result = subprocess.run(['slack', 'auth', 'test'], 
                                  env=os.environ.copy(),
                                  capture_output=True, text=True)
            
            if 'ok' in result.stdout.lower():
                print(f"  ✅ Slack authenticated")
                return True
            else:
                print(f"  ❌ Failed to authenticate")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_cloudflare(self) -> bool:
        """Setup Cloudflare credentials"""
        print("☁️  Setting up Cloudflare...")
        
        email = self.get_token('cloudflare', 'email')
        api_key = self.get_token('cloudflare', 'global_api_key')
        
        if not email or not api_key:
            print("  ❌ Cloudflare credentials not found")
            return False
        
        try:
            # Create .cloudflare directory
            cf_dir = Path.home() / '.cloudflare'
            cf_dir.mkdir(exist_ok=True)
            
            # Write credentials
            config = {
                'email': email,
                'api_key': api_key
            }
            
            config_file = cf_dir / 'credentials.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            os.chmod(config_file, 0o600)
            
            print(f"  ✅ Cloudflare credentials configured")
            print(f"     Email: {email}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_digikey(self) -> bool:
        """Setup DigiKey OAuth credentials"""
        print("📟 Setting up DigiKey API...")
        
        client_id = self.get_token('digikey', 'client_id')
        client_secret = self.get_token('digikey', 'client_secret')
        
        if not client_id or not client_secret:
            print("  ❌ DigiKey credentials not found")
            return False
        
        try:
            # Create .digikey directory
            dk_dir = Path.home() / '.digikey'
            dk_dir.mkdir(exist_ok=True)
            
            # Write credentials
            config = {
                'client_id': client_id,
                'client_secret': client_secret,
                'environment': self.get_token('digikey', 'environment') or 'sandbox'
            }
            
            # Add tokens if available
            access_token = self.get_token('digikey', 'access_token')
            refresh_token = self.get_token('digikey', 'refresh_token')
            
            if access_token:
                config['access_token'] = access_token
            if refresh_token:
                config['refresh_token'] = refresh_token
            
            config_file = dk_dir / 'credentials.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            os.chmod(config_file, 0o600)
            
            print(f"  ✅ DigiKey credentials configured")
            print(f"     Environment: {config['environment']}")
            print(f"     Client ID: {client_id[:10]}...")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_blynk(self) -> bool:
        """Setup Blynk IoT credentials"""
        print("📱 Setting up Blynk IoT...")
        
        auth_token = self.get_token('blynk', 'auth_token')
        
        if not auth_token:
            print("  ❌ Blynk auth token not found")
            return False
        
        try:
            # Create .blynk directory
            blynk_dir = Path.home() / '.blynk'
            blynk_dir.mkdir(exist_ok=True)
            
            # Write credentials
            config = {
                'auth_token': auth_token,
                'organization_id': self.get_token('blynk', 'organization_id'),
                'template_name': self.get_token('blynk', 'template_name'),
                'device_name': self.get_token('blynk', 'device_name')
            }
            
            config_file = blynk_dir / 'credentials.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            os.chmod(config_file, 0o600)
            
            print(f"  ✅ Blynk credentials configured")
            if config.get('device_name'):
                print(f"     Device: {config['device_name']}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def setup_all(self, services: list = None) -> Dict[str, bool]:
        """Setup all or specified services"""
        results = {}
        
        if not services:
            services = list(self.services.keys())
        
        for service in services:
            if service in self.services:
                results[service] = self.services[service]()
            else:
                print(f"⚠️  Unknown service: {service}")
                results[service] = False
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Setup services with Secrets Manager credentials')
    parser.add_argument('services', nargs='*', 
                       help='Services to setup (default: all)')
    parser.add_argument('--list', action='store_true',
                       help='List available services')
    
    args = parser.parse_args()
    
    configurator = ServiceConfigurator()
    
    if args.list:
        print("Available services:")
        for service in configurator.services.keys():
            print(f"  - {service}")
        return
    
    print("═══════════════════════════════════════════════════")
    print("   Service Configuration Manager")
    print("═══════════════════════════════════════════════════")
    print()
    
    results = configurator.setup_all(args.services if args.services else None)
    
    print()
    print("═══════════════════════════════════════════════════")
    print("Summary:")
    print("═══════════════════════════════════════════════════")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for service, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {service}")
    
    print()
    print(f"Configured: {success_count}/{total_count} services")
    
    if success_count < total_count:
        print()
        print("To configure missing services:")
        print("1. Add credentials in Secrets Manager at http://localhost:5000")
        print("2. Run this script again")

if __name__ == '__main__':
    main()