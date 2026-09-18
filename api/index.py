import os
import sys
from pathlib import Path

# Add project root directory to sys.path so Django can locate apps and packages
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
