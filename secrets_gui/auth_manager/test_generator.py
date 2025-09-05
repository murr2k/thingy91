#!/usr/bin/env python3
"""
Test script for authenticator generator functionality.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generator.generator import AuthenticatorGenerator

def test_template_listing():
    """Test listing available templates."""
    print("Testing template listing...")
    generator = AuthenticatorGenerator()
    templates = generator.list_templates()
    
    print(f"Found {len(templates)} templates:")
    for template in templates:
        print(f"  - {template['id']}: {template['name']}")
    print()
    return templates

def test_template_fields(template_id):
    """Test getting template fields."""
    print(f"Testing template fields for {template_id}...")
    generator = AuthenticatorGenerator()
    fields = generator.get_template_fields(template_id)
    
    print(f"Template: {fields['name']}")
    print(f"Description: {fields['description']}")
    
    # Extract field names from the list of field dicts
    required_names = [f['name'] for f in fields['required_fields']]
    optional_names = [f['name'] for f in fields['optional_fields']]
    
    print(f"Required fields: {', '.join(required_names)}")
    if optional_names:
        print(f"Optional fields: {', '.join(optional_names)}")
    print()
    return fields

def test_cli_token_generation():
    """Test generating a CLI token authenticator."""
    print("Testing CLI token authenticator generation...")
    generator = AuthenticatorGenerator()
    
    parameters = {
        "service_name": "Test CLI Service",
        "cli_command": "testcli",
        "token_env_var": "TEST_CLI_TOKEN",
        "credential_key": "test_token",
        "auth_command": "testcli auth login",
        "verify_command": "testcli status",
        "logout_command": "testcli auth logout",
        "update_shell_profile": True
    }
    
    result = generator.generate_authenticator(
        service_name="Test CLI Service",
        template_type="cli_token",
        parameters=parameters,
        use_claude=False
    )
    
    if result.get("success"):
        print("✓ Successfully generated CLI token authenticator")
        print(f"  File: {result['file_path']}")
        if 'validation' in result:
            print(f"  Validation: {result['validation']['valid']}")
            if result['validation'].get('warnings'):
                print(f"  Warnings: {result['validation']['warnings']}")
    else:
        error_msg = result.get('error') or result.get('message', 'Unknown error')
        print(f"✗ Failed to generate: {error_msg}")
    print()
    return result

def test_api_key_generation():
    """Test generating an API key authenticator."""
    print("Testing API key authenticator generation...")
    generator = AuthenticatorGenerator()
    
    parameters = {
        "service_name": "Test API Service",
        "api_endpoint": "https://api.test.com",
        "api_key_header": "X-API-Key",
        "credential_key": "api_key",
        "verify_endpoint": "/v1/user",
        "api_key_prefix": "Bearer ",
        "response_field": "authenticated"
    }
    
    result = generator.generate_authenticator(
        service_name="Test API Service",
        template_type="api_key",
        parameters=parameters,
        use_claude=False
    )
    
    if result.get("success"):
        print("✓ Successfully generated API key authenticator")
        print(f"  File: {result['file_path']}")
        if 'validation' in result:
            print(f"  Validation: {result['validation']['valid']}")
            if result['validation'].get('warnings'):
                print(f"  Warnings: {result['validation']['warnings']}")
    else:
        error_msg = result.get('error') or result.get('message', 'Unknown error')
        print(f"✗ Failed to generate: {error_msg}")
    print()
    return result

def test_config_file_generation():
    """Test generating a config file authenticator."""
    print("Testing config file authenticator generation...")
    generator = AuthenticatorGenerator()
    
    parameters = {
        "service_name": "Test Config Service",
        "config_path": "~/.test/config.json",
        "config_format": "json",
        "credential_key": "auth_token",
        "config_template": '{"auth": {"token": "{{ token }}"}}',
        "cli_command": "test-tool",
        "verify_cli_command": "test-tool status"
    }
    
    result = generator.generate_authenticator(
        service_name="Test Config Service",
        template_type="config_file",
        parameters=parameters,
        use_claude=False
    )
    
    if result.get("success"):
        print("✓ Successfully generated config file authenticator")
        print(f"  File: {result['file_path']}")
        if 'validation' in result:
            print(f"  Validation: {result['validation']['valid']}")
            if result['validation'].get('warnings'):
                print(f"  Warnings: {result['validation']['warnings']}")
    else:
        error_msg = result.get('error') or result.get('message', 'Unknown error')
        print(f"✗ Failed to generate: {error_msg}")
    print()
    return result

def cleanup_test_files():
    """Clean up generated test files."""
    print("Cleaning up test files...")
    test_files = [
        "authenticators/test_cli_service_auth.py",
        "authenticators/test_api_service_auth.py",
        "authenticators/test_config_service_auth.py"
    ]
    
    for file_path in test_files:
        full_path = Path(file_path)
        if full_path.exists():
            full_path.unlink()
            print(f"  Removed: {file_path}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Authenticator Generator Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test listing templates
        templates = test_template_listing()
        
        # Test getting fields for each template
        for template in templates:
            test_template_fields(template['id'])
        
        # Test generating authenticators
        cli_result = test_cli_token_generation()
        api_result = test_api_key_generation()
        config_result = test_config_file_generation()
        
        # Clean up test files
        cleanup_test_files()
        
        print("=" * 60)
        print("Test suite completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)