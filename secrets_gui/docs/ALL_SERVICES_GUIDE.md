# Complete Services Guide - Secrets Manager

## Overview
The Secrets Manager now supports **21 services** with secure credential storage, health monitoring, and automated CLI setup.

## 📋 Services Summary

| Service | Icon | Purpose | CLI Tool |
|---------|------|---------|----------|
| **GitHub** | 🐙 | Version control & CI/CD | `gh` |
| **Fly.io** | 🚀 | Application hosting | `flyctl` |
| **NPM** | 📦 | Package publishing | `npm` |
| **Docker** | 🐳 | Container registry | `docker` |
| **AWS** | ☁️ | Cloud services | `aws` |
| **Azure** | ☁️ | Microsoft cloud | `az` |
| **OpenAI** | 🤖 | GPT API access | API only |
| **Stripe** | 💳 | Payment processing | API only |
| **Database** | 🗄️ | Database connections | Various |
| **Redis** | ⚡ | Cache/message broker | `redis-cli` |
| **Grafana** | 📊 | Monitoring dashboards | API only |
| **Google Play** | 🎮 | Android app publishing | `fastlane` |
| **MacroFab** | 🔧 | PCB manufacturing | API only |
| **Cloudflare** | ☁️ | DNS & CDN | `cloudflared` |
| **Nexar** | 🔌 | Component search | API only |
| **Terraform** | 🏗️ | Infrastructure as Code | `terraform` |
| **Infisical** | 🔐 | Secrets management | `infisical` |
| **DigiKey** | 📟 | Electronic components | API only |
| **Blynk** | 📱 | IoT platform | API only |
| **Anthropic** | 🤖 | Claude AI API | API only |
| **Slack** | 💬 | Team communication | `slack` |

## 🚀 Quick Setup

### Access the GUI
```bash
# Start the service
docker-compose up -d

# Open in browser
http://localhost:5000

# Default credentials
Username: admin
Password: changeme
```

### Setup All Services at Once
```bash
# Configure all CLI tools with stored credentials
python3 scripts/setup_all_services.py

# Or setup specific services
python3 scripts/setup_all_services.py github npm flyio
```

## 📦 Service Details

### NPM Registry
**Purpose:** Package publishing and management

**Credentials:**
- `NPM_AUTH_TOKEN` - Authentication token (required)
- `NPM_USERNAME` - NPM username
- `NPM_EMAIL` - NPM email

**Setup:**
```bash
./scripts/npm_setup.sh
# Or
npm config set //registry.npmjs.org/:_authToken $NPM_AUTH_TOKEN
```

**Get Token:**
1. Visit https://www.npmjs.com/settings/[username]/tokens
2. Create token with "Publish" scope
3. Store in Secrets Manager

---

### Grafana
**Purpose:** Monitoring and observability dashboards

**Credentials:**
- `GRAFANA_TOKEN` - API token (required)
- `GRAFANA_URL` - Instance URL
- `GRAFANA_ORG_ID` - Organization ID

**Get Token:**
1. Go to Grafana instance → Configuration → API Keys
2. Create new API key with Editor/Admin role
3. Store in Secrets Manager

---

### Google Play
**Purpose:** Android app publishing and management

**Credentials:**
- `GOOGLE_PLAY_SERVICE_ACCOUNT` - Service account JSON (required)
- `GOOGLE_PLAY_PACKAGE_NAME` - App package name

**Setup:**
1. Create service account in Google Play Console
2. Download JSON key file
3. Store as single-line JSON in Secrets Manager

**Usage with Fastlane:**
```ruby
supply(
  json_key_data: ENV['GOOGLE_PLAY_SERVICE_ACCOUNT'],
  package_name: ENV['GOOGLE_PLAY_PACKAGE_NAME']
)
```

---

### MacroFab
**Purpose:** PCB manufacturing and assembly

**Credentials:**
- `MACROFAB_API_KEY` - API key (required)
- `MACROFAB_API_SECRET` - API secret

**Get Credentials:**
1. Log in to MacroFab account
2. Go to Account Settings → API
3. Generate API credentials

---

### Cloudflare
**Purpose:** DNS, CDN, and DDoS protection

**Credentials:**
- `CLOUDFLARE_EMAIL` - Account email (required)
- `CLOUDFLARE_GLOBAL_API_KEY` - Global API key (required)
- `CLOUDFLARE_ZONE_ID` - Zone ID for your domain

**Get Credentials:**
1. Log in to Cloudflare
2. Go to My Profile → API Tokens
3. View Global API Key
4. Find Zone ID in domain overview

**CLI Setup:**
```bash
# Install cloudflared
brew install cloudflared  # macOS
# Or download from https://github.com/cloudflare/cloudflared

# Configure
cloudflared tunnel login
```

---

### Nexar
**Purpose:** Electronic component search and supply chain

**Credentials:**
- `NEXAR_CLIENT_ID` - OAuth client ID (required)
- `NEXAR_CLIENT_SECRET` - OAuth client secret (required)
- `NEXAR_ACCESS_TOKEN` - Access token (auto-refreshed)

**Get Credentials:**
1. Register at https://nexar.com/api
2. Create application
3. Get OAuth credentials

---

### Terraform Cloud
**Purpose:** Infrastructure as Code management

**Credentials:**
- `TERRAFORM_API_TOKEN` - API token (required)
- `TERRAFORM_ORG` - Organization name
- `TERRAFORM_WORKSPACE` - Default workspace

**Setup:**
```bash
# Token will be auto-configured in ~/.terraform.d/credentials.tfrc.json
terraform login

# Or use the setup script
python3 scripts/setup_all_services.py terraform
```

**Get Token:**
1. Visit https://app.terraform.io/settings/tokens
2. Create API token
3. Store in Secrets Manager

---

### Infisical
**Purpose:** End-to-end encrypted secrets management

**Credentials:**
- `INFISICAL_SERVICE_TOKEN` - Service token (required)
- `INFISICAL_PROJECT_ID` - Project ID
- `INFISICAL_ENV` - Environment (dev/staging/prod)

**Get Token:**
1. Create project in Infisical
2. Go to Project Settings → Service Tokens
3. Create service token with required scopes

**CLI Setup:**
```bash
# Install Infisical CLI
curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
sudo apt-get install infisical

# Login with service token
infisical login --method=service-token --token=$INFISICAL_SERVICE_TOKEN
```

---

### DigiKey
**Purpose:** Electronic components ordering and search

**Credentials:**
- `DIGIKEY_CLIENT_ID` - OAuth client ID (required)
- `DIGIKEY_CLIENT_SECRET` - OAuth client secret (required)
- `DIGIKEY_ACCESS_TOKEN` - Access token
- `DIGIKEY_REFRESH_TOKEN` - Refresh token
- `DIGIKEY_ENVIRONMENT` - sandbox/production

**Setup:**
1. Register at https://developer.digikey.com/
2. Create application
3. Configure OAuth callback URL: `http://localhost:8080/callback`
4. Use provided OAuth flow scripts

**OAuth Flow:**
```bash
# Sandbox environment
./digikey-oauth-setup.sh

# Production environment
./digikey-production-oauth.sh
```

---

### Blynk
**Purpose:** IoT platform for Thingy91 and other devices

**Credentials:**
- `BLYNK_AUTH_TOKEN` - Device auth token (required)
- `BLYNK_ORGANIZATION_ID` - Organization ID
- `BLYNK_TEMPLATE_NAME` - Template name
- `BLYNK_DEVICE_NAME` - Device name

**Get Token:**
1. Create device in Blynk.Cloud
2. Copy auth token from device info
3. Store in Secrets Manager

**Usage in Thingy91:**
```c
// In your firmware
#define BLYNK_AUTH_TOKEN "YOUR_TOKEN"
Blynk.begin(BLYNK_AUTH_TOKEN);
```

---

### Anthropic
**Purpose:** Claude AI API access

**Credentials:**
- `ANTHROPIC_API_KEY` - API key (required)
- `ANTHROPIC_MODEL` - Default model (claude-3-opus, etc.)

**Get Key:**
1. Visit https://console.anthropic.com/
2. Go to API Keys
3. Create new key

**Usage:**
```python
import anthropic

client = anthropic.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"]
)
```

---

### Slack
**Purpose:** Team communication and notifications

**Credentials:**
- `SLACK_BOT_TOKEN` - Bot user OAuth token (required)
- `SLACK_WEBHOOK_URL` - Incoming webhook URL
- `SLACK_CHANNEL` - Default channel
- `SLACK_APP_TOKEN` - App-level token for Socket Mode

**Setup:**
1. Create Slack App at https://api.slack.com/apps
2. Add OAuth scopes (chat:write, etc.)
3. Install to workspace
4. Copy Bot User OAuth Token

**CLI Setup:**
```bash
# Install Slack CLI
curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash

# Authenticate
slack auth add

# Test
slack auth test
```

## 🔒 Security Features

### Encryption
- All credentials encrypted with AES-256
- Password-based key derivation (PBKDF2)
- Unique salt per service

### Access Control
- Session-based authentication
- Automatic timeout after 30 minutes
- Audit logging of all access

### Health Monitoring
- Real-time connection testing
- Visual status indicators
- WebSocket updates every 30 seconds

## 🛠️ Troubleshooting

### Service Not Connecting
1. Check credentials are correctly entered
2. Verify API endpoints are accessible
3. Check for expired tokens
4. Review service-specific documentation

### CLI Tool Not Found
Most CLI tools need separate installation:
```bash
# Examples
brew install gh              # GitHub CLI
brew install flyctl          # Fly.io
npm install -g npm@latest    # NPM
brew install terraform       # Terraform
```

### Token Expired
Many services use expiring tokens:
- **DigiKey**: Refresh using refresh token
- **Nexar**: OAuth refresh flow
- **Google Play**: Service account keys don't expire

## 📚 Additional Resources

### Service-Specific Docs
- [GitHub CLI Setup](./GITHUB_SETUP.md)
- [Fly.io Setup](./FLYIO_SETUP.md)
- [DigiKey OAuth Flow](../docs/services/digikey.md)

### API Documentation
- NPM: https://docs.npmjs.com/cli/v8/using-npm/config
- Grafana: https://grafana.com/docs/grafana/latest/http_api/
- Cloudflare: https://api.cloudflare.com/
- Terraform: https://www.terraform.io/cloud-docs/api-docs
- Slack: https://api.slack.com/

## 🚦 Service Status Check

Run this to check all services:
```bash
# Check health of all configured services
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/services/status

# Or use the dashboard
http://localhost:5000
```

## 💡 Best Practices

1. **Rotate Tokens Regularly**
   - Set calendar reminders for token rotation
   - Use short-lived tokens where possible

2. **Use Least Privilege**
   - Only grant necessary permissions
   - Use read-only tokens for monitoring

3. **Monitor Access**
   - Review audit logs regularly
   - Set up alerts for unusual access

4. **Backup Credentials**
   - Export encrypted backups
   - Store in secure location

5. **Environment Separation**
   - Use different tokens for dev/staging/prod
   - Label tokens clearly

## 🆘 Support

For issues or questions:
- Check service status in dashboard
- Review logs: `docker logs secrets-manager-gui`
- File issues in project repository