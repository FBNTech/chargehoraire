"""
Test pour reproduire l'erreur avec Course.objects.get()
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Course
from teachers.models import Teacher
from attribution.models import Attribution

print("=== TEST DE REQUÊTE COURSE ===\n")

# Test 1: Lister tous les cours
print("1. Liste de tous les cours:")
try:
    all_courses = Course.objects.all()
    print(f"   Nombre de cours: {all_courses.count()}")
    if all_courses.exists():
        print(f"   Premier cours: {all_courses.first()}")
except Exception as e:
    print(f"   ERREUR: {e}")

# Test 2: Chercher le cours AGV211 mentionné dans l'erreur
print("\n2. Recherche du cours AGV211:")
try:
    course = Course.objects.get(code_ue='AGV211')
    print(f"   Cours trouvé: {course}")
except Course.DoesNotExist:
    print("   Cours AGV211 n'existe pas")
except Exception as e:
    print(f"   ERREUR: {e}")

# Test 3: Rechercher n'importe quel cours
print("\n3. Test de création d'attribution:")
try:
    # Prendre le premier cours disponible
    course = Course.objects.first()
    if course:
        print(f"   Cours: {course.code_ue}")
        
        # Prendre le premier enseignant
        teacher = Teacher.objects.first()
        if teacher:
            print(f"   Enseignant: {teacher.nom_complet}")
            
            # Simuler la création (sans vraiment créer)
            print(f"   Test de vérification avant création...")
            exists = Attribution.objects.filter(
                matricule=teacher,
                code_ue=course,
                annee_academique='2025-2026'
            ).exists()
            print(f"   Attribution existe déjà: {exists}")
        else:
            print("   Aucun enseignant trouvé")
    else:
        print("   Aucun cours trouvé")
except Exception as e:
    print(f"   ERREUR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== FIN DU TEST ===")
