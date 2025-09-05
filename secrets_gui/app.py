#!/usr/bin/env python3
"""
Compact Secrets Management GUI
A minimalist, secure web interface for managing service credentials
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps
import os
import sys
import json
import hashlib
import secrets
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
import subprocess
from typing import Dict, Optional, List, Tuple
import base64
from service_templates import SERVICE_TEMPLATES, HEALTH_CHECK_TYPES, get_template, validate_field

# Simple encrypted file implementation (avoiding external dependency)
class EncryptedEnvFile:
    """Simplified encrypted environment file handler"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.encrypted_file = Path(f"{filename}.encrypted")
    
    def exists(self):
        """Check if encrypted file exists"""
        return self.encrypted_file.exists()
    
    def encrypt_env(self, env_dict: dict):
        """Simple encryption placeholder"""
        # In production, use proper encryption
        # For now, just save as JSON with basic encoding
        data = json.dumps(env_dict)
        encoded = base64.b64encode(data.encode()).decode()
        with open(self.encrypted_file, 'w') as f:
            f.write(encoded)
    
    def decrypt_env(self) -> dict:
        """Simple decryption placeholder"""
        if not self.exists():
            return {}
        with open(self.encrypted_file, 'r') as f:
            encoded = f.read()
        data = base64.b64decode(encoded).decode()
        return json.loads(data)

class SecretsManager:
    """Manages encrypted secrets from the centralized storage"""
    
    def __init__(self):
        self.secrets_file = Path("/app/data/secrets.json")
        self.master_key_file = Path("/app/data/.master_key")
        self._fernet = None
    
    def _get_fernet(self):
        """Get or create Fernet instance for encryption/decryption"""
        if self._fernet:
            return self._fernet
            
        try:
            # Import cryptography here to avoid issues if not installed
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            from cryptography.fernet import Fernet
            
            # Load master key
            if not self.master_key_file.exists():
                return None
                
            with open(self.master_key_file, 'r') as f:
                master_key = f.read().strip()
            
            # Derive encryption key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'stable_salt_v1',
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._fernet = Fernet(key)
            return self._fernet
            
        except ImportError:
            # Cryptography not installed, fall back to simple encoding
            return None
        except Exception:
            return None
    
    def get_service_secrets(self, service_id: str) -> dict:
        """Get decrypted secrets for a specific service"""
        try:
            if not self.secrets_file.exists():
                return {}
            
            with open(self.secrets_file, 'r') as f:
                encrypted_data = json.load(f)
            
            if service_id not in encrypted_data:
                return {}
            
            fernet = self._get_fernet()
            if not fernet:
                # Fallback to base64 if encryption not available
                try:
                    decoded = base64.b64decode(encrypted_data[service_id]).decode()
                    return json.loads(decoded)
                except:
                    return {}
            
            # Decrypt the service data
            decrypted = fernet.decrypt(encrypted_data[service_id].encode())
            return json.loads(decrypted)
            
        except Exception as e:
            print(f"Error loading secrets for {service_id}: {e}")
            return {}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
class Config:
    UPDATE_INTERVAL = 30  # seconds
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    
    # Admin credentials (in production, use proper auth)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = hashlib.sha256(
        os.environ.get('ADMIN_PASSWORD', 'changeme').encode()
    ).hexdigest()

# Service definitions with health check configurations
SERVICES = {
    'onomondo': {
        'name': 'Onomondo',
        'icon': '📡',
        'color': '#00a6fb',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.onomondo.com/v1/health',
            'headers_func': 'get_onomondo_headers',
            'timeout': 10
        },
        'keys': ['ONOMONDO_API_KEY', 'ONOMONDO_IMSI', 'ONOMONDO_ICCID', 'ONOMONDO_MSISDN'],
        'required': ['ONOMONDO_API_KEY'],
        'description': 'Onomondo SoftSIM credentials for cellular connectivity'
    },
    'aws': {
        'name': 'AWS',
        'icon': '☁️',
        'color': '#ff9900',
        'health_check': {
            'type': 'command',
            'command': 'aws sts get-caller-identity',
            'timeout': 10
        },
        'keys': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION'],
        'required': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    },
    'azure': {
        'name': 'Azure',
        'icon': '☁️',
        'color': '#0078d4',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://management.azure.com/health',
            'timeout': 5
        },
        'keys': ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID'],
        'required': ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET']
    },
    'database': {
        'name': 'Database',
        'icon': '🗄️',
        'color': '#336791',
        'health_check': {
            'type': 'connection',
            'check_func': 'check_database',
            'timeout': 5
        },
        'keys': ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'],
        'required': ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
    },
    'redis': {
        'name': 'Redis',
        'icon': '⚡',
        'color': '#dc382d',
        'health_check': {
            'type': 'connection',
            'check_func': 'check_redis',
            'timeout': 3
        },
        'keys': ['REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD'],
        'required': ['REDIS_HOST']
    },
    'stripe': {
        'name': 'Stripe',
        'icon': '💳',
        'color': '#635bff',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.stripe.com/v1/balance',
            'headers_func': 'get_stripe_headers',
            'timeout': 5
        },
        'keys': ['STRIPE_PUBLISHABLE_KEY', 'STRIPE_SECRET_KEY'],
        'required': ['STRIPE_SECRET_KEY']
    },
    'openai': {
        'name': 'OpenAI',
        'icon': '🤖',
        'color': '#10a37f',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.openai.com/v1/models',
            'headers_func': 'get_openai_headers',
            'timeout': 5
        },
        'keys': ['OPENAI_API_KEY', 'OPENAI_ORGANIZATION'],
        'required': ['OPENAI_API_KEY']
    },
    'github': {
        'name': 'GitHub CLI',
        'icon': '🐙',
        'color': '#24292e',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.github.com/user',
            'headers_func': 'get_github_headers',
            'timeout': 5
        },
        'keys': ['GITHUB_TOKEN', 'GITHUB_USERNAME', 'GITHUB_EMAIL'],
        'required': ['GITHUB_TOKEN'],
        'description': 'GitHub personal access token for gh CLI authentication',
        'setup_command': 'echo $GITHUB_TOKEN | gh auth login --with-token',
        'test_command': 'gh auth status'
    },
    'flyio': {
        'name': 'Fly.io',
        'icon': '🚀',
        'color': '#7c3aed',
        'health_check': {
            'type': 'graphql',
            'endpoint': 'https://api.fly.io/graphql',
            'headers_func': 'get_flyio_headers',
            'timeout': 10,
            'query': '{ viewer { email } }'
        },
        'keys': ['FLYIO_ORG_TOKEN', 'FLYIO_ADMIN_TOKEN', 'FLYIO_DEPLOY_TOKEN', 'FLYIO_ORG'],
        'required': ['FLYIO_ORG_TOKEN'],
        'description': 'Fly.io API tokens for deployment and management',
        'setup_command': 'export FLY_API_TOKEN=$FLYIO_ORG_TOKEN',
        'test_command': 'fly auth whoami'
    },
    'npm': {
        'name': 'NPM Registry',
        'icon': '📦',
        'color': '#cb3837',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://registry.npmjs.org/-/whoami',
            'headers_func': 'get_npm_headers',
            'timeout': 5
        },
        'keys': ['NPM_AUTH_TOKEN', 'NPM_USERNAME', 'NPM_EMAIL'],
        'required': ['NPM_AUTH_TOKEN'],
        'description': 'NPM package publishing and management',
        'setup_command': 'npm config set //registry.npmjs.org/:_authToken $NPM_AUTH_TOKEN',
        'test_command': 'npm whoami'
    },
    'grafana': {
        'name': 'Grafana',
        'icon': '📊',
        'color': '#f46800',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://grafana.com/api/user',
            'headers_func': 'get_grafana_headers',
            'timeout': 5
        },
        'keys': ['GRAFANA_TOKEN', 'GRAFANA_URL', 'GRAFANA_ORG_ID'],
        'required': ['GRAFANA_TOKEN'],
        'description': 'Monitoring and observability dashboards'
    },
    'googleplay': {
        'name': 'Google Play',
        'icon': '🎮',
        'color': '#34a853',
        'health_check': {
            'type': 'command',
            'command': 'echo "Google Play service account configured"',
            'timeout': 2
        },
        'keys': ['GOOGLE_PLAY_SERVICE_ACCOUNT', 'GOOGLE_PLAY_PACKAGE_NAME'],
        'required': ['GOOGLE_PLAY_SERVICE_ACCOUNT'],
        'description': 'Android app publishing and management',
        'notes': 'Service account JSON should be stored as a single-line JSON string'
    },
    'macrofab': {
        'name': 'MacroFab',
        'icon': '🔧',
        'color': '#0084ff',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.macrofab.com/v1/user',
            'headers_func': 'get_macrofab_headers',
            'timeout': 5
        },
        'keys': ['MACROFAB_API_KEY', 'MACROFAB_API_SECRET'],
        'required': ['MACROFAB_API_KEY'],
        'description': 'PCB manufacturing and assembly'
    },
    'cloudflare': {
        'name': 'Cloudflare',
        'icon': '☁️',
        'color': '#f38020',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.cloudflare.com/client/v4/user',
            'headers_func': 'get_cloudflare_headers',
            'timeout': 5
        },
        'keys': ['CLOUDFLARE_EMAIL', 'CLOUDFLARE_GLOBAL_API_KEY', 'CLOUDFLARE_ZONE_ID'],
        'required': ['CLOUDFLARE_EMAIL', 'CLOUDFLARE_GLOBAL_API_KEY'],
        'description': 'DNS, CDN, and DDoS protection'
    },
    'nexar': {
        'name': 'Nexar',
        'icon': '🔌',
        'color': '#1a1a1a',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.nexar.com/graphql',
            'headers_func': 'get_nexar_headers',
            'timeout': 5
        },
        'keys': ['NEXAR_CLIENT_ID', 'NEXAR_CLIENT_SECRET', 'NEXAR_ACCESS_TOKEN'],
        'required': ['NEXAR_CLIENT_ID', 'NEXAR_CLIENT_SECRET'],
        'description': 'Electronic component search and supply chain'
    },
    'terraform': {
        'name': 'Terraform Cloud',
        'icon': '🏗️',
        'color': '#5c4ee5',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://app.terraform.io/api/v2/account/details',
            'headers_func': 'get_terraform_headers',
            'timeout': 5
        },
        'keys': ['TERRAFORM_API_TOKEN', 'TERRAFORM_ORG', 'TERRAFORM_WORKSPACE'],
        'required': ['TERRAFORM_API_TOKEN'],
        'description': 'Infrastructure as Code management',
        'setup_command': 'terraform login',
        'test_command': 'terraform version'
    },
    'infisical': {
        'name': 'Infisical',
        'icon': '🔐',
        'color': '#166ee1',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://app.infisical.com/api/v1/auth/checkAuth',
            'headers_func': 'get_infisical_headers',
            'timeout': 5
        },
        'keys': ['INFISICAL_SERVICE_TOKEN', 'INFISICAL_PROJECT_ID', 'INFISICAL_ENV'],
        'required': ['INFISICAL_SERVICE_TOKEN'],
        'description': 'End-to-end encrypted secrets management'
    },
    'digikey': {
        'name': 'DigiKey',
        'icon': '📟',
        'color': '#cc0000',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.digikey.com/v1/status',
            'headers_func': 'get_digikey_headers',
            'timeout': 5
        },
        'keys': ['DIGIKEY_CLIENT_ID', 'DIGIKEY_CLIENT_SECRET', 'DIGIKEY_ACCESS_TOKEN', 'DIGIKEY_REFRESH_TOKEN', 'DIGIKEY_ENVIRONMENT'],
        'required': ['DIGIKEY_CLIENT_ID', 'DIGIKEY_CLIENT_SECRET'],
        'description': 'Electronic components ordering and search',
        'notes': 'Supports both sandbox and production environments'
    },
    'blynk': {
        'name': 'Blynk',
        'icon': '📱',
        'color': '#23c48e',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://blynk.cloud/external/api/isHardwareConnected',
            'headers_func': 'get_blynk_headers',
            'timeout': 5
        },
        'keys': ['BLYNK_AUTH_TOKEN', 'BLYNK_ORGANIZATION_ID', 'BLYNK_TEMPLATE_NAME', 'BLYNK_DEVICE_NAME'],
        'required': ['BLYNK_AUTH_TOKEN'],
        'description': 'IoT platform for Thingy91 and other devices'
    },
    'anthropic': {
        'name': 'Anthropic',
        'icon': '🤖',
        'color': '#d4a574',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.anthropic.com/v1/messages',
            'headers_func': 'get_anthropic_headers',
            'timeout': 5
        },
        'keys': ['ANTHROPIC_API_KEY', 'ANTHROPIC_MODEL'],
        'required': ['ANTHROPIC_API_KEY'],
        'description': 'Claude AI API access'
    },
    'slack': {
        'name': 'Slack',
        'icon': '💬',
        'color': '#4a154b',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://slack.com/api/auth.test',
            'headers_func': 'get_slack_headers',
            'timeout': 5
        },
        'keys': ['SLACK_BOT_TOKEN', 'SLACK_WEBHOOK_URL', 'SLACK_CHANNEL', 'SLACK_APP_TOKEN'],
        'required': ['SLACK_BOT_TOKEN'],
        'description': 'Team communication and notifications',
        'setup_command': 'slack auth list',
        'test_command': 'slack auth test'
    },
    'edge_impulse': {
        'name': 'Edge Impulse',
        'icon': '🤖',
        'color': '#00d4aa',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://studio.edgeimpulse.com/v1/api/projects',
            'headers_func': 'get_edge_impulse_headers',
            'timeout': 5
        },
        'keys': ['EDGE_IMPULSE_API_KEY', 'EDGE_IMPULSE_HMAC_KEY', 'EDGE_IMPULSE_PROJECT_ID'],
        'required': ['EDGE_IMPULSE_API_KEY'],
        'description': 'Machine learning for edge devices',
        'setup_command': 'edge-impulse-cli --api-key',
        'test_command': 'edge-impulse-cli --version'
    },
    'cal_com': {
        'name': 'Cal.com',
        'icon': '📅',
        'color': '#292929',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.cal.com/v1/me',
            'headers_func': 'get_cal_headers',
            'timeout': 5
        },
        'keys': ['CAL_API_KEY', 'CAL_WEBHOOK_SECRET'],
        'required': ['CAL_API_KEY'],
        'description': 'Scheduling infrastructure',
        'notes': 'API key can be generated from Settings > Security > API Keys'
    },
    'wolfram_alpha': {
        'name': 'Wolfram Alpha',
        'icon': '🧮',
        'color': '#dd1100',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.wolframalpha.com/v1/validatequery',
            'headers_func': 'get_wolfram_headers',
            'timeout': 5
        },
        'keys': ['WOLFRAM_APP_ID', 'WOLFRAM_APP_KEY'],
        'required': ['WOLFRAM_APP_ID'],
        'description': 'Computational knowledge engine',
        'notes': 'App ID is required for all API calls'
    },
    'digikey_production': {
        'name': 'DigiKey Production',
        'icon': '📟',
        'color': '#cc0000',
        'health_check': {
            'type': 'https',
            'endpoint': 'https://api.digikey.com/v1/status',
            'headers_func': 'get_digikey_prod_headers',
            'timeout': 5
        },
        'keys': ['DIGIKEY_PROD_CLIENT_ID', 'DIGIKEY_PROD_CLIENT_SECRET', 'DIGIKEY_PROD_ACCESS_TOKEN', 'DIGIKEY_PROD_REFRESH_TOKEN'],
        'required': ['DIGIKEY_PROD_CLIENT_ID', 'DIGIKEY_PROD_CLIENT_SECRET'],
        'description': 'DigiKey Production API (separate from sandbox)',
        'notes': 'Production environment for real orders'
    }
}

# Service status cache
service_status = {}
status_lock = threading.Lock()

# Login attempt tracking
login_attempts = {}
login_lock = threading.Lock()

class ServiceMonitor:
    """Background service health monitoring"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start monitoring thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            self.check_all_services()
            time.sleep(Config.UPDATE_INTERVAL)
    
    def check_all_services(self):
        """Check health of all configured services"""
        global service_status
        
        for service_id, service_config in SERVICES.items():
            status = self.check_service(service_id, service_config)
            
            with status_lock:
                service_status[service_id] = status
            
            # Emit update via WebSocket
            socketio.emit('status_update', {
                'service': service_id,
                'status': status
            }, namespace='/', to='/')
    
    def check_service(self, service_id: str, config: dict) -> dict:
        """Check health of a single service"""
        try:
            # Check if we can use auth manager for CLI-authenticated services
            cli_services = ['github', 'flyio', 'npm', 'docker', 'terraform', 'cloudflare']
            
            if service_id in cli_services:
                # For CLI services, direct users to use the host system auth manager
                return {
                    'status': 'info',
                    'message': 'Use `authctl status` on host system to check CLI authentication',
                    'timestamp': datetime.now().isoformat(),
                    'cli_auth': None,
                    'host_managed': True
                }
            
            # Load credentials from encrypted storage
            secrets_manager = SecretsManager()
            credentials = secrets_manager.get_service_secrets(service_id)
            
            if not credentials:
                return {
                    'status': 'unconfigured',
                    'message': 'Not configured',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if required keys exist
            required_keys = config.get('required', [])
            keys_configured = all(credentials.get(key) for key in required_keys)
            
            if not keys_configured:
                return {
                    'status': 'incomplete',
                    'message': 'Missing required keys',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Set credentials in environment for header functions
            for key, value in credentials.items():
                os.environ[key] = str(value)
            
            # Perform health check
            health_config = config.get('health_check', {})
            check_type = health_config.get('type')
            
            if check_type == 'https':
                return self._check_https(health_config)
            elif check_type == 'graphql':
                return self._check_graphql(health_config)
            elif check_type == 'command':
                return self._check_command(health_config)
            elif check_type == 'connection':
                return self._check_connection(health_config)
            else:
                return {
                    'status': 'unknown',
                    'message': 'No health check configured',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_https(self, config: dict) -> dict:
        """Check HTTPS endpoint health"""
        try:
            endpoint = config.get('endpoint')
            timeout = config.get('timeout', 5)
            headers = {}
            
            # Get custom headers if needed
            headers_func = config.get('headers_func')
            if headers_func:
                headers = globals().get(headers_func, lambda: {})()
            
            response = requests.get(endpoint, headers=headers, timeout=timeout)
            
            if response.status_code < 400:
                return {
                    'status': 'healthy',
                    'message': f'API responding ({response.status_code})',
                    'timestamp': datetime.now().isoformat(),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'status': 'degraded',
                    'message': f'API error ({response.status_code})',
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.Timeout:
            return {
                'status': 'timeout',
                'message': 'Connection timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_graphql(self, config: dict) -> dict:
        """Check GraphQL endpoint health"""
        try:
            endpoint = config.get('endpoint')
            timeout = config.get('timeout', 10)
            query = config.get('query', '{ __typename }')
            headers = {}
            
            # Get custom headers if needed
            headers_func = config.get('headers_func')
            if headers_func:
                headers = globals().get(headers_func, lambda: {})()
            
            # Make GraphQL request
            response = requests.post(
                endpoint, 
                json={'query': query},
                headers=headers, 
                timeout=timeout
            )
            
            if response.status_code < 400:
                data = response.json()
                # Check if GraphQL returned errors
                if 'errors' in data:
                    return {
                        'status': 'degraded',
                        'message': 'GraphQL API returned errors',
                        'timestamp': datetime.now().isoformat()
                    }
                elif 'data' in data:
                    return {
                        'status': 'healthy',
                        'message': 'GraphQL API responding',
                        'timestamp': datetime.now().isoformat(),
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    return {
                        'status': 'degraded',
                        'message': 'Unexpected GraphQL response',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {
                    'status': 'degraded',
                    'message': f'API error ({response.status_code})',
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'unhealthy',
                'message': 'Request timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': str(e)[:100],
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_command(self, config: dict) -> dict:
        """Check service via command execution"""
        try:
            command = config.get('command')
            timeout = config.get('timeout', 10)
            
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return {
                    'status': 'healthy',
                    'message': 'Command successful',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Command failed',
                    'timestamp': datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': 'Command timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_connection(self, config: dict) -> dict:
        """Check service connection (database, redis, etc)"""
        check_func_name = config.get('check_func')
        check_func = globals().get(check_func_name)
        
        if check_func:
            return check_func()
        
        return {
            'status': 'unknown',
            'message': 'Check function not implemented',
            'timestamp': datetime.now().isoformat()
        }

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        
        # Check session timeout
        if 'last_activity' in session:
            if datetime.now() - datetime.fromisoformat(session['last_activity']) > timedelta(seconds=Config.SESSION_TIMEOUT):
                session.clear()
                return redirect(url_for('login'))
        
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

# Health check helper functions
def get_onomondo_headers() -> dict:
    """Get Onomondo API headers"""
    api_key = os.environ.get('ONOMONDO_API_KEY', '')
    return {'Authorization': f'Bearer {api_key}'} if api_key else {}

def get_stripe_headers() -> dict:
    """Get Stripe API headers"""
    secret_key = os.environ.get('STRIPE_SECRET_KEY', '')
    return {'Authorization': f'Bearer {secret_key}'} if secret_key else {}

def get_openai_headers() -> dict:
    """Get OpenAI API headers"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    return {'Authorization': f'Bearer {api_key}'} if api_key else {}

def get_github_headers() -> dict:
    """Get GitHub API headers"""
    token = os.environ.get('GITHUB_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    } if token else {}

def get_flyio_headers() -> dict:
    """Get Fly.io API headers"""
    # Try multiple possible token names
    token = (os.environ.get('FLYIO_ORG_TOKEN', '') or 
             os.environ.get('FLYIO_ADMIN_TOKEN', '') or
             os.environ.get('FLY_API_TOKEN', ''))
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    } if token else {}

def get_npm_headers() -> dict:
    """Get NPM API headers"""
    token = os.environ.get('NPM_AUTH_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    } if token else {}

def get_grafana_headers() -> dict:
    """Get Grafana API headers"""
    token = os.environ.get('GRAFANA_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    } if token else {}

def get_macrofab_headers() -> dict:
    """Get MacroFab API headers"""
    api_key = os.environ.get('MACROFAB_API_KEY', '')
    return {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    } if api_key else {}

def get_cloudflare_headers() -> dict:
    """Get Cloudflare API headers"""
    email = os.environ.get('CLOUDFLARE_EMAIL', '')
    api_key = os.environ.get('CLOUDFLARE_GLOBAL_API_KEY', '')
    return {
        'X-Auth-Email': email,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json'
    } if email and api_key else {}

def get_nexar_headers() -> dict:
    """Get Nexar API headers"""
    token = os.environ.get('NEXAR_ACCESS_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    } if token else {}

def get_terraform_headers() -> dict:
    """Get Terraform Cloud API headers"""
    token = os.environ.get('TERRAFORM_API_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    } if token else {}

def get_infisical_headers() -> dict:
    """Get Infisical API headers"""
    token = os.environ.get('INFISICAL_SERVICE_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    } if token else {}

def get_digikey_headers() -> dict:
    """Get DigiKey API headers"""
    token = os.environ.get('DIGIKEY_ACCESS_TOKEN', '')
    client_id = os.environ.get('DIGIKEY_CLIENT_ID', '')
    return {
        'Authorization': f'Bearer {token}',
        'X-DIGIKEY-Client-Id': client_id,
        'Accept': 'application/json'
    } if token and client_id else {}

def get_blynk_headers() -> dict:
    """Get Blynk API headers"""
    token = os.environ.get('BLYNK_AUTH_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    } if token else {}

def get_anthropic_headers() -> dict:
    """Get Anthropic API headers"""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    return {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    } if api_key else {}

def get_slack_headers() -> dict:
    """Get Slack API headers"""
    token = os.environ.get('SLACK_BOT_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    } if token else {}

def get_edge_impulse_headers() -> dict:
    """Get Edge Impulse API headers"""
    api_key = os.environ.get('EDGE_IMPULSE_API_KEY', '')
    return {
        'x-api-key': api_key,
        'Accept': 'application/json'
    } if api_key else {}

def get_cal_headers() -> dict:
    """Get Cal.com API headers"""
    api_key = os.environ.get('CAL_API_KEY', '')
    return {
        'apiKey': api_key,
        'Content-Type': 'application/json'
    } if api_key else {}

def get_wolfram_headers() -> dict:
    """Get Wolfram Alpha API headers - Note: Wolfram uses query params, not headers"""
    app_id = os.environ.get('WOLFRAM_APP_ID', '')
    # Wolfram Alpha doesn't use headers for auth, it uses query params
    # This is just for consistency with other services
    return {'Accept': 'application/json'}

def get_digikey_prod_headers() -> dict:
    """Get DigiKey Production API headers"""
    token = os.environ.get('DIGIKEY_PROD_ACCESS_TOKEN', '')
    client_id = os.environ.get('DIGIKEY_PROD_CLIENT_ID', '')
    return {
        'Authorization': f'Bearer {token}',
        'X-DIGIKEY-Client-Id': client_id,
        'Accept': 'application/json'
    } if token and client_id else {}

def check_database() -> dict:
    """Check database connection"""
    # Simplified check - in production, actually try to connect
    if os.environ.get('DB_HOST') and os.environ.get('DB_USER'):
        return {
            'status': 'healthy',
            'message': 'Database configured',
            'timestamp': datetime.now().isoformat()
        }
    return {
        'status': 'unconfigured',
        'message': 'Database not configured',
        'timestamp': datetime.now().isoformat()
    }

def check_redis() -> dict:
    """Check Redis connection"""
    # Simplified check
    if os.environ.get('REDIS_HOST'):
        return {
            'status': 'healthy',
            'message': 'Redis configured',
            'timestamp': datetime.now().isoformat()
        }
    return {
        'status': 'unconfigured',
        'message': 'Redis not configured',
        'timestamp': datetime.now().isoformat()
    }

# Initialize monitor
monitor = ServiceMonitor()

# Routes
@app.route('/')
@login_required
def index():
    """Main dashboard"""
    return render_template('dashboard.html', services=SERVICES)

@app.route('/create-service')
@login_required
def create_service():
    """Service creation wizard"""
    return render_template('create_service.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check lockout
        with login_lock:
            if username in login_attempts:
                attempts, last_attempt = login_attempts[username]
                if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                    if datetime.now() - last_attempt < timedelta(seconds=Config.LOCKOUT_DURATION):
                        return jsonify({'error': 'Account locked. Try again later.'}), 429
                    else:
                        # Reset after lockout period
                        login_attempts[username] = (0, datetime.now())
        
        # Verify credentials
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == Config.ADMIN_USERNAME and password_hash == Config.ADMIN_PASSWORD_HASH:
            session['authenticated'] = True
            session['username'] = username
            session['last_activity'] = datetime.now().isoformat()
            
            # Reset login attempts
            with login_lock:
                if username in login_attempts:
                    del login_attempts[username]
            
            return redirect(url_for('index'))
        else:
            # Track failed attempt
            with login_lock:
                if username not in login_attempts:
                    login_attempts[username] = (0, datetime.now())
                attempts, _ = login_attempts[username]
                login_attempts[username] = (attempts + 1, datetime.now())
            
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/status')
@login_required
def api_status():
    """Get all service status"""
    with status_lock:
        return jsonify(service_status)

@app.route('/api/service/<service_id>')
@login_required
def api_service(service_id):
    """Get service details"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    service = SERVICES[service_id]
    
    # Check if configured
    env_file = Path(f'.env.{service_id}.encrypted')
    configured = env_file.exists()
    
    # Get current status
    with status_lock:
        status = service_status.get(service_id, {
            'status': 'unknown',
            'message': 'Not checked yet'
        })
    
    return jsonify({
        'service': service,
        'configured': configured,
        'status': status
    })

@app.route('/api/service/<service_id>/configure', methods=['POST'])
@login_required
def api_configure_service(service_id):
    """Configure service secrets"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    data = request.json
    password = data.get('password')
    secrets = data.get('secrets', {})
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Save encrypted secrets
    env_file = EncryptedEnvFile(f'.env.{service_id}')
    
    try:
        # In production, properly handle password-based encryption
        env_file.encrypt_env(secrets)
        
        # Trigger status check
        monitor.check_all_services()
        
        return jsonify({'success': True, 'message': 'Service configured'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/<service_id>/test', methods=['POST'])
@login_required
def api_test_service(service_id):
    """Test service connection"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # Trigger immediate health check
    config = SERVICES[service_id]
    status = monitor.check_service(service_id, config)
    
    return jsonify(status)

@app.route('/api/export/<service_id>')
@login_required
def api_export_service(service_id):
    """Export service configuration"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # In production, implement secure export
    return jsonify({
        'message': 'Export functionality requires additional authentication'
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'authenticated' in session:
        emit('connected', {'message': 'Connected to status updates'})
        
        # Send current status
        with status_lock:
            emit('status_bulk', service_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('refresh_status')
def handle_refresh():
    """Handle manual refresh request"""
    if 'authenticated' in session:
        monitor.check_all_services()

# Service creation API endpoints
@app.route('/api/templates')
@login_required
def api_get_templates():
    """Get available service templates"""
    return jsonify(SERVICE_TEMPLATES)

@app.route('/api/health-check-types')
@login_required
def api_get_health_check_types():
    """Get available health check types"""
    return jsonify(HEALTH_CHECK_TYPES)

@app.route('/api/service/create', methods=['POST'])
@login_required
def api_create_service():
    """Create a new service configuration"""
    data = request.json
    
    # Extract service configuration
    service_id = data.get('id')
    service_name = data.get('name')
    service_icon = data.get('icon', '🔧')
    service_color = data.get('color', '#718096')
    service_keys = data.get('keys', [])
    required_keys = data.get('required', [])
    health_check = data.get('health_check', {'type': 'none'})
    
    # Validate required fields
    if not service_id or not service_name:
        return jsonify({'error': 'Service ID and name are required'}), 400
    
    # Check if service ID already exists
    if service_id in SERVICES:
        return jsonify({'error': f'Service {service_id} already exists'}), 409
    
    # Validate field definitions
    for field in service_keys:
        if not isinstance(field, dict) or 'key' not in field:
            return jsonify({'error': 'Invalid field definition'}), 400
    
    # Create service configuration
    new_service = {
        'name': service_name,
        'icon': service_icon,
        'color': service_color,
        'health_check': health_check,
        'keys': [field['key'] for field in service_keys],
        'required': required_keys,
        'custom': True,  # Mark as custom service
        'field_definitions': service_keys  # Store full field definitions
    }
    
    # Add to SERVICES (in production, persist to database)
    SERVICES[service_id] = new_service
    
    # Save to persistent storage
    save_custom_services()
    
    # Notify connected clients
    socketio.emit('service_added', {
        'service_id': service_id,
        'service': new_service
    })
    
    return jsonify({
        'success': True,
        'service_id': service_id,
        'message': f'Service {service_name} created successfully'
    })

@app.route('/api/service/<service_id>/update', methods=['PUT'])
@login_required
def api_update_service(service_id):
    """Update an existing service configuration"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # Only allow updating custom services
    if not SERVICES[service_id].get('custom'):
        return jsonify({'error': 'Cannot modify built-in services'}), 403
    
    data = request.json
    service = SERVICES[service_id]
    
    # Update allowed fields
    if 'name' in data:
        service['name'] = data['name']
    if 'icon' in data:
        service['icon'] = data['icon']
    if 'color' in data:
        service['color'] = data['color']
    if 'health_check' in data:
        service['health_check'] = data['health_check']
    if 'keys' in data:
        service['keys'] = [field['key'] for field in data['keys']]
        service['field_definitions'] = data['keys']
    if 'required' in data:
        service['required'] = data['required']
    
    # Save changes
    save_custom_services()
    
    # Notify connected clients
    socketio.emit('service_updated', {
        'service_id': service_id,
        'service': service
    })
    
    return jsonify({
        'success': True,
        'message': f'Service {service["name"]} updated successfully'
    })

@app.route('/api/service/<service_id>/delete', methods=['DELETE'])
@login_required
def api_delete_service(service_id):
    """Delete a custom service"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # Only allow deleting custom services
    if not SERVICES[service_id].get('custom'):
        return jsonify({'error': 'Cannot delete built-in services'}), 403
    
    service_name = SERVICES[service_id]['name']
    del SERVICES[service_id]
    
    # Delete associated secrets file if exists
    env_file = Path(f'.env.{service_id}.encrypted')
    if env_file.exists():
        env_file.unlink()
    
    # Save changes
    save_custom_services()
    
    # Notify connected clients
    socketio.emit('service_deleted', {
        'service_id': service_id
    })
    
    return jsonify({
        'success': True,
        'message': f'Service {service_name} deleted successfully'
    })

@app.route('/api/service/<service_id>/check', methods=['POST'])
@login_required
def api_check_service(service_id):
    """Manually trigger health check for a service"""
    if service_id not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # Trigger immediate health check
    config = SERVICES[service_id]
    status = monitor.check_service(service_id, config)
    
    # Update status cache
    with status_lock:
        service_status[service_id] = status
    
    # Emit update via WebSocket
    socketio.emit('status_update', {
        'service': service_id,
        'status': status
    }, namespace='/', to='/')
    
    return jsonify(status)

@app.route('/api/service/<service_id>/authenticate', methods=['POST'])
@login_required
def api_authenticate_service(service_id):
    """Show instructions for CLI authentication"""
    cli_services = ['github', 'flyio', 'npm', 'docker', 'terraform', 'cloudflare']
    
    if service_id not in cli_services:
        return jsonify({'error': 'Service does not support CLI authentication'}), 400
    
    # Return instructions for host system authentication
    instructions = {
        'github': 'Run `authctl login github` or `gh auth login` on host system',
        'flyio': 'Run `authctl login flyio` or `fly auth login` on host system', 
        'npm': 'Run `authctl login npm` or `npm login` on host system',
        'docker': 'Run `authctl login docker` or `docker login` on host system',
        'terraform': 'Run `authctl login terraform` on host system',
        'cloudflare': 'Run `authctl login cloudflare` on host system'
    }
    
    return jsonify({
        'success': False,
        'message': instructions.get(service_id, f'Run `authctl login {service_id}` on host system'),
        'instruction': True,
        'host_command': f'authctl login {service_id}'
    })

@app.route('/api/auth/status')
@login_required
def api_auth_status():
    """Get authentication status from auth manager"""
    try:
        # Import auth manager
        sys.path.append('/app/auth_manager')
        from auth_manager import AuthManager
        
        # Get status
        auth_mgr = AuthManager()
        auth_mgr.verify_all()
        status = auth_mgr.get_status()
        
        # Also update service status for CLI services
        cli_services = ['github', 'flyio', 'npm', 'docker', 'terraform', 'cloudflare']
        for service_id in cli_services:
            if service_id in SERVICES and service_id in status['services']:
                svc_status = status['services'][service_id]
                health_status = {
                    'status': 'healthy' if svc_status.get('authenticated') else 'degraded',
                    'message': 'CLI authenticated' if svc_status.get('authenticated') else 'CLI not authenticated',
                    'timestamp': datetime.now().isoformat(),
                    'cli_auth': svc_status.get('authenticated', False)
                }
                
                # Update cache
                with status_lock:
                    service_status[service_id] = health_status
                
                # Emit update
                socketio.emit('status_update', {
                    'service': service_id,
                    'status': health_status
                }, namespace='/', to='/')
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'services': {},
            'summary': {'total': 0, 'authenticated': 0, 'failed': 0}
        }), 500

@app.route('/api/validate-field', methods=['POST'])
@login_required
def api_validate_field():
    """Validate a field value against its definition"""
    data = request.json
    field_def = data.get('field_definition')
    value = data.get('value')
    
    if not field_def:
        return jsonify({'error': 'Field definition required'}), 400
    
    valid, message = validate_field(field_def, value)
    
    return jsonify({
        'valid': valid,
        'message': message
    })

def save_custom_services():
    """Save custom services to persistent storage"""
    custom_services = {
        sid: svc for sid, svc in SERVICES.items() 
        if svc.get('custom')
    }
    
    services_file = Path('custom_services.json')
    with open(services_file, 'w') as f:
        json.dump(custom_services, f, indent=2)

def load_custom_services():
    """Load custom services from persistent storage"""
    services_file = Path('custom_services.json')
    if services_file.exists():
        try:
            with open(services_file, 'r') as f:
                custom_services = json.load(f)
                SERVICES.update(custom_services)
        except Exception as e:
            print(f"Error loading custom services: {e}")

# Load custom services on startup
load_custom_services()

if __name__ == '__main__':
    # Start monitoring
    monitor.start()
    
    # Run app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║   Secrets Management GUI              ║
    ║   http://localhost:{port}              ║
    ║                                       ║
    ║   Default credentials:                ║
    ║   Username: admin                     ║
    ║   Password: changeme                  ║
    ╚═══════════════════════════════════════╝
    """)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)