# Arial Sense — Auth System

A production-grade authentication system built with a **FastAPI** backend and a **vanilla JS** frontend. Deployed on **Railway** (backend) + **Vercel** (frontend).

**Live demo:** [https://auth-system-liard.vercel.app](https://auth-system-liard.vercel.app)  
**API docs:** `https://<your-railway-url>/docs`

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [API Reference](#api-reference)
7. [Security Design](#security-design)
8. [Environment Variables](#environment-variables)
9. [Local Development](#local-development)
10. [Deployment](#deployment)
11. [Email Service](#email-service)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.115 + Uvicorn |
| Database | PostgreSQL (Railway managed) |
| ORM | SQLAlchemy 2.0 |
| Auth tokens | JWT (python-jose) + bcrypt (passlib) |
| Email | Brevo HTTP API (httpx) |
| Rate limiting | SlowAPI |
| Input validation | Pydantic v2 |
| Frontend | Vanilla JS + HTML + CSS |
| Frontend host | Vercel |
| Backend host | Railway |

---

## Features

- **Sign up** with email, username, and password — account inactive until email is verified
- **Email verification** — 24-hour token, single-use, SHA-256 hashed in DB
- **Login** with brute-force protection — account locked 30 min after 5 failed attempts
- **Two-factor authentication (2FA)** — email OTP, 6-digit, 5-minute TTL, max 5 attempts
- **JWT access tokens** — 15-minute expiry, signed HS256
- **Refresh token rotation** — opaque 64-byte token, hashed in DB, revoked on every rotation
- **Logout** — refresh token immediately revoked
- **Forgot / reset password** — 1-hour single-use token, revokes all active sessions on use
- **Resend verification email** — rate-limited to 3 per hour per IP
- **CORS** — origin whitelist parsed from env var, trailing-slash tolerant
- **Rate limiting** — per-IP via SlowAPI (login: 5/min, forgot-password: 5/hour)
- **Hourly cleanup task** — removes expired OTPs and consumed tokens automatically

---

## Project Structure

```
arial-sense/
├── backend/
│   ├── app/
│   │   ├── main.py                  # App entry, middleware, lifespan, cleanup task
│   │   ├── api/
│   │   │   ├── auth.py              # 9 auth endpoints (thin HTTP layer, no logic)
│   │   │   └── users.py             # /users/me, /2fa/enable, /2fa/disable
│   │   ├── core/
│   │   │   ├── config.py            # All env vars → typed Settings object
│   │   │   ├── security.py          # bcrypt, JWT creation/decoding, rate limiter
│   │   │   ├── email.py             # Brevo API client, 3 send_* functions
│   │   │   └── dependencies.py      # JWT → User resolver for protected routes
│   │   ├── db/
│   │   │   ├── base.py              # SQLAlchemy declarative Base
│   │   │   └── session.py           # Engine, SessionLocal, get_db dependency
│   │   ├── models/
│   │   │   └── user.py              # ORM: User, UserSession, OneTimeToken, OTPCode
│   │   ├── schemas/
│   │   │   ├── auth.py              # Pydantic request/response models for auth
│   │   │   └── user.py              # UserResponse schema
│   │   └── services/
│   │       └── auth.py              # ALL business logic (signup → reset password)
│   ├── tests/
│   │   ├── conftest.py              # pytest fixtures (in-memory DB, TestClient)
│   │   ├── test_auth.py             # Auth endpoint tests
│   │   └── test_users.py            # User endpoint tests
│   ├── alembic/                     # DB migration scripts
│   ├── requirements.txt
│   ├── Procfile                     # Railway start command
│   ├── nixpacks.toml                # Railway build config
│   ├── .env.example                 # Safe template — copy to .env locally
│   └── Dockerfile                   # Optional container build
│
└── frontend/
    ├── index.html                   # Sign in / Sign up / OTP / Forgot password
    ├── dashboard.html               # Authenticated view, 2FA toggle, logout
    ├── verify-email.html            # Reads ?token= and calls /auth/verify-email
    ├── reset-password.html          # Reads ?token= and calls /auth/reset-password
    ├── app.js                       # All API calls, token storage, UI logic
    └── style.css                    # All styling
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Browser (Vercel)                        │
│  index.html · dashboard.html · verify-email.html         │
│  reset-password.html · app.js · style.css                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS API calls (fetch + JWT)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Railway (FastAPI)                        │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Middleware                                         │ │
│  │  CORSMiddleware (origin whitelist)                  │ │
│  │  SlowAPIMiddleware (IP rate limiting)               │ │
│  └────────────────────────────────────────────────────┘ │
│                         │                               │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │  API Layer  (app/api/)                              │ │
│  │  auth.py  ·  users.py                               │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                               │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │  Service Layer  (app/services/)                     │ │
│  │  All business logic — signup, login, 2FA,           │ │
│  │  refresh rotation, logout, password reset           │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                               │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │  Core  (app/core/)                                  │ │
│  │  config · security (JWT/bcrypt) · email (Brevo)     │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                               │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │  Data Layer  (app/models/ + app/db/)                │ │
│  │  SQLAlchemy ORM → PostgreSQL                        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴────────────┐
          ▼                           ▼
┌──────────────────┐      ┌────────────────────────┐
│  PostgreSQL DB   │      │  Brevo Email API        │
│  (Railway)       │      │  (api.brevo.com/HTTPS)  │
└──────────────────┘      └────────────────────────┘
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | auto-generated |
| `email` | VARCHAR(255) | unique, indexed |
| `username` | VARCHAR(50) | unique, indexed, case-insensitive |
| `hashed_password` | VARCHAR(255) | bcrypt |
| `is_verified` | BOOLEAN | false until email confirmed |
| `is_active` | BOOLEAN | admin can deactivate |
| `is_locked` | BOOLEAN | set after 5 failed logins |
| `is_2fa_enabled` | BOOLEAN | user-controlled |
| `failed_login_attempts` | INTEGER | reset on successful login |
| `locked_until` | TIMESTAMPTZ | null unless locked |
| `created_at` | TIMESTAMPTZ | server default |
| `updated_at` | TIMESTAMPTZ | auto-updated |

### `user_sessions`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | CASCADE delete |
| `refresh_token_hash` | VARCHAR(64) | SHA-256 of raw token |
| `expires_at` | TIMESTAMPTZ | 7 days from creation |
| `is_revoked` | BOOLEAN | set on logout / rotation |

### `one_time_tokens`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | CASCADE delete |
| `token_hash` | VARCHAR(64) | SHA-256 of raw token |
| `purpose` | ENUM | `email_verification` or `password_reset` |
| `expires_at` | TIMESTAMPTZ | 24h (verify) / 1h (reset) |
| `is_used` | BOOLEAN | consumed on first use |

### `otp_codes`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | CASCADE delete |
| `otp_hash` | VARCHAR(64) | SHA-256 of 6-digit code |
| `expires_at` | TIMESTAMPTZ | 5 minutes from creation |
| `attempt_count` | INTEGER | deleted after 5 wrong attempts |

---

## API Reference

Base URL: `https://<railway-url>` · All bodies are JSON · Auth endpoints return `application/json`

### Auth — no token required

| Method | Endpoint | Body fields | Success |
|---|---|---|---|
| POST | `/auth/signup` | `email`, `username`, `password`, `confirm_password` | 201 |
| POST | `/auth/verify-email` | `token` | 200 |
| POST | `/auth/resend-verification` | `email` | 200 |
| POST | `/auth/login` | `email`, `password` | 200 (tokens or OTP pending) |
| POST | `/auth/verify-otp` | `pending_token`, `otp` | 200 (tokens) |
| POST | `/auth/refresh` | `refresh_token` | 200 (new token pair) |
| POST | `/auth/logout` | `refresh_token` | 200 |
| POST | `/auth/forgot-password` | `email` | 200 |
| POST | `/auth/reset-password` | `token`, `password`, `confirm_password` | 200 |

### Users — `Authorization: Bearer <access_token>` required

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/users/me` | Returns current user profile |
| POST | `/users/2fa/enable` | Enables 2FA for the account |
| POST | `/users/2fa/disable` | Disables 2FA for the account |

### curl examples

```bash
# Sign up
curl -X POST https://<api>/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"yourname","password":"StrongPass1!","confirm_password":"StrongPass1!"}'

# Login
curl -X POST https://<api>/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"StrongPass1!"}'

# Get profile
curl https://<api>/users/me \
  -H "Authorization: Bearer <access_token>"

# Refresh tokens
curl -X POST https://<api>/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Logout
curl -X POST https://<api>/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Forgot password
curl -X POST https://<api>/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'
```

---

## Security Design

| Concern | Implementation |
|---|---|
| Password storage | bcrypt via passlib (cost factor 12) |
| Password policy | 8–128 chars · must have upper + lower + digit + special |
| Access token | JWT HS256 · `type: access` claim · 15-min expiry |
| Refresh token | 64-byte `secrets.token_urlsafe` · SHA-256 hashed before DB storage |
| 2FA pending token | JWT HS256 · `type: 2fa_pending` claim · 5-min expiry |
| Token rotation | Old refresh token revoked on every `/auth/refresh` call |
| Brute-force protection | 5 failed logins → account locked 30 min |
| OTP security | SHA-256 hashed · 5-min TTL · max 5 wrong attempts · `hmac.compare_digest` |
| One-time tokens | SHA-256 hashed · `is_used` flag · single-use enforced |
| Session revocation | Password reset revokes **all** active sessions |
| Rate limiting | Login: 5/min · Forgot password: 5/hour · Resend: 3/hour (per IP) |
| CORS | Explicit origin whitelist · trailing-slash normalised |
| SQL injection | Prevented by SQLAlchemy parameterised queries — no raw SQL |
| Input validation | Pydantic strict models on every endpoint |
| Error responses | Generic messages — never leak internal state or user existence |
| Raw tokens | Never logged or stored — only SHA-256 hashes persisted |
| DB cleanup | Hourly background task purges expired OTPs and used tokens |

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` for local development.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing secret (min 32 random bytes) |
| `JWT_ALGORITHM` | No | Default: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Default: `7` |
| `ALLOWED_ORIGINS` | Yes | CSV or JSON array of allowed CORS origins |
| `APP_BASE_URL` | Yes | Frontend base URL (used in email links) |
| `BREVO_API_KEY` | Yes | Brevo transactional email API key |
| `MAIL_FROM` | Yes | Verified sender email in Brevo |
| `MAIL_FROM_NAME` | No | Display name — default: `Arial Sense` |
| `REDIS_URL` | No | Redis for rate-limit storage (in-memory fallback if unset) |

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`ALLOWED_ORIGINS` accepts either format:
```
# CSV (recommended for Railway):
ALLOWED_ORIGINS=https://yourapp.vercel.app,http://localhost:3000

# JSON array (also valid):
ALLOWED_ORIGINS=["https://yourapp.vercel.app","http://localhost:3000"]
```

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL running locally

### Steps

```bash
# 1. Clone
git clone https://github.com/choksi2212/auth-system.git
cd auth-system

# 2. Create virtual environment
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create local database
psql -U postgres -c "CREATE DATABASE arial_sense;"

# 5. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, etc.

# 6. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically on first startup via `Base.metadata.create_all`.

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running tests

```bash
psql -U postgres -c "CREATE DATABASE arial_sense_test;"
pytest tests/ -v
```

---

## Deployment

### Backend — Railway

1. Connect your GitHub repo in Railway → select the `backend/` subdirectory as the root
2. Railway detects `nixpacks.toml` / `Procfile` automatically
3. Add all environment variables from the table above in Railway's Variables tab
4. Railway provisions a PostgreSQL database — copy the `DATABASE_URL` it provides
5. Tables are auto-created on first boot; use Alembic for schema migrations going forward

Start command (in `Procfile`):
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend — Vercel

1. Connect your GitHub repo in Vercel → set `frontend/` as the root directory
2. No build step — purely static files
3. Set the API base URL inside `frontend/app.js` to your Railway service URL

---

## Email Service

Email is sent via the **Brevo** transactional API over HTTPS (Railway blocks all outbound SMTP ports).

### Setup
1. Sign up free at [brevo.com](https://brevo.com) (300 emails/day free)
2. Go to **Senders & IP → Senders → Add a Sender** — verify your Gmail address
3. Go to **SMTP & API → API Keys** — create and copy a key
4. Add `BREVO_API_KEY` and `MAIL_FROM` to Railway environment variables

### Emails sent by the system

| Trigger | Subject | Content |
|---|---|---|
| Sign up | `Verify your email — Arial Sense` | Verification link (24h) |
| 2FA login | `Your login OTP — Arial Sense` | 6-digit code (5 min) |
| Forgot password | `Reset your password — Arial Sense` | Reset link (1h) |

---

## License

MIT
