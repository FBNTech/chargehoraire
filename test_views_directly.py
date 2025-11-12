#!/usr/bin/env python
"""Script pour tester directement les vues Django"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from attribution.views import ScheduleEntryListView, ScheduleEntryCreateView
from attribution.models import ScheduleEntry

print("=== Test des vues Django ===\n")

# Créer une factory de requêtes
factory = RequestFactory()

# Test 1: Vue Liste
print("1. Test de ScheduleEntryListView")
try:
    request = factory.get('/attribution/schedule/entry/list/')
    request.user = AnonymousUser()
    
    view = ScheduleEntryListView.as_view()
    response = view(request)
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Vue accessible")
    else:
        print(f"   ✗ Erreur: {response.status_code}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Vue Création
print("\n2. Test de ScheduleEntryCreateView (GET)")
try:
    request = factory.get('/attribution/schedule/entry/create/')
    request.user = AnonymousUser()
    
    view = ScheduleEntryCreateView.as_view()
    response = view(request)
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Formulaire accessible")
    else:
        print(f"   ✗ Erreur: {response.status_code}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Vérifier les données
print("\n3. Vérification des données")
print(f"   Nombre d'horaires: {ScheduleEntry.objects.count()}")
print(f"   Années disponibles: {list(ScheduleEntry.objects.values_list('annee_academique', flat=True).distinct())}")

# Test 4: Afficher quelques horaires
print("\n4. Premiers horaires dans la base:")
for entry in ScheduleEntry.objects.all()[:5]:
    print(f"   - {entry.get_jour_display()} {entry.get_creneau_display()}: {entry.attribution.code_ue.code_ue} ({entry.attribution.code_ue.classe})")

print("\n=== Fin des tests ===")
