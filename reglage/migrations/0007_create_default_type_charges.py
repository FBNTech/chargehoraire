from django.db import migrations

def create_default_type_charges(apps, schema_editor):
    """Créer les types de charge par défaut"""
    TypeCharge = apps.get_model('reglage', 'TypeCharge')
    
    default_types = [
        ('REG', 'Régulière'),
        ('SUP', 'Supplémentaire'),
        ('VAC', 'Vacante'),
        ('REM', 'Remplacement'),
        ('COMP', 'Complémentaire'),
    ]
    
    for code, designation in default_types:
        TypeCharge.objects.get_or_create(
            code_type_charge=code,
            defaults={'designation_type_charge': designation}
        )

def reverse_create_default_type_charges(apps, schema_editor):
    """Supprimer les types de charge par défaut"""
    TypeCharge = apps.get_model('reglage', 'TypeCharge')
    
    default_codes = ['REG', 'SUP', 'VAC', 'REM', 'COMP']
    TypeCharge.objects.filter(code_type_charge__in=default_codes).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('reglage', '0006_typecharge'),
    ]

    operations = [
        migrations.RunPython(
            create_default_type_charges,
            reverse_create_default_type_charges
        ),
    ]
