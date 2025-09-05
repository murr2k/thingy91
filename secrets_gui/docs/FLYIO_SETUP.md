# Fly.io CLI Integration Guide

## Overview
The Secrets Manager now includes built-in support for Fly.io CLI (`flyctl`) authentication, allowing you to securely store and use your Fly.io API token for application deployments.

## Features

### 🚀 Fly.io Service
- **Service ID**: `flyio`
- **Icon**: 🚀
- **Required Credentials**:
  - `FLY_API_TOKEN` (required) - Personal Access Token
  - `FLY_ORG` (optional) - Default organization
  - `FLY_REGION` (optional) - Default deployment region

### Health Check
- Automatically verifies token validity via Fly.io GraphQL API
- Real-time status monitoring in dashboard
- Shows authentication and organization status

## Setup Instructions

### Step 1: Create Fly.io Personal Access Token

1. Visit [Fly.io Personal Access Tokens](https://fly.io/user/personal_access_tokens)
2. Click "Create token"
3. Give it a descriptive name (e.g., "CLI Access")
4. Copy the generated token immediately (it won't be shown again)

Alternative: Get token from existing installation:
```bash
# If already logged in elsewhere
fly auth token
```

### Step 2: Configure in Secrets Manager

1. Access the Secrets Manager GUI at http://localhost:5000
2. Login with your credentials (default: admin/changeme)
3. Find the "Fly.io" service card (🚀 icon)
4. Click to configure and enter:
   - `FLY_API_TOKEN`: Your personal access token
   - `FLY_ORG`: Your organization slug (optional)
   - `FLY_REGION`: Default region like `iad`, `lhr`, `sin` (optional)
5. Save the configuration

### Step 3: Authenticate Fly.io CLI

#### Option A: Using the Setup Script
```bash
# Run the automated setup script
./scripts/fly_setup.sh

# Or with Python helper
python3 scripts/get_fly_token.py --setup
```

#### Option B: Manual Setup
```bash
# Export token from secrets manager
export FLY_API_TOKEN=$(python3 scripts/get_fly_token.py)

# Configure flyctl
fly auth token $FLY_API_TOKEN

# Verify authentication
fly auth whoami
```

#### Option C: Direct Configuration
```bash
# Create config directly
mkdir -p ~/.fly
echo "access_token: $(python3 scripts/get_fly_token.py)" > ~/.fly/config.yml
chmod 600 ~/.fly/config.yml

# Test
fly apps list
```

## Usage Examples

Once configured, you can use `flyctl` normally:

### Application Management
```bash
# List your applications
fly apps list

# Create a new app
fly launch

# Show app status
fly status

# Open app in browser
fly open
```

### Deployment
```bash
# Deploy application
fly deploy

# Deploy with specific settings
fly deploy --strategy rolling --wait-timeout 300

# Scale application
fly scale count 3 --region iad

# Autoscale configuration
fly autoscale set min=1 max=10
```

### Monitoring & Logs
```bash
# View logs
fly logs

# Stream logs
fly logs -f

# SSH into app
fly ssh console

# Execute commands
fly ssh console -C "ls -la"
```

### Secrets Management
```bash
# Set secrets
fly secrets set DATABASE_URL="postgres://..."

# List secrets
fly secrets list

# Import from .env file
fly secrets import < .env.production
```

### Database Management
```bash
# Create Postgres database
fly postgres create

# Attach database to app
fly postgres attach <db-name>

# Connect to database
fly postgres connect
```

### Regions & Scaling
```bash
# List regions
fly regions list

# Add region
fly regions add sin

# Remove region
fly regions remove lhr

# Set backup regions
fly regions backup iad ord
```

## Helper Scripts

### `scripts/fly_setup.sh`
Automated setup script that:
- Checks for flyctl installation
- Retrieves token from secrets manager
- Configures flyctl authentication
- Validates the setup
- Shows your apps and organizations

### `scripts/get_fly_token.py`
Python utility for token management:
```bash
# Setup flyctl
python3 scripts/get_fly_token.py --setup

# Display token (be careful!)
python3 scripts/get_fly_token.py --show

# Export as environment variables
eval $(python3 scripts/get_fly_token.py --export)

# Show current token from flyctl config
python3 scripts/get_fly_token.py --current

# Show organization
python3 scripts/get_fly_token.py --org
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup flyctl
        uses: superfly/flyctl-actions/setup-flyctl@master
      
      - name: Deploy
        run: fly deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Docker Integration
```dockerfile
# Multi-stage build for Fly.io
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 8080
CMD ["node", "server.js"]
```

### fly.toml Configuration
```toml
app = "your-app-name"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[services]]
  protocol = "tcp"
  internal_port = 8080
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

## Security Notes

1. **Token Storage**: Tokens are encrypted using AES-256 encryption
2. **Access Control**: Requires authentication to access secrets
3. **Token Rotation**: Rotate tokens periodically for security
4. **Audit Logging**: All access attempts are logged
5. **Network Security**: Use HTTPS in production

## Troubleshooting

### Token Not Working
- Verify token hasn't been revoked
- Check token was copied correctly (no spaces)
- Ensure you have correct organization permissions
- Try generating a new token

### Health Check Failing
- Token may be invalid or expired
- Network connectivity to Fly.io API
- Rate limiting (rare)

### flyctl Not Found
Install Fly.io CLI:
```bash
# macOS
brew install flyctl

# Linux/WSL
curl -L https://fly.io/install.sh | sh

# Add to PATH
export PATH="$HOME/.fly/bin:$PATH"
```

### Authentication Issues
```bash
# Clear existing auth
rm ~/.fly/config.yml

# Re-authenticate
./scripts/fly_setup.sh
```

### Organization Issues
```bash
# List organizations
fly orgs list

# Switch organization
fly orgs switch <org-slug>

# Set default org
export FLY_ORG=<org-slug>
```

## API Integration

Access programmatically:

```python
import requests
import subprocess

# Get token via API
def get_fly_token():
    response = requests.get(
        'http://localhost:5000/api/service/flyio/secrets',
        headers={'X-API-Key': 'your-api-key'}
    )
    return response.json()['FLY_API_TOKEN']

# Use with flyctl
token = get_fly_token()
subprocess.run(['fly', 'auth', 'token', token])

# Or use Fly.io API directly
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'https://api.fly.io/graphql',
    headers=headers,
    json={'query': '{ apps { nodes { name } } }'}
)
```

## Best Practices

1. **Use Dedicated Tokens**: Create separate tokens for different environments
2. **Limit Token Scope**: Use organization-specific tokens when possible
3. **Monitor Usage**: Check audit logs regularly
4. **Automate Deployments**: Use CI/CD for consistent deployments
5. **Version Control**: Keep fly.toml in version control
6. **Secret Management**: Use fly secrets for app secrets, not code

## Common Commands Reference

```bash
# Apps
fly apps create <name>      # Create app
fly apps destroy <name>     # Delete app
fly apps restart <name>     # Restart app

# Deployment
fly deploy --now           # Deploy immediately
fly deploy --local-only    # Build locally
fly deploy --remote-only   # Build on Fly.io

# Scaling
fly scale vm shared-cpu-1x  # Set VM size
fly scale memory 512        # Set memory
fly scale count 2           # Set instance count

# Certificates
fly certs list             # List certificates
fly certs add example.com  # Add custom domain
fly certs check example.com # Check cert status

# Monitoring
fly status                 # App status
fly vm status <id>        # VM status
fly checks list           # Health checks

# Volumes
fly volumes list          # List volumes
fly volumes create <name> # Create volume
fly volumes extend <id>   # Extend volume
```

## Support

For issues or questions:
- Check dashboard for real-time Fly.io service status
- View logs: `docker logs secrets-manager-gui`
- Fly.io Status: https://status.fly.io/
- Fly.io Community: https://community.fly.io/