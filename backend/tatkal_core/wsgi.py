# Owner: Person A
"""
WSGI config for tatkal_core project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tatkal_core.settings")

application = get_wsgi_application()
