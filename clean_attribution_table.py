#!/usr/bin/env python
"""
Script pour nettoyer les tables orphelines SQLite dans attribution
"""
import sqlite3
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

# Chemin vers la base de données
db_path = settings.DATABASES['default']['NAME']

print(f"Connexion à la base de données : {db_path}")

# Connexion à SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Lister toutes les tables
print("\n=== Tables dans la base de données ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

# Chercher les tables "old"
print("\n=== Tables orphelines (_old) ===")
old_tables = [t[0] for t in tables if '_old' in t[0]]
if old_tables:
    for table in old_tables:
        print(f"  ⚠️ Trouvé: {table}")
else:
    print("  ✓ Aucune table orpheline trouvée")

# Vérifier les déclencheurs (triggers) qui pourraient référencer des tables old
print("\n=== Déclencheurs (triggers) ===")
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='trigger';")
triggers = cursor.fetchall()
if triggers:
    for trigger in triggers:
        print(f"  - {trigger[0]} (sur table: {trigger[1]})")
        # Afficher le SQL du trigger
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (trigger[0],))
        trigger_sql = cursor.fetchone()
        if trigger_sql and 'attribution_old' in str(trigger_sql[0]).lower():
            print(f"    ⚠️ Référence à attribution_old détectée!")
            print(f"    SQL: {trigger_sql[0][:100]}...")
else:
    print("  ✓ Aucun déclencheur trouvé")

# Vérifier les indexes
print("\n=== Index sur attribution_attribution ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='attribution_attribution';")
indexes = cursor.fetchall()
for idx in indexes:
    print(f"  - {idx[0]}")

# Proposition de nettoyage
if old_tables or any('attribution_old' in str(t).lower() for t in triggers):
    print("\n" + "="*60)
    print("🔧 ACTIONS CORRECTIVES RECOMMANDÉES:")
    print("="*60)
    
    if old_tables:
        print("\n1. Supprimer les tables orphelines:")
        for table in old_tables:
            print(f"   DROP TABLE IF EXISTS {table};")
    
    if any('attribution_old' in str(t).lower() for t in triggers):
        print("\n2. Supprimer les triggers problématiques:")
        problematic_triggers = [t[0] for t in triggers if 'attribution_old' in str(cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (t[0],)).fetchone()[0]).lower()]
        for trigger in problematic_triggers:
            print(f"   DROP TRIGGER IF EXISTS {trigger};")
    
    print("\n3. Voulez-vous appliquer ces corrections automatiquement? (y/n)")
    response = input("Réponse: ").strip().lower()
    
    if response == 'y':
        try:
            for table in old_tables:
                print(f"   Suppression de {table}...")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            for trigger in [t[0] for t in triggers]:
                trigger_sql = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (trigger,)).fetchone()
                if trigger_sql and 'attribution_old' in str(trigger_sql[0]).lower():
                    print(f"   Suppression du trigger {trigger}...")
                    cursor.execute(f"DROP TRIGGER IF EXISTS {trigger}")
            
            conn.commit()
            print("\n✅ Nettoyage effectué avec succès!")
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Erreur lors du nettoyage: {e}")
    else:
        print("\n⏸️ Aucune action effectuée. Vous pouvez exécuter les commandes SQL manuellement.")
else:
    print("\n✅ Aucun problème détecté dans la base de données!")

conn.close()
print("\n" + "="*60)
print("Script terminé.")
print("="*60)
