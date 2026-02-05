# Generated migration for creating default creneaux AM and PM

from django.db import migrations

def create_default_creneaux(apps, schema_editor):
    """Create default AM and PM creneaux"""
    Creneau = apps.get_model('reglage', 'Creneau')
    Section = apps.get_model('reglage', 'Section')
    
    # Créer les créneaux par défaut
    default_creneaux = [
        {
            'code': 'AM',
            'designation': 'Matinée',
            'type_creneau': 'les_deux',
            'heure_debut': '08:00',
            'heure_fin': '12:00',
            'ordre': 1
        },
        {
            'code': 'PM',
            'designation': 'Après-midi',
            'type_creneau': 'les_deux',
            'heure_debut': '14:00',
            'heure_fin': '18:00',
            'ordre': 2
        }
    ]
    
    for creneau_data in default_creneaux:
        creneau, created = Creneau.objects.get_or_create(
            code=creneau_data['code'],
            defaults=creneau_data
        )
        if created:
            print(f"Créneau {creneau_data['code']} créé avec succès")

def delete_default_creneaux(apps, schema_editor):
    """Delete default AM and PM creneaux"""
    Creneau = apps.get_model('reglage', 'Creneau')
    
    codes_to_delete = ['AM', 'PM']
    Creneau.objects.filter(code__in=codes_to_delete).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('reglage', '0010_update_taux_currency'),
    ]

    operations = [
        migrations.RunPython(create_default_creneaux, delete_default_creneaux),
    ]
