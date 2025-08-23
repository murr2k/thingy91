# Secrets Management Quick Start for WSL

Since you're using WSL (Windows Subsystem for Linux), the system keyring is not available. Instead, we'll use encrypted file storage which is equally secure.

## Quick Setup (Option 1 - Encrypted File)

### 1. Store Your Secrets

Run the interactive setup:
```bash
python3 scripts/secrets_manager.py setup
```

Or manually create encrypted storage:
```bash
python3 scripts/secrets_manager.py encrypt
```

You'll be prompted to:
1. Create an encryption password (remember this!)
2. Enter each secret value:
   - `ONOMONDO_API_KEY`: Your Onomondo API key
   - `ONOMONDO_IMSI`: Device IMSI
   - `ONOMONDO_ICCID`: Device ICCID
   - `ONOMONDO_KI`: Authentication key
   - `ONOMONDO_OPC`: Operator key
   - `SOFTSIM_PROFILE_ID`: Profile ID (optional)

This creates:
- `.env.encrypted` - Your encrypted secrets (safe to backup)
- `~/.config/thingy91/encryption.key` - Your encryption key (keep secure!)

### 2. Use Your Secrets

#### Load to Environment (Recommended)
```bash
# Load secrets to current shell session
python3 scripts/secrets_manager.py decrypt
# This sets environment variables for the current session
```

#### Export to Script
```bash
# Create a source-able script
python3 scripts/secrets_manager.py export
# This creates load_secrets.sh

# Use it:
source load_secrets.sh
```

### 3. Provision Device

With secrets loaded:
```bash
# Secrets are now in environment
python3 scripts/provision_softsim.py /dev/ttyACM0 \
  --profile profiles/example_onomondo_profile.json \
  --activate
```

Or use secure provisioning that prompts for secrets:
```bash
python3 scripts/secure_provision.py /dev/ttyACM0
```

## Alternative: Direct Environment Variables

If you prefer, you can set environment variables directly:

```bash
export ONOMONDO_API_KEY="your-api-key-here"
export ONOMONDO_IMSI="your-imsi"
export ONOMONDO_ICCID="your-iccid"
export ONOMONDO_KI="your-ki"
export ONOMONDO_OPC="your-opc"
```

## Security Notes

### What's Safe
✅ `.env.encrypted` - Encrypted with AES-256, safe to backup
✅ Encryption password - Only you know it
✅ Environment variables - Only exist in memory

### What to Protect
⚠️ `~/.config/thingy91/encryption.key` - Contains derived key
⚠️ `load_secrets.sh` - Contains plaintext (delete after use)
⚠️ Never commit actual secret values

### Best Practices
1. Use a strong encryption password
2. Don't share the encryption key file
3. Delete `load_secrets.sh` after sourcing
4. Clear shell history if you typed secrets:
   ```bash
   history -c
   ```

## Troubleshooting

### "cryptography not available"
```bash
pip3 install cryptography
```

### "keyring not available"
This is normal in WSL. The script automatically uses encrypted file storage.

### Lost encryption password
Unfortunately, you'll need to re-enter all secrets. The encryption is secure and cannot be bypassed.

### Permission denied on .env.encrypted
```bash
chmod 600 .env.encrypted
```

## For GitHub Actions

Set repository secrets at:
https://github.com/murr2k/thingy91/settings/secrets/actions

Or use the helper script:
```bash
python3 scripts/secrets_manager.py github
./set_github_secrets.sh
```

## Quick Commands Reference

```bash
# First time setup
python3 scripts/secrets_manager.py setup

# Load secrets to environment
python3 scripts/secrets_manager.py decrypt

# Verify secrets are loaded
python3 scripts/secrets_manager.py verify

# Update a single secret
python3 scripts/secrets_manager.py encrypt  # Re-enter all

# Export for team member
# Share .env.encrypted (safe) + password (secure channel)
# They run: python3 scripts/secrets_manager.py decrypt
```