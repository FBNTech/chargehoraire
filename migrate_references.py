import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teachers.models import Teacher
from reglage.models import Fonction, Grade, CategorieEnseignant, Departement, Section

def migrate_references():
    """
    Migre toutes les valeurs existantes des enseignants vers les tables de référence
    pour éviter les problèmes de validation des formulaires.
    """
    print("Début de la migration des références...")
    
    # Migration des fonctions
    fonctions_existantes = set(Teacher.objects.values_list('fonction', flat=True).distinct())
    print(f"Fonctions existantes trouvées: {fonctions_existantes}")
    
    for fonction in fonctions_existantes:
        if not fonction:
            continue
        fonction_obj, created = Fonction.objects.get_or_create(
            CodeFonction=fonction,
            defaults={'DesignationFonction': fonction}
        )
        if created:
            print(f"Fonction ajoutée: {fonction}")
    
    # Migration des grades
    grades_existants = set(Teacher.objects.values_list('grade', flat=True).distinct())
    print(f"Grades existants trouvés: {grades_existants}")
    
    for grade in grades_existants:
        if not grade:
            continue
        grade_obj, created = Grade.objects.get_or_create(
            CodeGrade=grade,
            defaults={'DesignationGrade': grade}
        )
        if created:
            print(f"Grade ajouté: {grade}")
    
    # Migration des catégories
    categories_existantes = set(Teacher.objects.values_list('categorie', flat=True).distinct())
    print(f"Catégories existantes trouvées: {categories_existantes}")
    
    for categorie in categories_existantes:
        if not categorie:
            continue
        categorie_obj, created = CategorieEnseignant.objects.get_or_create(
            CodeCategorie=categorie,
            defaults={'DesignationCategorie': categorie}
        )
        if created:
            print(f"Catégorie ajoutée: {categorie}")
    
    # Migration des départements
    departements_existants = set(Teacher.objects.values_list('departement', flat=True).distinct())
    print(f"Départements existants trouvés: {departements_existants}")
    
    for departement in departements_existants:
        if not departement:
            continue
        dept_obj, created = Departement.objects.get_or_create(
            CodeDept=departement,
            defaults={
                'DesignationDept': departement,
                # Nous devons associer à une section existante ou en créer une par défaut
                'section': Section.objects.first() or Section.objects.create(
                    CodeSection="DEFAULT",
                    DesignationSection="Section par défaut"
                )
            }
        )
        if created:
            print(f"Département ajouté: {departement}")
    
    # Migration des sections
    sections_existantes = set(Teacher.objects.values_list('section', flat=True).distinct())
    print(f"Sections existantes trouvées: {sections_existantes}")
    
    for section in sections_existantes:
        if not section:
            continue
        section_obj, created = Section.objects.get_or_create(
            CodeSection=section,
            defaults={'DesignationSection': section}
        )
        if created:
            print(f"Section ajoutée: {section}")
    
    print("Migration des références terminée.")

if __name__ == '__main__':
    migrate_references()
