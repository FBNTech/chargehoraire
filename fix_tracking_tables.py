"""
Script pour recréer les tables tracking avec le bon schéma
"""
import os
import django
import sqlite3
from datetime import datetime
import shutil

# Sauvegarde
backup_file = f'db.sqlite3.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"=== CORRECTION DES TABLES TRACKING ===\n")
print(f"1. Sauvegarde: {backup_file}")
shutil.copy2('db.sqlite3', backup_file)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys=OFF")

# Supprimer les anciennes tables tracking
print("\n2. Suppression des tables tracking incorrectes...")
cursor.execute("DROP TABLE IF EXISTS tracking_teachingprogress")
cursor.execute("DROP TABLE IF EXISTS tracking_progressstats")
print("   ✓ Tables supprimées")

# Réactiver les clés étrangères
cursor.execute("PRAGMA foreign_keys=ON")
conn.commit()
conn.close()

print("\n3. Recréation des tables via migrations Django...")
from django.core.management import call_command

# Refaire les migrations tracking
call_command('migrate', 'tracking')

print("\n=== CORRECTION TERMINÉE ===")
print(f"\nSauvegarde: {backup_file}")
print("\nLes tables tracking ont été recréées avec le bon schéma.")
print("Redémarrez le serveur Django.")
