import os
import sys

path = '/home/henil_shingala/Downloads/Bilipefirs/bilipefirs/django/ecom'
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application
os.environ['DJANGO_SETTINGS_MODULE'] = 'ecom.settings'
application = get_wsgi_application()

