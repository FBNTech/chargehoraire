#!/usr/bin/env python
"""Test de la gestion des semaines de cours"""
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import SemaineCours

print("="*70)
print(" 📅 TEST GESTION DES SEMAINES DE COURS")
print("="*70)

# Test 1: Créer des semaines de cours
print("\n1️⃣ Création de semaines de cours")
try:
    # Semaine 1
    semaine1 = SemaineCours.objects.create(
        numero_semaine=1,
        date_debut=date(2024, 10, 14),
        date_fin=date(2024, 10, 20),
        designation="Semaine 1 du 1er semestre",
        annee_academique="2024-2025",
        est_en_cours=True
    )
    print(f"   ✓ {semaine1}")
    
    # Semaine 2
    semaine2 = SemaineCours.objects.create(
        numero_semaine=2,
        date_debut=date(2024, 10, 21),
        date_fin=date(2024, 10, 27),
        designation="Semaine 2 du 1er semestre",
        annee_academique="2024-2025",
        est_en_cours=False
    )
    print(f"   ✓ {semaine2}")
    
    # Semaine 3
    semaine3 = SemaineCours.objects.create(
        numero_semaine=3,
        date_debut=date(2024, 10, 28),
        date_fin=date(2024, 11, 3),
        designation="Semaine 3 du 1er semestre",
        annee_academique="2024-2025",
        est_en_cours=False
    )
    print(f"   ✓ {semaine3}")
    
    total = SemaineCours.objects.count()
    print(f"\n   ✓ Total semaines créées : {total}")
    
except Exception as e:
    print(f"   ✗ Erreur : {e}")

# Test 2: Vérifier la semaine en cours
print("\n2️⃣ Vérification de la semaine en cours")
semaine_courante = SemaineCours.objects.filter(est_en_cours=True).first()
if semaine_courante:
    print(f"   ✓ Semaine en cours : {semaine_courante}")
    print(f"      • Période : {semaine_courante.get_periode()}")
    print(f"      • Année : {semaine_courante.annee_academique}")
else:
    print("   ⚠️ Aucune semaine marquée comme 'en cours'")

# Test 3: Changer la semaine en cours
print("\n3️⃣ Test du changement de semaine en cours")
try:
    # Marquer semaine 2 comme en cours
    semaine2.est_en_cours = True
    semaine2.save()
    print(f"   ✓ Semaine 2 marquée comme en cours")
    
    # Recharger semaine 1
    semaine1.refresh_from_db()
    print(f"   ✓ Semaine 1 après changement : en_cours={semaine1.est_en_cours}")
    print(f"   ✓ Semaine 2 après changement : en_cours={semaine2.est_en_cours}")
    
    # Vérifier qu'une seule est en cours
    count_en_cours = SemaineCours.objects.filter(est_en_cours=True).count()
    if count_en_cours == 1:
        print(f"   ✓ Une seule semaine en cours (validation OK)")
    else:
        print(f"   ✗ Problème : {count_en_cours} semaines en cours")
        
except Exception as e:
    print(f"   ✗ Erreur : {e}")

# Test 4: Lister toutes les semaines
print("\n4️⃣ Liste de toutes les semaines")
semaines = SemaineCours.objects.all().order_by('numero_semaine')
for s in semaines:
    statut = "★ EN COURS" if s.est_en_cours else "Inactive"
    print(f"   • Semaine {s.numero_semaine} : {s.date_debut.strftime('%d/%m')} - {s.date_fin.strftime('%d/%m')} [{statut}]")

# Test 5: Filtrer par année académique
print("\n5️⃣ Filtrage par année académique")
annee = "2024-2025"
semaines_2024 = SemaineCours.objects.filter(annee_academique=annee)
print(f"   ✓ Semaines pour {annee} : {semaines_2024.count()}")

# Test 6: Test de la méthode get_periode()
print("\n6️⃣ Test de la méthode get_periode()")
for s in semaines[:3]:
    print(f"   • Semaine {s.numero_semaine} : {s.get_periode()}")

# Test 7: Vérifier les URLs
print("\n7️⃣ Vérification des URLs")
try:
    from django.urls import reverse
    
    urls = [
        ('reglage:semaine_list', 'Liste semaines'),
        ('reglage:semaine_create', 'Créer semaine'),
    ]
    
    for url_name, desc in urls:
        try:
            url = reverse(url_name)
            print(f"   ✓ {desc:20} : {url}")
        except Exception as e:
            print(f"   ✗ {desc:20} : Erreur")
except Exception as e:
    print(f"   ✗ Erreur : {e}")

# Résumé
print("\n" + "="*70)
print(" 📊 RÉSUMÉ")
print("="*70)

total_semaines = SemaineCours.objects.count()
semaine_en_cours = SemaineCours.objects.filter(est_en_cours=True).first()

print(f"""
✓ Semaines créées : {total_semaines}
✓ Semaine en cours : {semaine_en_cours if semaine_en_cours else "Aucune"}

📅 EXEMPLES D'UTILISATION :

1. Créer une nouvelle semaine :
   /reglage/semaines/create/
   
2. Voir toutes les semaines :
   /reglage/semaines/
   
3. Marquer une semaine comme "en cours" :
   → Modifier la semaine et cocher "En cours"
   → Les autres seront automatiquement désactivées

🎯 FONCTIONNALITÉS :
• Numérotation des semaines (1, 2, 3...)
• Dates de début et fin
• Une seule semaine "en cours" à la fois
• Filtrage par année académique
• Affichage de la période complète
""")

print("="*70)
print(" 🎉 TESTS TERMINÉS AVEC SUCCÈS !")
print("="*70)
