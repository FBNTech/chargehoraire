"""
Script pour obtenir directement le nom d'un chef de département
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import des modèles
from teachers.models import Teacher
from gestion_administrative.models import Etudiant

# Prendre un étudiant comme exemple
etudiant = Etudiant.objects.first()
if etudiant:
    # Afficher les informations de l'étudiant
    print(f"Étudiant: {etudiant.nom_complet}")
    print(f"Département: {etudiant.departement}")
    
    # Chercher le chef de département
    dept_chef = Teacher.objects.filter(departement=etudiant.departement, fonction='CD').first()
    if dept_chef:
        print(f"\nChef de département trouvé:")
        print(f"Nom: {dept_chef.nom_complet}")
        print(f"Matricule: {dept_chef.matricule}")
        print(f"Grade: {dept_chef.grade}")
        print(f"Fonction: {dept_chef.fonction}")
    else:
        # Essayer avec d'autres codes fonction possibles
        for code in ['CHEF', 'DIR', 'DOYEN']:
            dept_chef = Teacher.objects.filter(departement=etudiant.departement, fonction__icontains=code).first()
            if dept_chef:
                print(f"\nChef potentiel trouvé (fonction contient '{code}'):")
                print(f"Nom: {dept_chef.nom_complet}")
                print(f"Matricule: {dept_chef.matricule}")
                print(f"Grade: {dept_chef.grade}")
                print(f"Fonction: {dept_chef.fonction}")
                break
        else:
            # Si aucun chef n'est trouvé, afficher tous les enseignants du département
            teachers = Teacher.objects.filter(departement=etudiant.departement)
            print(f"\nAucun chef de département identifié. Liste des enseignants du département:")
            for teacher in teachers[:5]:  # Limiter à 5 pour éviter une liste trop longue
                print(f"- {teacher.nom_complet} (Fonction: {teacher.fonction})")
else:
    print("Aucun étudiant trouvé dans la base de données.")
