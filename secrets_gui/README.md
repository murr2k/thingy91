# Secrets Manager GUI

A compact, aesthetically pleasing web interface for managing service credentials with real-time health monitoring.

![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)
![License: MIT](https://img.shields.io/badge/License-MIT-blue)

## Features

### 🎯 Compact Design
- **Minimalist UI** - Clean, modern interface that displays all services at a glance
- **Service Cards** - Each service shown as a compact card with status indicator
- **Real-time Updates** - WebSocket-based live status updates
- **Responsive Layout** - Automatically adjusts to screen size

### 🔐 Security Features
- **Session-based Authentication** - Secure login with timeout
- **Encrypted Storage** - All secrets stored with AES-256 encryption
- **Rate Limiting** - Protection against brute force attacks
- **No Plain Text** - Secrets never stored or transmitted in plain text

### 📊 Service Monitoring
- **Health Checks** - Automatic periodic health checks every 30 seconds
- **Visual Status** - Color-coded status indicators with animations
  - 🟢 Healthy - Service is operational
  - 🟠 Degraded - Service has issues
  - 🔴 Error - Service is down
  - ⚪ Unconfigured - Not set up yet
- **Multiple Check Types**
  - HTTPS endpoint monitoring
  - Command execution checks
  - Database connection tests
  - Custom health check functions

### 🛠️ Supported Services
- **Onomondo** - SoftSIM management
- **AWS** - Amazon Web Services
- **Azure** - Microsoft Azure
- **Database** - PostgreSQL/MySQL
- **Redis** - Cache service
- **Stripe** - Payment processing
- **OpenAI** - AI/ML APIs
- More can be easily added

## Quick Start

### Option 1: Direct Python

```bash
# Install dependencies
pip3 install -r secrets_gui/requirements.txt

# Run the application
cd secrets_gui
python3 app.py

# Access at http://localhost:5000
# Default: admin / changeme
```

### Option 2: Docker

```bash
# Build and run with Docker Compose
cd secrets_gui
docker-compose up -d

# Access at http://localhost:5000
```

### Option 3: Production with Custom Settings

```bash
# Set environment variables
export ADMIN_USERNAME="your-username"
export ADMIN_PASSWORD="your-secure-password"
export FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Run with gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## Usage

### 1. Login
- Navigate to http://localhost:5000
- Login with credentials (default: admin/changeme)
- Session expires after 1 hour of inactivity

### 2. View Service Status
- Dashboard shows all services in a grid
- Each card displays:
  - Service name and icon
  - Current status indicator
  - Status message
  - Required and optional keys
- Status updates automatically every 30 seconds

### 3. Configure a Service
- Click on any service card
- Enter encryption password (protects your secrets)
- Fill in required credentials
- Optional: Test connection before saving
- Click Save to store encrypted

### 4. Monitor Health
- Green pulse = healthy connection
- Orange pulse = degraded service
- Red pulse = service error
- Gray = not configured
- Status messages show details

## Architecture

### Components

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│  Flask App   │────▶│  Encrypted  │
│  (Client)   │◀────│   (Server)   │◀────│   Storage   │
└─────────────┘     └──────────────┘     └─────────────┘
       ↕                    ↕
   WebSocket          Health Checks
   Real-time          to Services
```

### File Structure

```
secrets_gui/
├── app.py                 # Main Flask application
├── templates/
│   ├── dashboard.html     # Main dashboard UI
│   └── login.html        # Login page
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image
└── docker-compose.yml    # Orchestration
```

## Security Considerations

### Authentication
- Session-based with secure cookies
- Password hashing with SHA-256
- Automatic session timeout
- Rate limiting on login attempts

### Encryption
- Secrets encrypted with AES-256
- PBKDF2 key derivation
- Separate encryption per service
- Keys never logged or displayed

### Network Security
- HTTPS recommended for production
- WebSocket over WSS in production
- CORS configured for security
- No sensitive data in URLs

## Customization

### Add New Service

Edit `app.py` and add to `SERVICES` dict:

```python
'myservice': {
    'name': 'My Service',
    'icon': '🚀',
    'color': '#123456',
    'health_check': {
        'type': 'https',
        'endpoint': 'https://api.myservice.com/health',
        'timeout': 5
    },
    'keys': ['MYSERVICE_API_KEY', 'MYSERVICE_SECRET'],
    'required': ['MYSERVICE_API_KEY']
}
```

### Custom Health Checks

Add a function in `app.py`:

```python
def check_myservice() -> dict:
    # Your health check logic
    if service_is_healthy():
        return {
            'status': 'healthy',
            'message': 'Service operational',
            'timestamp': datetime.now().isoformat()
        }
    return {
        'status': 'error',
        'message': 'Service down',
        'timestamp': datetime.now().isoformat()
    }
```

### Change Update Interval

Edit `Config` class in `app.py`:

```python
class Config:
    UPDATE_INTERVAL = 60  # Check every 60 seconds
```

## Production Deployment

### 1. Secure Setup

```bash
# Generate secure secret key
export FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Set strong admin password
export ADMIN_PASSWORD="your-very-secure-password"

# Use HTTPS (required for production)
# Configure reverse proxy (nginx/traefik) with SSL
```

### 2. Reverse Proxy (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name secrets.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Systemd Service

```ini
# /etc/systemd/system/secrets-gui.service
[Unit]
Description=Secrets Manager GUI
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/secrets-gui
Environment="FLASK_ENV=production"
EnvironmentFile=/opt/secrets-gui/.env
ExecStart=/usr/local/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Cannot Connect to Service
- Check firewall rules
- Verify service credentials are correct
- Check network connectivity
- Review service logs

### Status Shows Unknown
- Ensure health check is configured
- Check if service URL is accessible
- Verify authentication headers

### WebSocket Disconnected
- Check if running behind proxy
- Ensure WebSocket upgrade headers are passed
- Verify firewall allows WebSocket

### High Memory Usage
- Reduce UPDATE_INTERVAL
- Limit number of monitored services
- Use production WSGI server

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/murr2k/thingy91/issues
- Documentation: https://github.com/murr2k/thingy91/wiki