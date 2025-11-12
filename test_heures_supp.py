#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Attribution

print("=" * 60)
print("TEST DES ATTRIBUTIONS SUPPLÉMENTAIRES")
print("=" * 60)

total = Attribution.objects.count()
print(f"\n📊 Total attributions: {total}")

supp_minuscule = Attribution.objects.filter(type_charge='supplementaire').count()
print(f"✅ Supplémentaires (minuscule): {supp_minuscule}")

supp_majuscule = Attribution.objects.filter(type_charge='Supplementaire').count()
print(f"✅ Supplémentaires (majuscule): {supp_majuscule}")

reguliere_minuscule = Attribution.objects.filter(type_charge='reguliere').count()
print(f"📝 Régulières (minuscule): {reguliere_minuscule}")

reguliere_majuscule = Attribution.objects.filter(type_charge='Reguliere').count()
print(f"📝 Régulières (majuscule): {reguliere_majuscule}")

# Afficher toutes les valeurs uniques de type_charge
types_uniques = Attribution.objects.values_list('type_charge', flat=True).distinct()
print(f"\n🔍 Types de charge uniques en base: {list(types_uniques)}")

# Tester la vue
print("\n" + "=" * 60)
print("TEST DE LA VUE heures_supplementaires_par_grade")
print("=" * 60)

if supp_minuscule > 0:
    attributions_supp = Attribution.objects.filter(type_charge='supplementaire').select_related('matricule', 'code_ue')
    
    stats_par_grade = {}
    
    for attribution in attributions_supp:
        grade = attribution.matricule.grade if attribution.matricule and attribution.matricule.grade else "Non spécifié"
        
        if grade not in stats_par_grade:
            stats_par_grade[grade] = {
                'grade': grade,
                'nombre_enseignants': set(),
                'nombre_cours': 0,
                'total_heures': 0,
            }
        
        stats_par_grade[grade]['nombre_enseignants'].add(attribution.matricule.matricule)
        stats_par_grade[grade]['nombre_cours'] += 1
        
        if attribution.code_ue:
            cmi = float(attribution.code_ue.cmi) if attribution.code_ue.cmi else 0
            td_tp = float(attribution.code_ue.td_tp) if attribution.code_ue.td_tp else 0
            stats_par_grade[grade]['total_heures'] += (cmi + td_tp)
    
    print("\n📈 Statistiques par grade:")
    for grade, stats in stats_par_grade.items():
        print(f"\n  Grade: {grade}")
        print(f"  - Enseignants: {len(stats['nombre_enseignants'])}")
        print(f"  - Cours: {stats['nombre_cours']}")
        print(f"  - Total heures: {stats['total_heures']}")
elif supp_majuscule > 0:
    print("\n⚠️  Les données sont enregistrées avec majuscule, la vue doit être modifiée!")
else:
    print("\n❌ Aucune attribution supplémentaire trouvée!")

print("\n" + "=" * 60)
