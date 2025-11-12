#!/usr/bin/env python
"""
Script pour tester la suppression d'attribution avec détails
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Attribution, ScheduleEntry
from django.db import connection

# ID à tester
attribution_id = 208

print(f"\n{'='*60}")
print(f"TEST DE SUPPRESSION - Attribution ID {attribution_id}")
print(f"{'='*60}\n")

try:
    # Récupérer l'attribution
    attribution = Attribution.objects.get(id=attribution_id)
    print(f"✓ Attribution trouvée:")
    print(f"  - ID: {attribution.id}")
    print(f"  - Enseignant: {attribution.matricule}")
    print(f"  - Code UE: {attribution.code_ue}")
    print(f"  - Année: {attribution.annee_academique}")
    
    # Compter les ScheduleEntry liés
    schedule_count = ScheduleEntry.objects.filter(attribution=attribution).count()
    print(f"\n  - Horaires liés: {schedule_count}")
    
    if schedule_count > 0:
        print(f"\n  📋 Liste des horaires liés:")
        for entry in ScheduleEntry.objects.filter(attribution=attribution)[:5]:
            print(f"     - ID {entry.id}: {entry.jour} {entry.creneau} ({entry.salle})")
        if schedule_count > 5:
            print(f"     ... et {schedule_count - 5} autres")
    
    # Vérifier les contraintes FK
    print(f"\n{'='*60}")
    print("VÉRIFICATION DES CONTRAINTES")
    print(f"{'='*60}\n")
    
    with connection.cursor() as cursor:
        # Activer les FK pour SQLite
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()
        print(f"Foreign Keys actives: {fk_status[0] == 1}")
        
        # Obtenir les informations de la table
        cursor.execute("PRAGMA table_info(attribution_attribution);")
        print(f"\n📊 Structure de attribution_attribution:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
    
    # Tester la suppression
    print(f"\n{'='*60}")
    print("TEST DE SUPPRESSION")
    print(f"{'='*60}\n")
    
    choice = input(f"⚠️  Voulez-vous vraiment supprimer l'attribution {attribution_id}? (yes/no): ")
    
    if choice.lower() == 'yes':
        print("\n🔄 Suppression en cours...")
        attribution.delete()
        print("✅ Attribution supprimée avec succès!")
    else:
        print("⏸️  Suppression annulée.")
        
except Attribution.DoesNotExist:
    print(f"❌ Attribution {attribution_id} introuvable")
except Exception as e:
    print(f"\n❌ ERREUR:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    
    import traceback
    print(f"\n📋 Traceback complet:")
    print(traceback.format_exc())

print(f"\n{'='*60}")
print("TEST TERMINÉ")
print(f"{'='*60}\n")
