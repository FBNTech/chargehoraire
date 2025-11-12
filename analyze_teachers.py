"""
Script pour analyser la liste des enseignants et identifier les chefs de département
"""
import os
import django
from django.db.models import Count

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Imports des modèles
from teachers.models import Teacher
from reglage.models import Fonction, Grade

# Analyser les fonctions des enseignants
def analyze_teacher_functions():
    print("\n===== ANALYSE DES FONCTIONS D'ENSEIGNANTS =====\n")
    
    # Compter les occurrences de chaque fonction
    functions = Teacher.objects.values('fonction').annotate(count=Count('fonction')).order_by('-count')
    
    print(f"Nombre total d'enseignants: {Teacher.objects.count()}")
    print("\nDistribution des fonctions:")
    for func in functions:
        print(f"- {func['fonction']}: {func['count']} enseignant(s)")
    
    # Vérifier s'il y a une fonction spécifique pour les chefs de département
    potential_dept_chief_codes = ['CD', 'CHEF', 'DEPT', 'DIR']
    
    print("\nCodes de fonction possibles pour les chefs de département:")
    for code in potential_dept_chief_codes:
        count = Teacher.objects.filter(fonction__icontains=code).count()
        if count > 0:
            print(f"- '{code}': {count} enseignant(s)")
    
    # Lister tous les codes de fonction uniques pour analyse
    print("\nTous les codes de fonction utilisés:")
    all_functions = Teacher.objects.values_list('fonction', flat=True).distinct()
    for func in all_functions:
        print(f"- '{func}'")
    
    # Vérifier les tables de référence
    print("\nFonctions définies dans la table de référence:")
    try:
        fonctions = Fonction.objects.all()
        for f in fonctions:
            print(f"- {f.CodeFonction}: {f.DesignationFonction}")
    except Exception as e:
        print(f"Erreur lors de l'accès à la table Fonction: {str(e)}")

# Analyser les départements et leurs chefs potentiels
def list_departments_with_chiefs():
    print("\n===== DÉPARTEMENTS ET CHEFS POTENTIELS =====\n")
    
    departments = Teacher.objects.values_list('departement', flat=True).distinct()
    
    for dept in departments:
        print(f"\nDépartement: {dept}")
        
        # Trouver les enseignants de ce département avec leurs fonctions
        teachers = Teacher.objects.filter(departement=dept)
        
        print(f"Nombre d'enseignants: {teachers.count()}")
        
        # Afficher les enseignants avec des fonctions potentielles de chef
        potential_chiefs = []
        for teacher in teachers:
            fonction = teacher.fonction.upper()
            if 'CHEF' in fonction or 'DIR' in fonction or 'CD' in fonction or teacher.fonction == 'CD':
                try:
                    grade_display = Grade.objects.get(pk=teacher.grade).DesignationGrade
                except:
                    grade_display = teacher.grade
                
                potential_chiefs.append({
                    'nom': teacher.nom_complet,
                    'matricule': teacher.matricule,
                    'fonction': teacher.fonction,
                    'grade': grade_display
                })
        
        if potential_chiefs:
            print("Chefs potentiels:")
            for chief in potential_chiefs:
                print(f"- {chief['nom']} (Matricule: {chief['matricule']}, Fonction: {chief['fonction']}, Grade: {chief['grade']})")
        else:
            print("Aucun chef potentiel identifié dans ce département.")
            # Afficher quelques enseignants du département
            print("Quelques enseignants de ce département:")
            for teacher in teachers[:3]:
                print(f"- {teacher.nom_complet} (Fonction: {teacher.fonction})")

# Exécuter les analyses
if __name__ == "__main__":
    analyze_teacher_functions()
    list_departments_with_chiefs()
