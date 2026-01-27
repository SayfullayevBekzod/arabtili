import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site

try:
    site = Site.objects.get(id=1)
    site.domain = '127.0.0.1:9000'
    site.name = 'AlifPro Local'
    site.save()
    print(f"SUCCESS: Updated Site ID {site.id} to {site.domain} ({site.name})")
except Site.DoesNotExist:
    print("ERROR: Site ID 1 does not exist.")
except Exception as e:
    print(f"ERROR: {e}")
