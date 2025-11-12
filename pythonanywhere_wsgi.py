"""
Configuration WSGI pour PythonAnywhere

Instructions :
1. Sur PythonAnywhere, allez dans l'onglet "Web"
2. Créez une nouvelle application web Python 3.11
3. Remplacez le contenu du fichier WSGI par ce code
4. Ajustez les chemins selon votre username PythonAnywhere
"""

import os
import sys

# Ajoutez le chemin de votre projet
# Remplacez 'yourusername' par votre nom d'utilisateur PythonAnywhere
path = '/home/yourusername/chargehoraire'
if path not in sys.path:
    sys.path.insert(0, path)

# Variables d'environnement pour PythonAnywhere
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('SECRET_KEY', 'REMPLACEZ_PAR_UNE_CLE_SECRETE_UNIQUE')
os.environ.setdefault('ALLOWED_HOSTS', 'yourusername.pythonanywhere.com')
os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'https://yourusername.pythonanywhere.com')

# Démarrer l'application Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
