#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate

# Test with CSRF disabled
client = Client(enforce_csrf_checks=False)

# Get login page first
response = client.get('/accounts/login/')
print(f'GET login page status: {response.status_code}')

# Test login
form_data = {
    'username': 'testuser',
    'password': 'testpass'
}

response = client.post('/accounts/login/', form_data)
print(f'POST login status: {response.status_code}')
print(f'Redirect location: {response.get("Location", "No redirect")}')

if response.status_code == 302:
    # Follow redirect
    response2 = client.get(response['Location'])
    print(f'After redirect status: {response2.status_code}')
    print(f'Final URL: {response2.request.get("PATH_INFO", "Unknown")}')
