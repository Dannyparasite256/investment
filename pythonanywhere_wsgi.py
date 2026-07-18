"""
PythonAnywhere WSGI entrypoint.

In the Web tab, open your WSGI configuration file and replace its contents
with this file (or paste these lines and fix the path).
"""
import os
import sys
from pathlib import Path

# >>> CHANGE THIS if your folder name/username differs <<<
project_home = '/home/investment256/investment'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load .env from the project root (django-environ also does this in settings)
os.chdir(project_home)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
