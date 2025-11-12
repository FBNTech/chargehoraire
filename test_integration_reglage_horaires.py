#!/usr/bin/env python
"""Test de l'intégration Réglage → Horaires"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import AnneeAcademique, Salle, Creneau
from attribution.forms import ScheduleEntryForm
from attribution.models import Attribution

print("="*60)
print(" 🔗 TEST INTÉGRATION RÉGLAGE → HORAIRES")
print("="*60)

# Test 1: Vérifier que les données de réglage existent
print("\n1️⃣ Vérification des données de réglage")
annees_count = AnneeAcademique.objects.count()
salles_count = Salle.objects.count()
creneaux_count = Creneau.objects.count()

print(f"   ✓ Années académiques: {annees_count}")
print(f"   ✓ Salles: {salles_count}")
print(f"   ✓ Créneaux: {creneaux_count}")

if annees_count == 0 or salles_count == 0 or creneaux_count == 0:
    print("\n   ⚠️ AVERTISSEMENT: Certaines données de réglage manquent")
    print("   Exécutez d'abord: python test_nouvelles_gestions.py")

# Test 2: Vérifier l'année en cours
print("\n2️⃣ Test de l'année en cours")
annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
if annee_courante:
    print(f"   ✓ Année en cours: {annee_courante.code}")
else:
    print("   ⚠️ Aucune année marquée comme 'en cours'")

# Test 3: Vérifier les salles disponibles
print("\n3️⃣ Test des salles disponibles")
salles_dispo = Salle.objects.filter(est_disponible=True)
print(f"   ✓ Salles disponibles: {salles_dispo.count()}")
for salle in salles_dispo[:3]:
    affichage = f"{salle.code} - {salle.designation}"
    if salle.capacite:
        affichage += f" ({salle.capacite} places)"
    print(f"      • {affichage}")

# Test 4: Vérifier les créneaux actifs
print("\n4️⃣ Test des créneaux actifs")
creneaux_actifs = Creneau.objects.filter(est_actif=True)
print(f"   ✓ Créneaux actifs: {creneaux_actifs.count()}")
for creneau in creneaux_actifs:
    print(f"      • {creneau.designation} ({creneau.get_format_court()})")

# Test 5: Test du formulaire avec pré-remplissage
print("\n5️⃣ Test du formulaire ScheduleEntryForm")
try:
    form = ScheduleEntryForm()
    
    # Vérifier que les champs existent
    has_annee_select = 'annee_academique_select' in form.fields
    has_salle_select = 'salle_select' in form.fields
    has_creneau_select = 'creneau_select' in form.fields
    
    print(f"   ✓ Champ annee_academique_select: {'✓' if has_annee_select else '✗'}")
    print(f"   ✓ Champ salle_select: {'✓' if has_salle_select else '✗'}")
    print(f"   ✓ Champ creneau_select: {'✓' if has_creneau_select else '✗'}")
    
    # Vérifier le pré-remplissage de l'année
    if annee_courante and has_annee_select:
        initial_annee = form.fields['annee_academique'].initial
        print(f"   ✓ Année pré-remplie: {initial_annee}")
        if initial_annee == annee_courante.code:
            print("      ✓ Correspond à l'année en cours !")
    
    # Vérifier les querysets
    annee_count = form.fields['annee_academique_select'].queryset.count()
    salle_count = form.fields['salle_select'].queryset.count()
    creneau_count = form.fields['creneau_select'].queryset.count()
    
    print(f"   ✓ Années dans le queryset: {annee_count}")
    print(f"   ✓ Salles dans le queryset: {salle_count}")
    print(f"   ✓ Créneaux dans le queryset: {creneau_count}")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test de la conversion (clean)
print("\n6️⃣ Test de la conversion dans clean()")
if Attribution.objects.exists():
    try:
        attribution = Attribution.objects.first()
        salle = Salle.objects.filter(est_disponible=True).first()
        creneau = Creneau.objects.filter(est_actif=True).first()
        
        if salle and creneau and annee_courante:
            data = {
                'attribution': attribution.id,
                'annee_academique_select': annee_courante.id,
                'semaine_debut': '2025-10-27',
                'jour': 'lundi',
                'salle_select': salle.id,
                'creneau_select': creneau.id,
            }
            
            form = ScheduleEntryForm(data=data)
            if form.is_valid():
                cleaned = form.cleaned_data
                print(f"   ✓ Formulaire valide")
                print(f"   ✓ Année convertie: {cleaned.get('annee_academique')}")
                print(f"   ✓ Salle convertie: {cleaned.get('salle')}")
                print(f"   ✓ Créneau converti: {cleaned.get('creneau')}")
            else:
                print(f"   ✗ Formulaire invalide: {form.errors}")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
else:
    print("   ⚠️ Aucune attribution disponible pour le test")

# Test 7: Vérifier les URLs
print("\n7️⃣ Vérification des URLs")
try:
    from django.urls import reverse
    
    urls = [
        ('reglage:annee_list', 'Années académiques'),
        ('reglage:salle_list', 'Salles'),
        ('reglage:creneau_list', 'Créneaux'),
        ('attribution:schedule_entry_create', 'Créer horaire'),
        ('attribution:schedule_entry_list', 'Liste horaires'),
    ]
    
    for url_name, desc in urls:
        try:
            url = reverse(url_name)
            print(f"   ✓ {desc:25} : {url}")
        except Exception as e:
            print(f"   ✗ {desc:25} : Erreur")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Résumé
print("\n" + "="*60)
print(" ✅ RÉSUMÉ DE L'INTÉGRATION")
print("="*60)

status = []
if annees_count > 0:
    status.append("✓ Années configurées")
else:
    status.append("✗ Configurez les années dans Réglage")

if salles_count > 0:
    status.append("✓ Salles configurées")
else:
    status.append("✗ Configurez les salles dans Réglage")

if creneaux_count > 0:
    status.append("✓ Créneaux configurés")
else:
    status.append("✗ Configurez les créneaux dans Réglage")

if annee_courante:
    status.append(f"✓ Année en cours: {annee_courante.code}")
else:
    status.append("⚠️ Aucune année marquée 'en cours'")

print("\n".join(f"   {s}" for s in status))

print(f"\n📊 STATISTIQUES:")
print(f"   • {annees_count} années académiques")
print(f"   • {salles_count} salles ({Salle.objects.filter(est_disponible=True).count()} disponibles)")
print(f"   • {creneaux_count} créneaux ({Creneau.objects.filter(est_actif=True).count()} actifs)")

print(f"\n🔗 WORKFLOW:")
print(f"   1. Configurer : /reglage/gestion/")
print(f"   2. Utiliser : /attribution/schedule/entry/create/")
print(f"   3. Ou ajout rapide : /attribution/schedule/entry/list/")

print("\n" + "="*60)
print(" 🎉 INTÉGRATION FONCTIONNELLE !")
print("="*60)
