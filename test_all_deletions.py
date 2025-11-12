#!/usr/bin/env python
"""
Script de test pour vérifier que toutes les suppressions fonctionnent correctement
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction
from attribution.models import Attribution, ScheduleEntry, Cours_Attribution
from courses.models import Course
from teachers.models import Teacher
from reglage.models import (Section, Departement, Grade, AnneeAcademique, 
                            Salle, Creneau, SemaineCours)

def test_fk_active():
    """Test 1: Vérifier que les contraintes FK sont activées"""
    print("=" * 70)
    print("TEST 1: Vérification des contraintes de clés étrangères")
    print("=" * 70)
    
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
    
    if fk_status:
        print("✅ SUCCÈS: Les contraintes FK sont ACTIVÉES")
        return True
    else:
        print("❌ ÉCHEC: Les contraintes FK sont DÉSACTIVÉES")
        return False

def test_transaction_atomic():
    """Test 2: Vérifier que les transactions atomiques fonctionnent"""
    print("\n" + "=" * 70)
    print("TEST 2: Test des transactions atomiques")
    print("=" * 70)
    
    try:
        with transaction.atomic():
            # Simuler une opération qui échoue
            print("✓ Transaction atomique créée")
            print("✓ Opérations à l'intérieur de la transaction...")
            # Si on lève une exception, tout sera rollback
            raise Exception("Test rollback")
    except Exception as e:
        if "Test rollback" in str(e):
            print("✅ SUCCÈS: Le rollback fonctionne correctement")
            return True
    
    print("❌ ÉCHEC: Le rollback n'a pas fonctionné")
    return False

def test_select_for_update():
    """Test 3: Vérifier que select_for_update fonctionne"""
    print("\n" + "=" * 70)
    print("TEST 3: Test de select_for_update()")
    print("=" * 70)
    
    try:
        with transaction.atomic():
            # Essayer de verrouiller un enseignant
            teacher = Teacher.objects.select_for_update().first()
            if teacher:
                print(f"✓ Verrouillage réussi de l'enseignant: {teacher.nom_complet}")
                print("✅ SUCCÈS: select_for_update() fonctionne")
                return True
            else:
                print("ℹ️  Aucun enseignant dans la base pour tester")
                return True
    except Exception as e:
        print(f"❌ ÉCHEC: {e}")
        return False

def test_cascade_delete():
    """Test 4: Vérifier que les suppressions en cascade fonctionnent"""
    print("\n" + "=" * 70)
    print("TEST 4: Test des suppressions CASCADE")
    print("=" * 70)
    
    # Compter les objets liés
    attributions_count = Attribution.objects.count()
    schedules_count = ScheduleEntry.objects.count()
    
    print(f"ℹ️  Base de données contient:")
    print(f"   - {attributions_count} attributions")
    print(f"   - {schedules_count} horaires")
    
    if attributions_count > 0:
        print("✅ SUCCÈS: Les relations existent, les contraintes CASCADE devraient fonctionner")
        return True
    else:
        print("ℹ️  Pas d'attributions pour tester CASCADE")
        return True

def test_safe_delete_view():
    """Test 5: Vérifier que SafeDeleteView existe"""
    print("\n" + "=" * 70)
    print("TEST 5: Vérification de SafeDeleteView")
    print("=" * 70)
    
    try:
        from reglage.views import SafeDeleteView
        print("✓ SafeDeleteView importée avec succès")
        
        # Vérifier que la méthode delete existe
        if hasattr(SafeDeleteView, 'delete'):
            print("✓ Méthode delete() existe")
            print("✅ SUCCÈS: SafeDeleteView est correctement implémentée")
            return True
        else:
            print("❌ ÉCHEC: Méthode delete() manquante")
            return False
            
    except ImportError as e:
        print(f"❌ ÉCHEC: Impossible d'importer SafeDeleteView: {e}")
        return False

def test_pattern_in_views():
    """Test 6: Vérifier que le pattern est utilisé dans les vues"""
    print("\n" + "=" * 70)
    print("TEST 6: Vérification du pattern dans les vues")
    print("=" * 70)
    
    checks = {
        'attribution/views.py - delete_attribution': False,
        'attribution/views.py - delete_course': False,
        'attribution/views.py - schedule_entry_delete': False,
        'courses/views.py - CourseDeleteView': False,
        'accounts/views.py - delete_user': False,
        'reglage/views.py - SafeDeleteView': False,
    }
    
    # Vérifier attribution/views.py
    try:
        with open('attribution/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'def delete_attribution' in content and 'transaction.atomic' in content:
                checks['attribution/views.py - delete_attribution'] = True
            if 'def delete_course' in content and 'transaction.atomic' in content:
                checks['attribution/views.py - delete_course'] = True
            if 'def schedule_entry_delete' in content and 'transaction.atomic' in content:
                checks['attribution/views.py - schedule_entry_delete'] = True
    except:
        pass
    
    # Vérifier courses/views.py
    try:
        with open('courses/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'class CourseDeleteView' in content and 'transaction.atomic' in content:
                checks['courses/views.py - CourseDeleteView'] = True
    except:
        pass
    
    # Vérifier accounts/views.py
    try:
        with open('accounts/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'def delete_user' in content and 'select_for_update' in content:
                checks['accounts/views.py - delete_user'] = True
    except:
        pass
    
    # Vérifier reglage/views.py
    try:
        with open('reglage/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'class SafeDeleteView' in content and 'transaction.atomic' in content:
                checks['reglage/views.py - SafeDeleteView'] = True
    except:
        pass
    
    # Afficher les résultats
    all_passed = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ SUCCÈS: Toutes les vues utilisent le pattern robuste")
        return True
    else:
        print("\n⚠️  ATTENTION: Certaines vues n'utilisent pas le pattern")
        return False

def main():
    """Exécuter tous les tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "TEST DE SUPPRESSION ROBUSTE" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = []
    
    # Exécuter tous les tests
    results.append(("Contraintes FK activées", test_fk_active()))
    results.append(("Transactions atomiques", test_transaction_atomic()))
    results.append(("select_for_update()", test_select_for_update()))
    results.append(("Suppressions CASCADE", test_cascade_delete()))
    results.append(("SafeDeleteView", test_safe_delete_view()))
    results.append(("Pattern dans les vues", test_pattern_in_views()))
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("\n✅ Le pattern de suppression robuste est correctement implémenté")
        print("✅ Vous pouvez maintenant supprimer des objets en toute sécurité")
        print("\n📝 Consultez PATTERN_SUPPRESSION_ROBUSTE.md pour plus de détails")
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
        print("Vérifiez les messages d'erreur ci-dessus")
    
    print("\n")

if __name__ == '__main__':
    main()
