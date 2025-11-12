#!/usr/bin/env python
"""
Test de suppression d'un cours avec la nouvelle méthode
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Course
from attribution.models import Attribution, ScheduleEntry
from django.db import transaction

def test_course_deletion():
    """Test de suppression d'un cours"""
    
    print("="*70)
    print("  TEST DE SUPPRESSION DE COURS")
    print("="*70)
    
    # Chercher un cours à supprimer (celui avec l'erreur)
    course_id = 1166
    
    try:
        course = Course.objects.get(id=course_id)
        print(f"\n✓ Cours trouvé : {course.code_ue} - {course.intitule_ue}")
    except Course.DoesNotExist:
        print(f"\n⚠️  Le cours ID={course_id} n'existe plus (peut-être déjà supprimé)")
        print("\n📋 Cours disponibles dans la base :")
        courses = Course.objects.all()[:10]
        if courses:
            for c in courses:
                attr_count = Attribution.objects.filter(code_ue=c).count()
                print(f"   - ID {c.id}: {c.code_ue} ({attr_count} attribution(s))")
        else:
            print("   Aucun cours dans la base")
        return
    
    # Compter les objets liés AVANT suppression
    attributions = Attribution.objects.filter(code_ue=course)
    attr_count = attributions.count()
    
    schedule_count = 0
    for attr in attributions:
        schedule_count += ScheduleEntry.objects.filter(attribution=attr).count()
    
    print(f"\n📊 Objets liés au cours :")
    print(f"   - {attr_count} attribution(s)")
    print(f"   - {schedule_count} horaire(s)")
    
    # Demander confirmation
    print(f"\n⚠️  Voulez-vous supprimer ce cours et tous ses objets liés ?")
    print(f"   Cours : {course.code_ue} - {course.intitule_ue}")
    print(f"   Total à supprimer : 1 cours + {attr_count} attributions + {schedule_count} horaires")
    
    response = input("\n   Taper 'OUI' pour confirmer : ")
    
    if response.strip().upper() != 'OUI':
        print("\n❌ Suppression annulée")
        return
    
    # Effectuer la suppression avec la méthode manuelle
    print("\n🔄 Suppression en cours...")
    
    try:
        with transaction.atomic():
            # Verrouiller le cours
            course = Course.objects.select_for_update().get(pk=course.pk)
            
            # 1. Supprimer les horaires
            print(f"   1. Suppression des {schedule_count} horaire(s)...")
            attributions = Attribution.objects.filter(code_ue=course)
            for attribution in attributions:
                deleted_schedules = ScheduleEntry.objects.filter(attribution=attribution).delete()
                print(f"      ✓ {deleted_schedules[0]} horaire(s) supprimé(s) pour {attribution}")
            
            # 2. Supprimer les attributions
            print(f"   2. Suppression des {attr_count} attribution(s)...")
            deleted_attrs = attributions.delete()
            print(f"      ✓ {deleted_attrs[0]} objet(s) supprimé(s)")
            
            # 3. Supprimer le cours
            print(f"   3. Suppression du cours...")
            course.delete()
            print(f"      ✓ Cours supprimé")
        
        print("\n✅ SUCCÈS : Cours supprimé avec tous ses objets liés !")
        print("   Aucune erreur 'attribution_attribution_old' !")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la suppression :")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        print("\n🔍 Détails de l'erreur :")
        traceback.print_exc()

if __name__ == '__main__':
    test_course_deletion()
    print("\n" + "="*70)
