#!/usr/bin/env python
"""
Script pour déboguer les valeurs exactes passées au template
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
from tracking.models import TeachingProgress, AcademicWeek
from courses.models import Course
from teachers.models import Teacher

def debug_stats():
    # Année académique actuelle
    current_year = timezone.now().year
    academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
    
    print(f"=== DÉBOGAGE DES STATISTIQUES ===")
    print(f"Année académique: {academic_year}")
    
    # Heures effectuées (total de tous les enregistrements)
    total_hours_done = TeachingProgress.objects.aggregate(total=Sum('hours_done'))['total'] or 0
    print(f"total_hours_done: {total_hours_done} (type: {type(total_hours_done)})")
    
    # Heures allouées (basé sur les charges des enseignants)
    total_hours_allocated = Attribution.objects.select_related('code_ue').filter(
        code_ue__isnull=False
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    )['total'] or 0
    print(f"total_hours_allocated: {total_hours_allocated} (type: {type(total_hours_allocated)})")
    
    # Calcul du pourcentage
    global_progress_percentage = 0
    if total_hours_allocated > 0:
        global_progress_percentage = (float(total_hours_done) / float(total_hours_allocated)) * 100
    
    print(f"global_progress_percentage: {global_progress_percentage}")
    
    # Statistiques pour la carte
    stats = {
        'current_week': AcademicWeek.objects.filter(is_active=True, academic_year=academic_year).order_by('codesemaine').first(),
        'total_hours_done': total_hours_done,
        'total_hours_allocated': total_hours_allocated,
        'global_progress_percentage': round(global_progress_percentage, 1),
        'total_courses': Course.objects.count(),
        'total_teachers': Teacher.objects.count(),
    }
    
    print(f"\n=== STATS FINALES ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == '__main__':
    debug_stats()
