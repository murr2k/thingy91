#!/bin/bash
# GitHub CLI Authentication Setup Script
# Uses token from Secrets Manager to authenticate gh CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════"
echo "   GitHub CLI Authentication Setup"
echo "════════════════════════════════════════════════════"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo ""
    echo "Install it using:"
    echo "  Ubuntu/Debian: sudo apt install gh"
    echo "  macOS: brew install gh"
    echo "  Or download from: https://cli.github.com/"
    exit 1
fi

# Function to get token from secrets manager
get_github_token() {
    # Try to get from environment first
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "$GITHUB_TOKEN"
        return 0
    fi
    
    # Try to get from encrypted env file
    if [ -f ".env.github.encrypted" ]; then
        echo -e "${YELLOW}Found encrypted GitHub credentials${NC}"
        read -s -p "Enter encryption password: " PASSWORD
        echo ""
        
        # Decrypt and extract token (simplified - in production use proper decryption)
        # This would need the actual decryption logic from the Python app
        echo -e "${RED}Manual decryption required. Please use the web UI to retrieve the token.${NC}"
        return 1
    fi
    
    # Try API if available
    if [ -n "$SECRETS_API_URL" ] && [ -n "$SECRETS_API_KEY" ]; then
        TOKEN=$(curl -s -H "X-API-Key: $SECRETS_API_KEY" \
                "$SECRETS_API_URL/api/service/github/secrets" | \
                jq -r '.GITHUB_TOKEN')
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            echo "$TOKEN"
            return 0
        fi
    fi
    
    return 1
}

# Check current gh auth status
echo -e "${YELLOW}Checking current GitHub CLI authentication status...${NC}"
if gh auth status &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI is already authenticated${NC}"
    gh auth status
    echo ""
    read -p "Do you want to re-authenticate? (y/N): " REAUTH
    if [[ ! "$REAUTH" =~ ^[Yy]$ ]]; then
        echo "Keeping existing authentication."
        exit 0
    fi
fi

# Get token
echo ""
echo -e "${YELLOW}Retrieving GitHub token from Secrets Manager...${NC}"

TOKEN=$(get_github_token)
if [ $? -ne 0 ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to retrieve GitHub token${NC}"
    echo ""
    echo "Options:"
    echo "1. Set GITHUB_TOKEN environment variable"
    echo "2. Configure token in the Secrets Manager web UI at http://localhost:5000"
    echo "3. Enter token manually now"
    echo ""
    read -p "Choose option (1-3): " OPTION
    
    case $OPTION in
        3)
            read -s -p "Enter GitHub Personal Access Token: " TOKEN
            echo ""
            if [ -z "$TOKEN" ]; then
                echo -e "${RED}No token provided${NC}"
                exit 1
            fi
            ;;
        *)
            echo "Please configure the token and run this script again."
            exit 1
            ;;
    esac
fi

# Authenticate with gh CLI
echo -e "${YELLOW}Authenticating GitHub CLI...${NC}"
echo "$TOKEN" | gh auth login --with-token

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Successfully authenticated GitHub CLI!${NC}"
    echo ""
    
    # Show auth status
    gh auth status
    
    echo ""
    echo "════════════════════════════════════════════════════"
    echo -e "${GREEN}GitHub CLI is ready to use!${NC}"
    echo ""
    echo "Example commands:"
    echo "  gh repo list                    # List your repositories"
    echo "  gh pr list                       # List pull requests"
    echo "  gh issue list                    # List issues"
    echo "  gh repo create my-new-repo      # Create a new repository"
    echo ""
    echo "For more commands: gh --help"
    echo "════════════════════════════════════════════════════"
else
    echo -e "${RED}✗ Failed to authenticate GitHub CLI${NC}"
    echo "Please check your token and try again."
    exit 1
fi