#!/usr/bin/env python
"""Script pour tester la validation du formulaire"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.forms import ScheduleEntryForm
from attribution.models import Attribution
from datetime import date

print("=== Test de validation du formulaire ScheduleEntryForm ===")

if Attribution.objects.exists():
    attribution = Attribution.objects.first()
    
    # Données de test
    test_data = {
        'attribution': attribution.id,
        'annee_academique': '2024-2025',
        'semaine_debut': '2024-10-21',
        'jour': 'lundi',
        'creneau': 'am',
        'salle': 'B1',
        'remarques': 'Test formulaire'
    }
    
    print(f"\nDonnées de test: {test_data}")
    
    # Test du formulaire
    form = ScheduleEntryForm(data=test_data)
    
    if form.is_valid():
        print("\n✓ Le formulaire est VALIDE")
        print(f"Cleaned data: {form.cleaned_data}")
        
        # Test de sauvegarde
        try:
            instance = form.save(commit=False)
            print(f"\n✓ Instance créée: {instance}")
            print(f"  - Attribution: {instance.attribution}")
            print(f"  - Année: {instance.annee_academique}")
            print(f"  - Jour: {instance.jour}")
            print(f"  - Créneau: {instance.creneau}")
            
        except Exception as e:
            print(f"\n✗ Erreur lors de la sauvegarde: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✗ Le formulaire est INVALIDE")
        print(f"Erreurs: {form.errors}")
        print(f"Erreurs non-field: {form.non_field_errors()}")
else:
    print("⚠ Aucune attribution disponible")

print("\n=== Fin du test ===")
