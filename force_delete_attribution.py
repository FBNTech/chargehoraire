#!/usr/bin/env python
"""
Script pour forcer la suppression d'attribution 208
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Attribution, ScheduleEntry
from django.db import connection, transaction

# ID à supprimer
attribution_id = 208

print(f"\n{'='*60}")
print(f"SUPPRESSION FORCÉE - Attribution ID {attribution_id}")
print(f"{'='*60}\n")

try:
    with transaction.atomic():
        # Récupérer l'attribution
        attribution = Attribution.objects.get(id=attribution_id)
        print(f"✓ Attribution trouvée:")
        print(f"  - ID: {attribution.id}")
        print(f"  - Enseignant: {attribution.matricule}")
        print(f"  - Code UE: {attribution.code_ue}")
        
        # Compter les horaires liés
        schedule_count = ScheduleEntry.objects.filter(attribution=attribution).count()
        print(f"  - Horaires liés: {schedule_count}")
        
        # Supprimer manuellement les horaires d'abord
        if schedule_count > 0:
            print(f"\n🗑️  Suppression des {schedule_count} horaires liés...")
            ScheduleEntry.objects.filter(attribution=attribution).delete()
            print(f"✓ Horaires supprimés")
        
        # Vérifier les FK
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys;")
            fk_enabled = cursor.fetchone()[0]
            print(f"\n🔗 Foreign Keys: {'Activées' if fk_enabled else 'Désactivées'}")
            
            if fk_enabled:
                # Désactiver temporairement les FK
                print("⚠️  Désactivation temporaire des FK...")
                cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Suppression de l'attribution
        print(f"\n🔄 Suppression de l'attribution...")
        attribution.delete()
        
        # Réactiver les FK
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
        
        print(f"✅ Attribution {attribution_id} supprimée avec succès!")
        
except Attribution.DoesNotExist:
    print(f"❌ Attribution {attribution_id} introuvable")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERREUR lors de la suppression:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    
    import traceback
    print(f"\n📋 Traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print(f"\n{'='*60}")
print("SUPPRESSION TERMINÉE")
print(f"{'='*60}\n")
