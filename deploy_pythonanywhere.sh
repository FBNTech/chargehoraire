#!/bin/bash
# Script de déploiement sur PythonAnywhere

echo "=== Mise à jour du code sur PythonAnywhere ==="

# 1. Se connecter à PythonAnywhere via SSH
# ssh votre_username@ssh.pythonanywhere.com

# 2. Aller dans le répertoire du projet
cd ~/chargehoraire

# 3. Récupérer les dernières modifications depuis GitHub
git fetch origin
git pull origin main

# 4. Activer l'environnement virtuel
source ~/virtualenvs/chargehoraire/bin/activate

# 5. Installer/mettre à jour les dépendances
pip install -r requirements.txt

# 6. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 7. Appliquer les migrations de base de données
python manage.py migrate

# 8. Redémarrer l'application web
# Aller sur le dashboard PythonAnywhere > Web > Reload

echo "=== Déploiement terminé ==="
echo "N'oubliez pas de cliquer sur 'Reload' dans le dashboard Web de PythonAnywhere !"
