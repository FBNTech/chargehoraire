"""
Script pour nettoyer les problèmes de base de données
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

print("=== NETTOYAGE ET VÉRIFICATION ===\n")

# 1. Vérifier les migrations
print("1. Vérification des migrations...")
call_command('showmigrations')

# 2. Vérifier si toutes les migrations sont appliquées
print("\n2. Application des migrations manquantes...")
call_command('migrate', '--run-syncdb')

print("\n=== NETTOYAGE TERMINÉ ===")
print("\nSi le problème persiste, essayez:")
print("1. Arrêter le serveur")
print("2. Supprimer les fichiers __pycache__")
print("3. Redémarrer le serveur")
