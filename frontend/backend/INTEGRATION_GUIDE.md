# Backend Integration Guide for VendorBridge

**Status**: Backend code copied from Arial Sense (production-grade FastAPI auth system)  
**Frontend Status**: Production-ready with mock auth service  
**Integration Effort**: ~2-4 hours for experienced backend developer

---

## 📁 What's Included

The `backend/` folder contains a complete, production-grade authentication system:

- **FastAPI backend** with async support
- **PostgreSQL database** with SQLAlchemy ORM
- **JWT access tokens** (15-minute expiry)
- **Refresh tokens** with automatic rotation (7-day expiry)
- **2FA with email OTP** (6-digit, 5-minute TTL)
- **Email verification** (24-hour token)
- **Password reset** (1-hour token)
- **Account locking** after 5 failed attempts
- **Rate limiting** with SlowAPI
- **Complete test suite** (pytest)
- **Alembic migrations** for schema management

---

## 🚀 Quick Start (Local Development)

### 1. Set Up Database

```bash
# Create PostgreSQL databases
psql -U postgres
CREATE DATABASE vendorbridge;
CREATE DATABASE vendorbridge_test;
\q
```

### 2. Install Dependencies

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vendorbridge

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-64-character-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (add your frontend URL)
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Frontend base URL (for email links)
APP_BASE_URL=http://localhost:5173

# Email (Brevo API - free 300 emails/day)
BREVO_API_KEY=your-brevo-api-key
MAIL_FROM=your-verified-email@gmail.com
MAIL_FROM_NAME=VendorBridge

# Redis (optional - uses in-memory if not set)
REDIS_URL=
```

### 4. Run Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

### 5. Start Backend

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

API Documentation: http://localhost:8000/docs

---

## 🔗 Frontend Integration Steps

The frontend is **already prepared** for backend integration. You only need to:

### Step 1: Update API Base URL

Edit `src/lib/auth/api-client.ts`:

```typescript
// Change this line:
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

// Or set in .env file:
VITE_API_URL=http://localhost:8000
```

### Step 2: Uncomment API Calls

In `src/lib/auth/api-client.ts`, each method has a `TODO` comment. Simply:

1. **Uncomment** the fetch implementation
2. **Remove** the mock service fallback

Example:

```typescript
// BEFORE:
async signup(request: SignupRequest) {
  // TODO: Uncomment when backend is ready
  // return await this.request('/auth/signup', { ... });
  
  // MOCK: Using mock service
  return await authService.signup(request);
}

// AFTER:
async signup(request: SignupRequest) {
  return await this.request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({
      email: request.email,
      username: request.username,
      password: request.password,
      confirm_password: request.confirmPassword,
    }),
  });
}
```

### Step 3: Test Integration

```bash
# Frontend (Vite dev server)
cd ..
bun run dev

# Backend (FastAPI)
cd backend
uvicorn app.main:app --reload
```

Navigate to http://localhost:5173 and test:
- Sign up
- Email verification (check backend logs for token)
- Login
- 2FA (if enabled)
- Dashboard access
- Logout

---

## 📋 API Endpoint Mapping

Frontend calls already match the backend API structure:

| Frontend Method | Backend Endpoint | Description |
|----------------|------------------|-------------|
| `apiClient.signup()` | `POST /auth/signup` | Create new account |
| `apiClient.login()` | `POST /auth/login` | Authenticate user |
| `apiClient.verifyOTP()` | `POST /auth/verify-otp` | Verify 2FA code |
| `apiClient.getCurrentUser()` | `GET /users/me` | Get profile |
| `apiClient.refreshToken()` | `POST /auth/refresh` | Refresh access token |
| `apiClient.logout()` | `POST /auth/logout` | Revoke refresh token |
| `apiClient.toggle2FA()` | `POST /users/2fa/enable` or `/users/2fa/disable` | Toggle 2FA |
| `apiClient.forgotPassword()` | `POST /auth/forgot-password` | Request reset link |
| `apiClient.resetPassword()` | `POST /auth/reset-password` | Reset password |

---

## 🗄️ Database Schema

The backend uses 4 tables:

### `users`
- id (UUID primary key)
- email (unique, indexed)
- username (unique, indexed, nullable)
- hashed_password
- is_verified (email confirmation)
- is_active (account enabled)
- is_locked (after failed logins)
- is_2fa_enabled
- failed_login_attempts
- locked_until (timestamp)
- created_at, updated_at

### `user_sessions`
- id (UUID primary key)
- user_id (foreign key → users)
- refresh_token_hash (SHA-256)
- expires_at
- is_revoked

### `one_time_tokens`
- id (UUID primary key)
- user_id (foreign key → users)
- token_hash (SHA-256)
- purpose (enum: email_verification | password_reset)
- expires_at
- is_used

### `otp_codes`
- id (UUID primary key)
- user_id (foreign key → users)
- otp_hash (SHA-256 of 6-digit code)
- expires_at (5 minutes)
- attempt_count (max 5)

---

## 🔐 Security Features

### Implemented in Backend:
✅ bcrypt password hashing (cost factor 12)  
✅ JWT access tokens (HS256, 15min expiry)  
✅ Refresh token rotation (SHA-256 hashed in DB)  
✅ 2FA with OTP (email-based)  
✅ Account locking (5 failed attempts → 30min lock)  
✅ Rate limiting (5/min on login, 5/hour on forgot password)  
✅ CORS whitelist  
✅ SQL injection prevention (parameterized queries)  
✅ Token-type confusion prevention  
✅ Constant-time password comparison  
✅ Generic error messages (no user enumeration)  

### Implemented in Frontend:
✅ Access token in-memory only (secure by design)  
✅ Refresh token in localStorage  
✅ Automatic token refresh  
✅ Password strength validation  
✅ Email normalization  
✅ Protected routes  
✅ Session management  

---

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage:
- 14 auth endpoint tests
- 4 user endpoint tests
- Edge cases covered:
  - Duplicate email signup
  - Password policy violations
  - Account locking
  - Token expiry
  - Invalid credentials
  - 2FA flow

---

## 📧 Email Service Setup

The backend uses **Brevo** (formerly Sendinblue) for transactional emails:

1. Sign up at https://brevo.com (free 300 emails/day)
2. Verify your sender email (Gmail works)
3. Get API key from dashboard
4. Add to `.env`:
   ```
   BREVO_API_KEY=xkeysib-...
   MAIL_FROM=your-email@gmail.com
   ```

Emails sent automatically for:
- Email verification (24h link)
- 2FA OTP (6-digit code, 5min)
- Password reset (1h link)

---

## 🚢 Deployment

### Backend Options:

**Railway** (Recommended)
```bash
# Railway automatically detects:
# - nixpacks.toml (build config)
# - Procfile (start command)
# - requirements.txt (dependencies)

# 1. Connect GitHub repo
# 2. Add all environment variables
# 3. Railway provisions PostgreSQL automatically
# 4. Deploy! 🚀
```

**Docker**
```bash
cd backend
docker build -t vendorbridge-api .
docker run -p 8000:8000 --env-file .env vendorbridge-api
```

**Heroku**
```bash
# Procfile already configured
heroku create vendorbridge-api
heroku addons:create heroku-postgresql
heroku config:set SECRET_KEY=...
git push heroku main
```

### Frontend Deployment:

Already configured for Vercel. Just set environment variable:
```
VITE_API_URL=https://your-backend.railway.app
```

---

## 🐛 Troubleshooting

### Issue: "Cannot reach the server"
- Check backend is running: `curl http://localhost:8000/docs`
- Check CORS in `backend/app/core/config.py`
- Verify `ALLOWED_ORIGINS` includes your frontend URL

### Issue: "Database connection failed"
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Run: `psql -U postgres -d vendorbridge -c "SELECT 1;"`

### Issue: "Email not sending"
- Check Brevo API key is valid
- Verify sender email is verified in Brevo
- Check backend logs for error details
- Test API key: `curl -H "api-key: YOUR_KEY" https://api.brevo.com/v3/account`

### Issue: "Token errors"
- Regenerate `SECRET_KEY` in `.env`
- Clear browser localStorage
- Check JWT_ALGORITHM matches (HS256)

---

## 📖 Additional Resources

### Backend Code Structure:
```
backend/app/
├── api/           # Route handlers (thin layer)
│   ├── auth.py    # 9 auth endpoints
│   └── users.py   # 3 user endpoints
├── core/          # Core services
│   ├── config.py  # Environment settings
│   ├── security.py # JWT, bcrypt, rate limiter
│   ├── email.py   # Brevo API client
│   └── dependencies.py # FastAPI dependencies
├── db/            # Database
│   ├── base.py    # SQLAlchemy base
│   └── session.py # DB session factory
├── models/        # ORM models
│   └── user.py    # User, Session, Token, OTP
├── schemas/       # Pydantic validation
│   ├── auth.py    # Request/response models
│   └── user.py    # User response
└── services/      # Business logic
    └── auth.py    # ALL auth logic here
```

### Key Files to Review:
- `backend/app/services/auth.py` - Core business logic
- `backend/app/core/security.py` - Crypto functions
- `backend/app/models/user.py` - Database models
- `backend/app/main.py` - App entry point
- `src/lib/auth/api-client.ts` - Frontend API client

### Documentation:
- Backend README: `backend/README.md`
- Full implementation: `auth-system-main/IMPLEMENTATION.md`
- API docs (when running): http://localhost:8000/docs

---

## ✅ Integration Checklist

- [ ] PostgreSQL database created
- [ ] Python dependencies installed
- [ ] `.env` file configured
- [ ] Database migrations run
- [ ] Backend server starts successfully
- [ ] API docs accessible at /docs
- [ ] Frontend API_BASE_URL updated
- [ ] API calls uncommented in api-client.ts
- [ ] Mock service calls removed
- [ ] CORS configured correctly
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test 2FA flow (if enabled)
- [ ] Test token refresh
- [ ] Test logout
- [ ] Email service configured (optional for demo)

---

## 🆘 Need Help?

The auth system is battle-tested and production-ready. Common issues:

1. **CORS errors**: Add your frontend URL to `ALLOWED_ORIGINS`
2. **Token errors**: Regenerate `SECRET_KEY`
3. **Database errors**: Check `DATABASE_URL` connection string
4. **Import errors**: Activate venv and reinstall requirements

For complex issues, check:
- Backend logs: Look for detailed error messages
- Frontend console: Check network tab for API responses
- Database logs: `tail -f /var/log/postgresql/*.log`

---

**The frontend is production-ready and waiting for your backend! Happy coding! 🚀**
