#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create admin user if not exists
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'GromAdmin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Victory164!')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@grombricks.ua')

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    Profile.objects.get_or_create(user=user, defaults={'is_email_verified': True})
    print(f'Superuser {username} created successfully.')
else:
    print(f'Superuser {username} already exists.')
"
