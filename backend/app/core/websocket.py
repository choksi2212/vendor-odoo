"""
WebSocket connection manager for real-time notifications.

Manages active WebSocket connections per user, enabling
instant notification delivery without polling.

Usage:
    # In a service layer after an event:
    from app.core.websocket import ws_manager
    await ws_manager.send_to_user(user_id, {
        "type": "notification",
        "data": {"title": "New RFQ", "message": "..."}
    })
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections grouped by user_id.
    
    Supports multiple connections per user (e.g., multiple browser tabs).
    Thread-safe for single-process deployment (uvicorn single worker).
    For multi-worker production, use Redis pub/sub as message broker.
    """

    def __init__(self):
        # user_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    @property
    def active_connections_count(self) -> int:
        """Total number of active connections across all users."""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def connected_users_count(self) -> int:
        """Number of unique connected users."""
        return len(self._connections)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept a WebSocket connection and register it for the user."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info(
            "WebSocket connected: user=%s total_connections=%d",
            user_id, self.active_connections_count,
        )

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection for the user."""
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
            except ValueError:
                pass
            # Clean up empty user entries
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(
            "WebSocket disconnected: user=%s total_connections=%d",
            user_id, self.active_connections_count,
        )

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """
        Send a message to all active connections for a specific user.
        
        Silently handles disconnected clients by removing them.
        """
        if user_id not in self._connections:
            return

        payload = json.dumps(message, default=str)
        disconnected = []

        for websocket in self._connections[user_id]:
            try:
                await websocket.send_text(payload)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected users."""
        payload = json.dumps(message, default=str)
        disconnected_pairs = []

        for user_id, connections in self._connections.items():
            for websocket in connections:
                try:
                    await websocket.send_text(payload)
                except Exception:
                    disconnected_pairs.append((user_id, websocket))

        for user_id, ws in disconnected_pairs:
            self.disconnect(user_id, ws)

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active WebSocket connections."""
        return user_id in self._connections and len(self._connections[user_id]) > 0


# Global singleton instance
ws_manager = ConnectionManager()
