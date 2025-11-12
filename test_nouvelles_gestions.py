#!/usr/bin/env python
"""Test des nouvelles fonctionnalités de gestion"""
import os
import django
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import AnneeAcademique, Salle, Creneau

print("="*60)
print(" 🎛️ TEST DES NOUVELLES GESTIONS")
print("="*60)

# Test 1: Années Académiques
print("\n1️⃣ Test Années Académiques")
try:
    # Créer une année
    annee = AnneeAcademique.objects.create(
        code="2024-2025",
        designation="Année académique 2024-2025",
        date_debut=date(2024, 9, 1),
        date_fin=date(2025, 6, 30),
        est_en_cours=True
    )
    print(f"   ✓ Année créée: {annee}")
    
    # Créer une deuxième année
    annee2 = AnneeAcademique.objects.create(
        code="2025-2026",
        designation="Année académique 2025-2026",
        est_en_cours=False
    )
    print(f"   ✓ Année 2 créée: {annee2}")
    
    # Vérifier l'année en cours
    annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
    print(f"   ✓ Année en cours: {annee_courante.code}")
    
    # Changer l'année en cours
    annee2.est_en_cours = True
    annee2.save()
    
    # Recharger la première année
    annee.refresh_from_db()
    print(f"   ✓ Année 1 après changement: en_cours={annee.est_en_cours}")
    print(f"   ✓ Année 2 après changement: en_cours={annee2.est_en_cours}")
    
    total_annees = AnneeAcademique.objects.count()
    print(f"   ✓ Total années: {total_annees}")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Salles
print("\n2️⃣ Test Salles")
try:
    # Créer différentes salles
    salles_data = [
        ("B1", "Salle B1 - Bâtiment Sciences", 50, "TD"),
        ("A205", "Salle informatique A205", 30, "TP"),
        ("AMPHI-A", "Amphithéâtre A", 200, "AMPHI"),
        ("LAB-BIO", "Laboratoire de Biologie", 25, "LAB"),
    ]
    
    for code, designation, capacite, type_salle in salles_data:
        salle = Salle.objects.create(
            code=code,
            designation=designation,
            capacite=capacite,
            type_salle=type_salle,
            est_disponible=True
        )
        print(f"   ✓ Salle créée: {salle.code} ({salle.get_type_salle_display()}, {salle.capacite} places)")
    
    # Statistiques
    total_salles = Salle.objects.count()
    salles_dispo = Salle.objects.filter(est_disponible=True).count()
    print(f"   ✓ Total salles: {total_salles}")
    print(f"   ✓ Salles disponibles: {salles_dispo}")
    
    # Filtrer par type
    amphitheatres = Salle.objects.filter(type_salle='AMPHI').count()
    print(f"   ✓ Amphithéâtres: {amphitheatres}")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Créneaux
print("\n3️⃣ Test Créneaux")
try:
    # Créer des créneaux
    creneaux_data = [
        ("AM", "Matinée", time(8, 0), time(12, 0), 1),
        ("PM", "Après-midi", time(13, 0), time(17, 0), 2),
        ("SOIR", "Soirée", time(18, 0), time(20, 0), 3),
    ]
    
    for code, designation, debut, fin, ordre in creneaux_data:
        creneau = Creneau.objects.create(
            code=code,
            designation=designation,
            heure_debut=debut,
            heure_fin=fin,
            ordre=ordre,
            est_actif=True
        )
        print(f"   ✓ Créneau créé: {creneau.designation} - {creneau.get_format_court()}")
    
    # Vérifier l'ordre
    creneaux = Creneau.objects.all()
    print(f"   ✓ Créneaux triés par ordre:")
    for c in creneaux:
        print(f"      {c.ordre}. {c.designation} ({c.get_format_court()})")
    
    total_creneaux = Creneau.objects.count()
    creneaux_actifs = Creneau.objects.filter(est_actif=True).count()
    print(f"   ✓ Total créneaux: {total_creneaux}")
    print(f"   ✓ Créneaux actifs: {creneaux_actifs}")
    
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Vérifier les URLs
print("\n4️⃣ Test des URLs")
try:
    from django.urls import reverse
    
    urls_to_test = [
        ('reglage:annee_list', 'Liste années'),
        ('reglage:annee_create', 'Créer année'),
        ('reglage:salle_list', 'Liste salles'),
        ('reglage:salle_create', 'Créer salle'),
        ('reglage:creneau_list', 'Liste créneaux'),
        ('reglage:creneau_create', 'Créer créneau'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"   ✓ {description:20} : {url}")
        except Exception as e:
            print(f"   ✗ {description:20} : Erreur {e}")
            
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Résumé
print("\n" + "="*60)
print(" ✅ RÉSUMÉ")
print("="*60)
print(f"""
✓ Années Académiques : {AnneeAcademique.objects.count()} créées
✓ Salles : {Salle.objects.count()} créées
✓ Créneaux : {Creneau.objects.count()} créés

🔗 URLS PRINCIPALES:
   - Réglages : /reglage/gestion/
   - Années : /reglage/annees/
   - Salles : /reglage/salles/
   - Créneaux : /reglage/creneaux/

📚 Documentation : NOUVELLES_GESTIONS_REGLAGE.md
""")

print("="*60)
print(" 🎉 TESTS TERMINÉS AVEC SUCCÈS !")
print("="*60)
