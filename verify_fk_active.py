#!/usr/bin/env python
"""
Vérifie que les contraintes FK sont activées après l'import du signal
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Maintenant que Django est configuré, le signal a été enregistré
from django.db import connection

print("=" * 60)
print("VÉRIFICATION DES CONTRAINTES DE CLÉS ÉTRANGÈRES")
print("=" * 60)

# Créer une nouvelle connexion (qui devrait déclencher le signal)
with connection.cursor() as cursor:
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    
    print(f"\n✅ Foreign keys: {'ACTIVÉES' if fk_status else 'DÉSACTIVÉES'}")
    
    if fk_status:
        print("\n🎉 Le signal fonctionne correctement!")
        print("   Les contraintes FK sont activées automatiquement.")
        print("   La suppression des attributions devrait maintenant fonctionner.")
    else:
        print("\n⚠️  Le signal ne s'est pas exécuté correctement.")
        print("   Activons les FK manuellement pour ce test...")
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("PRAGMA foreign_keys;")
        fk_status_after = cursor.fetchone()[0]
        
        if fk_status_after:
            print(f"   ✅ Activées manuellement avec succès")
        else:
            print(f"   ❌ Échec de l'activation manuelle")

print("\n" + "=" * 60)
print("\nPROCHAINE ÉTAPE:")
print("Testez la suppression d'une attribution depuis l'interface web")
print("  → /attribution/liste-charges/")
print("=" * 60)
