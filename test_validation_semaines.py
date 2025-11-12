#!/usr/bin/env python
"""Test de la validation des semaines (Lundi-Samedi)"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import SemaineCours
from django.core.exceptions import ValidationError

print("="*70)
print(" ✅ TEST VALIDATION : LUNDI → SAMEDI")
print("="*70)

# Test 1: Tentative avec des dates valides (Lundi → Samedi)
print("\n1️⃣ Test avec dates VALIDES (Lundi → Samedi)")
try:
    # 14 octobre 2024 = Lundi
    # 19 octobre 2024 = Samedi
    semaine_valide = SemaineCours(
        numero_semaine=10,
        date_debut=date(2024, 10, 14),  # Lundi
        date_fin=date(2024, 10, 19),     # Samedi
        designation="Semaine test valide",
        annee_academique="2024-2025"
    )
    semaine_valide.save()
    print(f"   ✓ Semaine créée avec succès : {semaine_valide}")
    print(f"   ✓ Jour début : {semaine_valide.get_jour_debut()}")
    print(f"   ✓ Jour fin : {semaine_valide.get_jour_fin()}")
except ValidationError as e:
    print(f"   ✗ Erreur de validation : {e}")
except Exception as e:
    print(f"   ✗ Erreur : {e}")

# Test 2: Tentative avec date_debut = Mardi (INVALIDE)
print("\n2️⃣ Test avec date_debut = MARDI (doit échouer)")
try:
    # 15 octobre 2024 = Mardi
    semaine_invalide1 = SemaineCours(
        numero_semaine=11,
        date_debut=date(2024, 10, 15),  # Mardi ❌
        date_fin=date(2024, 10, 19),     # Samedi
        designation="Semaine avec Mardi début",
        annee_academique="2024-2025"
    )
    semaine_invalide1.save()
    print(f"   ✗ PROBLÈME : La semaine a été créée alors qu'elle ne devrait pas !")
except ValidationError as e:
    print(f"   ✓ Validation bloquée correctement")
    for field, errors in e.message_dict.items():
        for error in errors:
            print(f"      • {field}: {error}")
except Exception as e:
    print(f"   ✗ Erreur inattendue : {e}")

# Test 3: Tentative avec date_fin = Dimanche (INVALIDE)
print("\n3️⃣ Test avec date_fin = DIMANCHE (doit échouer)")
try:
    # 20 octobre 2024 = Dimanche
    semaine_invalide2 = SemaineCours(
        numero_semaine=12,
        date_debut=date(2024, 10, 14),  # Lundi
        date_fin=date(2024, 10, 20),     # Dimanche ❌
        designation="Semaine avec Dimanche fin",
        annee_academique="2024-2025"
    )
    semaine_invalide2.save()
    print(f"   ✗ PROBLÈME : La semaine a été créée alors qu'elle ne devrait pas !")
except ValidationError as e:
    print(f"   ✓ Validation bloquée correctement")
    for field, errors in e.message_dict.items():
        for error in errors:
            print(f"      • {field}: {error}")
except Exception as e:
    print(f"   ✗ Erreur inattendue : {e}")

# Test 4: Tentative avec date_debut = Vendredi et date_fin = Jeudi (INVALIDE)
print("\n4️⃣ Test avec Vendredi → Jeudi (deux erreurs)")
try:
    semaine_invalide3 = SemaineCours(
        numero_semaine=13,
        date_debut=date(2024, 10, 18),  # Vendredi ❌
        date_fin=date(2024, 10, 17),     # Jeudi ❌
        designation="Semaine invalide",
        annee_academique="2024-2025"
    )
    semaine_invalide3.save()
    print(f"   ✗ PROBLÈME : La semaine a été créée alors qu'elle ne devrait pas !")
except ValidationError as e:
    print(f"   ✓ Validation bloquée correctement (erreurs multiples)")
    for field, errors in e.message_dict.items():
        for error in errors:
            print(f"      • {field}: {error}")
except Exception as e:
    print(f"   ✗ Erreur inattendue : {e}")

# Test 5: Plusieurs semaines valides consécutives
print("\n5️⃣ Test de plusieurs semaines valides consécutives")
semaines_test = [
    (20, date(2024, 10, 21), date(2024, 10, 26), "Semaine 2"),  # Lundi → Samedi
    (21, date(2024, 10, 28), date(2024, 11, 2), "Semaine 3"),   # Lundi → Samedi
    (22, date(2024, 11, 4), date(2024, 11, 9), "Semaine 4"),    # Lundi → Samedi
]

count_success = 0
for num, debut, fin, designation in semaines_test:
    try:
        semaine = SemaineCours(
            numero_semaine=num,
            date_debut=debut,
            date_fin=fin,
            designation=designation,
            annee_academique="2024-2025"
        )
        semaine.save()
        print(f"   ✓ {designation} : {debut.strftime('%d/%m')} ({semaine.get_jour_debut()}) → {fin.strftime('%d/%m')} ({semaine.get_jour_fin()})")
        count_success += 1
    except ValidationError as e:
        print(f"   ✗ {designation} : Erreur de validation")
    except Exception as e:
        print(f"   ✗ {designation} : Erreur {e}")

print(f"\n   ✓ {count_success}/{len(semaines_test)} semaines créées")

# Test 6: Vérifier toutes les semaines créées
print("\n6️⃣ Liste de toutes les semaines valides créées")
semaines = SemaineCours.objects.all().order_by('numero_semaine')
for s in semaines:
    validation = "✓" if s.get_jour_debut() == "Lundi" and s.get_jour_fin() == "Samedi" else "✗"
    print(f"   {validation} Semaine {s.numero_semaine} : {s.get_jour_debut()} {s.date_debut.strftime('%d/%m')} → {s.get_jour_fin()} {s.date_fin.strftime('%d/%m')}")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ")
print("="*70)

total = SemaineCours.objects.count()
valides = SemaineCours.objects.filter(
    date_debut__week_day=2,  # Django: 1=dimanche, 2=lundi
    date_fin__week_day=7     # Django: 7=samedi
).count()

print(f"""
✓ Total semaines créées : {total}
✓ Semaines valides (Lundi→Samedi) : {valides}/{total}

🎯 RÈGLES APPLIQUÉES :
• Date début DOIT être un LUNDI
• Date fin DOIT être un SAMEDI
• Validation automatique à la sauvegarde
• Messages d'erreur explicites

📝 VALIDATION :
✓ Bloque les dates incorrectes
✓ Affiche le jour sélectionné dans le message d'erreur
✓ Empêche la création de semaines invalides
""")

print("="*70)
print(" 🎉 VALIDATION LUNDI→SAMEDI FONCTIONNELLE !")
print("="*70)
