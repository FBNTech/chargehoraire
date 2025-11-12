import os
import django
from collections import defaultdict

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reglage.models import Fonction, Grade, CategorieEnseignant, Departement, Section

def diagnose_duplicates():
    """
    Examine en détail les tables de référence pour identifier la source des doublons.
    """
    print("=== DIAGNOSTIC DES DOUBLONS DANS LES TABLES DE RÉFÉRENCE ===\n")
    
    # Examiner les fonctions
    print("=== FONCTIONS ===")
    fonction_map = defaultdict(list)
    print("ID | CodeFonction | DesignationFonction")
    print("-" * 40)
    for f in Fonction.objects.all().order_by('CodeFonction'):
        print(f"{f.id} | {f.CodeFonction} | {f.DesignationFonction}")
        fonction_map[f.CodeFonction].append(f)
    
    print("\nDoublons détectés par CodeFonction:")
    for code, items in fonction_map.items():
        if len(items) > 1:
            print(f"  Code '{code}' apparaît {len(items)} fois: {[(i.id, i.DesignationFonction) for i in items]}")
    
    # Examiner les grades
    print("\n=== GRADES ===")
    grade_map = defaultdict(list)
    print("ID | CodeGrade | DesignationGrade")
    print("-" * 40)
    for g in Grade.objects.all().order_by('CodeGrade'):
        print(f"{g.id} | {g.CodeGrade} | {g.DesignationGrade}")
        grade_map[g.CodeGrade].append(g)
    
    print("\nDoublons détectés par CodeGrade:")
    for code, items in grade_map.items():
        if len(items) > 1:
            print(f"  Code '{code}' apparaît {len(items)} fois: {[(i.id, i.DesignationGrade) for i in items]}")
    
    # Examiner les catégories
    print("\n=== CATÉGORIES ===")
    categorie_map = defaultdict(list)
    print("ID | CodeCategorie | DesignationCategorie")
    print("-" * 40)
    for c in CategorieEnseignant.objects.all().order_by('CodeCategorie'):
        print(f"{c.id} | {c.CodeCategorie} | {c.DesignationCategorie}")
        categorie_map[c.CodeCategorie].append(c)
    
    print("\nDoublons détectés par CodeCategorie:")
    for code, items in categorie_map.items():
        if len(items) > 1:
            print(f"  Code '{code}' apparaît {len(items)} fois: {[(i.id, i.DesignationCategorie) for i in items]}")
    
    # Examiner les départements
    print("\n=== DÉPARTEMENTS ===")
    departement_map = defaultdict(list)
    print("ID | CodeDept | DesignationDept")
    print("-" * 40)
    for d in Departement.objects.all().order_by('CodeDept'):
        print(f"{d.id} | {d.CodeDept} | {d.DesignationDept}")
        departement_map[d.CodeDept].append(d)
    
    print("\nDoublons détectés par CodeDept:")
    for code, items in departement_map.items():
        if len(items) > 1:
            print(f"  Code '{code}' apparaît {len(items)} fois: {[(i.id, i.DesignationDept) for i in items]}")
    
    # Examiner les sections
    print("\n=== SECTIONS ===")
    section_map = defaultdict(list)
    print("ID | CodeSection | DesignationSection")
    print("-" * 40)
    for s in Section.objects.all().order_by('CodeSection'):
        print(f"{s.id} | {s.CodeSection} | {s.DesignationSection}")
        section_map[s.CodeSection].append(s)
    
    print("\nDoublons détectés par CodeSection:")
    for code, items in section_map.items():
        if len(items) > 1:
            print(f"  Code '{code}' apparaît {len(items)} fois: {[(i.id, i.DesignationSection) for i in items]}")

if __name__ == '__main__':
    diagnose_duplicates()
