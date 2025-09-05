# System-Wide Authentication Manager Plan

## 🎯 Vision
Create a centralized authentication system that provides system-wide authentication for all development tools and services, making credentials seamlessly available to any project running anywhere on the system.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Secrets Manager GUI                        │
│                  (Encrypted Storage)                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│              System Auth Manager (Daemon)                    │
│  • Loads encrypted credentials on startup                    │
│  • Authenticates all CLI tools                              │
│  • Maintains auth sessions                                   │
│  • Refreshes tokens before expiry                           │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┼────────┬────────┬────────┬─────────┐
    ▼        ▼        ▼        ▼        ▼         ▼
┌───────┐ ┌──────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌───────┐
│  gh   │ │ fly  │ │ npm │ │ gcloud│ │docker│ │  aws  │
└───────┘ └──────┘ └─────┘ └──────┘ └──────┘ └───────┘
    │        │        │        │        │         │
    └────────┴────────┴────────┴────────┴─────────┘
                        │
                        ▼
              System-Wide Availability
         (Any project, any directory, any user)
```

## 📋 Service Authentication Methods

### CLI-Based Services
These services support CLI authentication that persists system-wide:

| Service | CLI Tool | Auth Method | Scope | Persistence |
|---------|----------|-------------|-------|-------------|
| **GitHub** | `gh` | `gh auth login --with-token` | User config | `~/.config/gh/` |
| **Fly.io** | `fly` | `FLY_API_TOKEN` env var | Process/System | Environment |
| **NPM** | `npm` | `npm config set //registry.npmjs.org/:_authToken` | User config | `~/.npmrc` |
| **Docker Hub** | `docker` | `docker login -u USERNAME -p TOKEN` | User config | `~/.docker/config.json` |
| **Google Cloud** | `gcloud` | `gcloud auth activate-service-account` | User config | `~/.config/gcloud/` |
| **AWS** | `aws` | `aws configure set aws_access_key_id` | User config | `~/.aws/credentials` |
| **Terraform** | `terraform` | `terraform login` with token | User config | `~/.terraform.d/credentials.tfrc.json` |
| **Cloudflare** | `wrangler` | `wrangler config` | User config | `~/.wrangler/config/` |
| **Slack** | `slack` | `slack auth add` | User config | `~/.slack/` |

### API-Only Services
These require environment variables or config files:

| Service | Auth Method | Implementation |
|---------|-------------|----------------|
| **Grafana** | API Key in env/config | Export to shell profile |
| **Nexar** | OAuth tokens | Store in env vars |
| **DigiKey** | OAuth tokens | Store in env vars |
| **Anthropic** | API Key | Export to shell profile |
| **OpenAI** | API Key | Export to shell profile |

## 🔧 Implementation Components

### 1. **Auth Manager Daemon** (`auth_manager.py`)
- Runs as a system service or user daemon
- Loads credentials from encrypted Secrets Manager
- Performs initial authentication for all services
- Monitors auth status and refreshes tokens

### 2. **Service Authenticators** (`authenticators/`)
Individual authenticator classes for each service:
- `github_auth.py` - GitHub CLI authentication
- `fly_auth.py` - Fly.io token management
- `npm_auth.py` - NPM registry authentication
- `docker_auth.py` - Docker Hub login
- etc.

### 3. **Environment Manager** (`env_manager.py`)
- Manages system-wide environment variables
- Updates shell profiles (`~/.bashrc`, `~/.zshrc`)
- Provides secure credential injection

### 4. **Status Monitor** (`status_monitor.py`)
- Polls service health
- Verifies authentication status
- Triggers re-authentication when needed
- Provides status API/dashboard

### 5. **CLI Tool** (`authctl`)
Command-line interface for managing auth:
```bash
authctl status          # Show all service auth status
authctl login <service> # Manually trigger auth for a service
authctl refresh         # Refresh all expired tokens
authctl logout <service># Logout from a service
```

## 🚀 Implementation Steps

### Phase 1: Core Infrastructure
1. Create auth manager daemon structure
2. Implement credential loading from Secrets Manager
3. Create base authenticator class
4. Set up logging and monitoring

### Phase 2: Service Authenticators
1. Implement GitHub authenticator
2. Implement Fly.io authenticator
3. Implement NPM authenticator
4. Add remaining CLI-based services
5. Add API-only services

### Phase 3: System Integration
1. Create systemd service for daemon
2. Implement environment variable management
3. Update shell profiles automatically
4. Create status monitoring API

### Phase 4: User Interface
1. Create `authctl` CLI tool
2. Add web dashboard for status
3. Implement notification system
4. Add auto-refresh logic

## 🔐 Security Considerations

1. **Credential Storage**: All credentials remain encrypted in Secrets Manager
2. **Memory Protection**: Credentials in memory are cleared after use
3. **Process Isolation**: Each authenticator runs in isolated subprocess
4. **Audit Logging**: All auth operations are logged
5. **Token Rotation**: Automatic token refresh before expiry
6. **Access Control**: Only authorized users can access auth manager

## 📊 Monitoring & Health Checks

Each service will be monitored for:
- Authentication status (valid/expired/invalid)
- Token expiry time
- Last successful operation
- API rate limits
- Service availability

## 🔄 Auto-Recovery Features

1. **Token Refresh**: Automatically refresh expiring tokens
2. **Re-authentication**: Retry failed auth attempts
3. **Fallback Methods**: Use alternative auth methods if primary fails
4. **Circuit Breaker**: Prevent auth storms on service outages

## 📝 Configuration

### Main Config (`~/.authmanager/config.yaml`)
```yaml
services:
  github:
    enabled: true
    auto_refresh: true
    refresh_before_expiry: 3600  # seconds
  
  flyio:
    enabled: true
    auto_refresh: false  # Fly tokens don't expire
  
  npm:
    enabled: true
    registries:
      - https://registry.npmjs.org/

polling:
  interval: 300  # Check every 5 minutes
  
logging:
  level: INFO
  file: ~/.authmanager/auth.log
```

## 🎯 Success Criteria

1. **Zero Manual Auth**: Developers never need to manually authenticate
2. **Universal Access**: Any project can use authenticated services
3. **High Availability**: 99.9% uptime for auth services
4. **Fast Recovery**: Re-auth within 30 seconds of failure
5. **Transparent Operation**: Works silently in background

## 📈 Benefits

1. **Developer Productivity**: No interruption for auth issues
2. **Security**: Centralized, encrypted credential management
3. **Consistency**: Same auth state across all projects
4. **Automation**: CI/CD pipelines work without manual setup
5. **Monitoring**: Real-time visibility of auth status

## 🚦 Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Test with pilot services (GitHub, Fly.io)
5. Expand to all services
6. Deploy system-wide