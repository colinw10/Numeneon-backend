# CORS Configuration & Deployment Issues

> **Last Updated:** January 24, 2026

---

## Quick Summary

This doc covers all the deployment issues we encountered connecting the Vercel frontend to the Render backend, and how we fixed them.

---

## Issues We Encountered & Fixes

### 1. DisallowedHost Error (403)

**Symptom:** Django returned `DisallowedHost at /api/auth/signup/`

**Cause:** Django's `ALLOWED_HOSTS` didn't include the Render domain.

**Fix:**

```python
# settings.py
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'numeneon-backend.onrender.com',
    '.onrender.com',  # Allow all Render subdomains
]
```

---

### 2. CORS Error (Access-Control-Allow-Origin)

**Symptom:** Browser blocked request with "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause:** Backend didn't allow requests from Vercel's domain.

**Fix:**

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'https://numeneon-frontend.vercel.app',
    'https://numeneon-backend.onrender.com',
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',  # React dev server
]
```

---

### 3. CORS for Vercel Preview URLs

**Symptom:** Production worked but preview deployments got CORS errors.

**Cause:** Vercel creates random URLs like `numeneon-frontend-abc123-user.vercel.app` for each deployment/branch.

**Fix:** Use regex patterns to match all preview URLs:

```python
# settings.py
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://numeneon-frontend.*\.vercel\.app$",
    r"^https://numeneon-frontend-.*\.vercel\.app$",
]
```

**What is CORS regex?** A wildcard pattern to match multiple URLs:

```
Instead of listing:      Use pattern:
site-abc.vercel.app     site-*.vercel.app ← matches ALL
site-xyz.vercel.app
site-123.vercel.app
```

---

### 4. CSRF Verification Failed (403)

**Symptom:** Django returned `403 Forbidden - CSRF verification failed`

**Cause:** `CORS_ALLOW_CREDENTIALS = True` tells browser to send cookies, which triggers Django's CSRF protection.

**Fix:** For JWT-based APIs, we don't use cookies - tokens go in the `Authorization` header. So disable credentials:

```python
# settings.py
CORS_ALLOW_CREDENTIALS = False  # JWT uses headers, not cookies
```

**Why this works:**

- **Before:** Browser sends cookies → Django expects CSRF token → Error
- **After:** No cookies sent → JWT in `Authorization: Bearer <token>` header → No CSRF needed

---

### 5. Database Connection Error

**Symptom:** Backend connected to localhost instead of Render's PostgreSQL.

**Cause:** `DATABASES` was hardcoded to localhost. Render provides `DATABASE_URL` env var.

**Fix:**

```python
# settings.py
import os
import dj_database_url

if os.environ.get('DATABASE_URL'):
    # Production: use Render's PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
        )
    }
else:
    # Development: use local PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'numeneon',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
```

---

### 6. Build Script Path Error

**Symptom:** Render couldn't find `manage.py`.

**Cause:** `build.sh` was running from repo root, but `manage.py` is in `backend/`.

**Fix:**

```bash
# build.sh
cd backend  # ← Added this line
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
```

---

### 7. Static Files Error

**Symptom:** `collectstatic` failed - no `STATIC_ROOT` configured.

**Fix:**

```python
# settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

---

## Current Working Configuration

```python
# settings.py - Key settings for production

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'numeneon-backend.onrender.com',
    '.onrender.com',
]

CORS_ALLOWED_ORIGINS = [
    'https://numeneon-frontend.vercel.app',
    'https://numeneon-backend.onrender.com',
    'http://localhost:5173',
    'http://localhost:3000',
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://numeneon-frontend.*\.vercel\.app$",
    r"^https://numeneon-frontend-.*\.vercel\.app$",
]

CORS_ALLOW_CREDENTIALS = False  # JWT uses headers, not cookies

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # ...
}
```

---

## Architecture Diagram

```
┌─────────────────────────┐       HTTPS        ┌─────────────────────────┐
│      VERCEL             │                    │       RENDER            │
│  (React Frontend)       │                    │   (Django Backend)      │
│                         │                    │                         │
│  numeneon-frontend      │    POST /api/      │  numeneon-backend       │
│  .vercel.app            │  ───────────────►  │  .onrender.com          │
│                         │                    │                         │
│  Sends:                 │                    │  Checks:                │
│  - Origin header        │                    │  1. ALLOWED_HOSTS ✓     │
│  - Authorization:       │  ◄───────────────  │  2. CORS origin ✓       │
│    Bearer <JWT>         │    JSON response   │  3. JWT token ✓         │
└─────────────────────────┘                    └─────────────────────────┘
                                                          │
                                                          ▼
                                               ┌─────────────────────────┐
                                               │    RENDER PostgreSQL    │
                                               │    (DATABASE_URL)       │
                                               └─────────────────────────┘
```

---

## Render Settings

| Setting        | Value                                              |
| -------------- | -------------------------------------------------- |
| Root Directory | (empty - uses repo root)                           |
| Build Command  | `./build.sh`                                       |
| Start Command  | `cd backend && gunicorn numeneon.wsgi:application` |
| DATABASE_URL   | (auto-set by Render PostgreSQL)                    |

---

## Troubleshooting Checklist

If something breaks, check in this order:

1. **Is it deployed?** Check Render Events tab for green checkmark
2. **Is the URL right?** Backend is `/api/...` not just `/...`
3. **ALLOWED_HOSTS?** Does it include the domain?
4. **CORS origin?** Is the frontend URL in `CORS_ALLOWED_ORIGINS` or matched by regex?
5. **CSRF error?** Make sure `CORS_ALLOW_CREDENTIALS = False`
6. **Database?** Check `DATABASE_URL` is set in Render Environment

---

## Testing Backend Directly

Use curl to test without frontend:

```bash
# Test signup
curl -X POST https://numeneon-backend.onrender.com/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"test123"}'

# Test CORS preflight
curl -I -X OPTIONS https://numeneon-backend.onrender.com/api/auth/signup/ \
  -H "Origin: https://numeneon-frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST"
```

---

## Local Development Still Works!

All these changes are backwards compatible. Running locally:

- `localhost:5173` (Vite) ✅ Still in CORS list
- `localhost:3000` (React) ✅ Still in CORS list
- Local PostgreSQL ✅ Falls back when no `DATABASE_URL`
