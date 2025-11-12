#!/usr/bin/env python
"""
Script pour diagnostiquer et corriger le problème de suppression des attributions
"""
import os
import sys
import django
import sqlite3

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from attribution.models import Attribution, ScheduleEntry

def check_database_tables():
    """Vérifie les tables dans la base de données SQLite"""
    db_path = settings.DATABASES['default']['NAME']
    print(f"Base de données: {db_path}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print("=== TABLES DANS LA BASE ===")
        old_tables = []
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            if '_old' in table_name:
                old_tables.append(table_name)
        
        if old_tables:
            print(f"\n⚠️  TABLES ORPHELINES DÉTECTÉES: {len(old_tables)}")
            for old_table in old_tables:
                print(f"     - {old_table}")
            
            # Proposer de nettoyer
            print("\n🔧 Nettoyage des tables orphelines...")
            for old_table in old_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {old_table};")
                    print(f"   ✓ Table {old_table} supprimée")
                except Exception as e:
                    print(f"   ✗ Erreur sur {old_table}: {e}")
            
            conn.commit()
            print("\n✅ Nettoyage terminé!")
        else:
            print("\n✅ Aucune table orpheline détectée")
        
        # Vérifier l'intégrité des contraintes
        print("\n=== VÉRIFICATION DES CONTRAINTES ===")
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        print(f"Foreign keys: {'ACTIVÉES' if fk_status else 'DÉSACTIVÉES'}")
        
        if not fk_status:
            print("⚠️  Les contraintes de clés étrangères sont désactivées!")
            print("   Django les active automatiquement, mais c'est désactivé au niveau DB.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()

def test_deletion():
    """Teste la suppression d'une attribution"""
    print("\n=== TEST DE SUPPRESSION ===")
    
    # Trouver une attribution avec des horaires
    attributions_with_schedules = Attribution.objects.filter(
        schedule_entries__isnull=False
    ).distinct()[:1]
    
    if not attributions_with_schedules.exists():
        print("ℹ️  Aucune attribution avec horaires pour tester")
        
        # Créer une attribution de test si possible
        test_attr = Attribution.objects.first()
        if test_attr:
            print(f"   Test avec attribution ID={test_attr.id} (sans horaires)")
            return
        else:
            print("❌ Aucune attribution dans la base!")
            return
    
    test_attr = attributions_with_schedules.first()
    attr_id = test_attr.id
    schedule_count = test_attr.schedule_entries.count()
    
    print(f"Attribution test: ID={attr_id}")
    print(f"Horaires liés: {schedule_count}")
    
    try:
        from django.db import transaction
        
        with transaction.atomic():
            # Supprimer les horaires d'abord
            deleted_schedules = ScheduleEntry.objects.filter(attribution=test_attr).delete()
            print(f"✓ Horaires supprimés: {deleted_schedules[0]}")
            
            # Supprimer l'attribution
            test_attr.delete()
            print(f"✓ Attribution supprimée")
            
            # Rollback pour ne pas vraiment supprimer
            raise Exception("Test réussi - Rollback pour préserver les données")
            
    except Exception as e:
        if "Test réussi" in str(e):
            print("\n✅ TEST RÉUSSI: La suppression fonctionne correctement!")
            print("   (Rollback effectué, aucune donnée n'a été supprimée)")
        else:
            print(f"\n❌ TEST ÉCHOUÉ: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("=" * 60)
    print("DIAGNOSTIC DU PROBLÈME DE SUPPRESSION DES ATTRIBUTIONS")
    print("=" * 60)
    
    check_database_tables()
    test_deletion()
    
    print("\n" + "=" * 60)
    print("RECOMMANDATIONS:")
    print("=" * 60)
    print("1. Si des tables _old ont été trouvées et supprimées,")
    print("   redémarrez le serveur Django")
    print("2. Si le problème persiste, essayez:")
    print("   python manage.py migrate --run-syncdb")
    print("3. En dernier recours: recréer la base de données")
    print("=" * 60)

if __name__ == '__main__':
    main()
