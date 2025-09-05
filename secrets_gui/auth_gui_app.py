#!/usr/bin/env python3
"""
Auth Manager GUI
A web interface that communicates directly with the host system's auth manager
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
import asyncio
import websockets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD_HASH = '057ba03d6c44104863dc7361fe4578965d1887360f90a0895882e58a6248fc86'  # changeme
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    SESSION_TIMEOUT = 3600  # 1 hour
    AUTH_WEBSOCKET_HOST = 'localhost'  # Host auth manager WebSocket
    AUTH_WEBSOCKET_PORT = 8765

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
login_attempts = {}
login_lock = threading.Lock()

# Auth manager service definitions (for display purposes)
CLI_SERVICES = {
    'github': {
        'name': 'GitHub CLI',
        'icon': '🐙',
        'color': '#24292e',
        'description': 'GitHub CLI authentication'
    },
    'flyio': {
        'name': 'Fly.io',
        'icon': '🚀',
        'color': '#8b5cf6',
        'description': 'Fly.io deployment platform'
    },
    'npm': {
        'name': 'NPM Registry',
        'icon': '📦',
        'color': '#cb3837',
        'description': 'NPM package registry'
    },
    'docker': {
        'name': 'Docker Hub',
        'icon': '🐳',
        'color': '#2496ed',
        'description': 'Docker container registry'
    },
    'terraform': {
        'name': 'Terraform Cloud',
        'icon': '🏗️',
        'color': '#623ce4',
        'description': 'Infrastructure as Code'
    },
    'cloudflare': {
        'name': 'Cloudflare',
        'icon': '☁️',
        'color': '#f38020',
        'description': 'CDN and DNS services'
    }
}

# Helper functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        
        # Check session timeout
        last_activity = session.get('last_activity')
        if last_activity:
            last_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_time > timedelta(seconds=Config.SESSION_TIMEOUT):
                session.clear()
                if request.is_json:
                    return jsonify({'error': 'Session expired'}), 401
                return redirect(url_for('login'))
        
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

class AuthWebSocketClient:
    """WebSocket client to communicate with host auth manager"""
    
    def __init__(self):
        self.host = Config.AUTH_WEBSOCKET_HOST
        self.port = Config.AUTH_WEBSOCKET_PORT
        self.uri = f"ws://{self.host}:{self.port}"
        self.request_id = 0
    
    def _get_next_id(self):
        """Get next request ID."""
        self.request_id += 1
        return str(self.request_id)
    
    async def _send_request(self, action, **kwargs):
        """Send a request to the auth manager WebSocket server."""
        try:
            async with websockets.connect(self.uri, timeout=10) as websocket:
                request = {
                    "id": self._get_next_id(),
                    "action": action,
                    **kwargs
                }
                
                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                
                data = json.loads(response)
                return data.get("data", {})
                
        except Exception as e:
            return {"error": f"WebSocket connection failed: {str(e)}"}
    
    def get_status(self):
        """Get authentication status from auth manager"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._send_request("get_status"))
            loop.close()
            
            # If we got an error, return empty status
            if "error" in result:
                return {
                    'services': {}, 
                    'summary': {'total': 0, 'authenticated': 0, 'failed': 0},
                    'error': result["error"]
                }
            
            return result
        except Exception as e:
            return {
                'services': {}, 
                'summary': {'total': 0, 'authenticated': 0, 'failed': 0},
                'error': str(e)
            }
    
    def authenticate_service(self, service_id):
        """Authenticate a specific service"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_request("authenticate", service=service_id)
            )
            loop.close()
            
            success = result.get("success", False)
            message = result.get("message", "")
            error = result.get("error", "")
            
            return success, message, error
        except Exception as e:
            return False, "", str(e)
    
    def verify_service(self, service_id):
        """Verify authentication for a specific service"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_request("verify", service=service_id)
            )
            loop.close()
            
            return result.get("authenticated", False)
        except Exception as e:
            return False

# Initialize auth manager client
auth_client = AuthWebSocketClient()

# Routes
@app.route('/')
@login_required
def index():
    """Main dashboard"""
    return render_template('auth_dashboard.html', services=CLI_SERVICES)

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
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': '/'})
            return redirect('/')
        else:
            # Track failed attempt
            with login_lock:
                if username in login_attempts:
                    attempts, _ = login_attempts[username]
                    login_attempts[username] = (attempts + 1, datetime.now())
                else:
                    login_attempts[username] = (1, datetime.now())
            
            if request.is_json:
                return jsonify({'error': 'Invalid credentials'}), 401
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

# API Routes
@app.route('/api/status')
@login_required
def api_status():
    """Get authentication status from auth manager"""
    status_data = auth_client.get_status()
    
    # Convert to format expected by frontend
    service_statuses = {}
    for service_id in CLI_SERVICES.keys():
        if service_id in status_data.get('services', {}):
            svc_info = status_data['services'][service_id]
            service_statuses[service_id] = {
                'status': 'healthy' if svc_info.get('authenticated') else 'degraded',
                'message': 'CLI authenticated' if svc_info.get('authenticated') else 'CLI not authenticated',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': svc_info.get('authenticated', False)
            }
        else:
            service_statuses[service_id] = {
                'status': 'unknown',
                'message': 'Service not found in auth manager',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': False
            }
    
    return jsonify(service_statuses)

@app.route('/api/service/<service_id>/authenticate', methods=['POST'])
@login_required
def api_authenticate_service(service_id):
    """Authenticate a service using auth manager"""
    if service_id not in CLI_SERVICES:
        return jsonify({'error': 'Service not supported'}), 400
    
    success, stdout, stderr = auth_client.authenticate_service(service_id)
    
    if success:
        # Verify the authentication worked
        authenticated = auth_client.verify_service(service_id)
        
        status = {
            'status': 'healthy' if authenticated else 'degraded',
            'message': 'CLI authenticated successfully' if authenticated else 'Authentication may have failed',
            'timestamp': datetime.now().isoformat(),
            'cli_auth': authenticated
        }
        
        # Emit update via WebSocket
        socketio.emit('status_update', {
            'service': service_id,
            'status': status
        }, namespace='/')
        
        return jsonify({
            'success': True,
            'message': f'{CLI_SERVICES[service_id]["name"]} authenticated successfully',
            'status': status,
            'output': stdout
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Authentication failed: {stderr}',
            'error': stderr
        }), 500

@app.route('/api/service/<service_id>/verify', methods=['POST'])
@login_required
def api_verify_service(service_id):
    """Verify authentication status for a service"""
    if service_id not in CLI_SERVICES:
        return jsonify({'error': 'Service not supported'}), 400
    
    authenticated = auth_client.verify_service(service_id)
    
    status = {
        'status': 'healthy' if authenticated else 'degraded',
        'message': 'CLI authenticated' if authenticated else 'CLI not authenticated',
        'timestamp': datetime.now().isoformat(),
        'cli_auth': authenticated
    }
    
    return jsonify(status)

@app.route('/api/refresh', methods=['POST'])
@login_required
def api_refresh_all():
    """Refresh all service statuses"""
    status_data = auth_client.get_status()
    
    # Emit updates for all services
    for service_id in CLI_SERVICES.keys():
        if service_id in status_data.get('services', {}):
            svc_info = status_data['services'][service_id]
            status = {
                'status': 'healthy' if svc_info.get('authenticated') else 'degraded',
                'message': 'CLI authenticated' if svc_info.get('authenticated') else 'CLI not authenticated',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': svc_info.get('authenticated', False)
            }
        else:
            status = {
                'status': 'unknown',
                'message': 'Service not found in auth manager',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': False
            }
        
        socketio.emit('status_update', {
            'service': service_id,
            'status': status
        }, namespace='/')
    
    return jsonify({'success': True, 'message': 'Status refreshed'})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    if not session.get('authenticated'):
        return False
    
    emit('connected', {'message': 'Connected to auth manager'})
    
    # Send initial status
    status_data = auth_client.get_status()
    for service_id in CLI_SERVICES.keys():
        if service_id in status_data.get('services', {}):
            svc_info = status_data['services'][service_id]
            status = {
                'status': 'healthy' if svc_info.get('authenticated') else 'degraded',
                'message': 'CLI authenticated' if svc_info.get('authenticated') else 'CLI not authenticated',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': svc_info.get('authenticated', False)
            }
        else:
            status = {
                'status': 'unknown',
                'message': 'Service not found in auth manager',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': False
            }
        
        emit('status_update', {
            'service': service_id,
            'status': status
        })

@socketio.on('refresh_status')
def handle_refresh():
    if not session.get('authenticated'):
        return False
    
    # Get fresh status from auth manager
    status_data = auth_client.get_status()
    
    for service_id in CLI_SERVICES.keys():
        if service_id in status_data.get('services', {}):
            svc_info = status_data['services'][service_id]
            status = {
                'status': 'healthy' if svc_info.get('authenticated') else 'degraded',
                'message': 'CLI authenticated' if svc_info.get('authenticated') else 'CLI not authenticated',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': svc_info.get('authenticated', False)
            }
        else:
            status = {
                'status': 'unknown',
                'message': 'Service not found in auth manager',
                'timestamp': datetime.now().isoformat(),
                'cli_auth': False
            }
        
        emit('status_update', {
            'service': service_id,
            'status': status
        }, broadcast=True)

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Production server (gunicorn)
    pass