#!/usr/bin/env python
"""
Script pour nettoyer les tables temporaires _old dans SQLite
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def cleanup_old_tables():
    """Supprime toutes les tables temporaires _old de SQLite"""
    print("🔍 Recherche des tables _old dans la base de données...")
    
    with connection.cursor() as cursor:
        # Lister toutes les tables _old
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%_old'
        """)
        
        old_tables = cursor.fetchall()
        
        if not old_tables:
            print("✅ Aucune table _old trouvée. Base de données propre !")
            return
        
        print(f"\n📋 Tables _old trouvées : {len(old_tables)}")
        for table in old_tables:
            print(f"   - {table[0]}")
        
        print("\n🧹 Nettoyage en cours...")
        
        # Désactiver temporairement les FK pour le nettoyage
        cursor.execute('PRAGMA foreign_keys = OFF')
        
        count = 0
        for table in old_tables:
            table_name = table[0]
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
                print(f"   ✓ {table_name} supprimée")
                count += 1
            except Exception as e:
                print(f"   ✗ Erreur pour {table_name}: {e}")
        
        # Réactiver les FK
        cursor.execute('PRAGMA foreign_keys = ON')
        
        print(f"\n✅ Nettoyage terminé : {count}/{len(old_tables)} table(s) supprimée(s)")
        
        # Vérification finale
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%_old'
        """)
        remaining = cursor.fetchall()
        
        if remaining:
            print(f"\n⚠️ Tables restantes : {[t[0] for t in remaining]}")
        else:
            print("\n🎉 Base de données complètement nettoyée !")

if __name__ == '__main__':
    print("="*60)
    print("  NETTOYAGE DES TABLES TEMPORAIRES _OLD")
    print("="*60)
    cleanup_old_tables()
    print("="*60)
