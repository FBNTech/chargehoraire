#!/usr/bin/env python
"""
Suppression DIRECTE via SQL brut pour contourner le problème SQLite
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

# ID à supprimer
attribution_id = 208

print(f"\n{'='*60}")
print(f"SUPPRESSION SQL DIRECTE - Attribution ID {attribution_id}")
print(f"{'='*60}\n")

try:
    with connection.cursor() as cursor:
        # 1. Vérifier si l'attribution existe
        cursor.execute("SELECT id, annee_academique, type_charge FROM attribution_attribution WHERE id = %s", [attribution_id])
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Attribution {attribution_id} introuvable")
            exit(1)
        
        print(f"✓ Attribution trouvée:")
        print(f"  - ID: {result[0]}")
        print(f"  - Année: {result[1]}")
        print(f"  - Type: {result[2]}")
        
        # 2. Compter les horaires liés
        cursor.execute("SELECT COUNT(*) FROM attribution_scheduleentry WHERE attribution_id = %s", [attribution_id])
        schedule_count = cursor.fetchone()[0]
        print(f"  - Horaires liés: {schedule_count}")
        
        # 3. Supprimer les horaires liés si nécessaire
        if schedule_count > 0:
            print(f"\n🗑️  Suppression des horaires liés...")
            cursor.execute("DELETE FROM attribution_scheduleentry WHERE attribution_id = %s", [attribution_id])
            print(f"✓ {schedule_count} horaires supprimés")
        
        # 4. Supprimer l'attribution directement
        print(f"\n🔄 Suppression SQL directe de l'attribution...")
        cursor.execute("DELETE FROM attribution_attribution WHERE id = %s", [attribution_id])
        
        # 5. Vérifier la suppression
        cursor.execute("SELECT COUNT(*) FROM attribution_attribution WHERE id = %s", [attribution_id])
        remaining = cursor.fetchone()[0]
        
        if remaining == 0:
            print(f"✅ Attribution {attribution_id} supprimée avec succès!")
        else:
            print(f"⚠️  L'attribution existe toujours (count={remaining})")
            
except Exception as e:
    print(f"\n❌ ERREUR:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    
    import traceback
    print(f"\n📋 Traceback:")
    print(traceback.format_exc())
    exit(1)

print(f"\n{'='*60}")
print("OPÉRATION TERMINÉE")
print(f"{'='*60}\n")
