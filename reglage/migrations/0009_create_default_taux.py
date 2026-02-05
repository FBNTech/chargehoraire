from django.db import migrations

def create_default_taux(apps, schema_editor):
    """Créer les taux horaires par défaut"""
    Taux = apps.get_model('reglage', 'Taux')
    
    default_taux = [
        ('ASSISTANT', 25.00),
        ('MAITRE ASSISTANT', 35.00),
        ('MAITRE DE CONFERENCES', 45.00),
        ('PROFESSEUR', 60.00),
    ]
    
    for grade, montant in default_taux:
        Taux.objects.get_or_create(
            grade=grade,
            defaults={'montant_par_heure': montant}
        )

def reverse_create_default_taux(apps, schema_editor):
    """Supprimer les taux par défaut"""
    Taux = apps.get_model('reglage', 'Taux')
    
    default_grades = ['ASSISTANT', 'MAITRE ASSISTANT', 'MAITRE DE CONFERENCES', 'PROFESSEUR']
    Taux.objects.filter(grade__in=default_grades).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('reglage', '0008_taux'),
    ]

    operations = [
        migrations.RunPython(
            create_default_taux,
            reverse_create_default_taux
        ),
    ]
