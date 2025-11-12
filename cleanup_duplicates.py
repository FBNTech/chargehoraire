import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import Fonction, Grade, CategorieEnseignant, Departement, Section

def cleanup_duplicates():
    """
    Nettoie les doublons dans les tables de référence.
    Conserve un seul enregistrement pour chaque valeur unique (par code).
    """
    print("Début du nettoyage des doublons dans les tables de référence...")
    
    # Nettoyer les fonctions
    print("Nettoyage des fonctions...")
    fonction_codes = set()
    for fonction in Fonction.objects.all():
        if fonction.CodeFonction in fonction_codes:
            print(f"Suppression du doublon: {fonction.CodeFonction} - {fonction.DesignationFonction}")
            fonction.delete()
        else:
            fonction_codes.add(fonction.CodeFonction)
    
    # Nettoyer les grades
    print("Nettoyage des grades...")
    grade_codes = set()
    for grade in Grade.objects.all():
        if grade.CodeGrade in grade_codes:
            print(f"Suppression du doublon: {grade.CodeGrade} - {grade.DesignationGrade}")
            grade.delete()
        else:
            grade_codes.add(grade.CodeGrade)
    
    # Nettoyer les catégories
    print("Nettoyage des catégories...")
    categorie_codes = set()
    for categorie in CategorieEnseignant.objects.all():
        if categorie.CodeCategorie in categorie_codes:
            print(f"Suppression du doublon: {categorie.CodeCategorie} - {categorie.DesignationCategorie}")
            categorie.delete()
        else:
            categorie_codes.add(categorie.CodeCategorie)
    
    # Nettoyer les départements
    print("Nettoyage des départements...")
    departement_codes = set()
    for departement in Departement.objects.all():
        if departement.CodeDept in departement_codes:
            print(f"Suppression du doublon: {departement.CodeDept} - {departement.DesignationDept}")
            departement.delete()
        else:
            departement_codes.add(departement.CodeDept)
    
    # Nettoyer les sections
    print("Nettoyage des sections...")
    section_codes = set()
    for section in Section.objects.all():
        if section.CodeSection in section_codes:
            print(f"Suppression du doublon: {section.CodeSection} - {section.DesignationSection}")
            section.delete()
        else:
            section_codes.add(section.CodeSection)
    
    print("Nettoyage des doublons terminé.")

if __name__ == '__main__':
    cleanup_duplicates()
