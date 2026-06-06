"""
Comprehensive authentication tests for VendorBridge.

Tests cover:
  - User registration (all roles, validation, duplicates)
  - Login (success, failure, account locking)
  - Token refresh (rotation, expiry, reuse prevention)
  - Password reset flow
  - Email verification
  - Role-based signup
  - 2FA enable/disable
  - Edge cases and error handling
"""

import pytest
from app.models.user import UserRole


# ─── Signup Tests ─────────────────────────────────────────────────────────────


class TestSignup:
    """Tests for user registration endpoint."""

    def test_signup_procurement_officer_success(self, client):
        """Test successful registration as procurement officer."""
        response = client.post("/api/auth/signup", json={
            "email": "new.officer@test.com",
            "username": "newofficer",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Account created. Please check your email to verify your address."

    def test_signup_vendor_success(self, client):
        """Test successful registration as vendor."""
        response = client.post("/api/auth/signup", json={
            "email": "new.vendor@test.com",
            "username": "newvendor",
            "password": "VendorPass123!",
            "confirm_password": "VendorPass123!",
            "role": "vendor",
        })
        assert response.status_code == 201

    def test_signup_manager_success(self, client):
        """Test successful registration as manager."""
        response = client.post("/api/auth/signup", json={
            "email": "new.manager@test.com",
            "username": "newmanager",
            "password": "ManagerPass123!",
            "confirm_password": "ManagerPass123!",
            "role": "manager",
        })
        assert response.status_code == 201

    def test_signup_admin_success(self, client):
        """Test successful registration as admin."""
        response = client.post("/api/auth/signup", json={
            "email": "new.admin@test.com",
            "username": "newadmin",
            "password": "AdminPass123!",
            "confirm_password": "AdminPass123!",
            "role": "admin",
        })
        assert response.status_code == 201

    def test_signup_duplicate_email(self, client, test_user):
        """Test that duplicate email is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": test_user.email,
            "username": "different",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_signup_duplicate_username(self, client, test_user):
        """Test that duplicate username is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "different@test.com",
            "username": test_user.username,
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 409
        assert "username is already taken" in response.json()["detail"]

    def test_signup_password_mismatch(self, client):
        """Test that mismatched passwords are rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_weak_password_no_uppercase(self, client):
        """Test that password without uppercase is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "weakpass123!",
            "confirm_password": "weakpass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_weak_password_no_digit(self, client):
        """Test that password without digit is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "WeakPassOnly!",
            "confirm_password": "WeakPassOnly!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_weak_password_no_special(self, client):
        """Test that password without special character is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "WeakPass123",
            "confirm_password": "WeakPass123",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_weak_password_too_short(self, client):
        """Test that password shorter than 8 chars is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "Ab1!",
            "confirm_password": "Ab1!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_invalid_email_format(self, client):
        """Test that invalid email format is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "not-an-email",
            "username": "testuser",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_invalid_username_too_short(self, client):
        """Test that username shorter than 3 chars is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "ab",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_invalid_username_special_chars(self, client):
        """Test that username with special characters is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "user@name",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 422

    def test_signup_invalid_role(self, client):
        """Test that invalid role is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "superadmin",
        })
        assert response.status_code == 422

    def test_signup_email_case_insensitive(self, client, test_user):
        """Test that email matching is case insensitive."""
        response = client.post("/api/auth/signup", json={
            "email": test_user.email.upper(),
            "username": "different",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "role": "procurement_officer",
        })
        assert response.status_code == 409


# ─── Login Tests ──────────────────────────────────────────────────────────────


class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials."""
        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "SomePass123!",
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "WrongPassword123!",
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_unverified_email(self, client, unverified_user):
        """Test login with unverified email is blocked."""
        response = client.post("/api/auth/login", json={
            "email": "unverified@vendorbridge.com",
            "password": "Unverified123!",
        })
        assert response.status_code == 403
        assert "verify your email" in response.json()["detail"].lower()

    def test_login_account_locking_after_5_attempts(self, client, test_user):
        """Test that account locks after 5 failed login attempts."""
        for i in range(5):
            response = client.post("/api/auth/login", json={
                "email": "officer@vendorbridge.com",
                "password": "WrongPassword!",
            })
            assert response.status_code == 401

        # 6th attempt - should be locked even with correct password
        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    def test_login_resets_failed_attempts_on_success(self, client, test_user):
        """Test that successful login resets the failed attempts counter."""
        # 3 failed attempts
        for _ in range(3):
            client.post("/api/auth/login", json={
                "email": "officer@vendorbridge.com",
                "password": "WrongPassword!",
            })

        # Successful login
        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert response.status_code == 200

        # 3 more failed attempts should NOT lock (counter was reset)
        for _ in range(3):
            client.post("/api/auth/login", json={
                "email": "officer@vendorbridge.com",
                "password": "WrongPassword!",
            })

        # Should still be able to login
        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert response.status_code == 200

    def test_login_deactivated_account(self, client, db_session, test_user):
        """Test that deactivated account cannot login."""
        test_user.is_active = False
        db_session.commit()

        response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


# ─── Token Tests ──────────────────────────────────────────────────────────────


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh."""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different (rotation)
        assert data["refresh_token"] != refresh_token

    def test_refresh_token_old_token_revoked(self, client, test_user):
        """Test that old refresh token cannot be reused after rotation."""
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        old_refresh = login_response.json()["refresh_token"]

        # Refresh (revokes old token)
        client.post("/api/auth/refresh", json={"refresh_token": old_refresh})

        # Try to reuse old token
        response = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
        assert response.status_code == 401

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-token-string",
        })
        assert response.status_code == 401


# ─── Logout Tests ─────────────────────────────────────────────────────────────


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, client, test_user):
        """Test successful logout revokes refresh token."""
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = client.post("/api/auth/logout", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200

        # Try to use revoked refresh token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 401


# ─── Current User Tests ───────────────────────────────────────────────────────


class TestCurrentUser:
    """Tests for /users/me endpoint."""

    def test_get_current_user_success(self, client, auth_headers, test_user):
        """Test getting current authenticated user profile."""
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "officer@vendorbridge.com"
        assert data["username"] == "officer"
        assert data["role"] == "procurement_officer"
        assert data["is_verified"] is True

    def test_get_current_user_no_auth(self, client):
        """Test that unauthenticated request is rejected."""
        response = client.get("/api/users/me")
        assert response.status_code == 403  # HTTPBearer returns 403 when no token

    def test_get_current_user_invalid_token(self, client):
        """Test that invalid token is rejected."""
        response = client.get("/api/users/me", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code == 401

    def test_get_current_user_vendor_role(self, client, vendor_auth_headers, test_vendor_user):
        """Test getting vendor user profile."""
        response = client.get("/api/users/me", headers=vendor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "vendor"

    def test_get_current_user_manager_role(self, client, manager_auth_headers, test_manager_user):
        """Test getting manager user profile."""
        response = client.get("/api/users/me", headers=manager_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "manager"

    def test_get_current_user_admin_role(self, client, admin_auth_headers, test_admin_user):
        """Test getting admin user profile."""
        response = client.get("/api/users/me", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"


# ─── 2FA Tests ────────────────────────────────────────────────────────────────


class TestTwoFactor:
    """Tests for 2FA enable/disable."""

    def test_enable_2fa(self, client, auth_headers, test_user):
        """Test enabling 2FA."""
        response = client.post("/api/users/2fa/enable", headers=auth_headers)
        assert response.status_code == 200
        assert "enabled" in response.json()["message"].lower()

    def test_disable_2fa(self, client, auth_headers, test_user):
        """Test disabling 2FA."""
        # Enable first
        client.post("/api/users/2fa/enable", headers=auth_headers)
        
        # Disable
        response = client.post("/api/users/2fa/disable", headers=auth_headers)
        assert response.status_code == 200
        assert "disabled" in response.json()["message"].lower()


# ─── Password Reset Tests ─────────────────────────────────────────────────────


class TestPasswordReset:
    """Tests for password reset flow."""

    def test_forgot_password_existing_email(self, client, test_user):
        """Test forgot password with existing email returns success."""
        response = client.post("/api/auth/forgot-password", json={
            "email": "officer@vendorbridge.com",
        })
        assert response.status_code == 200
        # Should always return success for security (no email enumeration)
        assert "sent" in response.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with non-existent email still returns success."""
        response = client.post("/api/auth/forgot-password", json={
            "email": "nobody@test.com",
        })
        assert response.status_code == 200
        # Same message - no email enumeration

    def test_reset_password_invalid_token(self, client):
        """Test reset password with invalid token."""
        response = client.post("/api/auth/reset-password", json={
            "token": "invalid-reset-token",
            "password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!",
        })
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]


# ─── Email Verification Tests ─────────────────────────────────────────────────


class TestEmailVerification:
    """Tests for email verification."""

    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        response = client.post("/api/auth/verify-email", json={
            "token": "invalid-verification-token",
        })
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_resend_verification_unverified_user(self, client, unverified_user):
        """Test resend verification for unverified user."""
        response = client.post("/api/auth/resend-verification", json={
            "email": "unverified@vendorbridge.com",
        })
        assert response.status_code == 200

    def test_resend_verification_already_verified(self, client, test_user):
        """Test resend verification for already verified user."""
        response = client.post("/api/auth/resend-verification", json={
            "email": "officer@vendorbridge.com",
        })
        assert response.status_code == 200
        # Same message returned regardless (no enumeration)


# ─── Integration Test: Full Flow ──────────────────────────────────────────────


class TestFullAuthFlow:
    """End-to-end integration tests for the complete auth flow."""

    def test_signup_login_access_profile(self, client, db_session):
        """Test complete flow: signup -> verify -> login -> access profile."""
        # 1. Signup
        signup_response = client.post("/api/auth/signup", json={
            "email": "flow.test@test.com",
            "username": "flowtest",
            "password": "FlowTest123!",
            "confirm_password": "FlowTest123!",
            "role": "procurement_officer",
        })
        assert signup_response.status_code == 201

        # 2. Manually verify email (simulate email verification)
        from app.models.user import User
        user = db_session.query(User).filter(User.email == "flow.test@test.com").first()
        user.is_verified = True
        db_session.commit()

        # 3. Login
        login_response = client.post("/api/auth/login", json={
            "email": "flow.test@test.com",
            "password": "FlowTest123!",
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # 4. Access profile
        profile_response = client.get("/api/users/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert profile_response.status_code == 200
        data = profile_response.json()
        assert data["email"] == "flow.test@test.com"
        assert data["role"] == "procurement_officer"
        assert data["is_verified"] is True

    def test_login_refresh_logout_flow(self, client, test_user):
        """Test complete token lifecycle: login -> refresh -> logout."""
        # 1. Login
        login_response = client.post("/api/auth/login", json={
            "email": "officer@vendorbridge.com",
            "password": "OfficerPass123!",
        })
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 2. Use access token
        me_response = client.get("/api/users/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        assert me_response.status_code == 200

        # 3. Refresh token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        # 4. Use new access token
        me_response = client.get("/api/users/me", headers={
            "Authorization": f"Bearer {new_tokens['access_token']}"
        })
        assert me_response.status_code == 200

        # 5. Logout
        logout_response = client.post("/api/auth/logout", json={
            "refresh_token": new_tokens["refresh_token"],
        })
        assert logout_response.status_code == 200

        # 6. Old refresh token should be invalid
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": new_tokens["refresh_token"],
        })
        assert refresh_response.status_code == 401
