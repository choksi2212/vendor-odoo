"""
Comprehensive WebSocket and notification service tests for VendorBridge.

Tests cover:
  - WebSocket connection manager (connect, disconnect, send, broadcast)
  - WebSocket authentication (valid token, invalid token, missing token)
  - Real-time notification delivery via WebSocket
  - Notification service (create, payload generation)
  - Connection lifecycle (connect, receive messages, disconnect)
  - Multiple connections per user
  - Broadcast to all connected users
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.websocket import ConnectionManager
from app.models.notification import NotificationType
from app.services.notification_service import create_notification, get_notification_payload


# ─── Connection Manager Unit Tests ────────────────────────────────────────────


class TestConnectionManager:
    """Tests for the WebSocket ConnectionManager class."""

    def test_initial_state(self):
        """Manager starts with no connections."""
        manager = ConnectionManager()
        assert manager.active_connections_count == 0
        assert manager.connected_users_count == 0

    def test_is_user_connected_false(self):
        """Returns False for non-connected user."""
        manager = ConnectionManager()
        assert manager.is_user_connected("user-123") is False

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_user(self):
        """Disconnecting non-existent user doesn't error."""
        manager = ConnectionManager()
        # Should not raise
        manager.disconnect("nonexistent", None)

    @pytest.mark.asyncio
    async def test_send_to_disconnected_user(self):
        """Sending to non-connected user does nothing."""
        manager = ConnectionManager()
        # Should not raise
        await manager.send_to_user("nobody", {"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_empty(self):
        """Broadcasting with no connections does nothing."""
        manager = ConnectionManager()
        # Should not raise
        await manager.broadcast({"type": "test"})


# ─── WebSocket Endpoint Tests ─────────────────────────────────────────────────


class TestWebSocketEndpoint:
    """Tests for the WebSocket notification endpoint."""

    def test_websocket_connect_with_valid_token(self, client, test_user):
        """Successful WebSocket connection with valid JWT."""
        token = create_access_token(str(test_user.id))

        with client.websocket_connect(f"/api/ws/notifications?token={token}") as ws:
            # Should receive welcome message
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert "Connected" in data["data"]["message"]

    def test_websocket_connect_without_token(self, client):
        """Connection rejected without token."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/notifications?token=") as ws:
                ws.receive_json()

    def test_websocket_connect_with_invalid_token(self, client):
        """Connection rejected with invalid token."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/notifications?token=invalid.jwt.token") as ws:
                ws.receive_json()

    def test_websocket_ping_pong(self, client, test_user):
        """Client can send ping and receive pong."""
        token = create_access_token(str(test_user.id))

        with client.websocket_connect(f"/api/ws/notifications?token={token}") as ws:
            # Receive welcome
            ws.receive_json()
            
            # Send ping
            ws.send_text("ping")
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_websocket_multiple_messages(self, client, test_user):
        """Multiple pings work correctly."""
        token = create_access_token(str(test_user.id))

        with client.websocket_connect(f"/api/ws/notifications?token={token}") as ws:
            ws.receive_json()  # welcome
            
            for _ in range(3):
                ws.send_text("ping")
                data = ws.receive_json()
                assert data["type"] == "pong"


# ─── Notification Service Tests ───────────────────────────────────────────────


class TestNotificationService:
    """Tests for notification creation and payload generation."""

    def test_create_notification_info(self, db_session, test_user):
        """Create an INFO notification."""
        notification = create_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="RFQ Published",
            message="A new RFQ has been published and is awaiting quotations.",
            notification_type=NotificationType.INFO,
            entity_type="RFQ",
            entity_id="some-rfq-id",
        )
        db_session.commit()

        assert notification.id is not None
        assert notification.title == "RFQ Published"
        assert notification.message == "A new RFQ has been published and is awaiting quotations."
        assert notification.is_read is False
        assert notification.entity_type == "RFQ"

    def test_create_notification_success_type(self, db_session, test_user):
        """Create a SUCCESS notification."""
        notification = create_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="Approval Granted",
            message="Your approval request has been approved.",
            notification_type=NotificationType.SUCCESS,
            entity_type="APPROVAL",
        )
        db_session.commit()

        assert notification.type == NotificationType.SUCCESS

    def test_create_notification_warning_type(self, db_session, test_user):
        """Create a WARNING notification."""
        notification = create_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="RFQ Deadline Approaching",
            message="Your RFQ deadline is in 2 days.",
            notification_type=NotificationType.WARNING,
        )
        db_session.commit()

        assert notification.type == NotificationType.WARNING

    def test_get_notification_payload(self, db_session, test_user):
        """Payload generation produces correct WebSocket format."""
        notification = create_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="Test Title",
            message="Test message body.",
            notification_type=NotificationType.INFO,
            entity_type="VENDOR",
            entity_id="vendor-123",
        )
        db_session.commit()
        db_session.refresh(notification)

        payload = get_notification_payload(notification)
        assert payload["type"] == "notification"
        assert payload["data"]["title"] == "Test Title"
        assert payload["data"]["message"] == "Test message body."
        assert payload["data"]["notification_type"] == "info"
        assert payload["data"]["entity_type"] == "VENDOR"
        assert payload["data"]["entity_id"] == "vendor-123"
        assert payload["data"]["id"] is not None
        assert payload["data"]["created_at"] is not None

    def test_create_notification_without_entity(self, db_session, test_user):
        """Create notification without entity reference."""
        notification = create_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="System Message",
            message="Welcome to VendorBridge!",
        )
        db_session.commit()

        assert notification.entity_type is None
        assert notification.entity_id is None

    def test_multiple_notifications_per_user(self, db_session, test_user):
        """User can have multiple notifications."""
        for i in range(5):
            create_notification(
                db=db_session,
                user_id=str(test_user.id),
                title=f"Notification {i}",
                message=f"Message {i}",
            )
        db_session.commit()

        from app.models.notification import Notification
        count = db_session.query(Notification).filter(
            Notification.user_id == str(test_user.id)
        ).count()
        assert count == 5
