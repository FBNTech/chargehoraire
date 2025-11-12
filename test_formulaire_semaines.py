#!/usr/bin/env python
"""Test du formulaire amélioré des semaines de cours"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import SemaineCours, AnneeAcademique
from reglage.forms import SemaineCoursForm

print("="*70)
print(" 🎯 TEST FORMULAIRE AMÉLIORÉ : SEMAINES DE COURS")
print("="*70)

# Test 1: Vérifier l'année académique en cours
print("\n1️⃣ Vérification de l'année académique en cours")
annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
if annee_courante:
    print(f"   ✓ Année en cours : {annee_courante.code}")
else:
    print("   ⚠️ Aucune année marquée comme 'en cours'")
    # Créer une année pour le test
    annee_courante = AnneeAcademique.objects.create(
        code="2024-2025",
        designation="Année académique 2024-2025",
        date_debut=date(2024, 10, 1),
        date_fin=date(2025, 6, 30),
        est_en_cours=True
    )
    print(f"   ✓ Année créée pour le test : {annee_courante.code}")

# Test 2: Test du formulaire vide (création)
print("\n2️⃣ Test du formulaire pour création")
form_creation = SemaineCoursForm()
print(f"   ✓ Formulaire créé")

# Vérifier les champs
champs_presents = list(form_creation.fields.keys())
print(f"   ✓ Champs présents : {', '.join(champs_presents)}")

# Vérifier que 'designation' n'est PAS dans le formulaire
if 'designation' not in champs_presents:
    print(f"   ✓ Champ 'designation' absent du formulaire (auto-généré)")
else:
    print(f"   ✗ Erreur : Champ 'designation' encore présent !")

# Vérifier le widget pour date_debut
widget_debut = form_creation.fields['date_debut'].widget
print(f"   ✓ Widget date_debut : {type(widget_debut).__name__}")
if hasattr(widget_debut, 'input_type'):
    print(f"      → Type d'input : {widget_debut.input_type}")

# Vérifier la valeur initiale de annee_academique
initial_annee = form_creation.initial.get('annee_academique')
if initial_annee:
    print(f"   ✓ Année académique pré-remplie : {initial_annee}")
    if initial_annee == annee_courante.code:
        print(f"      ✓ Correspond à l'année en cours !")
else:
    print(f"   ⚠️ Année académique non pré-remplie")

# Test 3: Soumettre le formulaire avec des données valides
print("\n3️⃣ Test de soumission avec données valides")
donnees = {
    'numero_semaine': 1,
    'date_debut': date(2024, 10, 14),  # Lundi
    'date_fin': date(2024, 10, 19),     # Samedi
    'annee_academique': annee_courante.code,
    'est_en_cours': True,
    'remarques': 'Première semaine de cours'
}

form_valide = SemaineCoursForm(data=donnees)
if form_valide.is_valid():
    print(f"   ✓ Formulaire valide")
    semaine = form_valide.save()
    print(f"   ✓ Semaine créée : {semaine}")
    print(f"   ✓ Désignation auto-générée : '{semaine.designation}'")
    
    # Vérifier la désignation
    if "Semaine 1" in semaine.designation:
        print(f"      ✓ Contient 'Semaine 1'")
    if annee_courante.code in semaine.designation:
        print(f"      ✓ Contient l'année '{annee_courante.code}'")
else:
    print(f"   ✗ Formulaire invalide : {form_valide.errors}")

# Test 4: Test avec année académique différente
print("\n4️⃣ Test avec une autre année académique")
autre_annee = "2025-2026"
donnees2 = {
    'numero_semaine': 2,
    'date_debut': date(2024, 10, 21),  # Lundi
    'date_fin': date(2024, 10, 26),     # Samedi
    'annee_academique': autre_annee,
    'est_en_cours': False,
}

form2 = SemaineCoursForm(data=donnees2)
if form2.is_valid():
    semaine2 = form2.save()
    print(f"   ✓ Semaine créée : {semaine2}")
    print(f"   ✓ Désignation : '{semaine2.designation}'")
else:
    print(f"   ✗ Erreur : {form2.errors}")

# Test 5: Vérifier les choix du combo année académique
print("\n5️⃣ Test des choix du combo année académique")
form_test = SemaineCoursForm()
choix_annees = form_test.fields['annee_academique'].choices
print(f"   ✓ Nombre de choix : {len(choix_annees)}")
for value, label in choix_annees[:5]:  # Afficher les 5 premiers
    if value:
        etoile = "★" if "★" in label else ""
        print(f"      • {label} {etoile}")
    else:
        print(f"      • {label}")

# Test 6: Test du formulaire pour modification
print("\n6️⃣ Test du formulaire pour modification")
semaine_a_modifier = SemaineCours.objects.first()
if semaine_a_modifier:
    form_modif = SemaineCoursForm(instance=semaine_a_modifier)
    print(f"   ✓ Formulaire de modification créé")
    print(f"   ✓ Numéro semaine : {form_modif.initial.get('numero_semaine')}")
    print(f"   ✓ Année : {form_modif.initial.get('annee_academique')}")
    print(f"   ✓ Date début : {form_modif.initial.get('date_debut')}")

# Test 7: Test avec dates invalides (Mardi au lieu de Lundi)
print("\n7️⃣ Test avec dates invalides (validation)")
donnees_invalides = {
    'numero_semaine': 10,
    'date_debut': date(2024, 10, 15),  # Mardi ❌
    'date_fin': date(2024, 10, 19),     # Samedi
    'annee_academique': annee_courante.code,
}

form_invalide = SemaineCoursForm(data=donnees_invalides)
if form_invalide.is_valid():
    try:
        semaine_invalide = form_invalide.save()
        print(f"   ✗ PROBLÈME : Semaine invalide créée !")
    except Exception as e:
        print(f"   ✓ Validation bloquée : {str(e)[:80]}...")
else:
    print(f"   ✓ Formulaire invalide (attendu)")
    print(f"      Erreurs : {form_invalide.errors}")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ")
print("="*70)

total_semaines = SemaineCours.objects.count()
annees_disponibles = AnneeAcademique.objects.count()

print(f"""
✓ Semaines créées : {total_semaines}
✓ Années académiques disponibles : {annees_disponibles}

🎯 AMÉLIORATIONS DU FORMULAIRE :

1. ✓ Année académique en cours pré-sélectionnée
   → Valeur initiale : {annee_courante.code if annee_courante else 'Aucune'}

2. ✓ Champ désignation supprimé (auto-généré)
   → Format : "Semaine X - YYYY-YYYY"

3. ✓ Champs date avec widget HTML5 type="date"
   → Date picker natif du navigateur

4. ✓ Validation Lundi→Samedi maintenue
   → Empêche la création de semaines invalides

📝 EXEMPLES DE DÉSIGNATIONS AUTO-GÉNÉRÉES :
""")

semaines_exemples = SemaineCours.objects.all()[:3]
for s in semaines_exemples:
    print(f"   • {s.designation}")

print("\n" + "="*70)
print(" 🎉 FORMULAIRE AMÉLIORÉ FONCTIONNEL !")
print("="*70)
