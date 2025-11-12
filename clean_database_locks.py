"""
Script pour nettoyer les verrous et connexions SQLite
"""
import os
import sqlite3

db_path = 'db.sqlite3'

print("=== NETTOYAGE DES VERROUS SQLITE ===\n")

# 1. Vérifier si des fichiers de verrou existent
lock_files = [
    'db.sqlite3-journal',
    'db.sqlite3-wal',
    'db.sqlite3-shm'
]

print("1. Vérification des fichiers de verrou:")
for lock_file in lock_files:
    if os.path.exists(lock_file):
        print(f"   ⚠️  {lock_file} existe (fichier de verrou actif)")
        try:
            os.remove(lock_file)
            print(f"   ✓  {lock_file} supprimé")
        except Exception as e:
            print(f"   ✗  Impossible de supprimer {lock_file}: {e}")
    else:
        print(f"   ✓  {lock_file} n'existe pas")

# 2. Vérifier l'intégrité de la base de données
print("\n2. Vérification de l'intégrité de la base:")
try:
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    if result == 'ok':
        print(f"   ✓  Intégrité: {result}")
    else:
        print(f"   ⚠️  Problème d'intégrité: {result}")
    conn.close()
except Exception as e:
    print(f"   ✗  Erreur: {e}")

# 3. Vérifier le mode journal
print("\n3. Configuration du mode journal:")
try:
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"   Mode actuel: {mode}")
    
    # Passer en mode WAL (Write-Ahead Logging) pour de meilleures performances concurrentes
    if mode != 'wal':
        cursor.execute("PRAGMA journal_mode=WAL")
        new_mode = cursor.fetchone()[0]
        print(f"   ✓  Nouveau mode: {new_mode}")
    
    conn.close()
except Exception as e:
    print(f"   ✗  Erreur: {e}")

print("\n=== NETTOYAGE TERMINÉ ===")
print("\nActions recommandées:")
print("1. Arrêter le serveur Django (CTRL+C)")
print("2. Supprimer manuellement les dossiers __pycache__ si nécessaire")
print("3. Redémarrer le serveur: python manage.py runserver")
