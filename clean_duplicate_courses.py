"""
Script pour identifier et nettoyer les cours dupliqués
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Course
from django.db.models import Count

print("=== NETTOYAGE DES COURS DUPLIQUÉS ===\n")

# 1. Identifier les doublons
print("1. Identification des cours dupliqués:")
duplicates = (Course.objects
    .values('code_ue')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
    .order_by('code_ue'))

if not duplicates:
    print("   ✓ Aucun doublon trouvé")
else:
    print(f"   ⚠️  {len(duplicates)} codes UE dupliqués trouvés:\n")
    
    for dup in duplicates:
        code_ue = dup['code_ue']
        count = dup['count']
        print(f"   - {code_ue}: {count} occurrences")
        
        # Afficher les détails de chaque occurrence
        courses = Course.objects.filter(code_ue=code_ue).order_by('id')
        for i, course in enumerate(courses, 1):
            print(f"     [{i}] ID={course.id}, Classe={course.classe}, Dept={course.departement}")
    
    # 2. Supprimer les doublons (garder le premier, supprimer les autres)
    print("\n2. Suppression des doublons (conservation du premier):")
    total_deleted = 0
    
    for dup in duplicates:
        code_ue = dup['code_ue']
        courses = Course.objects.filter(code_ue=code_ue).order_by('id')
        
        # Garder le premier, supprimer les autres
        first_course = courses.first()
        to_delete = courses.exclude(id=first_course.id)
        
        deleted_count = to_delete.count()
        if deleted_count > 0:
            print(f"   - {code_ue}: conservation de l'ID={first_course.id}, suppression de {deleted_count} doublon(s)")
            to_delete.delete()
            total_deleted += deleted_count
    
    print(f"\n   ✓ Total supprimé: {total_deleted} cours dupliqués")

# 3. Vérification finale
print("\n3. Vérification finale:")
remaining_duplicates = (Course.objects
    .values('code_ue')
    .annotate(count=Count('id'))
    .filter(count__gt=1))

if remaining_duplicates.exists():
    print(f"   ⚠️  Il reste {remaining_duplicates.count()} doublons")
else:
    print("   ✓ Plus aucun doublon")

print("\n=== NETTOYAGE TERMINÉ ===")
