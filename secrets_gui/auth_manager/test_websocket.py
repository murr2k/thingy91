#!/usr/bin/env python3
"""
Test WebSocket server with generator functionality.
"""

import asyncio
import json
import websockets
import sys

async def test_websocket_connection():
    """Test WebSocket server operations."""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Test 1: List templates
            print("\n1. Testing list_templates...")
            request = {
                "id": "test1",
                "action": "list_templates"
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "response" and "templates" in data.get("data", {}):
                templates = data["data"]["templates"]
                print(f"   ✓ Found {len(templates)} templates")
                for template in templates:
                    print(f"     - {template['id']}: {template['name']}")
            else:
                print(f"   ✗ Failed: {data}")
            
            # Test 2: Get template fields
            print("\n2. Testing get_template_fields...")
            request = {
                "id": "test2",
                "action": "get_template_fields",
                "template_id": "cli_token"
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "response" and data.get("data"):
                fields = data["data"]
                if "error" not in fields:
                    print(f"   ✓ Got fields for template: {fields.get('name', 'Unknown')}")
                    required = [f['name'] for f in fields.get('required_fields', [])]
                    print(f"     Required: {', '.join(required)}")
                else:
                    print(f"   ✗ Error: {fields['error']}")
            else:
                print(f"   ✗ Failed: {data}")
            
            # Test 3: Create authenticator (dry run - won't save)
            print("\n3. Testing create_authenticator...")
            request = {
                "id": "test3",
                "action": "create_authenticator",
                "service_name": "WebSocket Test Service",
                "template_type": "api_key",
                "parameters": {
                    "api_endpoint": "https://api.websocket-test.com",
                    "api_key_header": "X-API-Key",
                    "credential_key": "test_api_key",
                    "verify_endpoint": "/v1/status"
                },
                "use_claude": False
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "response" and data.get("data"):
                result = data["data"]
                if result.get("success"):
                    print(f"   ✓ Authenticator created successfully")
                    print(f"     File: {result.get('file_path')}")
                    print(f"     Note: {result.get('message')}")
                else:
                    print(f"   ✗ Failed: {result.get('message')}")
            else:
                print(f"   ✗ Failed: {data}")
            
            # Test 4: Get status
            print("\n4. Testing get_status...")
            request = {
                "id": "test4",
                "action": "get_status"
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "response" and data.get("data"):
                status = data["data"]
                print(f"   ✓ Got status with {len(status.get('services', []))} services")
            else:
                print(f"   ✗ Failed: {data}")
            
            print("\n✅ All WebSocket tests completed!")
            
    except websockets.exceptions.ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server at ws://localhost:8765")
        print("   Make sure the WebSocket server is running:")
        print("   python3 websocket_server.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def cleanup_test_file():
    """Clean up test authenticator file if created."""
    import os
    from pathlib import Path
    
    test_file = Path("authenticators/websocket_test_service_auth.py")
    if test_file.exists():
        test_file.unlink()
        print(f"Cleaned up test file: {test_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Server Test Suite")
    print("=" * 60)
    
    # Run tests
    success = asyncio.run(test_websocket_connection())
    
    # Cleanup
    if success:
        asyncio.run(cleanup_test_file())
    
    print("=" * 60)
    sys.exit(0 if success else 1)