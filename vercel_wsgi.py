"""
Configuration WSGI adaptée pour Vercel (serverless)

ATTENTION : Cette configuration a des limitations importantes pour Django
"""

import os
from django.core.wsgi import get_wsgi_application

# Configuration pour environnement Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# L'application WSGI
app = get_wsgi_application()
