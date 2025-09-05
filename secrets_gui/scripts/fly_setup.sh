#!/bin/bash
# Fly.io CLI Authentication Setup Script
# Uses token from Secrets Manager to authenticate flyctl

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════"
echo "   🚀 Fly.io CLI Authentication Setup"
echo "════════════════════════════════════════════════════"
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null && ! command -v fly &> /dev/null; then
    echo -e "${RED}Error: Fly.io CLI (flyctl) is not installed${NC}"
    echo ""
    echo "Install it using:"
    echo "  curl -L https://fly.io/install.sh | sh"
    echo "  Or: brew install flyctl (macOS)"
    echo "  Or download from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Use fly or flyctl depending on what's available
FLY_CMD="fly"
if ! command -v fly &> /dev/null; then
    FLY_CMD="flyctl"
fi

# Function to get token from secrets manager
get_fly_token() {
    # Try to get from environment first
    if [ -n "$FLY_API_TOKEN" ]; then
        echo "$FLY_API_TOKEN"
        return 0
    fi
    
    # Try to get from encrypted env file
    if [ -f ".env.flyio.encrypted" ]; then
        echo -e "${YELLOW}Found encrypted Fly.io credentials${NC}"
        read -s -p "Enter encryption password: " PASSWORD
        echo ""
        
        # Call Python script to decrypt
        if [ -f "scripts/get_fly_token.py" ]; then
            TOKEN=$(python3 scripts/get_fly_token.py --password "$PASSWORD" 2>/dev/null)
            if [ -n "$TOKEN" ]; then
                echo "$TOKEN"
                return 0
            fi
        fi
        
        echo -e "${RED}Failed to decrypt credentials${NC}"
        return 1
    fi
    
    # Try API if available
    if [ -n "$SECRETS_API_URL" ] && [ -n "$SECRETS_API_KEY" ]; then
        TOKEN=$(curl -s -H "X-API-Key: $SECRETS_API_KEY" \
                "$SECRETS_API_URL/api/service/flyio/secrets" | \
                jq -r '.FLY_API_TOKEN')
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            echo "$TOKEN"
            return 0
        fi
    fi
    
    return 1
}

# Check current fly auth status
echo -e "${YELLOW}Checking current Fly.io authentication status...${NC}"
if $FLY_CMD auth whoami &> /dev/null; then
    echo -e "${GREEN}✓ Fly.io CLI is already authenticated${NC}"
    echo ""
    $FLY_CMD auth whoami
    echo ""
    read -p "Do you want to re-authenticate? (y/N): " REAUTH
    if [[ ! "$REAUTH" =~ ^[Yy]$ ]]; then
        echo "Keeping existing authentication."
        
        # Show current apps
        echo ""
        echo -e "${BLUE}Your Fly.io apps:${NC}"
        $FLY_CMD apps list
        exit 0
    fi
fi

# Get token
echo ""
echo -e "${YELLOW}Retrieving Fly.io token from Secrets Manager...${NC}"

TOKEN=$(get_fly_token)
if [ $? -ne 0 ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to retrieve Fly.io token${NC}"
    echo ""
    echo "Options:"
    echo "1. Set FLY_API_TOKEN environment variable"
    echo "2. Configure token in the Secrets Manager web UI at http://localhost:5000"
    echo "3. Get token from: fly auth token (if already logged in elsewhere)"
    echo "4. Enter token manually now"
    echo ""
    read -p "Choose option (1-4): " OPTION
    
    case $OPTION in
        3)
            echo ""
            echo "Run this command on a machine where you're logged in:"
            echo -e "${BLUE}fly auth token${NC}"
            echo ""
            read -s -p "Enter the token here: " TOKEN
            echo ""
            ;;
        4)
            read -s -p "Enter Fly.io API Token: " TOKEN
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

# Create auth config directory if it doesn't exist
FLY_CONFIG_DIR="$HOME/.fly"
mkdir -p "$FLY_CONFIG_DIR"

# Authenticate with flyctl
echo -e "${YELLOW}Authenticating Fly.io CLI...${NC}"

# Method 1: Try using the access-token flag (newer versions)
if $FLY_CMD auth token "$TOKEN" &> /dev/null; then
    echo -e "${GREEN}✓ Token set successfully${NC}"
elif echo "$TOKEN" | $FLY_CMD auth login --access-token "$TOKEN" &> /dev/null; then
    echo -e "${GREEN}✓ Authenticated successfully${NC}"
else
    # Method 2: Direct config file creation (fallback)
    echo -e "${YELLOW}Using direct configuration method...${NC}"
    cat > "$FLY_CONFIG_DIR/config.yml" <<EOF
access_token: $TOKEN
EOF
    chmod 600 "$FLY_CONFIG_DIR/config.yml"
fi

# Verify authentication
if $FLY_CMD auth whoami &> /dev/null; then
    echo ""
    echo -e "${GREEN}✓ Successfully authenticated Fly.io CLI!${NC}"
    echo ""
    
    # Show auth status
    echo -e "${BLUE}Authenticated as:${NC}"
    $FLY_CMD auth whoami
    
    echo ""
    echo -e "${BLUE}Your organizations:${NC}"
    $FLY_CMD orgs list 2>/dev/null || echo "No organizations found"
    
    echo ""
    echo -e "${BLUE}Your apps:${NC}"
    $FLY_CMD apps list 2>/dev/null || echo "No apps found"
    
    echo ""
    echo "════════════════════════════════════════════════════"
    echo -e "${GREEN}Fly.io CLI is ready to use!${NC}"
    echo ""
    echo "Example commands:"
    echo "  fly apps list              # List your applications"
    echo "  fly status                 # Show app status"
    echo "  fly deploy                 # Deploy an application"
    echo "  fly logs                   # View application logs"
    echo "  fly ssh console           # SSH into your app"
    echo "  fly launch                # Launch a new app"
    echo ""
    echo "For more commands: fly --help"
    echo "════════════════════════════════════════════════════"
else
    echo -e "${RED}✗ Failed to authenticate Fly.io CLI${NC}"
    echo "Please check your token and try again."
    echo ""
    echo "To get a new token:"
    echo "1. Visit https://fly.io/user/personal_access_tokens"
    echo "2. Create a new token"
    echo "3. Save it in the Secrets Manager"
    exit 1
fi