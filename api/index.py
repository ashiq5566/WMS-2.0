import os
import sys
from pathlib import Path

# Add project root directory to sys.path so Django can locate apps and packages
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

def app(environ, start_response):
    # If Vercel rewrote the path, restore the original URI path for Django routing
    original_uri = (
        environ.get('HTTP_X_FORWARDED_URI')
        or environ.get('HTTP_X_ORIGINAL_URI')
        or environ.get('RAW_URI')
    )
    if original_uri:
        environ['PATH_INFO'] = original_uri.split('?')[0]

    return django_app(environ, start_response)
