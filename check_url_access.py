#!/usr/bin/env python
"""Vérifier l'accès à la page liste des horaires"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse

print("=== Vérification des URLs ===\n")

try:
    # Générer l'URL de la liste
    list_url = reverse('attribution:schedule_entry_list')
    print(f"✓ URL de la liste : {list_url}")
    print(f"  Accès complet : http://127.0.0.1:8000{list_url}")
    
    # Générer l'URL de création
    create_url = reverse('attribution:schedule_entry_create')
    print(f"\n✓ URL de création : {create_url}")
    print(f"  Accès complet : http://127.0.0.1:8000{create_url}")
    
    # Générer l'URL du générateur rapide
    builder_url = reverse('attribution:schedule_builder')
    print(f"\n✓ URL générateur rapide : {builder_url}")
    print(f"  Accès complet : http://127.0.0.1:8000{builder_url}")
    
except Exception as e:
    print(f"✗ Erreur : {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("COPIEZ ET COLLEZ CETTE URL DANS VOTRE NAVIGATEUR:")
print("="*50)
print("http://127.0.0.1:8000/attribution/schedule/entry/list/")
print("="*50)
