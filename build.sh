#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
cd backend
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if it doesn't exist (for Render deployment)
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@numeneon.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

# Create team test users with profiles
python manage.py shell -c "
from django.contrib.auth.models import User
from users.models import Profile

team_users = [
    {'username': 'pabloPistola', 'email': 'pablo@test.com', 'password': 'test123', 'first_name': 'Pablo', 'last_name': 'Pistola'},
    {'username': 'natalia', 'email': 'natalia@test.com', 'password': 'test123', 'first_name': 'Natalia', 'last_name': 'Test'},
    {'username': 'crystal', 'email': 'crystal@test.com', 'password': 'test123', 'first_name': 'Crystal', 'last_name': 'Test'},
    {'username': 'colin', 'email': 'colin@test.com', 'password': 'test123', 'first_name': 'Colin', 'last_name': 'Test'},
]

for u in team_users:
    if not User.objects.filter(username=u['username']).exists():
        user = User.objects.create_user(u['username'], u['email'], u['password'], first_name=u['first_name'], last_name=u['last_name'])
        Profile.objects.get_or_create(user=user, defaults={'bio': f\"Team member {u['first_name']}\"})
        print(f\"Created: {u['username']} / {u['email']} / test123\")
    else:
        user = User.objects.get(username=u['username'])
        Profile.objects.get_or_create(user=user)
        print(f\"Already exists: {u['username']}\")
"

# Run seed scripts to populate sample data (standalone scripts, not manage.py commands)
python seed_posts.py || echo "seed_posts.py failed"
python manage.py seed_messages || echo "seed_messages not available or failed"
