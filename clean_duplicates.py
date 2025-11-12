import os
import django
from collections import defaultdict

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import Fonction, Grade, CategorieEnseignant, Departement, Section

def print_table_content(model_class, code_field, designation_field):
    """Affiche le contenu d'une table avec ses ID et champs principaux"""
    print(f"\n=== CONTENU DE LA TABLE {model_class.__name__} ===")
    print(f"{code_field} | {designation_field}")
    print("-" * 40)
    for item in model_class.objects.all().order_by(code_field):
        code_value = getattr(item, code_field)
        designation_value = getattr(item, designation_field)
        print(f"{code_value} | {designation_value}")

def find_duplicates(model_class, code_field, designation_field):
    """Trouve les doublons approximatifs dans une table"""
    items_by_code = defaultdict(list)
    items_by_designation = defaultdict(list)
    
    # Grouper par code et par désignation
    for item in model_class.objects.all():
        code_value = getattr(item, code_field)
        designation_value = getattr(item, designation_field)
        items_by_code[code_value].append(item)
        
        # Pour trouver des variations similaires (ex: "Technique" vs "Techniques")
        # On normalise en minuscules et on supprime les "s" finaux
        normalized = designation_value.lower().rstrip('s')
        items_by_designation[normalized].append((item, designation_value))
    
    # Vérifier les doublons par code
    print(f"\n=== DOUBLONS PAR {code_field.upper()} DANS {model_class.__name__} ===")
    for code, items in items_by_code.items():
        if len(items) > 1:
            print(f"Code '{code}' apparaît {len(items)} fois:")
            for item in items:
                print(f"  - {getattr(item, designation_field)}")
    
    # Vérifier les variations similaires par désignation
    print(f"\n=== VARIATIONS SIMILAIRES PAR {designation_field.upper()} DANS {model_class.__name__} ===")
    for norm, items in items_by_designation.items():
        if len(items) > 1:
            print(f"Désignation normalisée '{norm}' a {len(items)} variations:")
            for item, original in items:
                print(f"  - {original} (Code: {getattr(item, code_field)})")

def clean_duplicates_section():
    """Nettoie les doublons dans la table Section"""
    print("\n=== NETTOYAGE DE LA TABLE SECTION ===\n")
    
    # Standardiser les variations connues
    replacements = {
        "Science et Technologie": "Sciences et Technologie",
        "Technique": "Techniques", 
        "Lettre, Langues et Art": "Lettres, Langues et Arts"
    }
    
    # Première étape: afficher les sections actuelles
    print("Sections avant nettoyage:")
    print_table_content(Section, 'CodeSection', 'DesignationSection')
    
    # Deuxième étape: standardiser les désignations
    cleaned = 0
    for old_name, new_name in replacements.items():
        sections = Section.objects.filter(DesignationSection=old_name)
        for section in sections:
            # Chercher si une section avec la nouvelle désignation existe déjà
            existing = Section.objects.filter(DesignationSection=new_name).first()
            if existing:
                print(f"Suppression de '{section.DesignationSection}' (Code: {section.CodeSection}) - doublon de '{existing.DesignationSection}'")
                # Vérifier si des départements sont liés à cette section
                related_departments = Departement.objects.filter(section=section)
                if related_departments.exists():
                    print(f"  {related_departments.count()} départements sont liés à cette section, mise à jour...")
                    for dept in related_departments:
                        dept.section = existing
                        dept.save()
                        print(f"  - Département '{dept.DesignationDept}' migré vers la section '{existing.DesignationSection}'")
                section.delete()
            else:
                # Si aucune section avec la nouvelle désignation n'existe, renommer celle-ci
                print(f"Renommage de '{section.DesignationSection}' en '{new_name}'")
                section.DesignationSection = new_name
                section.save()
            cleaned += 1
    
    # Troisième étape: fusionner les codes identiques
    sections_by_code = defaultdict(list)
    for section in Section.objects.all():
        sections_by_code[section.CodeSection].append(section)
    
    for code, sections in sections_by_code.items():
        if len(sections) > 1:
            print(f"Code '{code}' a {len(sections)} occurrences, conservation de la première seulement")
            primary = sections[0]
            for duplicate in sections[1:]:
                # Vérifier si des départements sont liés à ce doublon
                related_departments = Departement.objects.filter(section=duplicate)
                if related_departments.exists():
                    print(f"  {related_departments.count()} départements sont liés à ce doublon, mise à jour...")
                    for dept in related_departments:
                        dept.section = primary
                        dept.save()
                        print(f"  - Département '{dept.DesignationDept}' migré vers la section principale")
                duplicate.delete()
                cleaned += 1
    
    # Quatrième étape: afficher les sections après nettoyage
    print("\nSections après nettoyage:")
    print_table_content(Section, 'CodeSection', 'DesignationSection')
    
    print(f"\nNettoyage terminé: {cleaned} modifications effectuées.")


def clean_duplicates_departement():
    """Nettoie les doublons dans la table Departement"""
    print("\n=== NETTOYAGE DE LA TABLE DEPARTEMENT ===\n")
    
    # Standardiser les variations connues
    replacements = {
        "Mathématique": "Mathématiques",
        "Informatique": "Informatique",
        "Biologie": "Biologie",
        "Chimie": "Chimie",
        "Physique": "Physique",
        "Histoire": "Histoire",
    }
    
    # Première étape: afficher les départements actuels
    print("Départements avant nettoyage:")
    print_table_content(Departement, 'CodeDept', 'DesignationDept')
    
    # Deuxième étape: définir les codes de référence pour chaque désignation
    reference_codes = {
        "Mathématiques": "MATH",
        "Informatique": "INFO",
        "Biologie": "BIO",
        "Chimie": "CHI",
        "Physique": "PHY",
        "Histoire": "HIST",
        "Anglais": "ANG",
    }
    
    # Troisième étape: normaliser les départements
    cleaned = 0
    for designation, code in reference_codes.items():
        # Trouver tous les départements avec une désignation similaire
        similar_depts = Departement.objects.filter(DesignationDept__icontains=designation)
        if similar_depts.exists():
            # Si plusieurs départements similaires, conserver celui avec le code de référence
            reference_dept = Departement.objects.filter(CodeDept=code).first()
            
            if not reference_dept and similar_depts.exists():
                # Si aucun département avec le code de référence n'existe, utiliser le premier trouvé
                reference_dept = similar_depts.first()
                reference_dept.CodeDept = code
                reference_dept.DesignationDept = designation
                reference_dept.save()
                print(f"Département '{reference_dept.DesignationDept}' standardisé avec le code '{code}'")
                cleaned += 1
            
            # Supprimer les autres départements similaires
            for dept in similar_depts:
                if dept.CodeDept != code:
                    print(f"Suppression du doublon '{dept.DesignationDept}' (Code: {dept.CodeDept})")
                    dept.delete()
                    cleaned += 1
    
    # Quatrième étape: afficher les départements après nettoyage
    print("\nDépartements après nettoyage:")
    print_table_content(Departement, 'CodeDept', 'DesignationDept')
    
    print(f"\nNettoyage terminé: {cleaned} modifications effectuées.")


def clean_duplicates_categorie():
    """Nettoie les doublons dans la table CategorieEnseignant"""
    print("\n=== NETTOYAGE DE LA TABLE CATEGORIEENSEIGNANT ===\n")
    
    # Première étape: afficher les catégories actuelles
    print("Catégories avant nettoyage:")
    print_table_content(CategorieEnseignant, 'CodeCategorie', 'DesignationCategorie')
    
    # Deuxième étape: définir les codes de référence
    reference_map = {
        "Permanent": "PERM",
        "Visiteur": "VIS"
    }
    
    # Troisième étape: standardiser les catégories
    cleaned = 0
    for designation, code in reference_map.items():
        # Trouver toutes les catégories avec cette désignation
        similar_cats = CategorieEnseignant.objects.filter(DesignationCategorie__icontains=designation)
        
        if similar_cats.exists():
            # Vérifier si une catégorie avec le code de référence existe
            reference_cat = CategorieEnseignant.objects.filter(CodeCategorie=code).first()
            
            if not reference_cat and similar_cats.exists():
                # Si aucune catégorie avec le code de référence n'existe, utiliser la première trouvée
                reference_cat = similar_cats.first()
                reference_cat.CodeCategorie = code
                reference_cat.DesignationCategorie = designation
                reference_cat.save()
                print(f"Catégorie '{reference_cat.DesignationCategorie}' standardisée avec le code '{code}'")
                cleaned += 1
            
            # Supprimer les autres catégories similaires
            for cat in similar_cats:
                if cat.CodeCategorie != code:
                    print(f"Suppression du doublon '{cat.DesignationCategorie}' (Code: {cat.CodeCategorie})")
                    cat.delete()
                    cleaned += 1
    
    # Quatrième étape: afficher les catégories après nettoyage
    print("\nCatégories après nettoyage:")
    print_table_content(CategorieEnseignant, 'CodeCategorie', 'DesignationCategorie')
    
    print(f"\nNettoyage terminé: {cleaned} modifications effectuées.")


def clean_duplicates_fonction():
    """Nettoie les doublons dans la table Fonction"""
    print("\n=== NETTOYAGE DE LA TABLE FONCTION ===\n")
    
    # Première étape: afficher les fonctions actuelles
    print("Fonctions avant nettoyage:")
    print_table_content(Fonction, 'CodeFonction', 'DesignationFonction')
    
    # Deuxième étape: standardiser l'entrée Enseignant
    cleaned = 0
    enseignant_fonctions = Fonction.objects.filter(DesignationFonction='Enseignant')
    
    if enseignant_fonctions.exists():
        # Conserver seulement la fonction avec le code ENS
        reference = Fonction.objects.filter(CodeFonction='ENS').first()
        
        if not reference and enseignant_fonctions.exists():
            reference = enseignant_fonctions.first()
            reference.CodeFonction = 'ENS'
            reference.save()
            print(f"Fonction '{reference.DesignationFonction}' standardisée avec le code 'ENS'")
            cleaned += 1
        
        # Supprimer les autres fonctions Enseignant
        for fonction in enseignant_fonctions:
            if fonction.CodeFonction != 'ENS':
                print(f"Suppression du doublon '{fonction.DesignationFonction}' (Code: {fonction.CodeFonction})")
                fonction.delete()
                cleaned += 1
    
    # Troisième étape: afficher les fonctions après nettoyage
    print("\nFonctions après nettoyage:")
    print_table_content(Fonction, 'CodeFonction', 'DesignationFonction')
    
    print(f"\nNettoyage terminé: {cleaned} modifications effectuées.")


def clean_duplicates_grade():
    """Nettoie les doublons dans la table Grade"""
    print("\n=== NETTOYAGE DE LA TABLE GRADE ===\n")
    
    # Première étape: afficher les grades actuels
    print("Grades avant nettoyage:")
    print_table_content(Grade, 'CodeGrade', 'DesignationGrade')
    
    # Deuxième étape: vérifier s'il y a des doublons à nettoyer
    # Le diagnostic n'a pas montré de doublons pour les grades, mais vérifions quand même
    cleaned = 0
    grade_by_code = defaultdict(list)
    
    for grade in Grade.objects.all():
        grade_by_code[grade.CodeGrade.strip().upper()].append(grade)
    
    for code, grades in grade_by_code.items():
        if len(grades) > 1:
            print(f"Code '{code}' a {len(grades)} occurrences, conservation de la première seulement")
            primary = grades[0]
            for duplicate in grades[1:]:
                print(f"Suppression du doublon '{duplicate.DesignationGrade}' (Code: {duplicate.CodeGrade})")
                duplicate.delete()
                cleaned += 1
    
    # Troisième étape: afficher les grades après nettoyage
    print("\nGrades après nettoyage:")
    print_table_content(Grade, 'CodeGrade', 'DesignationGrade')
    
    print(f"\nNettoyage terminé: {cleaned} modifications effectuées.")

if __name__ == '__main__':
    # Afficher le contenu initial de toutes les tables
    print("=== ÉTAT INITIAL DES TABLES ===")
    print_table_content(Section, 'CodeSection', 'DesignationSection')
    print_table_content(Departement, 'CodeDept', 'DesignationDept')
    print_table_content(Grade, 'CodeGrade', 'DesignationGrade')
    print_table_content(CategorieEnseignant, 'CodeCategorie', 'DesignationCategorie')
    print_table_content(Fonction, 'CodeFonction', 'DesignationFonction')
    
    # Trouver les doublons dans chaque table
    find_duplicates(Section, 'CodeSection', 'DesignationSection')
    find_duplicates(Departement, 'CodeDept', 'DesignationDept')
    find_duplicates(Grade, 'CodeGrade', 'DesignationGrade')
    find_duplicates(CategorieEnseignant, 'CodeCategorie', 'DesignationCategorie')
    find_duplicates(Fonction, 'CodeFonction', 'DesignationFonction')
    
    # Nettoyer les doublons dans toutes les tables
    print("\n=== DÉMARRAGE DU NETTOYAGE DE TOUTES LES TABLES ===\n")
    clean_duplicates_section()
    clean_duplicates_departement()
    clean_duplicates_categorie()
    clean_duplicates_fonction()
    clean_duplicates_grade()
    
    print("\n=== NETTOYAGE COMPLET TERMINÉ ===\n")
    print("Résumé des tables après nettoyage:")
    print("Sections: {0} entrées".format(Section.objects.count()))
    print("Départements: {0} entrées".format(Departement.objects.count()))
    print("Catégories: {0} entrées".format(CategorieEnseignant.objects.count()))
    print("Fonctions: {0} entrées".format(Fonction.objects.count()))
    print("Grades: {0} entrées".format(Grade.objects.count()))
