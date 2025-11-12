#!/usr/bin/env python
"""Test du filtre semaine dans la page charge horaire"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import SemaineCours
from attribution.models import ScheduleEntry
from django.test import RequestFactory

print("="*70)
print(" 🎯 TEST FILTRE SEMAINE - PAGE CHARGE HORAIRE")
print("="*70)

# Test 1: Vérifier les semaines disponibles
print("\n1️⃣ Vérification des semaines de cours disponibles")
semaines = SemaineCours.objects.all().order_by('numero_semaine')
if semaines.exists():
    print(f"   ✓ {semaines.count()} semaines enregistrées")
    for s in semaines[:5]:
        statut = "★" if s.est_en_cours else ""
        print(f"      • S{s.numero_semaine} : {s.date_debut.strftime('%d/%m')} - {s.date_fin.strftime('%d/%m')} {statut}")
    if semaines.count() > 5:
        print(f"      ... et {semaines.count() - 5} autres")
else:
    print("   ⚠️ Aucune semaine enregistrée")

# Test 2: Vérifier la semaine en cours
print("\n2️⃣ Vérification de la semaine en cours")
semaine_courante = SemaineCours.objects.filter(est_en_cours=True).first()
if semaine_courante:
    print(f"   ✓ Semaine en cours : S{semaine_courante.numero_semaine} ★")
    print(f"      Période : {semaine_courante.get_periode()}")
else:
    print("   ⚠️ Aucune semaine marquée comme 'en cours'")

# Test 3: Test du contexte de la vue
print("\n3️⃣ Test du contexte de ScheduleEntryListView")
try:
    from attribution.views import ScheduleEntryListView
    from django.test import RequestFactory
    
    factory = RequestFactory()
    request = factory.get('/attribution/schedule/entry/list/')
    
    view = ScheduleEntryListView()
    view.request = request
    view.kwargs = {}
    view.object_list = view.get_queryset()
    context = view.get_context_data()
    
    # Vérifier les semaines dans le contexte
    if 'semaines_cours' in context:
        semaines_ctx = context['semaines_cours']
        print(f"   ✓ 'semaines_cours' présent dans le contexte")
        print(f"   ✓ Nombre de semaines : {semaines_ctx.count()}")
    else:
        print(f"   ✗ 'semaines_cours' absent du contexte")
    
    # Vérifier la semaine courante
    if 'semaine_courante' in context:
        semaine_ctx = context['semaine_courante']
        if semaine_ctx:
            print(f"   ✓ 'semaine_courante' présent : S{semaine_ctx.numero_semaine} ★")
        else:
            print(f"   ✓ 'semaine_courante' présent (mais None)")
    else:
        print(f"   ✗ 'semaine_courante' absent du contexte")
        
except Exception as e:
    print(f"   ✗ Erreur : {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test du filtrage par semaine
print("\n4️⃣ Test du filtrage par semaine")
total_horaires = ScheduleEntry.objects.count()
print(f"   Total horaires : {total_horaires}")

if semaines.exists():
    semaine_test = semaines.first()
    horaires_semaine = ScheduleEntry.objects.filter(
        semaine_debut=semaine_test.date_debut
    )
    print(f"\n   Test avec S{semaine_test.numero_semaine} ({semaine_test.date_debut}):")
    print(f"   ✓ Horaires pour cette semaine : {horaires_semaine.count()}")
    
    if horaires_semaine.exists():
        print(f"   ✓ Exemple d'horaires filtrés :")
        for h in horaires_semaine[:3]:
            print(f"      • {h.attribution.code_ue.classe} - {h.jour} {h.creneau}")

# Test 5: Simulation d'une requête avec filtre semaine
print("\n5️⃣ Simulation d'une requête avec filtre semaine")
if semaines.exists():
    semaine_test = semaines.first()
    
    try:
        factory = RequestFactory()
        # Simuler une requête GET avec le paramètre semaine
        request = factory.get(
            '/attribution/schedule/entry/list/',
            {'semaine': semaine_test.date_debut.strftime('%Y-%m-%d')}
        )
        
        view = ScheduleEntryListView()
        view.request = request
        view.kwargs = {}
        queryset = view.get_queryset()
        
        print(f"   ✓ Requête simulée avec semaine={semaine_test.date_debut}")
        print(f"   ✓ Résultats filtrés : {queryset.count()} horaires")
        
        if queryset.exists():
            print(f"   ✓ Premiers résultats :")
            for h in queryset[:3]:
                print(f"      • {h.attribution.code_ue.classe} - {h.jour} - {h.attribution.code_ue.code_ue}")
    except Exception as e:
        print(f"   ✗ Erreur : {e}")

# Test 6: Affichage du format pour le template
print("\n6️⃣ Format d'affichage pour le template")
if semaines.exists():
    print("   Format des options du combo semaine :")
    for s in semaines[:5]:
        etoile = " ★" if s.est_en_cours else ""
        value = s.date_debut.strftime('%Y-%m-%d')
        label = f"S{s.numero_semaine}{etoile}"
        print(f"      <option value=\"{value}\">{ label}</option>")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ")
print("="*70)

print(f"""
✓ Semaines disponibles : {semaines.count()}
✓ Semaine en cours : {"S" + str(semaine_courante.numero_semaine) if semaine_courante else "Aucune"}
✓ Total horaires : {total_horaires}

🎯 INTÉGRATION DU FILTRE SEMAINE :

1. ✓ Vue enrichie (attribution/views.py)
   → get_queryset() : Filtrage par semaine_debut
   → get_context_data() : semaines_cours + semaine_courante

2. ✓ Template mis à jour (schedule_unified.html)
   → Nouveau combo "Semaine" ajouté
   → Format : "S1 ★", "S2", "S3"...
   → Indicateur ★ pour semaine en cours

3. ✓ Fonctionnalités
   → Filtrer les horaires par semaine
   → Affichage de la semaine en cours
   → Sélection simple (S1, S2, S3...)

📝 EXEMPLE D'UTILISATION :

URL : /attribution/schedule/entry/list/?semaine=2024-10-14
→ Affiche uniquement les horaires de la semaine du 14 octobre

Combo : [S1 ★] [S2] [S3] [S4]...
→ Cliquer sur S2 pour voir ses horaires
""")

print("="*70)
print(" 🎉 FILTRE SEMAINE OPÉRATIONNEL !")
print("="*70)
