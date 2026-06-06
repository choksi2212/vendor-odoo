"""
Unit tests for user endpoints.
"""

_VALID_USER = {
    "email": "me@example.com",
    "password": "StrongPass1!",
    "confirm_password": "StrongPass1!",
}


def _get_access_token(client) -> str:
    client.post("/auth/signup", json=_VALID_USER)
    resp = client.post("/auth/login", json={"email": _VALID_USER["email"], "password": _VALID_USER["password"]})
    return resp.json()["access_token"]


class TestGetMe:
    def test_authenticated_returns_user_profile(self, client):
        token = _get_access_token(client)
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == _VALID_USER["email"]
        assert "hashed_password" not in data
        assert "id" in data

    def test_unauthenticated_returns_403(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 403

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.core.config import settings

        expired_token = jwt.encode(
            {"sub": "00000000-0000-0000-0000-000000000000", "exp": datetime.now(timezone.utc) - timedelta(hours=1), "type": "access"},
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401
