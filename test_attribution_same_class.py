import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attribution.models import Cours_Attribution, Course, Attribution
from teachers.models import Teacher

# Données de test : 3 cours BIO308 - L3 BC avec CMI/TD_TP différents
selected_cours = [
    {"id": "39", "code_ue": "BIO308"},  # CMI=10, TD_TP=5
    {"id": "40", "code_ue": "BIO308"},  # CMI=5, TD_TP=10 (différent)
    {"id": "41", "code_ue": "BIO308"},  # CMI=10, TD_TP=5 (même que 39)
]

# Récupérer un enseignant
teacher = Teacher.objects.first()
matricule = teacher.matricule
annee = "2025-2026"
type_charge = "reguliere"

print("=" * 70)
print("TEST : MÊME CODE_UE + MÊME CLASSE AVEC CMI/TD_TP DIFFÉRENTS")
print("=" * 70)
print(f"Enseignant: {teacher.nom_complet}")
print(f"Nombre de cours à attribuer: {len(selected_cours)}")
print("-" * 70)

attributions_created = []
codes_ue_to_delete = []

print(f"\n🔄 TRAITEMENT DES COURS...\n")

for cours in selected_cours:
    try:
        # Récupérer depuis Cours_Attribution
        cours_attr = Cours_Attribution.objects.get(id=cours['id'])
        
        print(f"📌 Cours ID {cours['id']}: {cours_attr.code_ue} - {cours_attr.classe}")
        print(f"   Volume: CMI={cours_attr.cmi}, TD_TP={cours_attr.td_tp}")
        
        # Créer/récupérer dans Course AVEC CMI et TD_TP dans la clé
        course, created = Course.objects.get_or_create(
            code_ue=cours_attr.code_ue,
            intitule_ue=cours_attr.intitule_ue,
            classe=cours_attr.classe,
            semestre=cours_attr.semestre,
            cmi=cours_attr.cmi,
            td_tp=cours_attr.td_tp,
            defaults={
                'intitule_ec': cours_attr.intitule_ec,
                'credit': cours_attr.credit,
                'departement': cours_attr.departement,
                'section': cours_attr.section,
            }
        )
        
        if created:
            print(f"   ✅ NOUVEAU cours créé dans Course (ID: {course.id})")
        else:
            print(f"   ♻️  Cours EXISTANT récupéré (ID: {course.id})")
        
        # Vérifier si attribution existe
        existing = Attribution.objects.filter(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee
        ).first()
        
        if existing:
            print(f"   ⚠️  Attribution déjà existante (ignorée)")
            continue
        
        # Créer attribution
        attribution = Attribution.objects.create(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee,
            type_charge=type_charge
        )
        attributions_created.append(attribution)
        print(f"   ✅ Attribution créée (ID: {attribution.id})")
        print()
        
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}\n")

print("=" * 70)
print(f"📊 RÉSULTAT : {len(attributions_created)} attribution(s) créée(s)")
print("=" * 70)

if attributions_created:
    print("\n✅ COURS ATTRIBUÉS:")
    for attr in attributions_created:
        print(f"   - {attr.code_ue.code_ue} - {attr.code_ue.classe} (CMI={attr.code_ue.cmi}, TD_TP={attr.code_ue.td_tp})")

# Vérifier les cours créés dans Course
print("\n🔍 VÉRIFICATION dans Course:")
bio308_courses = Course.objects.filter(code_ue='BIO308', classe='L3 BC')
print(f"   Nombre de cours BIO308 - L3 BC dans Course: {bio308_courses.count()}")
for c in bio308_courses:
    print(f"   - ID {c.id}: CMI={c.cmi}, TD_TP={c.td_tp}")

# Rollback
print("\n🔄 ANNULATION (rollback)...")
for attr in attributions_created:
    attr.delete()
print("✅ Modifications annulées")
