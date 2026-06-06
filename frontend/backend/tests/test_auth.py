"""
Unit tests for authentication endpoints.
Requires a running PostgreSQL instance at the TEST_DATABASE_URL.
"""

_VALID_USER = {
    "email": "user@example.com",
    "password": "StrongPass1!",
    "confirm_password": "StrongPass1!",
}


def _signup(client, overrides: dict | None = None) -> None:
    payload = {**_VALID_USER, **(overrides or {})}
    client.post("/auth/signup", json=payload)


def _login(client, email: str = _VALID_USER["email"], password: str = _VALID_USER["password"]) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()


class TestSignup:
    def test_success_returns_201(self, client):
        resp = client.post("/auth/signup", json=_VALID_USER)
        assert resp.status_code == 201
        assert "message" in resp.json()

    def test_duplicate_email_returns_409(self, client):
        client.post("/auth/signup", json=_VALID_USER)
        resp = client.post("/auth/signup", json=_VALID_USER)
        assert resp.status_code == 409

    def test_weak_password_returns_422(self, client):
        resp = client.post("/auth/signup", json={**_VALID_USER, "password": "weak", "confirm_password": "weak"})
        assert resp.status_code == 422

    def test_password_mismatch_returns_422(self, client):
        resp = client.post(
            "/auth/signup",
            json={**_VALID_USER, "confirm_password": "DifferentPass1!"},
        )
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/auth/signup", json={**_VALID_USER, "email": "not-an-email"})
        assert resp.status_code == 422

    def test_response_never_contains_password(self, client):
        resp = client.post("/auth/signup", json=_VALID_USER)
        body = resp.text
        assert "StrongPass1!" not in body
        assert "hashed_password" not in body


class TestLogin:
    def test_success_returns_tokens(self, client):
        _signup(client)
        resp = client.post("/auth/login", json={"email": _VALID_USER["email"], "password": _VALID_USER["password"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client):
        _signup(client)
        resp = client.post("/auth/login", json={"email": _VALID_USER["email"], "password": "WrongPass1!"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials."

    def test_nonexistent_email_returns_401(self, client):
        resp = client.post("/auth/login", json={"email": "ghost@example.com", "password": "StrongPass1!"})
        assert resp.status_code == 401

    def test_account_locks_after_max_failures(self, client):
        _signup(client)
        for _ in range(5):
            client.post("/auth/login", json={"email": _VALID_USER["email"], "password": "WrongPass1!"})
        resp = client.post("/auth/login", json={"email": _VALID_USER["email"], "password": _VALID_USER["password"]})
        assert resp.status_code == 403

    def test_email_is_case_insensitive(self, client):
        _signup(client)
        resp = client.post("/auth/login", json={"email": _VALID_USER["email"].upper(), "password": _VALID_USER["password"]})
        assert resp.status_code == 200


class TestRefreshToken:
    def test_valid_refresh_token_returns_new_access_token(self, client):
        _signup(client)
        tokens = _login(client)
        resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_invalid_refresh_token_returns_401(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "fake-token"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_invalidates_refresh_token(self, client):
        _signup(client)
        tokens = _login(client)
        refresh_token = tokens["refresh_token"]

        logout_resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 200

        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401

    def test_logout_with_invalid_token_returns_200(self, client):
        resp = client.post("/auth/logout", json={"refresh_token": "nonexistent"})
        assert resp.status_code == 200


class TestForgotAndResetPassword:
    def test_forgot_password_always_returns_200(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
        assert resp.status_code == 200

    def test_reset_with_invalid_token_returns_400(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={"token": "fake", "password": "NewPass1!", "confirm_password": "NewPass1!"},
        )
        assert resp.status_code == 400
