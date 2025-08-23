#!/usr/bin/env python3
"""
Multi-Service Secrets Manager Extension
Easily manage secrets for multiple services beyond Onomondo
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Import the base secrets manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from secrets_manager import EncryptedEnvFile, EnvironmentSecrets

class MultiServiceSecretsManager:
    """Manage secrets for multiple services"""
    
    # Define service configurations
    SERVICES = {
        'onomondo': {
            'name': 'Onomondo SoftSIM',
            'file': '.env.onomondo',
            'keys': [
                ('ONOMONDO_API_KEY', True, 'API Key'),
                ('ONOMONDO_IMSI', False, 'IMSI'),
                ('ONOMONDO_ICCID', False, 'ICCID'),
                ('ONOMONDO_KI', True, 'KI Key'),
                ('ONOMONDO_OPC', True, 'OPC Key'),
                ('SOFTSIM_PROFILE_ID', False, 'Profile ID'),
            ]
        },
        'aws': {
            'name': 'Amazon Web Services',
            'file': '.env.aws',
            'keys': [
                ('AWS_ACCESS_KEY_ID', False, 'Access Key ID'),
                ('AWS_SECRET_ACCESS_KEY', True, 'Secret Access Key'),
                ('AWS_REGION', False, 'Region (e.g., us-east-1)'),
                ('AWS_SESSION_TOKEN', True, 'Session Token (optional)'),
            ]
        },
        'azure': {
            'name': 'Microsoft Azure',
            'file': '.env.azure',
            'keys': [
                ('AZURE_CLIENT_ID', False, 'Client ID'),
                ('AZURE_CLIENT_SECRET', True, 'Client Secret'),
                ('AZURE_TENANT_ID', False, 'Tenant ID'),
                ('AZURE_SUBSCRIPTION_ID', False, 'Subscription ID'),
            ]
        },
        'gcp': {
            'name': 'Google Cloud Platform',
            'file': '.env.gcp',
            'keys': [
                ('GCP_PROJECT_ID', False, 'Project ID'),
                ('GCP_CLIENT_EMAIL', False, 'Service Account Email'),
                ('GCP_PRIVATE_KEY', True, 'Private Key'),
                ('GCP_API_KEY', True, 'API Key (optional)'),
            ]
        },
        'database': {
            'name': 'Database',
            'file': '.env.database',
            'keys': [
                ('DB_HOST', False, 'Host'),
                ('DB_PORT', False, 'Port'),
                ('DB_NAME', False, 'Database Name'),
                ('DB_USER', False, 'Username'),
                ('DB_PASSWORD', True, 'Password'),
                ('DB_SSL_MODE', False, 'SSL Mode (optional)'),
            ]
        },
        'redis': {
            'name': 'Redis',
            'file': '.env.redis',
            'keys': [
                ('REDIS_HOST', False, 'Host'),
                ('REDIS_PORT', False, 'Port (default: 6379)'),
                ('REDIS_PASSWORD', True, 'Password (optional)'),
                ('REDIS_DB', False, 'Database Number (default: 0)'),
            ]
        },
        'stripe': {
            'name': 'Stripe',
            'file': '.env.stripe',
            'keys': [
                ('STRIPE_PUBLISHABLE_KEY', False, 'Publishable Key'),
                ('STRIPE_SECRET_KEY', True, 'Secret Key'),
                ('STRIPE_WEBHOOK_SECRET', True, 'Webhook Secret'),
            ]
        },
        'openai': {
            'name': 'OpenAI',
            'file': '.env.openai',
            'keys': [
                ('OPENAI_API_KEY', True, 'API Key'),
                ('OPENAI_ORGANIZATION', False, 'Organization ID (optional)'),
                ('OPENAI_API_BASE', False, 'API Base URL (optional)'),
            ]
        },
        'twilio': {
            'name': 'Twilio',
            'file': '.env.twilio',
            'keys': [
                ('TWILIO_ACCOUNT_SID', False, 'Account SID'),
                ('TWILIO_AUTH_TOKEN', True, 'Auth Token'),
                ('TWILIO_PHONE_NUMBER', False, 'Phone Number'),
            ]
        },
        'sendgrid': {
            'name': 'SendGrid',
            'file': '.env.sendgrid',
            'keys': [
                ('SENDGRID_API_KEY', True, 'API Key'),
                ('SENDGRID_FROM_EMAIL', False, 'From Email'),
                ('SENDGRID_FROM_NAME', False, 'From Name'),
            ]
        },
        'docker': {
            'name': 'Docker Registry',
            'file': '.env.docker',
            'keys': [
                ('DOCKER_REGISTRY', False, 'Registry URL'),
                ('DOCKER_USERNAME', False, 'Username'),
                ('DOCKER_PASSWORD', True, 'Password'),
            ]
        },
        'kubernetes': {
            'name': 'Kubernetes',
            'file': '.env.k8s',
            'keys': [
                ('KUBECONFIG', False, 'Config Path'),
                ('K8S_CLUSTER', False, 'Cluster Name'),
                ('K8S_NAMESPACE', False, 'Namespace'),
                ('K8S_TOKEN', True, 'Service Account Token'),
            ]
        },
        'custom': {
            'name': 'Custom Service',
            'file': '.env.custom',
            'keys': []  # Will be populated dynamically
        }
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'thingy91' / 'services'
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_service(self, service_name: str, custom_keys: Optional[List[tuple]] = None):
        """Interactive setup for a specific service"""
        
        if service_name not in self.SERVICES and service_name != 'custom':
            print(f"Unknown service: {service_name}")
            print(f"Available services: {', '.join(self.SERVICES.keys())}")
            return False
        
        service = self.SERVICES[service_name]
        
        if service_name == 'custom' and custom_keys:
            service['keys'] = custom_keys
        
        print(f"\n=== {service['name']} Setup ===")
        print(f"Configuring secrets for {service['name']}")
        print("Press Enter to skip optional values\n")
        
        secrets = {}
        
        for key_info in service['keys']:
            if len(key_info) == 3:
                key, is_secret, description = key_info
            else:
                key, is_secret = key_info
                description = key
            
            prompt = f"{description or key}: "
            
            if is_secret:
                from getpass import getpass
                value = getpass(prompt)
            else:
                value = input(prompt)
            
            if value:
                secrets[key] = value
            elif 'optional' not in description.lower():
                print(f"Warning: {key} is recommended")
        
        if secrets:
            # Save to encrypted file
            env_file = EncryptedEnvFile(f"{service['file']}.encrypted")
            env_file.encrypt_env(secrets)
            print(f"\n✓ {service['name']} secrets saved to {service['file']}.encrypted")
            return True
        else:
            print("No secrets provided")
            return False
    
    def load_service(self, service_name: str) -> bool:
        """Load secrets for a specific service"""
        
        if service_name not in self.SERVICES:
            print(f"Unknown service: {service_name}")
            return False
        
        service = self.SERVICES[service_name]
        env_file = EncryptedEnvFile(f"{service['file']}.encrypted")
        
        if not Path(f"{service['file']}.encrypted").exists():
            print(f"No secrets found for {service['name']}")
            print(f"Run: {sys.argv[0]} setup {service_name}")
            return False
        
        if env_file.load_to_environment():
            print(f"✓ {service['name']} secrets loaded to environment")
            return True
        
        return False
    
    def list_services(self):
        """List all available services and their status"""
        
        print("\n=== Available Services ===\n")
        
        for service_name, service in self.SERVICES.items():
            if service_name == 'custom':
                continue
            
            encrypted_file = f"{service['file']}.encrypted"
            if Path(encrypted_file).exists():
                status = "✓ Configured"
            else:
                status = "✗ Not configured"
            
            print(f"{service_name:15} - {service['name']:25} {status}")
        
        print("\nUsage:")
        print(f"  Setup:  {sys.argv[0]} setup <service>")
        print(f"  Load:   {sys.argv[0]} load <service>")
        print(f"  All:    {sys.argv[0]} load-all")
    
    def load_all(self) -> bool:
        """Load all configured services"""
        
        loaded = []
        failed = []
        
        for service_name, service in self.SERVICES.items():
            if service_name == 'custom':
                continue
            
            encrypted_file = f"{service['file']}.encrypted"
            if Path(encrypted_file).exists():
                env_file = EncryptedEnvFile(encrypted_file)
                try:
                    env_dict = env_file.decrypt_env()
                    if env_dict:
                        for k, v in env_dict.items():
                            os.environ[k] = v
                        loaded.append(service['name'])
                except Exception as e:
                    failed.append((service['name'], str(e)))
        
        if loaded:
            print(f"\n✓ Loaded {len(loaded)} service(s):")
            for name in loaded:
                print(f"  - {name}")
        
        if failed:
            print(f"\n✗ Failed to load {len(failed)} service(s):")
            for name, error in failed:
                print(f"  - {name}: {error}")
        
        return len(failed) == 0
    
    def add_custom_service(self):
        """Add a custom service interactively"""
        
        print("\n=== Add Custom Service ===")
        
        service_name = input("Service name (lowercase, no spaces): ").lower().replace(' ', '_')
        display_name = input("Display name: ")
        
        keys = []
        print("\nAdd secret keys (empty key name to finish):")
        
        while True:
            key = input("\nEnvironment variable name (e.g., MY_API_KEY): ").upper()
            if not key:
                break
            
            description = input(f"Description for {key}: ") or key
            is_secret = input("Is this sensitive? (y/N): ").lower() == 'y'
            
            keys.append((key, is_secret, description))
        
        if keys:
            # Save custom service definition
            custom_config = {
                'name': display_name,
                'file': f'.env.{service_name}',
                'keys': keys
            }
            
            config_file = self.config_dir / f'{service_name}.json'
            with open(config_file, 'w') as f:
                json.dump(custom_config, f, indent=2)
            
            print(f"\n✓ Custom service '{service_name}' added")
            print(f"Now run: {sys.argv[0]} setup {service_name}")
            
            # Add to SERVICES for this session
            self.SERVICES[service_name] = custom_config
            return True
        
        return False
    
    def load_custom_services(self):
        """Load all custom service definitions"""
        
        for config_file in self.config_dir.glob('*.json'):
            service_name = config_file.stem
            
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                # Convert keys to tuples
                config['keys'] = [tuple(k) for k in config['keys']]
                self.SERVICES[service_name] = config
            except Exception as e:
                print(f"Warning: Failed to load {service_name}: {e}")
    
    def export_service(self, service_name: str, format: str = 'env'):
        """Export service secrets in various formats"""
        
        if service_name not in self.SERVICES:
            print(f"Unknown service: {service_name}")
            return
        
        service = self.SERVICES[service_name]
        env_file = EncryptedEnvFile(f"{service['file']}.encrypted")
        
        try:
            secrets = env_file.decrypt_env()
            if not secrets:
                print(f"No secrets found for {service['name']}")
                return
        except Exception as e:
            print(f"Failed to decrypt: {e}")
            return
        
        if format == 'env':
            # Export as .env format
            output = f"# {service['name']} Secrets\n"
            for key, value in secrets.items():
                output += f"{key}={value}\n"
            
            filename = f"{service['file']}.env"
            
        elif format == 'json':
            # Export as JSON
            output = json.dumps(secrets, indent=2)
            filename = f"{service['file']}.json"
            
        elif format == 'docker':
            # Export as docker-compose env
            output = f"# {service['name']} Docker Environment\n"
            for key, value in secrets.items():
                output += f"      - {key}={value}\n"
            
            filename = f"{service['file']}.docker.yml"
            
        elif format == 'k8s':
            # Export as Kubernetes secret
            import base64
            k8s_secret = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'metadata': {
                    'name': f"{service_name}-secrets"
                },
                'type': 'Opaque',
                'data': {
                    key: base64.b64encode(value.encode()).decode()
                    for key, value in secrets.items()
                }
            }
            output = json.dumps(k8s_secret, indent=2)
            filename = f"{service['file']}.k8s.yaml"
        
        else:
            print(f"Unknown format: {format}")
            return
        
        with open(filename, 'w') as f:
            f.write(output)
        
        os.chmod(filename, 0o600)
        print(f"✓ Exported to {filename}")
        print("⚠️  Remember to delete this file after use!")


def main():
    """CLI for multi-service secrets management"""
    
    parser = argparse.ArgumentParser(
        description="Multi-Service Secrets Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all services
  %(prog)s setup aws               # Setup AWS credentials
  %(prog)s load aws                # Load AWS credentials
  %(prog)s load-all                # Load all configured services
  %(prog)s add-custom              # Add a custom service
  %(prog)s export aws --format env # Export as .env file
        """
    )
    
    parser.add_argument('command', choices=[
        'list', 'setup', 'load', 'load-all', 'add-custom', 'export'
    ], help='Command to execute')
    
    parser.add_argument('service', nargs='?', help='Service name')
    parser.add_argument('--format', default='env',
                       choices=['env', 'json', 'docker', 'k8s'],
                       help='Export format')
    
    args = parser.parse_args()
    
    manager = MultiServiceSecretsManager()
    manager.load_custom_services()
    
    if args.command == 'list':
        manager.list_services()
    
    elif args.command == 'setup':
        if not args.service:
            print("Please specify a service")
            manager.list_services()
        else:
            manager.setup_service(args.service)
    
    elif args.command == 'load':
        if not args.service:
            print("Please specify a service")
            manager.list_services()
        else:
            manager.load_service(args.service)
    
    elif args.command == 'load-all':
        manager.load_all()
    
    elif args.command == 'add-custom':
        manager.add_custom_service()
    
    elif args.command == 'export':
        if not args.service:
            print("Please specify a service")
        else:
            manager.export_service(args.service, args.format)


if __name__ == "__main__":
    main()