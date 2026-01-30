#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate, login

# Test without @login_required
client = Client()

# Create a simple test view without decorators
from django.http import HttpResponse
from django.urls import path
from django.conf import settings
from django.urls.conf import include

# Test direct function call
from arab.views import login_view

# Create a mock request
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

request = HttpRequest()
request.method = 'GET'
request.user = AnonymousUser()

try:
    response = login_view(request)
    print(f'Direct function call status: {response.status_code}')
    print(f'Response type: {type(response)}')
except Exception as e:
    print(f'Direct function call error: {e}')
    import traceback
    traceback.print_exc()
