#!/usr/bin/env python
"""Test de l'intégration complète : Années, Classes, Créneaux, Salles"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import AnneeAcademique, Salle, Creneau, Classe
from attribution.views import ScheduleEntryListView
from django.test import RequestFactory

print("="*70)
print(" 🎯 TEST INTÉGRATION COMPLÈTE : RÉGLAGE → HORAIRES")
print("="*70)

# Test 1: Vérifier les données de réglage
print("\n1️⃣ Vérification des données de Réglage")
annees_count = AnneeAcademique.objects.count()
classes_count = Classe.objects.count()
creneaux_count = Creneau.objects.count()
salles_count = Salle.objects.count()

print(f"   📅 Années académiques : {annees_count}")
print(f"   🎓 Classes            : {classes_count}")
print(f"   ⏰ Créneaux           : {creneaux_count}")
print(f"   🚪 Salles             : {salles_count}")

if annees_count == 0:
    print("\n   ⚠️ ATTENTION : Aucune année académique enregistrée")
    print("   → Allez dans /reglage/annees/ pour en créer")
    
if classes_count == 0:
    print("\n   ⚠️ ATTENTION : Aucune classe enregistrée")
    print("   → Allez dans /reglage/classes/ pour en créer")

# Test 2: Année en cours
print("\n2️⃣ Année Académique en cours")
annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
if annee_courante:
    print(f"   ✓ Année en cours : {annee_courante.code} ★")
    print(f"   ✓ Désignation    : {annee_courante.designation}")
else:
    print("   ⚠️ Aucune année marquée comme 'en cours'")
    if annees_count > 0:
        print("   → Modifiez une année dans /reglage/annees/ et cochez 'En cours'")

# Test 3: Classes disponibles
print("\n3️⃣ Classes disponibles")
classes = Classe.objects.all()[:5]
if classes:
    print(f"   ✓ {Classe.objects.count()} classes enregistrées")
    for classe in classes:
        print(f"      • {classe.CodeClasse} - {classe.DesignationClasse}")
    if Classe.objects.count() > 5:
        print(f"      ... et {Classe.objects.count() - 5} autres")
else:
    print("   ⚠️ Aucune classe enregistrée")

# Test 4: Créneaux actifs
print("\n4️⃣ Créneaux actifs")
creneaux_actifs = Creneau.objects.filter(est_actif=True).order_by('ordre')
if creneaux_actifs:
    print(f"   ✓ {creneaux_actifs.count()} créneaux actifs")
    for creneau in creneaux_actifs:
        print(f"      {creneau.ordre}. {creneau.designation} - {creneau.get_format_court()}")
else:
    print("   ⚠️ Aucun créneau actif")

# Test 5: Salles disponibles
print("\n5️⃣ Salles disponibles")
salles_dispo = Salle.objects.filter(est_disponible=True)[:5]
if salles_dispo:
    print(f"   ✓ {Salle.objects.filter(est_disponible=True).count()} salles disponibles")
    for salle in salles_dispo:
        capacite_str = f" ({salle.capacite} pl.)" if salle.capacite else ""
        print(f"      • {salle.code} - {salle.designation}{capacite_str}")
else:
    print("   ⚠️ Aucune salle disponible")

# Test 6: Test du contexte de la vue
print("\n6️⃣ Test du contexte de la vue ScheduleEntryListView")
try:
    factory = RequestFactory()
    request = factory.get('/attribution/schedule/entry/list/')
    
    view = ScheduleEntryListView()
    view.request = request
    view.object_list = view.get_queryset()
    context = view.get_context_data()
    
    # Vérifier les données dans le contexte
    checks = [
        ('annees_reglage', 'Années de réglage'),
        ('annee_courante', 'Année courante'),
        ('classes_reglage', 'Classes de réglage'),
        ('creneaux_actifs', 'Créneaux actifs'),
        ('salles_disponibles', 'Salles disponibles'),
    ]
    
    for key, label in checks:
        if key in context:
            value = context[key]
            if hasattr(value, 'count'):
                count = value.count()
                status = "✓" if count > 0 else "⚠️"
                print(f"   {status} {label:25} : {count} éléments")
            elif value is not None:
                print(f"   ✓ {label:25} : {value}")
            else:
                print(f"   ⚠️ {label:25} : None")
        else:
            print(f"   ✗ {label:25} : Clé manquante")
    
    # Vérifier le filtre année
    if context.get('annees_reglage') and context['annees_reglage'].exists():
        print(f"\n   ✓ Filtre Année utilisera les données de Réglage")
        if context.get('annee_courante'):
            print(f"      → Année en cours : {context['annee_courante'].code} ★")
    else:
        print(f"\n   ⚠️ Filtre Année utilisera le fallback (horaires existants)")
    
    # Vérifier le filtre classe
    if context.get('classes_reglage') and context['classes_reglage'].exists():
        print(f"   ✓ Filtre Classe utilisera les données de Réglage ({context['classes_reglage'].count()} classes)")
    else:
        print(f"   ⚠️ Filtre Classe utilisera le fallback (champ texte)")
    
    # Vérifier le filtre créneau
    if context.get('creneaux_actifs') and context['creneaux_actifs'].exists():
        print(f"   ✓ Filtre Créneau utilisera les données de Réglage ({context['creneaux_actifs'].count()} créneaux)")
    else:
        print(f"   ⚠️ Filtre Créneau utilisera le fallback (AM/PM)")
        
except Exception as e:
    print(f"   ✗ Erreur : {e}")
    import traceback
    traceback.print_exc()

# Test 7: Simulation de filtres
print("\n7️⃣ Simulation des filtres")
print("   Scénario : Utilisateur filtre par année, classe et créneau")
print()

if annee_courante:
    print(f"   📅 Année sélectionnée : {annee_courante.code} ★")
else:
    print(f"   📅 Année sélectionnée : (aucune année en cours)")

if classes.exists():
    classe_exemple = classes.first()
    print(f"   🎓 Classe sélectionnée : {classe_exemple.CodeClasse} - {classe_exemple.DesignationClasse}")
else:
    print(f"   🎓 Classe sélectionnée : (aucune classe disponible)")

if creneaux_actifs.exists():
    creneau_exemple = creneaux_actifs.first()
    print(f"   ⏰ Créneau sélectionné : {creneau_exemple.designation} ({creneau_exemple.get_format_court()})")
else:
    print(f"   ⏰ Créneau sélectionné : (aucun créneau disponible)")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ DE L'INTÉGRATION")
print("="*70)

total_config = sum([
    1 if annees_count > 0 else 0,
    1 if classes_count > 0 else 0,
    1 if creneaux_count > 0 else 0,
    1 if salles_count > 0 else 0,
])

print(f"\n   Configuration complétée : {total_config}/4")
print()

if annees_count > 0:
    status_annee = "✓" if annee_courante else "⚠️"
    extra = f" (dont {annee_courante.code} ★ en cours)" if annee_courante else " (aucune marquée 'en cours')"
    print(f"   {status_annee} Années : {annees_count} enregistrées{extra}")
else:
    print(f"   ✗ Années : Non configurées → /reglage/annees/")

if classes_count > 0:
    print(f"   ✓ Classes : {classes_count} enregistrées")
else:
    print(f"   ✗ Classes : Non configurées → /reglage/classes/")

if creneaux_count > 0:
    actifs = Creneau.objects.filter(est_actif=True).count()
    print(f"   ✓ Créneaux : {creneaux_count} enregistrés ({actifs} actifs)")
else:
    print(f"   ✗ Créneaux : Non configurés → /reglage/creneaux/")

if salles_count > 0:
    dispo = Salle.objects.filter(est_disponible=True).count()
    print(f"   ✓ Salles : {salles_count} enregistrées ({dispo} disponibles)")
else:
    print(f"   ✗ Salles : Non configurées → /reglage/salles/")

# Recommandations
print("\n" + "="*70)
print(" 💡 RECOMMANDATIONS")
print("="*70)

if total_config == 4:
    print("\n   🎉 PARFAIT ! Tous les modèles sont configurés.")
    print("\n   ✨ FILTRES DE LA PAGE HORAIRE :")
    print("      • Année académique : Combo avec années de Réglage ★")
    print("      • Classe : Combo avec classes de Réglage")
    print("      • Créneau : Combo avec créneaux de Réglage")
    print("      • Salle : Combo avec salles de Réglage")
    print("\n   → Testez maintenant : /attribution/schedule/entry/list/")
else:
    print("\n   🔧 Configuration incomplète. Actions recommandées :\n")
    
    if annees_count == 0:
        print("   1. Créez des années académiques :")
        print("      → /reglage/annees/create/")
        print("      → Ex: 2024-2025, 2025-2026")
        print("      → Marquez une année comme 'En cours' ★\n")
    
    if classes_count == 0:
        print("   2. Créez des classes :")
        print("      → /reglage/classes/create/")
        print("      → Ex: L1BC, L1MI, L2CST, M1INFO\n")
    
    if creneaux_count == 0:
        print("   3. Créez des créneaux :")
        print("      → /reglage/creneaux/create/")
        print("      → Ex: AM (08:00-12:00), PM (13:00-17:00)\n")
    
    if salles_count == 0:
        print("   4. Créez des salles :")
        print("      → /reglage/salles/create/")
        print("      → Ex: B1, A205, AMPHI-A\n")

print("\n" + "="*70)
print(" 🎯 URLS PRINCIPALES")
print("="*70)
print("""
   Configuration :
   • Page Réglage    : /reglage/gestion/
   • Années          : /reglage/annees/
   • Classes         : /reglage/classes/
   • Créneaux        : /reglage/creneaux/
   • Salles          : /reglage/salles/
   
   Utilisation :
   • Liste horaires  : /attribution/schedule/entry/list/
   • Créer horaire   : /attribution/schedule/entry/create/
""")

print("="*70)
print(" ✅ TEST TERMINÉ")
print("="*70)
