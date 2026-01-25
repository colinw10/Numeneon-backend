# Test Accounts on Production (Render)

> **Last Updated:** January 24, 2026

---

## Pre-Created Test Accounts

When the backend deploys to Render, these accounts are automatically created:

| Username | Email | Password |
|----------|-------|----------|
| pabloPistola | pablo@test.com | test123 |
| natalia | natalia@test.com | test123 |
| crystal | crystal@test.com | test123 |
| colin | colin@test.com | test123 |
| admin | admin@numeneon.com | admin123 |

---

## How to Log In

1. Go to the frontend: https://numeneon-frontend.vercel.app/login
2. Enter your **email** (not username!) and password
3. Click Login

Example:
```
Email: pablo@test.com
Password: test123
```

---

## Admin Panel

To access Django admin:
1. Go to: https://numeneon-backend.onrender.com/admin/
2. Login with:
   - Username: `admin`
   - Password: `admin123`

---

## How This Works

The `build.sh` script runs on every Render deploy and:

1. Creates the team user accounts (if they don't exist)
2. Creates a Profile for each user
3. Runs `seed_posts` to create sample posts
4. Runs `seed_messages` to create sample conversations

This happens automatically - **you don't need to do anything**.

---

## Adding a New Test User

If you want to add another test user, edit `build.sh` in the repo root:

```bash
# Find this section and add to the team_users list:
team_users = [
    {'username': 'pabloPistola', 'email': 'pablo@test.com', ...},
    {'username': 'natalia', 'email': 'natalia@test.com', ...},
    # ADD YOUR USER HERE:
    {'username': 'yourname', 'email': 'yourname@test.com', 'password': 'test123', 'first_name': 'Your', 'last_name': 'Name'},
]
```

Then push to trigger a redeploy.

---

## Resetting the Database

If you need a fresh database on Render:

1. Go to Render Dashboard → your PostgreSQL database
2. Click **"Reset Database"** (this deletes everything!)
3. Go to your Web Service → **Manual Deploy** → **Deploy latest commit**
4. The seed scripts will recreate all users and sample data

---

## Sample Data Included

After deploy, the database has:
- ✅ 5 user accounts with profiles
- ✅ Sample posts (from `seed_posts`)
- ✅ Sample messages/conversations (from `seed_messages`)

You can start testing immediately!
