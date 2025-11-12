#!/usr/bin/env python
"""Script pour tester la création d'horaires"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import ScheduleEntry, Attribution
from datetime import date

# Test 1: Vérifier le modèle
print("=== Test du modèle ScheduleEntry ===")
print(f"Nombre d'entrées actuelles: {ScheduleEntry.objects.count()}")

# Test 2: Vérifier qu'il y a des attributions disponibles
print(f"\nNombre d'attributions disponibles: {Attribution.objects.count()}")

if Attribution.objects.exists():
    # Test 3: Créer une entrée de test
    print("\n=== Test de création ===")
    try:
        attribution = Attribution.objects.first()
        print(f"Attribution utilisée: {attribution}")
        
        entry = ScheduleEntry(
            attribution=attribution,
            annee_academique="2024-2025",
            semaine_debut=date(2024, 10, 21),
            jour='lundi',
            creneau='am',
            salle='B1',
            remarques='Test'
        )
        entry.save()
        print(f"✓ Entrée créée avec succès: ID={entry.id}")
        
        # Vérifier que l'entrée existe
        if ScheduleEntry.objects.filter(id=entry.id).exists():
            print("✓ L'entrée est bien dans la base de données")
        
        # Supprimer l'entrée de test
        entry.delete()
        print("✓ Entrée de test supprimée")
        
    except Exception as e:
        print(f"✗ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⚠ Aucune attribution disponible. Créez d'abord des attributions.")

print("\n=== Fin des tests ===")
