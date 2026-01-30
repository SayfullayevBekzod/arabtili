#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from arab.forms import LoginForm

# Test form validation
form_data = {
    'username': 'testuser',
    'password': 'testpass'
}

form = LoginForm(data=form_data)
print(f'Form is valid: {form.is_valid()}')
if not form.is_valid():
    print(f'Form errors: {form.errors}')

# Test with client
client = Client()
response = client.post('/accounts/login/', form_data)
print(f'Response status: {response.status_code}')
print(f'Response content: {response.content.decode()}')
