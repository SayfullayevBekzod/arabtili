#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Test progress page directly
client = Client()

# Login first
user = User.objects.get(username='testuser')
client.force_login(user)

# Test progress page
print("Testing progress page...")
response = client.get('/progress/')
print(f'Progress page status: {response.status_code}')

if response.status_code == 200:
    print("✅ Progress page loads successfully")
else:
    print(f'❌ Progress page failed: {response.status_code}')
    print(f'Error content: {response.content.decode()[:500]}')
