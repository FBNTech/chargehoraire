#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Attribution

print("=" * 60)
print("TEST DE LA VUE CORRIGÉE")
print("=" * 60)

# Test avec le bon filtre (Majuscule)
attributions = Attribution.objects.filter(type_charge='Supplementaire').select_related('matricule', 'code_ue')

print(f"\n✅ Attributions supplémentaires trouvées: {attributions.count()}")

# Grouper par grade et calculer les statistiques
stats_par_grade = {}

for attribution in attributions:
    grade = attribution.matricule.grade if attribution.matricule and attribution.matricule.grade else "Non spécifié"
    
    if grade not in stats_par_grade:
        stats_par_grade[grade] = {
            'grade': grade,
            'nombre_enseignants': set(),
            'nombre_cours': 0,
            'total_cmi': 0,
            'total_td_tp': 0,
            'total_heures': 0,
        }
    
    # Ajouter l'enseignant (set pour éviter les doublons)
    stats_par_grade[grade]['nombre_enseignants'].add(attribution.matricule.matricule)
    
    # Compter le cours
    stats_par_grade[grade]['nombre_cours'] += 1
    
    # Calculer les heures
    if attribution.code_ue:
        cmi = float(attribution.code_ue.cmi) if attribution.code_ue.cmi else 0
        td_tp = float(attribution.code_ue.td_tp) if attribution.code_ue.td_tp else 0
        
        stats_par_grade[grade]['total_cmi'] += cmi
        stats_par_grade[grade]['total_td_tp'] += td_tp
        stats_par_grade[grade]['total_heures'] += (cmi + td_tp)

# Convertir les sets en nombres
for grade in stats_par_grade:
    stats_par_grade[grade]['nombre_enseignants'] = len(stats_par_grade[grade]['nombre_enseignants'])

# Convertir en liste pour le template et trier par grade
stats_list = sorted(stats_par_grade.values(), key=lambda x: x['grade'])

print("\n📈 RÉSULTATS PAR GRADE:")
print("-" * 60)

for stat in stats_list:
    print(f"\n🎓 Grade: {stat['grade']}")
    print(f"   👥 Enseignants: {stat['nombre_enseignants']}")
    print(f"   📚 Cours: {stat['nombre_cours']}")
    print(f"   ⏰ CMI: {stat['total_cmi']:.1f}h")
    print(f"   ⏰ TP+TD: {stat['total_td_tp']:.1f}h")
    print(f"   ⏰ TOTAL: {stat['total_heures']:.1f}h")

# Calculer les totaux généraux
totaux = {
    'nombre_enseignants': sum(s['nombre_enseignants'] for s in stats_list),
    'nombre_cours': sum(s['nombre_cours'] for s in stats_list),
    'total_cmi': sum(s['total_cmi'] for s in stats_list),
    'total_td_tp': sum(s['total_td_tp'] for s in stats_list),
    'total_heures': sum(s['total_heures'] for s in stats_list),
}

print("\n" + "=" * 60)
print("📊 TOTAUX GÉNÉRAUX")
print("=" * 60)
print(f"👥 Total enseignants: {totaux['nombre_enseignants']}")
print(f"📚 Total cours: {totaux['nombre_cours']}")
print(f"⏰ Total CMI: {totaux['total_cmi']:.1f}h")
print(f"⏰ Total TP+TD: {totaux['total_td_tp']:.1f}h")
print(f"⏰ TOTAL HEURES: {totaux['total_heures']:.1f}h")
print("=" * 60)

# Récupérer les années disponibles
annees = Attribution.objects.filter(
    type_charge='Supplementaire'
).values_list('annee_academique', flat=True).distinct().order_by('-annee_academique')

print(f"\n📅 Années académiques disponibles: {list(annees)}")
print("\n✅ La vue devrait maintenant fonctionner correctement!")
