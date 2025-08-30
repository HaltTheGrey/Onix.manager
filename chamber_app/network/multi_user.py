"""
Multi-user support for collaborative chamber management.
Handles socket-based communication and data synchronization.
"""

import asyncio
import json
import logging
import socket
import threading
from datetime import datetime
from typing import Dict, Any, Set, Callable, Optional, Union
from dataclasses import dataclass

from ..utils import get_logger


@dataclass
class UserSession:
    """Represents a connected user session."""
    user_id: str
    username: str
    ip_address: str
    connected_at: datetime
    last_activity: datetime
    permissions: Set[str]


@dataclass
class SyncMessage:
    """Message for synchronizing data between users."""
    message_type: str  # chamber_update, state_change, work_request, etc.
    chamber_id: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: str


class MultiUserManager:
    """
    Manages multi-user connections and data synchronization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Network configuration
        self.port = config.get('SOCKET_PORT', 8765)
        self.multicast_group = config.get('MULTICAST_GROUP', '224.1.1.1')
        
        # Connection management
        self.active_sessions: Dict[str, UserSession] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.server = None
        self.running = False
        
        # Message queue for synchronization
        self.message_queue = asyncio.Queue()
        
        # Setup default message handlers
        self._setup_message_handlers()
        
        self.logger.info(f"MultiUserManager initialized on port {self.port}")
    
    def _setup_message_handlers(self):
        """Setup default message handlers."""
        self.message_handlers.update({
            'chamber_update': self._handle_chamber_update,
            'state_change': self._handle_state_change,
            'work_request': self._handle_work_request,
            'user_join': self._handle_user_join,
            'user_leave': self._handle_user_leave,
            'heartbeat': self._handle_heartbeat
        })
    
    def start(self):
        """Start the multi-user server."""
        if self.running:
            return
        
        self.running = True
        
        # Start server in background thread
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._start_server())
            except Exception as e:
                self.logger.error(f"Multi-user server error: {e}", exc_info=True)
            finally:
                loop.close()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        self.logger.info("Multi-user manager started")
    
    def stop(self):
        """Stop the multi-user server."""
        self.running = False
        
        if self.server:
            self.server.close()
          # Clear active sessions
        self.active_sessions.clear()
        
        self.logger.info("Multi-user manager stopped")
    
    async def _start_server(self):
        """Start the WebSocket server."""
        try:
            import websockets
            
            async def handle_client(websocket):
                try:
                    await self._handle_new_connection(websocket)
                except Exception as e:
                    self.logger.error(f"Client handling error: {e}")
            
            self.server = await websockets.serve(
                handle_client,
                "localhost", 
                self.port
            )
            
            self.logger.info(f"WebSocket server started on port {self.port}")
            
            # Process message queue
            await self._process_message_queue()
            
        except ImportError:
            self.logger.warning("websockets library not available, using fallback TCP server")
            await self._start_tcp_server()
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}", exc_info=True)
    
    async def _start_tcp_server(self):
        """Fallback TCP server if websockets not available."""
        try:
            server = await asyncio.start_server(
                self._handle_tcp_client,
                "localhost",
                self.port
            )
            
            self.logger.info(f"TCP server started on port {self.port}")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
    
    async def _handle_new_connection(self, websocket):
        """Handle a new WebSocket connection."""
        user_id = None
        try:
            # Wait for authentication message
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)
            
            if auth_data.get('type') != 'auth':
                await websocket.close(code=4001, reason="Authentication required")
                return
            
            # Create user session
            user_id = auth_data.get('user_id', f"user_{len(self.active_sessions)}")
            username = auth_data.get('username', user_id)
            
            session = UserSession(
                user_id=user_id,
                username=username,
                ip_address=websocket.remote_address[0],
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                permissions=set(auth_data.get('permissions', ['read']))
            )
            
            self.active_sessions[user_id] = session
            
            # Send welcome message
            welcome_msg = {
                'type': 'welcome',
                'user_id': user_id,
                'session_info': {
                    'connected_users': len(self.active_sessions),
                    'permissions': list(session.permissions)
                }
            }
            
            await websocket.send(json.dumps(welcome_msg))
            
            # Broadcast user join
            await self._broadcast_message({
                'type': 'user_join',
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.now().isoformat()
            }, exclude_user=user_id)
            
            # Handle messages from this client
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(user_id, data)
                    session.last_activity = datetime.now()
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON from user {user_id}")
                except Exception as e:
                    self.logger.error(f"Error handling message from user {user_id}: {e}")
        
        except asyncio.TimeoutError:
            self.logger.warning("Client authentication timeout")
        except Exception as e:
            self.logger.error(f"Connection handling error: {e}")
        finally:
            # Clean up user session
            if user_id and user_id in self.active_sessions:
                del self.active_sessions[user_id]
                
                # Broadcast user leave
                await self._broadcast_message({
                    'type': 'user_leave',
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }, exclude_user=user_id)
    
    async def _handle_tcp_client(self, reader, writer):
        """Handle TCP client connection (fallback)."""
        # Simplified TCP handling - in real implementation would be more robust
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Echo back for now - real implementation would process messages
                writer.write(data)
                await writer.drain()
        
        except Exception as e:
            self.logger.error(f"TCP client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _handle_client_message(self, user_id: str, message: Dict[str, Any]):
        """Handle a message from a client."""
        message_type = message.get('type')
        
        if message_type in self.message_handlers:
            handler = self.message_handlers[message_type]
            await handler(user_id, message)
        else:
            self.logger.warning(f"Unknown message type: {message_type}")
    
    async def _process_message_queue(self):
        """Process the message queue for broadcasting."""
        while self.running:
            try:
                # Wait for messages to broadcast
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._broadcast_message(message.data, exclude_user=message.user_id)
            except asyncio.TimeoutError:                continue
            except Exception as e:
                self.logger.error(f"Message queue processing error: {e}")
    
    async def _broadcast_message(self, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """Broadcast a message to all connected users."""
        if not self.active_sessions:
            return
        
        message_json = json.dumps(message)
        
        # In a real implementation, you'd send to actual WebSocket connections
        # For now, just log the broadcast
        recipients = [
            user_id for user_id in self.active_sessions.keys()
            if user_id != exclude_user
        ]
        
        if recipients:            self.logger.debug(f"Broadcasting message to {len(recipients)} users: {message.get('type', 'unknown')}")
    
    # Message handlers
    async def _handle_chamber_update(self, user_id: str, message: Dict[str, Any]):
        """Handle chamber update message."""
        chamber_id = message.get('chamber_id')
        update_data = message.get('data', {})
        
        # Validate required fields
        if not chamber_id:
            self.logger.warning(f"Chamber update message missing chamber_id from user {user_id}")
            return
        
        # Validate user permissions
        session = self.active_sessions.get(user_id)
        if not session or 'write' not in session.permissions:
            self.logger.warning(f"User {user_id} attempted chamber update without permissions")
            return
        
        # Queue message for broadcast
        sync_message = SyncMessage(
            message_type='chamber_update',
            chamber_id=chamber_id,
            data=update_data,
            timestamp=datetime.now(),            user_id=user_id
        )
        
        await self.message_queue.put(sync_message)
        self.logger.info(f"Chamber {chamber_id} updated by user {user_id}")
    
    async def _handle_state_change(self, user_id: str, message: Dict[str, Any]):
        """Handle chamber state change message."""
        chamber_id = message.get('chamber_id')
        new_state = message.get('new_state')
        reason = message.get('reason', '')
        
        # Validate required fields
        if not chamber_id:
            self.logger.warning(f"State change message missing chamber_id from user {user_id}")
            return
        
        # Validate and broadcast
        sync_message = SyncMessage(
            message_type='state_change',
            chamber_id=chamber_id,
            data={
                'new_state': new_state,
                'reason': reason,
                'user': self.active_sessions[user_id].username if user_id in self.active_sessions else user_id
            },
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        await self.message_queue.put(sync_message)
        self.logger.info(f"Chamber {chamber_id} state changed to {new_state} by user {user_id}")
    
    async def _handle_work_request(self, user_id: str, message: Dict[str, Any]):
        """Handle work request message."""
        # Similar to other handlers - validate and broadcast
        pass
    
    async def _handle_user_join(self, user_id: str, message: Dict[str, Any]):
        """Handle user join message."""
        # Already handled in connection setup
        pass
    
    async def _handle_user_leave(self, user_id: str, message: Dict[str, Any]):
        """Handle user leave message."""
        # Already handled in connection cleanup
        pass
    
    async def _handle_heartbeat(self, user_id: str, message: Dict[str, Any]):
        """Handle heartbeat message."""
        if user_id in self.active_sessions:
            self.active_sessions[user_id].last_activity = datetime.now()
    
    # Public API methods
    
    def get_active_users(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active users."""
        return {
            user_id: {
                'username': session.username,
                'connected_at': session.connected_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'permissions': list(session.permissions)
            }
            for user_id, session in self.active_sessions.items()        }
    
    def broadcast_chamber_update(self, chamber_id: str, update_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast a chamber update to all users."""
        sync_message = SyncMessage(
            message_type='chamber_update',
            chamber_id=chamber_id,
            data=update_data,
            timestamp=datetime.now(),
            user_id=user_id or 'system'
        )
        
        # Add to queue if event loop is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.message_queue.put(sync_message))
        except:
            pass
    
    def is_running(self) -> bool:
        """Check if the multi-user manager is running."""
        return self.running
    
    def get_user_count(self) -> int:
        """Get the number of active users."""
        return len(self.active_sessions)
