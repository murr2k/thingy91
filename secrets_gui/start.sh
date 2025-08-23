#!/bin/bash
# Secrets Manager GUI - Quick Start Script

set -e

echo "╔═══════════════════════════════════════╗"
echo "║   Secrets Manager GUI Launcher        ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade requirements
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set default credentials if not provided
if [ -z "$ADMIN_USERNAME" ]; then
    export ADMIN_USERNAME="admin"
    echo "ℹ Using default username: admin"
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    export ADMIN_PASSWORD="changeme"
    echo "⚠ Using default password: changeme"
    echo "  (Set ADMIN_PASSWORD environment variable for custom password)"
fi

# Generate secret key if not set
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "✓ Generated secure session key"
fi

# Check if port is available
PORT=${PORT:-5000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port $PORT is already in use"
    echo "Try: PORT=5001 ./start.sh"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════"
echo "Starting Secrets Manager GUI..."
echo "═══════════════════════════════════════"
echo ""
echo "📍 URL: http://localhost:$PORT"
echo "👤 Username: $ADMIN_USERNAME"
echo "🔑 Password: ${ADMIN_PASSWORD//?/*}"
echo ""
echo "Press Ctrl+C to stop"
echo "═══════════════════════════════════════"
echo ""

# Run the application
export FLASK_ENV=${FLASK_ENV:-development}
python3 app.py