"""
Script simplifié pour trouver les chefs de département
"""
import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import des modèles
from teachers.models import Teacher

# Fonction principale
def print_teacher_data():
    # Afficher tous les enseignants
    print("\n===== LISTE DES ENSEIGNANTS =====")
    teachers = Teacher.objects.all()
    for teacher in teachers:
        print(f"Nom: {teacher.nom_complet}")
        print(f"Matricule: {teacher.matricule}")
        print(f"Département: {teacher.departement}")
        print(f"Fonction: {teacher.fonction}")
        print(f"Grade: {teacher.grade}")
        print("-" * 40)

# Exécution
if __name__ == "__main__":
    print_teacher_data()
