#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client

# Test login with proper middleware
client = Client()

# Step 1: Get login page
print("Step 1: GET login page")
response = client.get('/accounts/login/')
print(f'Status: {response.status_code}')
if response.status_code == 200:
    print("✅ Login page loaded successfully")
else:
    print(f'❌ Login page failed: {response.content.decode()[:200]}')

# Step 2: Test login with correct credentials
print("\nStep 2: POST login with correct credentials")
response = client.post('/accounts/login/', {
    'username': 'testuser',
    'password': 'testpass'
})
print(f'Status: {response.status_code}')
if response.status_code == 302:
    print(f'✅ Login successful, redirecting to: {response["Location"]}')
    
    # Step 3: Follow redirect
    print("\nStep 3: Follow redirect")
    response2 = client.get(response['Location'])
    print(f'After redirect status: {response2.status_code}')
    print(f'Final URL content preview: {response2.content.decode()[:200]}...')
elif response.status_code == 200:
    print('❌ Login failed - showing login page again')
    # Check for error messages
    content = response.content.decode()
    if 'error' in content.lower():
        print('Error message found in response')
else:
    print(f'❌ Unexpected status: {response.content.decode()[:200]}')
