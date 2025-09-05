#!/usr/bin/env python3
"""
WebSocket server for auth manager GUI communication.
Provides real-time authentication status and control interface.
"""

import asyncio
import json
import logging
import websockets
import threading
from typing import Set, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthManager
from generator import AuthenticatorGenerator

class AuthWebSocketServer:
    """WebSocket server for auth manager communication."""
    
    def __init__(self, auth_manager: AuthManager, host: str = "0.0.0.0", port: int = 8765):
        self.auth_manager = auth_manager
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.logger = logging.getLogger("auth.websocket")
        self.running = False
        self.generator = AuthenticatorGenerator()
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection."""
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")
        
        # Don't send initial status - let client request it
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection."""
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if self.clients:
            disconnected = []
            for client in self.clients.copy():
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.append(client)
                except Exception as e:
                    self.logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.clients.discard(client)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        status = await loop.run_in_executor(None, self.auth_manager.get_status)
        return status
    
    async def authenticate_service(self, service_id: str) -> Dict[str, Any]:
        """Authenticate a specific service."""
        loop = asyncio.get_event_loop()
        
        def auth_task():
            authenticator = self.auth_manager.authenticators.get(service_id)
            if not authenticator:
                return {
                    "success": False,
                    "error": f"Service {service_id} not found",
                    "service": service_id
                }
            
            try:
                success = authenticator.authenticate()
                return {
                    "success": success,
                    "service": service_id,
                    "message": f"Authentication {'successful' if success else 'failed'} for {service_id}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "service": service_id
                }
        
        result = await loop.run_in_executor(None, auth_task)
        
        # Broadcast status update after authentication
        try:
            status = await self.get_status()
            await self.broadcast({
                "type": "status_update",
                "data": status
            })
        except Exception as e:
            self.logger.error(f"Error broadcasting status update: {e}")
        
        return result
    
    async def verify_service(self, service_id: str) -> Dict[str, Any]:
        """Verify authentication for a specific service."""
        loop = asyncio.get_event_loop()
        
        def verify_task():
            authenticator = self.auth_manager.authenticators.get(service_id)
            if not authenticator:
                return {
                    "success": False,
                    "error": f"Service {service_id} not found",
                    "service": service_id
                }
            
            try:
                authenticated = authenticator.verify_auth()
                return {
                    "success": True,
                    "authenticated": authenticated,
                    "service": service_id,
                    "message": f"{service_id} is {'authenticated' if authenticated else 'not authenticated'}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "service": service_id
                }
        
        result = await loop.run_in_executor(None, verify_task)
        
        # Broadcast status update after verification
        try:
            status = await self.get_status()
            await self.broadcast({
                "type": "status_update",
                "data": status
            })
        except Exception as e:
            self.logger.error(f"Error broadcasting status update: {e}")
        
        return result
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            action = data.get("action")
            service_id = data.get("service")
            
            response = {
                "id": data.get("id"),  # For request correlation
                "type": "response"
            }
            
            if action == "get_status":
                status = await self.get_status()
                response["data"] = status
                
            elif action == "authenticate" and service_id:
                result = await self.authenticate_service(service_id)
                response["data"] = result
                
            elif action == "verify" and service_id:
                result = await self.verify_service(service_id)
                response["data"] = result
                
            elif action == "refresh":
                status = await self.get_status()
                # Broadcast to all clients
                await self.broadcast({
                    "type": "status_update",
                    "data": status
                })
                response["data"] = {"success": True, "message": "Status refreshed"}
                
            elif action == "list_templates":
                templates = self.generator.list_templates()
                response["data"] = {"templates": templates}
                
            elif action == "get_template_fields":
                template_id = data.get("template_id")
                if template_id:
                    fields = self.generator.get_template_fields(template_id)
                    response["data"] = fields
                else:
                    response["data"] = {"error": "template_id required"}
                    
            elif action == "create_authenticator":
                service_name = data.get("service_name")
                template_type = data.get("template_type")
                parameters = data.get("parameters", {})
                use_claude = data.get("use_claude", False)
                
                if not service_name or not template_type:
                    response["data"] = {
                        "success": False,
                        "error": "service_name and template_type required"
                    }
                else:
                    # Generate authenticator
                    result = self.generator.generate_authenticator(
                        service_name,
                        template_type,
                        parameters,
                        use_claude
                    )
                    response["data"] = result
                    
                    # If successful, trigger auth manager reload
                    if result.get("success"):
                        self.logger.info(f"Created authenticator for {service_name}")
                        # Note: Auth manager would need to be reloaded to pick up new authenticator
                        response["data"]["requires_restart"] = True
                        
            elif action == "test_authenticator":
                service_id = data.get("service_id")
                if service_id:
                    result = self.generator.test_authenticator(service_id)
                    response["data"] = result
                else:
                    response["data"] = {"error": "service_id required"}
                
            else:
                response["data"] = {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
            
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"error": "Invalid JSON message"}
            }))
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"error": str(e)}
            }))
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a client connection."""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.running = True
        self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            self.logger.info("WebSocket server started successfully")
            
            # Keep the server running and periodically broadcast status
            while self.running:
                try:
                    await asyncio.sleep(30)  # Broadcast status every 30 seconds
                    if self.clients:
                        status = await self.get_status()
                        await self.broadcast({
                            "type": "status_update",
                            "data": status
                        })
                except Exception as e:
                    self.logger.error(f"Error in periodic status broadcast: {e}")
                    await asyncio.sleep(5)
    
    def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        self.logger.info("WebSocket server stopped")


def run_websocket_server(auth_manager: AuthManager, host: str = "0.0.0.0", port: int = 8765):
    """Run the WebSocket server in the current event loop."""
    server = AuthWebSocketServer(auth_manager, host, port)
    return asyncio.run(server.start_server())


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Run WebSocket server
    try:
        run_websocket_server(auth_manager)
    except KeyboardInterrupt:
        print("\nShutting down WebSocket server...")