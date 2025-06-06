"""WebSocket support for real-time communication."""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

from .security_enhanced import verify_token
from .vector_enhanced import vector_manager
from .schemas_enhanced import Question

logger = logging.getLogger("chaxai.websocket")

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        """Accept and track a new connection."""
        await websocket.accept()
        
        # Track by tenant
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        
        # Track by user
        self.user_connections[user_id] = websocket
        
        logger.info(f"WebSocket connected: tenant={tenant_id}, user={user_id}")
    
    def disconnect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        """Remove a connection."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
        
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: tenant={tenant_id}, user={user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user."""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Broadcast message to all connections in a tenant."""
        if tenant_id in self.active_connections:
            for connection in self.active_connections[tenant_id]:
                await connection.send_json(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections."""
    tenant_id = None
    user_id = None
    
    try:
        # Wait for authentication message
        auth_data = await websocket.receive_json()
        
        if auth_data.get("type") != "auth":
            await websocket.close(code=1008)
            return
        
        # Verify token
        token = auth_data.get("token")
        if not token:
            await websocket.close(code=1008)
            return
        
        user = verify_token(token)
        if not user:
            await websocket.close(code=1008)
            return
        
        tenant_id = user.tenant_id
        user_id = user.user_id
        
        # Connect
        await manager.connect(websocket, tenant_id, user_id)
        
        # Send confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "tenant_id": tenant_id
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                # Process chat message
                question = Question(question=data.get("message", ""))
                
                # Send typing indicator
                await manager.broadcast_to_tenant(tenant_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "isTyping": True
                })
                
                # Get answer
                answer = await vector_manager.ask_question(
                    question,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "message": {
                        "content": answer.answer,
                        "sources": answer.sources,
                        "confidence": answer.confidence
                    }
                })
                
                # Stop typing indicator
                await manager.broadcast_to_tenant(tenant_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "isTyping": False
                })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if tenant_id and user_id:
            manager.disconnect(websocket, tenant_id, user_id)