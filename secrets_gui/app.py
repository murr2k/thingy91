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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.secrets_manager import EncryptedEnvFile

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
            'endpoint': 'https://api.onomondo.com/health',
            'timeout': 5
        },
        'keys': ['ONOMONDO_API_KEY', 'ONOMONDO_IMSI', 'ONOMONDO_ICCID'],
        'required': ['ONOMONDO_API_KEY']
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
            }, namespace='/', broadcast=True)
    
    def check_service(self, service_id: str, config: dict) -> dict:
        """Check health of a single service"""
        # Check if required keys exist
        env_file = EncryptedEnvFile(f'.env.{service_id}')
        
        try:
            # Check if encrypted file exists
            if not Path(f'.env.{service_id}.encrypted').exists():
                return {
                    'status': 'unconfigured',
                    'message': 'Not configured',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Try to load secrets (without password for status check)
            # In real implementation, we'd cache decrypted values securely
            keys_configured = True  # Simplified for demo
            
            if not keys_configured:
                return {
                    'status': 'incomplete',
                    'message': 'Missing required keys',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Perform health check
            health_config = config.get('health_check', {})
            check_type = health_config.get('type')
            
            if check_type == 'https':
                return self._check_https(health_config)
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
def get_stripe_headers() -> dict:
    """Get Stripe API headers"""
    secret_key = os.environ.get('STRIPE_SECRET_KEY', '')
    return {'Authorization': f'Bearer {secret_key}'} if secret_key else {}

def get_openai_headers() -> dict:
    """Get OpenAI API headers"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    return {'Authorization': f'Bearer {api_key}'} if api_key else {}

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
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)