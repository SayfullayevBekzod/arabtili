#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate

# Test authentication
user = authenticate(username='testuser', password='testpass')
print(f'Authentication result: {user}')

if user:
    # Test login via client
    client = Client()
    response = client.post('/accounts/login/', {
        'username': 'testuser',
        'password': 'testpass'
    })
    print(f'Login response status: {response.status_code}')
    print(f'Redirect location: {response.get("Location", "No redirect")}')
    
    if response.status_code == 302:
        # Follow redirect
        response2 = client.get(response['Location'])
        print(f'After redirect status: {response2.status_code}')
else:
    print('Authentication failed')
