#!/usr/bin/env python
"""
Script pour synchroniser le champ section des cours d'attribution avec le code de l'organisation
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Cours_Attribution

def sync_cours_section():
    """Synchronise le champ section avec le code de l'organisation"""
    cours_list = Cours_Attribution.objects.exclude(organisation__isnull=True)
    
    updated_count = 0
    for cours in cours_list:
        if cours.organisation and cours.section != cours.organisation.code:
            print(f"Cours {cours.code_ue}: section '{cours.section}' -> '{cours.organisation.code}'")
            cours.section = cours.organisation.code
            cours.save()
            updated_count += 1
    
    print(f"\n{updated_count} cours mis à jour")
    
    # Afficher la nouvelle répartition
    from django.db.models import Count
    repartition = Cours_Attribution.objects.values('section').annotate(count=Count('id'))
    print("\nNouvelle répartition par section:")
    for r in repartition:
        print(f"  Section {r['section']}: {r['count']} cours")

if __name__ == '__main__':
    sync_cours_section()
