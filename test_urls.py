#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse
from django.test import Client

# Test URL resolution
try:
    login_url = reverse('arab:login')
    print(f'Login URL resolved: {login_url}')
except Exception as e:
    print(f'URL resolution error: {e}')

# Test direct URL access
client = Client()
response = client.get('/accounts/login/')
print(f'Direct GET /accounts/login/ status: {response.status_code}')

# Test alternative URL
response2 = client.get('/login/')
print(f'Direct GET /login/ status: {response2.status_code}')

# List all URL patterns
from django.urls import get_resolver
from django.urls.resolvers import URLResolver, URLPattern

def show_urls(urllist, depth=0):
    for entry in urllist:
        if isinstance(entry, URLResolver):
            print("  " * depth + f"{entry.pattern}")
            show_urls(entry.url_patterns, depth + 1)
        elif isinstance(entry, URLPattern):
            print("  " * depth + f"{entry.pattern} -> {entry.callback}")

resolver = get_resolver()
print("\nURL Patterns:")
show_urls(resolver.url_patterns)
