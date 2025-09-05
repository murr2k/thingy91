#!/usr/bin/env python3
"""
Auth Manager Server - Host-side authentication server with WebSocket interface.
Runs the auth manager with a WebSocket server for GUI communication.
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthManager
from websocket_server import AuthWebSocketServer

class AuthServer:
    """Complete authentication server with WebSocket interface."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.auth_manager = None
        self.websocket_server = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("auth.server")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    async def start(self):
        """Start the authentication server."""
        try:
            self.logger.info("Starting Authentication Server...")
            
            # Initialize auth manager
            self.logger.info("Initializing Auth Manager...")
            self.auth_manager = AuthManager()
            
            # Initialize WebSocket server
            self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
            self.websocket_server = AuthWebSocketServer(
                self.auth_manager, 
                self.host, 
                self.port
            )
            
            self.running = True
            
            # Start the WebSocket server
            await self.websocket_server.start_server()
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    def stop(self):
        """Stop the authentication server."""
        self.running = False
        if self.websocket_server:
            self.websocket_server.stop()
        self.logger.info("Authentication Server stopped")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auth Manager Server")
    parser.add_argument("--host", default="0.0.0.0", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    
    args = parser.parse_args()
    
    server = AuthServer(args.host, args.port)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())