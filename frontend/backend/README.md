# Arial Sense — Production Auth API

A production-grade authentication system built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **JWT**.

---

## Architecture

```
Frontend (UI only)
      │  HTTPS
      ▼
Backend (FastAPI) — all logic, validation, authentication
      │  secure connection
      ▼
Database (PostgreSQL) — never accessed directly by the frontend
```

### Folder Structure

```
arial-sense/
├── app/
│   ├── main.py              # FastAPI app, middleware, exception handlers
│   ├── api/
│   │   ├── auth.py          # Auth routes: signup, login, refresh, logout, etc.
│   │   └── users.py         # Protected routes: /users/me
│   ├── core/
│   │   ├── config.py        # Settings loaded from environment variables
│   │   ├── security.py      # JWT, bcrypt, rate limiter
│   │   └── dependencies.py  # FastAPI dependency injection (get_current_user)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy declarative Base
│   │   └── session.py       # Engine, SessionLocal, get_db dependency
│   ├── models/
│   │   └── user.py          # ORM models: User, UserSession, OneTimeToken
│   ├── schemas/
│   │   ├── auth.py          # Pydantic request/response models for auth
│   │   └── user.py          # Pydantic UserResponse schema
│   └── services/
│       └── auth.py          # Business logic: signup, login, refresh, logout, pw-reset
├── tests/
│   ├── conftest.py          # pytest fixtures (DB setup/teardown, TestClient)
│   ├── test_auth.py         # Auth endpoint tests
│   └── test_users.py        # User endpoint tests
├── alembic/
│   ├── env.py               # Alembic migration environment
│   ├── script.py.mako       # Migration file template
│   └── versions/            # Auto-generated migration files
├── alembic.ini              # Alembic configuration
├── requirements.txt
├── .env                     # Secrets — never commit to version control
└── .env.example             # Safe template to share with the team
```

---

## Security Features

| Feature | Implementation |
|---|---|
| Password hashing | bcrypt via `passlib` |
| Password policy | 8–128 chars, upper + lower + digit + special |
| Access tokens | JWT, 15-minute expiry |
| Refresh tokens | Cryptographically random, SHA-256 hashed in DB |
| Token revocation | Refresh tokens invalidated on logout & password reset |
| Account locking | Locked for 30 min after 5 consecutive failed logins |
| Rate limiting | 5 login attempts/min per IP via `slowapi` |
| CORS | Configurable trusted origins only |
| SQL injection | Prevented by SQLAlchemy ORM (parameterized queries) |
| Input validation | Strict Pydantic models on every endpoint |
| Error messages | Generic — never leak internal details |
| Email verification | Token-based (24-hour expiry) |
| Password reset | Single-use token (1-hour expiry), revokes all sessions |

---

## Setup

### 1. Create PostgreSQL databases

```sql
CREATE DATABASE arial_sense;
CREATE DATABASE arial_sense_test;  -- for running tests
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, etc.
```

Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run database migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

> The app also auto-creates tables on startup via `Base.metadata.create_all` (dev convenience). In production, use Alembic exclusively.

---

## Running

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

### POST /auth/signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass1!","confirm_password":"StrongPass1!"}'
```

### POST /auth/login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass1!"}'
```

### POST /auth/refresh
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<your_refresh_token>"}'
```

### POST /auth/logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<your_refresh_token>"}'
```

### POST /auth/forgot-password
```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

### POST /auth/reset-password
```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token":"<token_from_email>","password":"NewPass1!","confirm_password":"NewPass1!"}'
```

### POST /auth/verify-email
```bash
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token":"<token_from_email>"}'
```

### GET /users/me
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Email Service Integration

The signup and forgot-password flows log verification/reset tokens to the console (look for `[EMAIL VERIFICATION]` and `[PASSWORD RESET]` log lines). Replace the `logger.info` calls in `app/services/auth.py` with your email provider:

- **SendGrid**: `sendgrid-python`
- **AWS SES**: `boto3`
- **Resend**: `resend`

---

## Testing

```bash
# Ensure arial_sense_test database exists, then:
pytest tests/ -v
```

To use a different test database:

```bash
TEST_DATABASE_URL=postgresql://postgres:pass@localhost:5432/mytest pytest tests/ -v
```

---

## Deployment (Render / Railway / AWS EC2)

1. Set all environment variables from `.env.example` in your hosting dashboard
2. Set `DATABASE_URL` to your hosted PostgreSQL connection string
3. Run migrations before starting: `alembic upgrade head`
4. Start command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. All traffic must go through HTTPS (enforced at the load balancer / platform level)

> **Never commit `.env` to version control.** Add it to `.gitignore`.
