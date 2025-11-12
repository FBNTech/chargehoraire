import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Cours_Attribution, Course, Attribution
from teachers.models import Teacher
import json

# Données de test : 4 cours BIO221 pour différentes classes
selected_cours = [
    {"id": "25", "code_ue": "BIO221"},  # L2 IT
    {"id": "26", "code_ue": "BIO221"},  # L2 GCAF/GE/TSD
    {"id": "27", "code_ue": "BIO221"},  # L2 BC
    {"id": "28", "code_ue": "BIO221"},  # L2 CST
]

# Récupérer un enseignant
teacher = Teacher.objects.first()
if not teacher:
    print("❌ Aucun enseignant trouvé dans la base")
    exit()

matricule = teacher.matricule
annee = "2025-2026"
type_charge = "reguliere"

print("=" * 60)
print("TEST D'ATTRIBUTION MULTIPLE")
print("=" * 60)
print(f"Enseignant: {teacher.nom_complet} (Matricule: {matricule})")
print(f"Année: {annee}")
print(f"Type charge: {type_charge}")
print(f"Nombre de cours à attribuer: {len(selected_cours)}")
print("-" * 60)

# Compter avant
cours_attr_avant = Cours_Attribution.objects.count()
course_avant = Course.objects.count()
attribution_avant = Attribution.objects.count()

print(f"\n📊 AVANT L'ATTRIBUTION:")
print(f"  - Cours_Attribution: {cours_attr_avant} cours")
print(f"  - Course: {course_avant} cours")
print(f"  - Attribution: {attribution_avant} attributions")

# Simulation du backend
attributions_created = []
codes_ue_to_delete = []
skipped_courses = []
errors = []

print(f"\n🔄 TRAITEMENT DES COURS...")

for cours in selected_cours:
    try:
        # Récupération du cours depuis Cours_Attribution
        cours_attr = Cours_Attribution.objects.get(id=cours['id'])
        print(f"\n  ✓ Trouvé dans Cours_Attribution: {cours_attr.code_ue} - {cours_attr.classe}")
        
        # Créer/récupérer dans Course
        course, created = Course.objects.get_or_create(
            code_ue=cours_attr.code_ue,
            intitule_ue=cours_attr.intitule_ue,
            classe=cours_attr.classe,
            semestre=cours_attr.semestre,
            defaults={
                'intitule_ec': cours_attr.intitule_ec,
                'credit': cours_attr.credit,
                'cmi': cours_attr.cmi,
                'td_tp': cours_attr.td_tp,
                'departement': cours_attr.departement,
                'section': cours_attr.section,
            }
        )
        
        if created:
            print(f"    → Créé dans Course (ID: {course.id})")
        else:
            print(f"    → Déjà dans Course (ID: {course.id})")
        
        # Vérifier si attribution existe
        existing = Attribution.objects.filter(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee
        ).first()
        
        if existing:
            print(f"    ⚠️  Attribution déjà existante")
            skipped_courses.append(f"{cours['code_ue']} - {cours_attr.classe}")
            continue
        
        # Créer attribution
        attribution = Attribution.objects.create(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee,
            type_charge=type_charge
        )
        attributions_created.append(attribution)
        codes_ue_to_delete.append(cours['code_ue'])
        print(f"    ✅ Attribution créée (ID: {attribution.id})")
        
    except Cours_Attribution.DoesNotExist:
        error_msg = f"Cours avec ID {cours['id']} non trouvé dans Cours_Attribution"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")
    except Exception as e:
        error_msg = f"Erreur pour {cours['code_ue']} (ID:{cours['id']}): {str(e)}"
        errors.append(error_msg)
        print(f"    ❌ {error_msg}")

# Compter après
cours_attr_apres = Cours_Attribution.objects.count()
course_apres = Course.objects.count()
attribution_apres = Attribution.objects.count()

print(f"\n📊 APRÈS L'ATTRIBUTION:")
print(f"  - Cours_Attribution: {cours_attr_apres} cours")
print(f"  - Course: {course_apres} cours")
print(f"  - Attribution: {attribution_apres} attributions")

print(f"\n📈 RÉSULTATS:")
print(f"  ✅ Attributions créées: {len(attributions_created)}")
print(f"  ⚠️  Cours ignorés: {len(skipped_courses)}")
print(f"  ❌ Erreurs: {len(errors)}")

if attributions_created:
    print(f"\n✅ SUCCÈS - {len(attributions_created)} cours attribués:")
    for attr in attributions_created:
        print(f"     - {attr.code_ue.code_ue} ({attr.code_ue.classe})")

if skipped_courses:
    print(f"\n⚠️  IGNORÉS:")
    for course in skipped_courses:
        print(f"     - {course}")

if errors:
    print(f"\n❌ ERREURS:")
    for error in errors:
        print(f"     - {error}")

print("\n" + "=" * 60)

# Annuler les changements
print("\n🔄 ANNULATION DES MODIFICATIONS (rollback)...")
for attr in attributions_created:
    attr.delete()
print(f"   ✓ {len(attributions_created)} attributions supprimées")

print("\n✅ TEST TERMINÉ (aucune modification conservée)")
