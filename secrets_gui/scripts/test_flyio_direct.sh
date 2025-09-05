#!/bin/bash
# Direct test of Fly.io tokens using curl

echo "Testing Fly.io tokens directly..."
echo "================================"

# Extract the tokens from the Python script output
python3 -c "
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

SECRETS_FILE = '/home/murr2k/projects/thingy91/secrets_gui/data/secrets.json'
MASTER_KEY_FILE = '/home/murr2k/projects/thingy91/secrets_gui/data/.master_key'

def derive_key(master_key: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'stable_salt_v1',
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    return key

with open(MASTER_KEY_FILE, 'r') as f:
    master_key = f.read().strip()

key = derive_key(master_key)
fernet = Fernet(key)

with open(SECRETS_FILE, 'r') as f:
    encrypted_data = json.load(f)

if 'flyio' in encrypted_data:
    decrypted = fernet.decrypt(encrypted_data['flyio'].encode())
    creds = json.loads(decrypted)
    
    # Output tokens for bash to use
    for k, v in creds.items():
        if 'TOKEN' in k and v:
            print(f'{k}={v}')
" > /tmp/fly_tokens.env

# Source the tokens
source /tmp/fly_tokens.env

# Test each token if it exists
if [ ! -z "$FLYIO_ORG_TOKEN" ]; then
    echo ""
    echo "Testing Organization Token..."
    echo "Token format: ${FLYIO_ORG_TOKEN:0:20}..."
    
    # Check if token looks valid (should start with FlyV1 or similar)
    if [[ $FLYIO_ORG_TOKEN == FlyV1* ]]; then
        echo "Token format looks correct (FlyV1)"
        
        # Test with fly CLI
        FLY_API_TOKEN="$FLYIO_ORG_TOKEN" fly auth whoami 2>&1 | head -5
    else
        echo "Token format might be incorrect"
        echo "First 50 chars: ${FLYIO_ORG_TOKEN:0:50}"
    fi
fi

if [ ! -z "$FLYIO_ADMIN_TOKEN" ]; then
    echo ""
    echo "Testing Admin Token..."
    echo "Token format: ${FLYIO_ADMIN_TOKEN:0:20}..."
    
    if [[ $FLYIO_ADMIN_TOKEN == FlyV1* ]]; then
        echo "Token format looks correct (FlyV1)"
        FLY_API_TOKEN="$FLYIO_ADMIN_TOKEN" fly auth whoami 2>&1 | head -5
    else
        echo "Token format might be incorrect"
    fi
fi

# Clean up
rm -f /tmp/fly_tokens.env

echo ""
echo "================================"
echo "Test complete"