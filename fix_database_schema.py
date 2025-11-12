#!/usr/bin/env python
"""
Script pour corriger le schéma de la base de données
Résout le problème des tables _old en reconstruisant les contraintes FK
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def fix_database_schema():
    """Reconstruit le schéma avec les bonnes contraintes FK"""
    
    print("="*70)
    print("  CORRECTION DU SCHÉMA DE BASE DE DONNÉES")
    print("="*70)
    
    print("\n📋 Étape 1 : Vérification des contraintes FK")
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA foreign_keys')
        fk_status = cursor.fetchone()[0]
        print(f"   Foreign Keys : {'✓ ACTIVÉES' if fk_status else '✗ DÉSACTIVÉES'}")
        
        if not fk_status:
            print("   ⚠️ Activation des FK...")
            cursor.execute('PRAGMA foreign_keys = ON')
            print("   ✓ FK activées")
    
    print("\n📋 Étape 2 : Vérification de l'intégrité de la base")
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()[0]
        if result == 'ok':
            print("   ✓ Intégrité OK")
        else:
            print(f"   ✗ Problème d'intégrité : {result}")
    
    print("\n📋 Étape 3 : Liste des tables _old résiduelles")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%_old'
        """)
        old_tables = cursor.fetchall()
        
        if old_tables:
            print(f"   ⚠️ {len(old_tables)} table(s) _old trouvée(s) :")
            for table in old_tables:
                print(f"      - {table[0]}")
            
            print("\n   🧹 Suppression des tables _old...")
            cursor.execute('PRAGMA foreign_keys = OFF')
            for table in old_tables:
                cursor.execute(f'DROP TABLE IF EXISTS {table[0]}')
                print(f"      ✓ {table[0]} supprimée")
            cursor.execute('PRAGMA foreign_keys = ON')
        else:
            print("   ✓ Aucune table _old")
    
    print("\n📋 Étape 4 : Recréation des migrations attribution")
    print("   ⚠️ Ceci va supprimer et recréer les tables Attribution et ScheduleEntry")
    print("   ⚠️ TOUTES LES DONNÉES SERONT PERDUES !")
    
    response = input("\n   Continuer ? (OUI/non) : ")
    if response.strip().upper() != 'OUI':
        print("\n❌ Opération annulée")
        return
    
    print("\n   🔄 Suppression des anciennes migrations attribution...")
    
    # Supprimer les tables manuellement
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA foreign_keys = OFF')
        
        tables_to_drop = ['attribution_scheduleentry', 'attribution_attribution']
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"      ✓ Table {table} supprimée")
            except Exception as e:
                print(f"      ⚠️ {table}: {e}")
        
        cursor.execute('PRAGMA foreign_keys = ON')
    
    print("\n   🔄 Suppression des enregistrements de migration...")
    from django.db.migrations.recorder import MigrationRecorder
    recorder = MigrationRecorder(connection)
    recorder.migration_qs.filter(app='attribution').delete()
    print("      ✓ Enregistrements supprimés")
    
    print("\n   🔄 Recréation des tables avec migrations...")
    try:
        call_command('migrate', 'attribution', verbosity=2)
        print("      ✓ Migrations appliquées")
    except Exception as e:
        print(f"      ✗ Erreur : {e}")
        return
    
    print("\n✅ SCHÉMA CORRIGÉ AVEC SUCCÈS !")
    print("\n📝 Prochaines étapes :")
    print("   1. Réimporter vos données (cours, enseignants, attributions)")
    print("   2. Tester la suppression d'un cours")
    print("   3. Vérifier qu'il n'y a plus d'erreur _old")

if __name__ == '__main__':
    fix_database_schema()
    print("\n" + "="*70)
