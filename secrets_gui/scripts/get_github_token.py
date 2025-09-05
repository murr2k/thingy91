#!/usr/bin/env python3
"""
GitHub Token Retrieval Script
Retrieves GitHub token from the Secrets Manager for use with gh CLI
"""

import os
import sys
import json
import getpass
from pathlib import Path
import subprocess

# Add parent directory to path to import the encryption module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app import EncryptedEnvFile
except ImportError:
    # Simplified version if app.py is not available
    print("Warning: Could not import EncryptedEnvFile, using environment variables only", file=sys.stderr)
    EncryptedEnvFile = None

def get_token_from_env():
    """Get token from environment variable"""
    return os.environ.get('GITHUB_TOKEN')

def get_token_from_encrypted_file():
    """Get token from encrypted file"""
    if not EncryptedEnvFile:
        return None
    
    env_file_path = Path('.env.github')
    if not Path(f'{env_file_path}.encrypted').exists():
        env_file_path = Path(__file__).parent.parent / '.env.github'
        if not Path(f'{env_file_path}.encrypted').exists():
            return None
    
    try:
        password = getpass.getpass('Enter encryption password: ')
        env_file = EncryptedEnvFile(str(env_file_path))
        
        # Try to decrypt and load
        # This is a simplified approach - in production, use proper decryption
        secrets = env_file.decrypt_env(password.encode())
        return secrets.get('GITHUB_TOKEN')
    except Exception as e:
        print(f"Error decrypting file: {e}", file=sys.stderr)
        return None

def get_token_from_api():
    """Get token from Secrets Manager API"""
    api_url = os.environ.get('SECRETS_API_URL', 'http://localhost:5000')
    api_key = os.environ.get('SECRETS_API_KEY')
    
    if not api_key:
        # Try to get from cookie/session if running locally
        try:
            import requests
            # This would need proper session handling
            return None
        except ImportError:
            return None
    
    return None

def setup_gh_cli(token):
    """Configure gh CLI with the token"""
    try:
        # Check if gh is installed
        result = subprocess.run(['which', 'gh'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: GitHub CLI (gh) is not installed", file=sys.stderr)
            print("Install from: https://cli.github.com/", file=sys.stderr)
            return False
        
        # Authenticate gh with token
        process = subprocess.Popen(
            ['gh', 'auth', 'login', '--with-token'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=token)
        
        if process.returncode == 0:
            print("✓ Successfully authenticated GitHub CLI!")
            
            # Show status
            subprocess.run(['gh', 'auth', 'status'])
            return True
        else:
            print(f"Error authenticating: {stderr}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Error setting up gh CLI: {e}", file=sys.stderr)
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Token Management')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup gh CLI with token')
    parser.add_argument('--show', action='store_true',
                       help='Display the token (careful!)')
    parser.add_argument('--export', action='store_true',
                       help='Export as environment variable command')
    
    args = parser.parse_args()
    
    # Try to get token from various sources
    token = get_token_from_env()
    
    if not token:
        print("Attempting to retrieve GitHub token...", file=sys.stderr)
        token = get_token_from_encrypted_file()
    
    if not token:
        token = get_token_from_api()
    
    if not token:
        print("Error: Could not retrieve GitHub token", file=sys.stderr)
        print("\nPlease either:", file=sys.stderr)
        print("1. Set GITHUB_TOKEN environment variable", file=sys.stderr)
        print("2. Configure token in Secrets Manager at http://localhost:5000", file=sys.stderr)
        print("3. Run with encrypted file in current directory", file=sys.stderr)
        sys.exit(1)
    
    if args.setup:
        # Setup gh CLI
        if setup_gh_cli(token):
            print("\nGitHub CLI is ready to use!")
            print("\nExample commands:")
            print("  gh repo list         # List your repositories")
            print("  gh pr list          # List pull requests")
            print("  gh issue list       # List issues")
            print("  gh repo create      # Create a new repository")
        else:
            sys.exit(1)
    elif args.show:
        # Display token (with warning)
        print("WARNING: Displaying sensitive token!", file=sys.stderr)
        print(token)
    elif args.export:
        # Print export command
        print(f"export GITHUB_TOKEN='{token}'")
        print("# Run: eval $(python3 get_github_token.py --export)")
    else:
        # Default: just output the token for piping
        print(token)

if __name__ == '__main__':
    main()