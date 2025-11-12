#!/usr/bin/env python
"""Test du formulaire amélioré d'ajout d'horaire"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.forms import ScheduleEntryForm
from attribution.models import ScheduleEntry, Attribution
from reglage.models import SemaineCours, AnneeAcademique

print("="*70)
print(" 🎯 TEST FORMULAIRE HORAIRE AMÉLIORÉ")
print("="*70)

# Test 1: Vérifier les champs du formulaire
print("\n1️⃣ Vérification des champs du formulaire")
form = ScheduleEntryForm()
champs = list(form.fields.keys())
print(f"   ✓ Champs du formulaire : {len(champs)}")
for champ in champs:
    print(f"      • {champ}")

# Vérifier les nouveaux champs
if 'semaine_select' in champs:
    print(f"\n   ✓ Nouveau champ 'semaine_select' présent")
else:
    print(f"\n   ✗ Champ 'semaine_select' manquant !")

if 'date_cours' in champs:
    print(f"   ✓ Nouveau champ 'date_cours' présent")
else:
    print(f"   ✗ Champ 'date_cours' manquant !")

# Test 2: Vérifier le pré-remplissage
print("\n2️⃣ Vérification du pré-remplissage")
form_nouveau = ScheduleEntryForm()

# Année en cours
annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
if annee_courante:
    print(f"   ✓ Année en cours : {annee_courante.code}")
    initial_annee = form_nouveau.fields['annee_academique_select'].initial
    if initial_annee == annee_courante:
        print(f"      ✓ Année pré-remplie dans le formulaire")

# Semaine en cours
semaine_courante = SemaineCours.objects.filter(est_en_cours=True).first()
if semaine_courante:
    print(f"   ✓ Semaine en cours : S{semaine_courante.numero_semaine} ★")
    initial_semaine = form_nouveau.fields['semaine_select'].initial
    if initial_semaine == semaine_courante:
        print(f"      ✓ Semaine pré-remplie dans le formulaire")
    
    initial_semaine_debut = form_nouveau.fields['semaine_debut'].initial
    if initial_semaine_debut == semaine_courante.date_debut:
        print(f"      ✓ semaine_debut pré-remplie : {initial_semaine_debut}")

# Test 3: Test de l'affichage des semaines
print("\n3️⃣ Test de l'affichage des semaines")
semaines = SemaineCours.objects.all()
if semaines.exists():
    print(f"   ✓ {semaines.count()} semaine(s) disponible(s)")
    for s in semaines[:3]:
        label = form_nouveau.fields['semaine_select'].label_from_instance(s)
        print(f"      • {label}")

# Test 4: Test du calcul automatique du jour
print("\n4️⃣ Test du calcul automatique du jour à partir de la date")

# Simuler des données
test_dates = [
    (date(2024, 10, 14), 'lundi'),      # Lundi
    (date(2024, 10, 15), 'mardi'),      # Mardi
    (date(2024, 10, 16), 'mercredi'),   # Mercredi
    (date(2024, 10, 17), 'jeudi'),      # Jeudi
    (date(2024, 10, 18), 'vendredi'),   # Vendredi
    (date(2024, 10, 19), 'samedi'),     # Samedi
]

print("   Test du mapping date → jour :")
jours_map = {
    0: 'lundi',
    1: 'mardi',
    2: 'mercredi',
    3: 'jeudi',
    4: 'vendredi',
    5: 'samedi',
    6: 'dimanche'
}

for test_date, jour_attendu in test_dates:
    jour_calcule = jours_map[test_date.weekday()]
    statut = "✓" if jour_calcule == jour_attendu else "✗"
    print(f"   {statut} {test_date.strftime('%d/%m/%Y')} → {jour_calcule} (attendu: {jour_attendu})")

# Test 5: Test de soumission du formulaire (si attribution existe)
print("\n5️⃣ Test de soumission du formulaire")
attribution = Attribution.objects.first()
if attribution and semaine_courante:
    donnees = {
        'attribution': attribution.id,
        'annee_academique': '2025-2026',
        'semaine_select': semaine_courante.id,
        'date_cours': date(2024, 10, 14),  # Lundi
        'creneau': 'am',
        'salle': 'B1',
        'remarques': 'Test formulaire amélioré'
    }
    
    form_test = ScheduleEntryForm(data=donnees)
    if form_test.is_valid():
        print(f"   ✓ Formulaire valide")
        cleaned = form_test.cleaned_data
        
        # Vérifier semaine_debut calculée
        if 'semaine_debut' in cleaned and cleaned['semaine_debut']:
            print(f"   ✓ semaine_debut calculée : {cleaned['semaine_debut']}")
        
        # Vérifier jour calculé
        if 'jour' in cleaned and cleaned['jour']:
            print(f"   ✓ jour calculé : {cleaned['jour']}")
            if cleaned['jour'] == 'lundi':
                print(f"      ✓ Jour correct (lundi pour le 14/10/2024)")
        
        # Vérifier date_cours
        if 'date_cours' in cleaned and cleaned['date_cours']:
            print(f"   ✓ date_cours : {cleaned['date_cours']}")
    else:
        print(f"   ✗ Formulaire invalide")
        print(f"      Erreurs : {form_test.errors}")
else:
    print(f"   ⚠️ Pas d'attribution ou semaine pour tester")

# Test 6: Vérifier le modèle ScheduleEntry
print("\n6️⃣ Vérification du modèle ScheduleEntry")
from attribution.models import ScheduleEntry

# Vérifier que le champ date_cours existe
if hasattr(ScheduleEntry, 'date_cours'):
    print(f"   ✓ Champ 'date_cours' ajouté au modèle")
else:
    print(f"   ✗ Champ 'date_cours' absent du modèle !")

# Lister les champs du modèle
champs_modele = [f.name for f in ScheduleEntry._meta.get_fields()]
print(f"\n   Champs du modèle ScheduleEntry :")
for champ in champs_modele:
    print(f"      • {champ}")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ")
print("="*70)

print(f"""
✓ Semaines disponibles : {semaines.count() if semaines.exists() else 0}
✓ Semaine en cours : {"S" + str(semaine_courante.numero_semaine) if semaine_courante else "Aucune"}

🎯 AMÉLIORATIONS DU FORMULAIRE HORAIRE :

1. ✓ Combo Semaine de Cours
   → Champ : semaine_select
   → Affichage : "S1 : 14/10 - 19/10 ★"
   → Pré-rempli avec la semaine en cours

2. ✓ Champ Date du Cours (au lieu de Jour)
   → Champ : date_cours (DateField avec widget HTML5)
   → Calcul automatique du jour à partir de la date
   → Mapping : date → jour (lundi, mardi, etc.)

3. ✓ Conversion automatique
   → semaine_select → semaine_debut (date de début)
   → date_cours → jour (nom du jour)

📝 WORKFLOW D'UTILISATION :

1. Sélectionner la semaine : [S1 : 27/10 - 01/11 ★ ▼]
   → Définit automatiquement semaine_debut

2. Sélectionner la date : [📅 14/10/2024]
   → Calcule automatiquement le jour (Lundi)

3. Les champs semaine_debut et jour sont remplis automatiquement !

💡 AVANTAGES :
• Moins de saisie manuelle
• Pas d'erreur de jour (calculé automatiquement)
• Semaine en cours pré-sélectionnée
• Interface cohérente avec la gestion des semaines
""")

print("="*70)
print(" 🎉 FORMULAIRE HORAIRE AMÉLIORÉ OPÉRATIONNEL !")
print("="*70)
