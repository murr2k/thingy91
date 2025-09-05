#!/bin/bash
# NPM Registry Authentication Setup Script
# Uses token from Secrets Manager to authenticate npm CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════"
echo "   📦 NPM Registry Authentication Setup"
echo "════════════════════════════════════════════════════"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    echo ""
    echo "Install Node.js and npm from: https://nodejs.org/"
    exit 1
fi

# Function to get token from secrets manager
get_npm_token() {
    # Try environment variable first
    if [ -n "$NPM_AUTH_TOKEN" ]; then
        echo "$NPM_AUTH_TOKEN"
        return 0
    fi
    
    # Try to get from encrypted env file
    if [ -f ".env.npm.encrypted" ] || [ -f "../.env.npm.encrypted" ]; then
        echo -e "${YELLOW}Found encrypted NPM credentials${NC}"
        
        if [ -f "scripts/get_npm_token.py" ]; then
            python3 scripts/get_npm_token.py 2>/dev/null && return 0
        fi
    fi
    
    return 1
}

# Check current npm auth status
echo -e "${YELLOW}Checking current NPM authentication status...${NC}"
if npm whoami 2>/dev/null; then
    CURRENT_USER=$(npm whoami 2>/dev/null)
    echo -e "${GREEN}✓ NPM is already authenticated as: $CURRENT_USER${NC}"
    echo ""
    read -p "Do you want to re-authenticate? (y/N): " REAUTH
    if [[ ! "$REAUTH" =~ ^[Yy]$ ]]; then
        echo "Keeping existing authentication."
        exit 0
    fi
fi

# Get token
echo ""
echo -e "${YELLOW}Retrieving NPM token from Secrets Manager...${NC}"

TOKEN=$(get_npm_token)
if [ $? -ne 0 ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to retrieve NPM token${NC}"
    echo ""
    echo "Options:"
    echo "1. Set NPM_AUTH_TOKEN environment variable"
    echo "2. Configure token in Secrets Manager at http://localhost:5000"
    echo "3. Get token from: https://www.npmjs.com/settings/[username]/tokens"
    echo "4. Enter token manually now"
    echo ""
    read -p "Choose option (1-4): " OPTION
    
    case $OPTION in
        3)
            echo ""
            echo "Visit: https://www.npmjs.com/settings/[username]/tokens"
            echo "Create a token with 'Publish' scope"
            echo ""
            read -s -p "Enter NPM auth token: " TOKEN
            echo ""
            ;;
        4)
            read -s -p "Enter NPM auth token: " TOKEN
            echo ""
            ;;
        *)
            echo "Please configure the token and run this script again."
            exit 1
            ;;
    esac
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}No token provided${NC}"
        exit 1
    fi
fi

# Configure npm with token
echo -e "${YELLOW}Configuring NPM with auth token...${NC}"

# Set the auth token for npmjs registry
npm config set //registry.npmjs.org/:_authToken "$TOKEN"

# Verify authentication
if npm whoami &> /dev/null; then
    USER=$(npm whoami)
    echo ""
    echo -e "${GREEN}✓ Successfully authenticated NPM!${NC}"
    echo ""
    echo -e "Authenticated as: ${GREEN}$USER${NC}"
    
    # Show npm config
    echo ""
    echo "NPM Registry Configuration:"
    npm config get registry
    
    echo ""
    echo "════════════════════════════════════════════════════"
    echo -e "${GREEN}NPM is ready to use!${NC}"
    echo ""
    echo "Example commands:"
    echo "  npm publish              # Publish a package"
    echo "  npm whoami              # Check authentication"
    echo "  npm access ls-packages  # List your packages"
    echo "  npm team ls <org>       # List organization teams"
    echo ""
    echo "For more commands: npm --help"
    echo "════════════════════════════════════════════════════"
else
    echo -e "${RED}✗ Failed to authenticate NPM${NC}"
    echo "Please check your token and try again."
    exit 1
fi