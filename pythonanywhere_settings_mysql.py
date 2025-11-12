# Configuration MySQL pour PythonAnywhere
# 
# Ajoutez ce code à la fin de config/settings.py
# OU créez un fichier .env avec ces variables

# Si vous utilisez MySQL sur PythonAnywhere
import os

# Configuration MySQL (si DATABASE_URL n'est pas défini)
if 'PYTHONANYWHERE_DOMAIN' in os.environ or 'pythonanywhere.com' in os.environ.get('ALLOWED_HOSTS', ''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'yourusername$chargehoraire',  # Remplacez yourusername
            'USER': 'yourusername',                # Remplacez yourusername
            'PASSWORD': 'your-mysql-password',     # Mot de passe MySQL
            'HOST': 'yourusername.mysql.pythonanywhere-services.com',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# Alternative : Utiliser des variables d'environnement
# Dans le fichier WSGI, définissez :
# os.environ['MYSQL_NAME'] = 'yourusername$chargehoraire'
# os.environ['MYSQL_USER'] = 'yourusername'
# os.environ['MYSQL_PASSWORD'] = 'your-password'
# os.environ['MYSQL_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
#
# Puis dans settings.py :
# if all(key in os.environ for key in ['MYSQL_NAME', 'MYSQL_USER', 'MYSQL_PASSWORD']):
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': os.environ['MYSQL_NAME'],
#             'USER': os.environ['MYSQL_USER'],
#             'PASSWORD': os.environ['MYSQL_PASSWORD'],
#             'HOST': os.environ['MYSQL_HOST'],
#         }
#     }
