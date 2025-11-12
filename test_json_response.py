#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from attribution.views import heures_supplementaires_par_grade

# Créer une fausse requête
factory = RequestFactory()
request = factory.get('/attribution/heures-supplementaires-grade/')
request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

# Appeler la vue
response = heures_supplementaires_par_grade(request)

print("=" * 60)
print("TEST DE LA RÉPONSE JSON")
print("=" * 60)

print(f"\nStatus Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'Not set')}")

# Parser le JSON
try:
    data = json.loads(response.content.decode('utf-8'))
    
    print("\n📋 STRUCTURE DES DONNÉES:")
    print(f"  - stats_par_grade: {len(data.get('stats_par_grade', []))} grades")
    print(f"  - totaux: {data.get('totaux', {})}")
    print(f"  - annee_selectionnee: {data.get('annee_selectionnee', 'None')}")
    print(f"  - annees_disponibles: {data.get('annees_disponibles', [])}")
    
    print("\n📊 DONNÉES DÉTAILLÉES:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n✅ La vue retourne correctement les données JSON!")
    
except json.JSONDecodeError as e:
    print(f"\n❌ ERREUR: Impossible de parser le JSON: {e}")
    print(f"\nContenu brut: {response.content.decode('utf-8')[:500]}")
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
