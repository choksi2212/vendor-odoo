# Arial Sense — Full Implementation Reference

> **Last updated:** April 22, 2026  
> A production-grade authentication system — FastAPI backend + vanilla JS frontend.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Technology Stack](#2-technology-stack)
3. [Database Schema](#3-database-schema)
4. [Backend — Core Modules](#4-backend--core-modules)
5. [Backend — API Endpoints](#5-backend--api-endpoints)
6. [Backend — Business Logic](#6-backend--business-logic)
7. [Backend — Validation & Schemas](#7-backend--validation--schemas)
8. [Security Implementation](#8-security-implementation)
9. [Frontend](#9-frontend)
10. [Environment Variables](#10-environment-variables)
11. [Dependencies](#11-dependencies)
12. [Tests](#12-tests)
13. [Setup & Running](#13-setup--running)
14. [API Reference with curl Examples](#14-api-reference-with-curl-examples)
15. [What Is NOT Yet Implemented](#15-what-is-not-yet-implemented)

---

## 1. Project Structure

```
arial-sense/
│
├── backend/                        ← All server-side code
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 ← FastAPI app entry point
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             ← Auth routes (7 endpoints)
│   │   │   └── users.py            ← User routes (1 endpoint)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           ← Settings loaded from .env
│   │   │   ├── security.py         ← bcrypt, JWT, rate limiter
│   │   │   └── dependencies.py     ← FastAPI dependency injection
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             ← SQLAlchemy DeclarativeBase
│   │   │   └── session.py          ← Engine, SessionLocal, get_db
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py         ← Re-exports models for Alembic
│   │   │   └── user.py             ← User, UserSession, OneTimeToken
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             ← Request/response Pydantic models
│   │   │   └── user.py             ← UserResponse schema
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── auth.py             ← All authentication business logic
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             ← pytest fixtures (PostgreSQL)
│   │   ├── test_auth.py            ← 14 auth endpoint tests
│   │   └── test_users.py           ← 4 user endpoint tests
│   │
│   ├── alembic/
│   │   ├── env.py                  ← Migration environment
│   │   ├── script.py.mako          ← Migration file template
│   │   └── versions/               ← Auto-generated migrations go here
│   │
│   ├── alembic.ini                 ← Alembic configuration
│   ├── requirements.txt            ← Pinned Python dependencies
│   ├── .env                        ← Secrets (never commit)
│   └── .env.example                ← Safe template for team sharing
│
└── frontend/                       ← All client-side code (no framework)
    ├── index.html                  ← Sign In / Sign Up page
    ├── dashboard.html              ← Protected profile dashboard
    ├── style.css                   ← Complete design system
    └── app.js                      ← Auth flow, API client, token handling
```

---

## 2. Technology Stack

### Backend

| Layer | Choice | Version | Reason |
|---|---|---|---|
| Framework | FastAPI | 0.115.5 | Async-compatible, auto OpenAPI docs, Pydantic integration |
| Server | Uvicorn + Gunicorn | 0.32.1 | ASGI server; Gunicorn for multi-worker production |
| Database | PostgreSQL | any | Fully relational, ACID-compliant, UUID native support |
| ORM | SQLAlchemy | 2.0.36 | Industry standard, prevents SQL injection, migration support |
| Migrations | Alembic | 1.14.0 | Schema versioning tied to SQLAlchemy models |
| Password hashing | passlib + bcrypt | 1.7.4 | bcrypt is the industry standard for password storage |
| JWT | python-jose | 3.3.0 | Signed HS256 JWTs with expiry claims |
| Settings | pydantic-settings | 2.6.1 | Typed env var loading with `.env` support |
| Validation | pydantic | 2.9.2 | Request/response validation with field-level errors |
| Rate limiting | slowapi | 0.1.9 | Per-IP request limits, integrates with FastAPI |
| DB driver | psycopg2-binary | 2.9.10 | PostgreSQL adapter for SQLAlchemy |

### Frontend

| Layer | Choice | Reason |
|---|---|---|
| Language | Vanilla JavaScript (ES2022) | Zero dependencies, no build step |
| Styling | Pure CSS with custom properties | Fast, maintainable, no framework lock-in |
| HTTP | Fetch API (native) | Built into every modern browser |
| Storage | `localStorage` for refresh token, in-memory for access token | Balances security and UX |

---

## 3. Database Schema

### Table: `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `uuid4` | Unique user identifier |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, indexed | Lowercase-normalised email |
| `username` | `VARCHAR(50)` | UNIQUE, nullable, indexed | Optional display name |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | bcrypt hash — never plain text |
| `is_verified` | `BOOLEAN` | NOT NULL, default `false` | Email verification status |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Account enabled flag |
| `is_locked` | `BOOLEAN` | NOT NULL, default `false` | Temporarily locked after failed logins |
| `failed_login_attempts` | `INTEGER` | NOT NULL, default `0` | Counter reset on successful login |
| `locked_until` | `TIMESTAMPTZ` | nullable | Lock expiry timestamp |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, server default `now()` | Account creation time |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, server default + `onupdate` | Last modification time |

**Indexes:** `ix_users_email`, `ix_users_username`  
**Relationships:** one-to-many → `user_sessions`, `one_time_tokens`

---

### Table: `user_sessions`

Stores hashed refresh tokens. A user can have multiple concurrent sessions (e.g. multiple devices).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | Session identifier |
| `user_id` | `UUID` | FK → `users.id` CASCADE DELETE | Owning user |
| `refresh_token_hash` | `VARCHAR(64)` | UNIQUE, NOT NULL, indexed | SHA-256 of the raw refresh token |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | Token expiry (default: 7 days) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, server default | When the session was created |
| `is_revoked` | `BOOLEAN` | NOT NULL, default `false` | Revoked on logout or password reset |

**Indexes:** `ix_user_sessions_user_id`, `ix_user_sessions_refresh_token_hash`

---

### Table: `one_time_tokens`

Shared table for both email verification and password reset tokens, distinguished by `purpose`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | Token identifier |
| `user_id` | `UUID` | FK → `users.id` CASCADE DELETE | Owning user |
| `token_hash` | `VARCHAR(64)` | UNIQUE, NOT NULL, indexed | SHA-256 of the raw token |
| `purpose` | `ENUM` | NOT NULL | `email_verification` or `password_reset` |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | 24h for email verify, 1h for password reset |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, server default | When generated |
| `is_used` | `BOOLEAN` | NOT NULL, default `false` | Consumed on use; cannot be reused |

**Indexes:** `ix_one_time_tokens_user_id`, `ix_one_time_tokens_token_hash`

---

## 4. Backend — Core Modules

### `app/core/config.py`

Typed settings class powered by `pydantic-settings`. All values are loaded from the `.env` file (or real environment variables in production). The instance is cached with `@lru_cache` so `.env` is parsed exactly once.

```
Settings fields:
  DATABASE_URL               str       — PostgreSQL connection string
  SECRET_KEY                 str       — HMAC signing key for JWTs
  JWT_ALGORITHM              str       — "HS256" (default)
  ACCESS_TOKEN_EXPIRE_MINUTES int      — 15 (default)
  REFRESH_TOKEN_EXPIRE_DAYS  int       — 7 (default)
  ALLOWED_ORIGINS            list[str] — CORS whitelist
```

---

### `app/core/security.py`

All cryptographic primitives live here.

| Function / Object | Description |
|---|---|
| `pwd_context` | `passlib.CryptContext` configured for bcrypt |
| `hash_password(password)` | Returns bcrypt hash of a plain-text password |
| `verify_password(plain, hashed)` | Constant-time bcrypt comparison |
| `create_access_token(subject)` | Encodes a JWT with `sub`, `exp`, `type:"access"` claims |
| `create_refresh_token()` | Returns `secrets.token_urlsafe(64)` — 64-byte random string |
| `decode_access_token(token)` | Decodes and validates JWT; raises `JWTError` on any problem |
| `limiter` | `slowapi.Limiter` keyed on remote IP address |

The `type` claim inside the JWT prevents a refresh token (which is a random string, not a JWT) from accidentally being used as an access token, and protects against token-type confusion attacks.

---

### `app/core/dependencies.py`

FastAPI dependency used on every protected route.

```
get_current_user(credentials, db) -> User
  1. Extracts Bearer token from Authorization header
  2. Calls decode_access_token() — raises 401 on invalid/expired token
  3. Loads User from DB by UUID in the "sub" claim
  4. Raises 401 if user not found or not active
  5. Raises 403 if account is locked
  6. Returns the User ORM object
```

---

### `app/db/base.py`

Defines `Base = DeclarativeBase()`. All ORM models inherit from this single base. Alembic's `env.py` imports it to access `Base.metadata` for autogenerate.

---

### `app/db/session.py`

```
engine        — SQLAlchemy engine with pool_size=5, max_overflow=10, pool_pre_ping=True
SessionLocal  — sessionmaker factory (autocommit=False, autoflush=False)
get_db()      — FastAPI dependency; yields a Session and closes it in finally
```

`pool_pre_ping=True` silently reconnects dropped PostgreSQL connections, which is essential for long-running deployments.

---

### `app/main.py`

Application entry point. Responsibilities:

- **Lifespan hook** — runs `Base.metadata.create_all()` on startup to ensure tables exist
- **Structured logging** — `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
- **Rate limiter** — attaches `slowapi` to `app.state.limiter`
- **SlowAPIMiddleware** — enables the `@limiter.limit()` decorator on routes
- **CORSMiddleware** — only allows origins in `ALLOWED_ORIGINS`, methods GET/POST only
- **Router mounting** — `/auth` and `/users` prefixes
- **Exception handlers**:
  - `RateLimitExceeded` → `429 Too Many Requests`
  - All other unhandled exceptions → `500 Internal Server Error` with generic message (no stack trace exposed)

---

## 5. Backend — API Endpoints

All endpoints are under the FastAPI app. Interactive docs: `http://localhost:8000/docs`

### Auth Router — `POST /auth/*`

| Method | Path | Auth Required | Rate Limited | Description |
|---|---|---|---|---|
| POST | `/auth/signup` | No | No | Create a new account |
| POST | `/auth/verify-email` | No | No | Confirm email with a token |
| POST | `/auth/login` | No | **5/min per IP** | Authenticate and receive tokens |
| POST | `/auth/refresh` | No | No | Exchange refresh token for new access token |
| POST | `/auth/logout` | No | No | Revoke a refresh token |
| POST | `/auth/forgot-password` | No | No | Request a password reset link |
| POST | `/auth/reset-password` | No | No | Set a new password using reset token |

### Users Router — `GET /users/*`

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/users/me` | **Yes** (Bearer JWT) | Return the authenticated user's profile |

---

## 6. Backend — Business Logic

All logic lives in `app/services/auth.py`. The API layer is thin — it only calls the service and formats the response.

### `signup(payload, db)`
1. Queries for an existing user with the same email → `409` if found
2. Hashes the password with bcrypt
3. Creates the `User` row with `db.flush()` (so we have the UUID before committing)
4. Generates a `secrets.token_urlsafe(32)` verification token
5. Stores SHA-256 hash of that token in `one_time_tokens` (purpose: `email_verification`, expires 24h)
6. Commits both rows atomically
7. Logs `[EMAIL VERIFICATION] user_id=... | token=...` *(replace with real email service)*

### `verify_email(token, db)`
1. SHA-256 hashes the incoming token and queries `one_time_tokens`
2. Filters: `purpose=email_verification`, `is_used=false`, `expires_at > now()`
3. If not found → `400 Bad Request`
4. Marks `otp.is_used = True` and `otp.user.is_verified = True`
5. Commits

### `login(payload, db)`
1. Fetches user by email → `401` if not found
2. Checks `is_active` → `403` if false
3. Checks `is_locked` + `locked_until > now()` → `403` with unlock time
4. Calls `verify_password()`:
   - **Failure:** increments `failed_login_attempts`; if ≥ 5, sets `is_locked=True` and `locked_until = now() + 30min`; commits; raises `401`
   - **Success:** resets `failed_login_attempts=0`, clears lock fields
5. Creates a JWT access token (`sub` = user UUID, `exp` = 15 min)
6. Creates a 64-byte random refresh token; stores its SHA-256 hash in `user_sessions`
7. Commits; returns `(access_token, raw_refresh_token)`

### `refresh_access_token(refresh_token, db)`
1. Hashes the token; queries `user_sessions` where `is_revoked=false` and `expires_at > now()`
2. If not found → `401`
3. Issues and returns a new access token for the session's `user_id`

### `logout(refresh_token, db)`
1. Hashes the token; finds the session
2. If found and not already revoked, sets `is_revoked = True` and commits
3. Always returns silently (no error if token is unknown — idempotent)

### `forgot_password(email, db)`
1. Looks up user by email
2. If **not found** → returns silently *(intentional — never reveal if an email exists)*
3. Generates a `secrets.token_urlsafe(32)` reset token
4. Stores SHA-256 hash in `one_time_tokens` (purpose: `password_reset`, expires **1 hour**)
5. Logs `[PASSWORD RESET] user_id=... | token=...` *(replace with real email service)*

### `reset_password(payload, db)`
1. Hashes the token; queries `one_time_tokens` where `purpose=password_reset`, `is_used=false`, `expires_at > now()`
2. If not found → `400 Bad Request`
3. Marks `otp.is_used = True`
4. Hashes and sets the new password on the user
5. **Revokes ALL active sessions** for that user (bulk UPDATE) — forces re-login everywhere
6. Commits

---

## 7. Backend — Validation & Schemas

All request bodies are validated by Pydantic before the route handler runs.

### Password Policy (enforced via regex in `schemas/auth.py`)

```
Length:     8–128 characters
Uppercase:  at least 1 (A–Z)
Lowercase:  at least 1 (a–z)
Digit:      at least 1 (0–9)
Special:    at least 1 from: @$!%*?&#^()_-+=[]{} etc.
```

Invalid passwords return `422 Unprocessable Entity` before any DB query runs.

### Email Normalization

Every email field uses a `@field_validator` that calls `.lower().strip()`. This ensures `User@Example.COM` and `user@example.com` are treated as the same address at both signup and login.

### Request Schemas

| Schema | Fields | Validators |
|---|---|---|
| `SignupRequest` | `email`, `password`, `confirm_password` | email normalised; password strength; passwords match |
| `LoginRequest` | `email`, `password` | email normalised |
| `VerifyEmailRequest` | `token` | — |
| `EmailRequest` | `email` | email normalised |
| `ResetPasswordRequest` | `token`, `password`, `confirm_password` | password strength; passwords match |
| `RefreshRequest` | `refresh_token` | — |

### Response Schemas

| Schema | Fields |
|---|---|
| `TokenResponse` | `access_token`, `refresh_token`, `token_type: "bearer"` |
| `AccessTokenResponse` | `access_token`, `token_type: "bearer"` |
| `MessageResponse` | `message` |
| `UserResponse` | `id`, `email`, `username`, `is_verified`, `is_active`, `created_at` |

`UserResponse` **never** includes `hashed_password`, `failed_login_attempts`, `locked_until`, or any internal fields.

---

## 8. Security Implementation

### Password Storage

```
Algorithm:  bcrypt (work factor: passlib default ~12 rounds)
Storage:    only the bcrypt hash — raw password is never persisted or logged
Comparison: passlib.verify() — constant-time, safe against timing attacks
```

### JWT Access Tokens

```
Algorithm:  HS256 (HMAC-SHA256)
Claims:     sub (user UUID), exp (expiry), type ("access")
Expiry:     15 minutes (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)
Secret:     loaded from SECRET_KEY env var (64 hex chars generated at setup)
Type claim: prevents token-type confusion if someone passes a refresh token
```

### Refresh Tokens

```
Generation:  secrets.token_urlsafe(64) — 64 bytes of CSPRNG output
Storage:     SHA-256 hash stored in user_sessions table
Transport:   sent as plain string in JSON response body (not in cookie)
Expiry:      7 days (configurable via REFRESH_TOKEN_EXPIRE_DAYS)
Revocation:  is_revoked flag set to true on logout or password reset
```

### Account Locking

```
Threshold:  5 consecutive failed login attempts
Lock duration: 30 minutes from last failed attempt
Unlock:     automatic when locked_until timestamp passes
Reset:      failed_login_attempts counter resets on any successful login
Logging:    WARNING logged with user_id on lock event
```

### Rate Limiting

```
Applies to: POST /auth/login only
Limit:      5 requests per minute per IP address
Response:   429 Too Many Requests with generic message
Engine:     slowapi (in-memory — use Redis for multi-process production)
```

### CORS Policy

```
Allowed origins:  configurable list via ALLOWED_ORIGINS env var
Allowed methods:  GET, POST only
Allowed headers:  Authorization, Content-Type
Credentials:      allowed (for cookie-based future extension)
```

### SQL Injection Prevention

All database access uses SQLAlchemy ORM with parameterized queries. Raw SQL is never used anywhere in the codebase.

### Error Message Policy

```
Authentication failures: always "Invalid credentials." (no hint about which field was wrong)
Email enumeration:        forgot-password always returns 200 regardless of email existence
Internal errors:          all unhandled exceptions return "An internal error occurred."
Stack traces:             never exposed to the client; logged server-side only
```

### Logging

Structured log lines include timestamp, level, module name, and message. Events logged:

| Event | Level | Details |
|---|---|---|
| Startup | INFO | "Database schema verified." |
| New registration | INFO | user_id |
| Successful login | INFO | user_id |
| Failed login (lock triggered) | WARNING | user_id, attempt count |
| Login attempt on locked account | WARNING | user_id |
| Unhandled exception | ERROR | method, path, exception (with traceback) |
| Email token generation | INFO | user_id, raw token *(replace with email service)* |
| Password reset token generated | INFO | user_id, raw token *(replace with email service)* |

---

## 9. Frontend

Four files — no framework, no build step, no `node_modules`.

### `style.css`

Complete design system built with CSS custom properties:

```
Theme:        Dark (near-black background #080810)
Accent:       Indigo (#6366f1) → Purple (#a855f7) gradient
Surface:      #0f0f1a card, #14141f inputs
Typography:   System font stack (Segoe UI, -apple-system, etc.)
Radius:       14px cards, 9px inputs/buttons, 6px small elements
Animations:   fadeSlide on panel switch, shimmer on skeleton, spin on button loader
```

Components implemented in CSS:

| Component | Notes |
|---|---|
| `.auth-body` | Full-viewport centering with two radial bg gradients |
| `.card` | Auth form container with border and surface background |
| `.brand` | Logo mark (gradient SVG) + name |
| `.tabs` | Underline-style tab switcher; active tab = indigo underline |
| `.form-panel` | Hidden by default; `.active` triggers `fadeSlide` animation |
| `.field` | Label (uppercase, dimmed) + input group |
| `.input-wrap` | Relative wrapper for password Show/Hide toggle |
| `.pw-toggle` | Absolute-positioned text button inside input |
| `.strength-track` / `.strength-fill` | 3px bar that fills and changes color as password is typed |
| `.btn-primary` | Full-width indigo button; hover glow; `.loading` → spinner overlay |
| `.toast` | Success (green) / error (red) notification bar with slide-in animation |
| `.navbar` | Sticky frosted-glass navbar on dashboard |
| `.user-card` | Profile info card with header + info rows |
| `.avatar` | Circle with gradient background showing initials |
| `.badge` | Pill badge: verified (green), unverified (amber), active (green) |
| `.skeleton` | Shimmer placeholder rows shown while profile loads |
| `.info-value.mono` | Monospace font for UUID display |

---

### `app.js`

Shared JavaScript loaded on both pages.

**Token Management:**

```
Access token:   in-memory variable (_accessToken)
                — lost on page refresh (by design — more secure than localStorage)
                — automatically re-acquired from refresh token on page load
Refresh token:  localStorage key "as_refresh_token"
                — persists across browser sessions
                — cleared on logout or failed refresh
```

**Functions:**

| Function | Description |
|---|---|
| `api(method, path, body, auth)` | Thin Fetch wrapper; adds `Authorization: Bearer` when `auth=true` |
| `silentRefresh()` | Posts refresh token → stores new access token; clears on failure |
| `toast(message, type)` | Shows success/error toast in `#toast` element |
| `setLoading(btn, state)` | Toggles `.loading` class and `disabled` on submit buttons |
| `measureStrength(pw)` | Scores password 0–5 (length, upper, lower, digit, special) |
| `updateStrengthBar(input)` | Fills strength bar width and color based on score |
| `extractError(data)` | Parses Pydantic `detail` (string or array) into a human message |
| `initAuthPage()` | Entry for `index.html` — auto-redirects if refresh token valid |
| `initDashboardPage()` | Entry for `dashboard.html` — redirects to login if no valid token |
| `_setupTabs()` | Tab click → switches active panel + clears toast |
| `_setupPasswordToggles()` | Show/Hide button toggles `input.type` between `password`/`text` |
| `_setupSigninForm()` | Handles sign-in submit, stores tokens, redirects |
| `_setupSignupForm()` | Handles sign-up submit, shows success toast, auto-switches to sign-in tab |
| `_setupForgotFlow()` | Forgot-link → shows forgot panel; back link → returns to sign-in |
| `_loadProfile()` | Fetches `/users/me`, populates all dashboard fields, swaps skeleton for card |
| `_handleLogout()` | Calls `/auth/logout`, clears tokens, redirects to `index.html` |

**Page flow:**

```
index.html loads
  └─ initAuthPage()
       ├─ If localStorage has refresh token → silentRefresh()
       │     ├─ Success → redirect to dashboard.html
       │     └─ Fail   → clear tokens, show sign-in form
       └─ Set up tabs, forms, password toggles, forgot flow

dashboard.html loads
  └─ initDashboardPage()
       ├─ If no access token → silentRefresh()
       │     ├─ Fail → redirect to index.html
       │     └─ Success → continue
       └─ _loadProfile() → populate card, hide skeleton
```

---

### `index.html`

Three panels (only one visible at a time, controlled by `.form-panel.active`):

1. **Sign In panel** (`#signin-panel`) — email, password (with Show/Hide), forgot link, submit
2. **Sign Up panel** (`#signup-panel`) — email, password (with Show/Hide + strength bar), confirm password, submit
3. **Forgot Password panel** (`#forgot-panel`) — back link, email, submit

Single `#toast` element at the bottom of the card is used by all three panels.

---

### `dashboard.html`

- **Sticky navbar** — logo on left, Sign Out button on right
- **Heading** — "Welcome back"
- **Skeleton card** — shown immediately on load (4 shimmer rows)
- **Real user card** — hidden until `_loadProfile()` completes, then swapped in

User card displays:

| Row | Value source |
|---|---|
| Email | `user.email` |
| Email status | `user.is_verified` → green "Verified" / amber "Unverified" badge |
| Account | `user.is_active` → green "Active" badge |
| Member since | `user.created_at` formatted as "April 22, 2026" |
| User ID | `user.id` in monospace font |

---

## 10. Environment Variables

File: `backend/.env`

| Variable | Example Value | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:pass@localhost:5432/arial_sense` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | 64-char hex string | Yes | HMAC key for JWT signing — must be kept secret |
| `JWT_ALGORITHM` | `HS256` | No (default) | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | No (default) | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | No (default) | Refresh token lifetime |
| `ALLOWED_ORIGINS` | `["http://localhost:5500"]` | No (default) | JSON array of trusted frontend origins |

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 11. Dependencies

All pinned to exact versions in `backend/requirements.txt`:

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
alembic==1.14.0
pydantic[email]==2.9.2
pydantic-settings==2.6.1
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.12
slowapi==0.1.9
email-validator==2.2.0
pytest==8.3.4
httpx==0.27.2
```

---

## 12. Tests

**Location:** `backend/tests/`  
**Runner:** pytest  
**Database:** Real PostgreSQL (`arial_sense_test` database)  
**Isolation:** Tables are created before each test function and dropped after via `Base.metadata.create_all / drop_all`

### `test_auth.py` — 14 tests across 5 classes

| Class | Test | What it verifies |
|---|---|---|
| `TestSignup` | `test_success_returns_201` | Valid signup → 201 + message key |
| `TestSignup` | `test_duplicate_email_returns_409` | Second signup with same email → 409 |
| `TestSignup` | `test_weak_password_returns_422` | Short password → 422 before DB |
| `TestSignup` | `test_password_mismatch_returns_422` | Non-matching passwords → 422 |
| `TestSignup` | `test_invalid_email_returns_422` | Malformed email → 422 |
| `TestSignup` | `test_response_never_contains_password` | Response body never leaks password |
| `TestLogin` | `test_success_returns_tokens` | Valid credentials → 200 + both tokens + `bearer` |
| `TestLogin` | `test_wrong_password_returns_401` | Wrong password → 401 with "Invalid credentials." |
| `TestLogin` | `test_nonexistent_email_returns_401` | Unknown email → 401 (no user enumeration) |
| `TestLogin` | `test_account_locks_after_max_failures` | 5 failures → account locked → 403 on correct login |
| `TestLogin` | `test_email_is_case_insensitive` | UPPERCASE email still logs in |
| `TestRefreshToken` | `test_valid_refresh_token_returns_new_access_token` | Valid refresh → 200 + new access token |
| `TestRefreshToken` | `test_invalid_refresh_token_returns_401` | Fake token → 401 |
| `TestLogout` | `test_logout_invalidates_refresh_token` | Logout → subsequent refresh → 401 |
| `TestLogout` | `test_logout_with_invalid_token_returns_200` | Unknown token → still 200 (idempotent) |
| `TestForgotAndResetPassword` | `test_forgot_password_always_returns_200` | Nonexistent email → still 200 |
| `TestForgotAndResetPassword` | `test_reset_with_invalid_token_returns_400` | Fake reset token → 400 |

### `test_users.py` — 4 tests

| Test | What it verifies |
|---|---|
| `test_authenticated_returns_user_profile` | Valid JWT → 200 + correct email + no hashed_password field |
| `test_unauthenticated_returns_403` | No Authorization header → 403 |
| `test_invalid_token_returns_401` | Garbage token → 401 |
| `test_expired_token_returns_401` | Crafted expired JWT → 401 |

---

## 13. Setup & Running

### Step 1 — Create PostgreSQL databases

```sql
CREATE DATABASE arial_sense;
CREATE DATABASE arial_sense_test;
```

### Step 2 — Activate the virtual environment

```bash
# Windows
backend\.venv\Scripts\activate

# macOS / Linux
source backend/.venv/bin/activate
```

### Step 3 — Install dependencies (if not already done)

```bash
cd backend
pip install -r requirements.txt
```

### Step 4 — Configure environment

Edit `backend/.env` with your PostgreSQL password and a generated `SECRET_KEY`.

### Step 5 — Run database migrations

```bash
cd backend

# Generate the initial migration from your models
alembic revision --autogenerate -m "initial schema"

# Apply it
alembic upgrade head
```

> The app also calls `Base.metadata.create_all()` on startup as a safety net in development. Use Alembic exclusively in production.

### Step 6 — Start the backend

```bash
# Development
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 7 — Serve the frontend

```bash
# From project root
python -m http.server 5500 --directory frontend
```

Open: [http://localhost:5500](http://localhost:5500)  
API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## 14. API Reference with curl Examples

### POST /auth/signup

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass1!",
    "confirm_password": "StrongPass1!"
  }'
```

**Response 201:**
```json
{ "message": "Account created. Please check your email to verify your address." }
```

---

### POST /auth/login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass1!"
  }'
```

**Response 200:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "dGhpc2lzYXJhbmRvbXRva2Vu...",
  "token_type": "bearer"
}
```

---

### POST /auth/refresh

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "<your_refresh_token>" }'
```

**Response 200:**
```json
{ "access_token": "eyJhbGci...", "token_type": "bearer" }
```

---

### POST /auth/logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "<your_refresh_token>" }'
```

**Response 200:**
```json
{ "message": "Logged out successfully." }
```

---

### POST /auth/verify-email

```bash
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{ "token": "<token_from_server_log>" }'
```

**Response 200:**
```json
{ "message": "Email verified successfully." }
```

---

### POST /auth/forgot-password

```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{ "email": "user@example.com" }'
```

**Response 200 (always, even if email not found):**
```json
{ "message": "If an account with that email exists, a reset link has been sent." }
```

---

### POST /auth/reset-password

```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<token_from_server_log>",
    "password": "NewPass1!",
    "confirm_password": "NewPass1!"
  }'
```

**Response 200:**
```json
{ "message": "Password reset successfully. Please log in with your new password." }
```

---

### GET /users/me

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>"
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": null,
  "is_verified": false,
  "is_active": true,
  "created_at": "2026-04-22T13:14:00.000Z"
}
```

---

## 15. What Is NOT Yet Implemented

These items are partially scaffolded (models and token logic exist) but need additional work for production use:

### Email Sending
The email verification and password reset flows **generate tokens and log them** but do not actually send emails. To complete this:

1. Choose a provider: **SendGrid**, **AWS SES**, **Resend**, **Mailgun**
2. In `backend/app/services/auth.py`, replace the two `logger.info("[EMAIL ...")` lines with actual email delivery calls
3. Add provider API key to `.env`

### Rate Limiting — Multi-Process
The current `slowapi` rate limiter uses an in-memory store. In production with multiple Uvicorn/Gunicorn workers, each process has its own counter. To fix this:
- Configure `slowapi` with a **Redis** backend: `Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")`

### HTTPS Enforcement
The backend assumes HTTPS is terminated at the load balancer or reverse proxy (Nginx, Caddy, AWS ALB). No redirect middleware is included. Ensure your deployment platform enforces HTTPS.

### Refresh Token Rotation
Currently, the same refresh token can be used multiple times until it expires or is explicitly revoked. A more secure pattern is **refresh token rotation** — issuing a new refresh token on every `/auth/refresh` call and invalidating the old one.

### 2FA / TOTP
Not implemented. Would require an `otp_secret` column on `User` and a TOTP library (e.g. `pyotp`).

### Username-based Signup
The `username` column exists in the database but is not exposed in the signup form or API payload yet.

### Frontend — Email Verification UI
The verify-email endpoint exists on the backend, but the frontend has no page to handle `?token=xxx` links. A `verify.html` page would complete this flow.

### Frontend — Reset Password UI
Similarly, a `reset-password.html` page that reads the `?token=xxx` from the URL and posts to `/auth/reset-password` is needed to complete the end-to-end password reset flow.
