#!/usr/bin/env python
"""
Solution NON DESTRUCTIVE : Réparer les contraintes FK sans perdre les données
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
import sqlite3

def fix_fk_constraints():
    """Répare les contraintes FK en reconstruisant la base de manière propre"""
    
    print("="*70)
    print("  RÉPARATION DES CONTRAINTES FK (SANS PERTE DE DONNÉES)")
    print("="*70)
    
    db_path = 'd:\\FABONK\\ACH WEB\\chargehoraire\\db.sqlite3'
    backup_path = db_path + '.backup'
    
    print(f"\n📋 Étape 1 : Sauvegarde de la base")
    print(f"   Source : {db_path}")
    print(f"   Backup : {backup_path}")
    
    import shutil
    try:
        shutil.copy2(db_path, backup_path)
        print("   ✅ Sauvegarde créée avec succès")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde : {e}")
        return
    
    print("\n📋 Étape 2 : Nettoyage des tables _old")
    with connection.cursor() as cursor:
        # Lister les tables _old
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%_old'
        """)
        old_tables = cursor.fetchall()
        
        if old_tables:
            print(f"   Trouvé {len(old_tables)} table(s) _old")
            cursor.execute('PRAGMA foreign_keys = OFF')
            for table in old_tables:
                cursor.execute(f'DROP TABLE IF EXISTS {table[0]}')
                print(f"   ✓ {table[0]} supprimée")
            cursor.execute('PRAGMA foreign_keys = ON')
        else:
            print("   ✓ Aucune table _old à nettoyer")
    
    print("\n📋 Étape 3 : Reconstruction de la base avec FK activées")
    
    # Créer une nouvelle base propre
    new_db_path = db_path + '.new'
    
    try:
        # Connecter à l'ancienne base
        old_conn = sqlite3.connect(db_path)
        old_conn.row_factory = sqlite3.Row
        
        # Créer nouvelle base avec FK activées
        new_conn = sqlite3.connect(new_db_path)
        new_conn.execute('PRAGMA foreign_keys = ON')
        
        print("   🔄 Export du schéma...")
        
        # Exporter le schéma (sans les tables _old)
        old_cursor = old_conn.cursor()
        old_cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE '%_old'
            AND sql IS NOT NULL
        """)
        
        schemas = old_cursor.fetchall()
        new_cursor = new_conn.cursor()
        
        for schema in schemas:
            try:
                new_cursor.execute(schema[0])
            except Exception as e:
                print(f"      ⚠️ Schéma: {e}")
        
        print("   ✓ Schéma exporté")
        
        print("\n   🔄 Copie des données...")
        
        # Copier les données table par table
        old_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE '%_old'
        """)
        
        tables = [row[0] for row in old_cursor.fetchall()]
        
        # Désactiver FK temporairement pour la copie
        new_cursor.execute('PRAGMA foreign_keys = OFF')
        
        for table in tables:
            try:
                # Lire les données
                old_cursor.execute(f'SELECT * FROM {table}')
                rows = old_cursor.fetchall()
                
                if rows:
                    # Obtenir les noms de colonnes
                    columns = [description[0] for description in old_cursor.description]
                    placeholders = ','.join(['?' for _ in columns])
                    cols = ','.join(columns)
                    
                    # Insérer dans la nouvelle base
                    insert_sql = f'INSERT INTO {table} ({cols}) VALUES ({placeholders})'
                    new_cursor.executemany(insert_sql, rows)
                    
                    print(f"   ✓ {table}: {len(rows)} ligne(s) copiée(s)")
                else:
                    print(f"   - {table}: vide")
                    
            except Exception as e:
                print(f"   ⚠️ {table}: {e}")
        
        # Réactiver FK
        new_cursor.execute('PRAGMA foreign_keys = ON')
        
        new_conn.commit()
        
        print("\n   ✅ Nouvelle base créée avec succès")
        
        # Fermer les connexions
        old_conn.close()
        new_conn.close()
        
        print("\n📋 Étape 4 : Remplacement de l'ancienne base")
        print("   ⚠️ L'ancienne base sera remplacée par la nouvelle")
        
        response = input("   Continuer ? (OUI/non) : ")
        if response.strip().upper() != 'OUI':
            print("\n   ❌ Opération annulée")
            print(f"   ℹ️  Nouvelle base disponible : {new_db_path}")
            print(f"   ℹ️  Backup disponible : {backup_path}")
            return
        
        # Remplacer l'ancienne base
        import os
        os.replace(new_db_path, db_path)
        
        print("\n✅ BASE DE DONNÉES RÉPARÉE AVEC SUCCÈS !")
        print(f"\n📝 Fichiers :")
        print(f"   - Base active : {db_path}")
        print(f"   - Backup : {backup_path}")
        print("\n🧪 Test recommandé :")
        print("   python test_deletion_course.py")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        print(f"\n💾 Votre base originale est sauvegardée : {backup_path}")

if __name__ == '__main__':
    fix_fk_constraints()
    print("\n" + "="*70)
