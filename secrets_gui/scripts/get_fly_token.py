#!/usr/bin/env python3
"""
Fly.io Token Retrieval Script
Retrieves Fly.io API token from the Secrets Manager for use with flyctl
"""

import os
import sys
import json
import getpass
import subprocess
from pathlib import Path
import configparser

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app import EncryptedEnvFile
except ImportError:
    print("Warning: Could not import EncryptedEnvFile, using environment variables only", file=sys.stderr)
    EncryptedEnvFile = None

def get_token_from_env():
    """Get token from environment variable"""
    return os.environ.get('FLY_API_TOKEN')

def get_token_from_encrypted_file(password=None):
    """Get token from encrypted file"""
    if not EncryptedEnvFile:
        return None
    
    env_file_path = Path('.env.flyio')
    if not Path(f'{env_file_path}.encrypted').exists():
        env_file_path = Path(__file__).parent.parent / '.env.flyio'
        if not Path(f'{env_file_path}.encrypted').exists():
            return None
    
    try:
        if not password:
            password = getpass.getpass('Enter encryption password: ')
        
        env_file = EncryptedEnvFile(str(env_file_path))
        # Decrypt and load
        secrets = env_file.decrypt_env(password.encode())
        return secrets.get('FLY_API_TOKEN')
    except Exception as e:
        print(f"Error decrypting file: {e}", file=sys.stderr)
        return None

def get_current_fly_token():
    """Get current token from flyctl config"""
    fly_config = Path.home() / '.fly' / 'config.yml'
    
    if fly_config.exists():
        try:
            import yaml
            with open(fly_config, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('access_token')
        except ImportError:
            # Fallback to simple parsing if yaml not available
            with open(fly_config, 'r') as f:
                for line in f:
                    if 'access_token:' in line:
                        return line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"Error reading fly config: {e}", file=sys.stderr)
    
    return None

def setup_flyctl(token):
    """Configure flyctl with the token"""
    try:
        # Check if flyctl is installed
        fly_cmd = 'fly'
        result = subprocess.run(['which', 'fly'], capture_output=True, text=True)
        if result.returncode != 0:
            fly_cmd = 'flyctl'
            result = subprocess.run(['which', 'flyctl'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error: Fly.io CLI (flyctl) is not installed", file=sys.stderr)
                print("Install from: https://fly.io/docs/hands-on/install-flyctl/", file=sys.stderr)
                return False
        
        # Create config directory
        fly_config_dir = Path.home() / '.fly'
        fly_config_dir.mkdir(exist_ok=True)
        
        # Write config file
        config_file = fly_config_dir / 'config.yml'
        with open(config_file, 'w') as f:
            f.write(f'access_token: {token}\n')
        
        # Set proper permissions
        os.chmod(config_file, 0o600)
        
        # Verify authentication
        result = subprocess.run([fly_cmd, 'auth', 'whoami'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully authenticated Fly.io CLI!")
            print(f"\nAuthenticated as: {result.stdout.strip()}")
            
            # Show apps
            result = subprocess.run([fly_cmd, 'apps', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("\nYour Fly.io apps:")
                print(result.stdout)
            
            return True
        else:
            print(f"Error verifying authentication: {result.stderr}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Error setting up flyctl: {e}", file=sys.stderr)
        return False

def get_org_from_env():
    """Get organization from environment or encrypted file"""
    org = os.environ.get('FLY_ORG')
    if org:
        return org
    
    # Try to get from current flyctl config
    try:
        result = subprocess.run(['fly', 'orgs', 'list', '--json'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            orgs = json.loads(result.stdout)
            if orgs and len(orgs) > 0:
                return orgs[0].get('slug')
    except:
        pass
    
    return None

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fly.io Token Management')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup flyctl with token')
    parser.add_argument('--show', action='store_true',
                       help='Display the token (careful!)')
    parser.add_argument('--export', action='store_true',
                       help='Export as environment variable command')
    parser.add_argument('--current', action='store_true',
                       help='Show current flyctl token')
    parser.add_argument('--org', action='store_true',
                       help='Show organization')
    parser.add_argument('--password', help='Encryption password (optional)')
    
    args = parser.parse_args()
    
    if args.current:
        # Show current token from flyctl config
        token = get_current_fly_token()
        if token:
            print(token)
        else:
            print("No token found in flyctl config", file=sys.stderr)
            sys.exit(1)
        return
    
    if args.org:
        # Show organization
        org = get_org_from_env()
        if org:
            print(org)
        else:
            print("No organization found", file=sys.stderr)
            sys.exit(1)
        return
    
    # Try to get token from various sources
    token = get_token_from_env()
    
    if not token:
        print("Attempting to retrieve Fly.io token...", file=sys.stderr)
        token = get_token_from_encrypted_file(args.password)
    
    if not token:
        # Try current flyctl config as last resort
        token = get_current_fly_token()
        if token:
            print("Using token from existing flyctl config", file=sys.stderr)
    
    if not token:
        print("Error: Could not retrieve Fly.io token", file=sys.stderr)
        print("\nPlease either:", file=sys.stderr)
        print("1. Set FLY_API_TOKEN environment variable", file=sys.stderr)
        print("2. Configure token in Secrets Manager at http://localhost:5000", file=sys.stderr)
        print("3. Get token from: fly auth token (if logged in)", file=sys.stderr)
        print("4. Visit: https://fly.io/user/personal_access_tokens", file=sys.stderr)
        sys.exit(1)
    
    if args.setup:
        # Setup flyctl
        if setup_flyctl(token):
            print("\nFly.io CLI is ready to use!")
            print("\nExample commands:")
            print("  fly apps list         # List your applications")
            print("  fly status           # Show app status")
            print("  fly deploy           # Deploy an application")
            print("  fly logs             # View application logs")
            print("  fly launch           # Launch a new app")
        else:
            sys.exit(1)
    elif args.show:
        # Display token (with warning)
        print("WARNING: Displaying sensitive token!", file=sys.stderr)
        print(token)
    elif args.export:
        # Print export commands
        print(f"export FLY_API_TOKEN='{token}'")
        org = get_org_from_env()
        if org:
            print(f"export FLY_ORG='{org}'")
        print("# Run: eval $(python3 get_fly_token.py --export)")
    else:
        # Default: just output the token for piping
        print(token)

if __name__ == '__main__':
    main()