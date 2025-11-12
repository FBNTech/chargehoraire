"""
Test de création d'attribution avec les données exactes de l'erreur
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Course
from teachers.models import Teacher
from attribution.models import Attribution
from django.db import transaction

print("=== TEST DE CRÉATION D'ATTRIBUTION ===\n")

# Données exactes de la requête
matricule = "7.893.009 C"
annee = "2025-2026"
type_charge = "Reguliere"
selected_cours = [
    {"id": "6", "code_ue": "AGV211", "cmi": 15, "td_tp": 0},
    {"id": "7", "code_ue": "AVG101", "cmi": 25, "td_tp": 20},
    {"id": "8", "code_ue": "AVG301B", "cmi": 50, "td_tp": 40}
]

# Test 1: Vérifier l'enseignant
print("1. Vérification de l'enseignant:")
try:
    teacher = Teacher.objects.get(matricule=matricule)
    print(f"   ✓ Enseignant trouvé: {teacher.nom_complet}")
except Teacher.DoesNotExist:
    print(f"   ✗ ERREUR: Enseignant avec matricule '{matricule}' non trouvé")
    print(f"\n   Enseignants disponibles:")
    for t in Teacher.objects.all()[:5]:
        print(f"      - {t.matricule} : {t.nom_complet}")
    exit(1)

# Test 2: Vérifier chaque cours
print("\n2. Vérification des cours:")
for cours in selected_cours:
    code_ue = cours['code_ue']
    try:
        course = Course.objects.get(code_ue=code_ue)
        print(f"   ✓ {code_ue}: {course.intitule_ue}")
    except Course.DoesNotExist:
        print(f"   ✗ ERREUR: Cours '{code_ue}' non trouvé")
    except Exception as e:
        print(f"   ✗ ERREUR sur {code_ue}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# Test 3: Simuler la création
print("\n3. Simulation de création d'attributions:")
try:
    attributions_created = []
    codes_ue_to_delete = []
    
    with transaction.atomic():
        for cours in selected_cours:
            code_ue = cours['code_ue']
            print(f"\n   Traitement de {code_ue}...")
            
            try:
                # Récupération des instances
                teacher = Teacher.objects.get(matricule=matricule)
                course = Course.objects.get(code_ue=code_ue)
                
                # Vérification si l'attribution existe déjà
                exists = Attribution.objects.filter(
                    matricule=teacher,
                    code_ue=course,
                    annee_academique=annee
                ).exists()
                
                if exists:
                    print(f"      ⚠️  Attribution déjà existante")
                    raise Exception(f"Une attribution existe déjà pour {code_ue}")
                
                # Création de l'attribution (EN MODE TEST, on rollback)
                attribution = Attribution.objects.create(
                    matricule=teacher,
                    code_ue=course,
                    annee_academique=annee,
                    type_charge=type_charge
                )
                attributions_created.append(attribution)
                codes_ue_to_delete.append(code_ue)
                print(f"      ✓ Attribution créée (sera annulée pour le test)")
                
            except Exception as e:
                print(f"      ✗ ERREUR: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Forcer le rollback pour ne pas vraiment créer
        print(f"\n   Rollback pour test (aucune modification enregistrée)")
        raise Exception("Test terminé - rollback forcé")
        
except Exception as e:
    if "Test terminé" in str(e):
        print(f"\n✓ Test réussi : {len(attributions_created)} attributions créées (puis annulées)")
    else:
        print(f"\n✗ Test échoué : {e}")

print("\n=== FIN DU TEST ===")
