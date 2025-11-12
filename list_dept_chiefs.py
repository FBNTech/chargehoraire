"""
Script pour lister les chefs de département par département
"""
import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Imports des modèles
from reglage.models import Departement, Grade, Fonction
from teachers.models import Teacher
from gestion_administrative.models import Etudiant

def get_department_chiefs():
    """Récupère les chefs de département pour chaque département"""
    departments = {}
    # Récupérer tous les départements uniques des enseignants
    teacher_depts = Teacher.objects.values_list('departement', flat=True).distinct()
    
    for dept in teacher_depts:
        # Chercher l'enseignant avec fonction CD dans ce département
        chief = Teacher.objects.filter(departement=dept, fonction='CD').first()
        if chief:
            grade = chief.grade
            try:
                grade_obj = Grade.objects.get(pk=grade)
                grade = grade_obj.DesignationGrade
            except:
                pass
            departments[dept] = {
                'chef': chief.nom_complet,
                'matricule': chief.matricule,
                'grade': grade
            }
        else:
            departments[dept] = {
                'chef': "Aucun chef assigné",
                'matricule': "",
                'grade': ""
            }
    
    return departments

if __name__ == '__main__':
    chiefs = get_department_chiefs()
    
    print("\n===== LISTE DES CHEFS DE DÉPARTEMENT =====\n")
    for dept, info in chiefs.items():
        print(f"Département: {dept}")
        print(f"Chef: {info['chef']}")
        if info['matricule']:
            print(f"Matricule: {info['matricule']}")
        if info['grade']:
            print(f"Grade: {info['grade']}")
        print("")
    
    # Afficher aussi les étudiants par département pour vérification
    print("\n===== ÉTUDIANTS PAR DÉPARTEMENT =====\n")
    student_depts = Etudiant.objects.values_list('departement', flat=True).distinct()
    for dept in student_depts:
        students = Etudiant.objects.filter(departement=dept).count()
        chief_info = chiefs.get(dept, {'chef': "Pas de chef assigné"})
        print(f"Département: {dept}")
        print(f"Nombre d'étudiants: {students}")
        print(f"Chef: {chief_info['chef']}")
        print("")
