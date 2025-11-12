#!/usr/bin/env python
"""
Script pour déboguer les valeurs du dashboard
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from attribution.models import Attribution
from tracking.models import TeachingProgress

def debug_dashboard():
    # Année académique actuelle
    current_year = timezone.now().year
    academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
    
    print(f"Année académique: {academic_year}")
    
    # Heures effectuées
    total_hours_done = TeachingProgress.objects.filter(
        week__academic_year=academic_year
    ).aggregate(total=Sum('hours_done'))['total'] or 0
    
    print(f"Heures effectuées (année courante): {total_hours_done}")
    
    # Heures effectuées toutes années
    total_hours_done_all = TeachingProgress.objects.aggregate(total=Sum('hours_done'))['total'] or 0
    print(f"Heures effectuées (toutes années): {total_hours_done_all}")
    
    # Attributions pour l'année courante
    attributions_current = Attribution.objects.filter(
        matricule__isnull=False,
        code_ue__isnull=False,
        annee_academique=academic_year
    )
    
    print(f"Attributions année courante: {attributions_current.count()}")
    
    # Attributions toutes années
    attributions_all = Attribution.objects.filter(
        matricule__isnull=False,
        code_ue__isnull=False
    )
    
    print(f"Attributions toutes années: {attributions_all.count()}")
    
    # Heures allouées année courante
    total_hours_allocated_current = attributions_current.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    )['total'] or 0
    
    print(f"Heures allouées (année courante): {total_hours_allocated_current}")
    
    # Heures allouées toutes années
    total_hours_allocated_all = attributions_all.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    )['total'] or 0
    
    print(f"Heures allouées (toutes années): {total_hours_allocated_all}")

if __name__ == '__main__':
    debug_dashboard()
