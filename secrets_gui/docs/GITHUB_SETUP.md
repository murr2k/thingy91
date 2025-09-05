# GitHub CLI Integration Guide

## Overview
The Secrets Manager now includes built-in support for GitHub CLI (`gh`) authentication, allowing you to securely store and use your GitHub Personal Access Token.

## Features

### 🐙 GitHub CLI Service
- **Service ID**: `github`
- **Icon**: 🐙
- **Required Credentials**:
  - `GITHUB_TOKEN` (required) - Personal Access Token
  - `GITHUB_USERNAME` (optional) - Your GitHub username
  - `GITHUB_EMAIL` (optional) - Your GitHub email

### Health Check
- Automatically verifies token validity via GitHub API
- Checks `/user` endpoint to confirm authentication
- Real-time status monitoring in dashboard

## Setup Instructions

### Step 1: Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)" or use fine-grained tokens
3. Select required scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Action workflows
   - `admin:org` (optional) - Manage organizations
   - `admin:public_key` (optional) - Manage SSH keys
   - `gist` (optional) - Create gists

4. Copy the generated token

### Step 2: Configure in Secrets Manager

1. Access the Secrets Manager GUI at http://localhost:5000
2. Login with your credentials (default: admin/changeme)
3. Find the "GitHub CLI" service card
4. Click to configure and enter:
   - `GITHUB_TOKEN`: Your personal access token
   - `GITHUB_USERNAME`: Your GitHub username (optional)
   - `GITHUB_EMAIL`: Your GitHub email (optional)
5. Save the configuration

### Step 3: Authenticate GitHub CLI

#### Option A: Using the Setup Script
```bash
# Run the automated setup script
./scripts/gh_setup.sh

# Or with Python helper
python3 scripts/get_github_token.py --setup
```

#### Option B: Manual Setup
```bash
# Export token from secrets manager
export GITHUB_TOKEN=$(python3 scripts/get_github_token.py)

# Authenticate gh CLI
echo $GITHUB_TOKEN | gh auth login --with-token

# Verify authentication
gh auth status
```

#### Option C: Direct from Container
```bash
# If running in Docker, exec into container
docker exec -it secrets-manager-gui bash

# Use the stored token
python3 scripts/get_github_token.py --setup
```

## Usage Examples

Once configured, you can use `gh` CLI normally:

### Repository Management
```bash
# List your repositories
gh repo list

# Create a new repository
gh repo create my-new-project --private

# Clone a repository
gh repo clone owner/repo
```

### Pull Requests
```bash
# List pull requests
gh pr list

# Create a pull request
gh pr create --title "Feature" --body "Description"

# Review a pull request
gh pr review 123 --approve
```

### Issues
```bash
# List issues
gh issue list

# Create an issue
gh issue create --title "Bug report" --body "Description"

# Close an issue
gh issue close 123
```

### Workflows
```bash
# List workflow runs
gh run list

# View workflow details
gh run view 123

# Trigger a workflow
gh workflow run build.yml
```

## Helper Scripts

### `scripts/gh_setup.sh`
Automated setup script that:
- Checks for gh CLI installation
- Retrieves token from secrets manager
- Configures gh authentication
- Validates the setup

### `scripts/get_github_token.py`
Python utility for token management:
```bash
# Setup gh CLI
python3 scripts/get_github_token.py --setup

# Display token (be careful!)
python3 scripts/get_github_token.py --show

# Export as environment variable
eval $(python3 scripts/get_github_token.py --export)

# Pipe to other commands
python3 scripts/get_github_token.py | gh auth login --with-token
```

## Security Notes

1. **Token Storage**: Tokens are encrypted using AES-256 encryption
2. **Access Control**: Requires authentication to access secrets
3. **Audit Logging**: All access attempts are logged
4. **Session Security**: Automatic timeout after inactivity
5. **Network Security**: Use HTTPS in production

## Troubleshooting

### Token Not Working
- Verify token has correct scopes
- Check token hasn't expired
- Ensure no typos or extra spaces

### Health Check Failing
- Token may be invalid or revoked
- Network connectivity issues
- GitHub API rate limiting

### gh CLI Not Found
Install GitHub CLI:
```bash
# Ubuntu/Debian
sudo apt install gh

# macOS
brew install gh

# Or download from
https://cli.github.com/
```

## API Integration

The service can also be accessed programmatically:

```python
import requests

# Get token via API (requires API key)
response = requests.get(
    'http://localhost:5000/api/service/github/secrets',
    headers={'X-API-Key': 'your-api-key'}
)
token = response.json()['GITHUB_TOKEN']

# Use with PyGithub
from github import Github
g = Github(token)
```

## Docker Integration

When using with Docker:

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    env_file:
      - .env.github.encrypted
```

## Best Practices

1. **Use Fine-Grained Tokens**: Limit scope to minimum required permissions
2. **Rotate Regularly**: Change tokens periodically
3. **Monitor Usage**: Check audit logs for unauthorized access
4. **Backup Securely**: Keep encrypted backups of credentials
5. **Use in CI/CD**: Integrate with GitHub Actions securely

## Support

For issues or questions:
- Check the dashboard for real-time status
- View logs: `docker logs secrets-manager-gui`
- Report issues in the project repository