"""
WebSocket endpoint for real-time notifications.

Clients connect with a JWT token as query parameter.
Once authenticated, they receive real-time notifications
pushed from the server whenever relevant events occur.

Usage from frontend:
    const ws = new WebSocket("ws://localhost:8000/api/ws/notifications?token=<jwt>");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // data.type === "notification"
        // data.data contains notification details
    };
"""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.websocket import ws_manager
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = "",
):
    """
    WebSocket endpoint for real-time notifications.
    
    Requires JWT token as query parameter for authentication.
    Connection is maintained until client disconnects or token expires.
    """
    # Authenticate via JWT token
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token.")
        return

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token.")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Invalid or expired token.")
        return

    # Accept connection and register
    await ws_manager.connect(user_id, websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to VendorBridge notifications."},
        })

        # Keep connection alive - listen for client messages (ping/pong)
        while True:
            data = await websocket.receive_text()
            # Handle ping from client
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error("WebSocket error for user %s: %s", user_id, e)
        ws_manager.disconnect(user_id, websocket)
