#!/usr/bin/env python
"""
Script pour calculer le nombre total d'heures allouées basé sur les charges des enseignants
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Course
from attribution.models import Attribution
from teachers.models import Teacher
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Count

def calculate_total_hours():
    """Calcule le nombre total d'heures allouées basé sur les charges des enseignants"""
    
    print("=== CALCUL DU NOMBRE TOTAL D'HEURES ALLOUÉES (BASÉ SUR LES CHARGES) ===\n")
    
    # Récupérer toutes les attributions avec leurs cours associés
    attributions = Attribution.objects.select_related('matricule', 'code_ue').filter(
        matricule__isnull=False,
        code_ue__isnull=False
    )
    
    total_hours = 0
    total_attributions = 0
    
    print("📊 STATISTIQUES GÉNÉRALES:")
    print(f"   • Nombre total d'attributions: {attributions.count()}")
    print(f"   • Nombre d'enseignants avec charges: {attributions.values('matricule').distinct().count()}")
    print(f"   • Nombre de cours attribués: {attributions.values('code_ue').distinct().count()}")
    
    # Calcul du total des heures allouées via les attributions
    total_result = attributions.aggregate(
        total_hours=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    )
    
    total_hours = total_result['total_hours'] or 0
    
    print(f"   • TOTAL HEURES ALLOUÉES: {total_hours}")
    
    print("\n📋 RÉPARTITION PAR TYPE DE CHARGE:")
    charge_stats = attributions.values('type_charge').annotate(
        nombre_attributions=Count('id'),
        total_heures=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    ).order_by('-total_heures')
    
    for charge in charge_stats:
        type_charge = charge['type_charge'] or 'Non défini'
        print(f"   • {type_charge.capitalize()}: {charge['total_heures']} heures ({charge['nombre_attributions']} attributions)")
    
    print("\n📋 RÉPARTITION PAR DÉPARTEMENT:")
    dept_stats = attributions.values('code_ue__departement').annotate(
        nombre_attributions=Count('id'),
        total_heures=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    ).order_by('-total_heures')
    
    for dept in dept_stats:
        departement = dept['code_ue__departement'] or 'Non défini'
        print(f"   • {departement}: {dept['total_heures']} heures ({dept['nombre_attributions']} attributions)")
    
    print("\n📋 RÉPARTITION PAR CLASSE:")
    classe_stats = attributions.values('code_ue__classe').annotate(
        nombre_attributions=Count('id'),
        total_heures=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    ).order_by('-total_heures')
    
    for classe in classe_stats[:10]:  # Top 10 des classes
        classe_nom = classe['code_ue__classe'] or 'Non défini'
        print(f"   • {classe_nom}: {classe['total_heures']} heures ({classe['nombre_attributions']} attributions)")
    
    print("\n📋 TOP 10 ENSEIGNANTS PAR HEURES ALLOUÉES:")
    teacher_stats = attributions.values('matricule__nom_complet').annotate(
        nombre_attributions=Count('id'),
        total_heures=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    ).order_by('-total_heures')[:10]
    
    for teacher in teacher_stats:
        nom = teacher['matricule__nom_complet'] or 'Non défini'
        print(f"   • {nom}: {teacher['total_heures']} heures ({teacher['nombre_attributions']} cours)")
    
    print(f"\n🎯 RÉSULTAT FINAL: {total_hours} heures allouées au total (basé sur les charges des enseignants)")
    
    return total_hours

if __name__ == '__main__':
    calculate_total_hours()
