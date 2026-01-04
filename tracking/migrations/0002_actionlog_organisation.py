# Generated migration for ActionLog organisation field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('tracking', '0001_initial'),
    ]

    operations = [
        # Add organisation field to ActionLog
        migrations.AddField(
            model_name='actionlog',
            name='organisation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='action_logs',
                to='accounts.organisation',
                verbose_name='Organisation'
            ),
        ),
        
        # Update action_type field length to accommodate new action types
        migrations.AlterField(
            model_name='actionlog',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('create', 'Création'),
                    ('update', 'Modification'),
                    ('delete', 'Suppression'),
                    ('view', 'Consultation'),
                    ('login', 'Connexion'),
                    ('logout', 'Déconnexion'),
                    ('export', 'Exportation'),
                    ('import', 'Importation'),
                    ('print', 'Impression'),
                    ('dashboard_view', 'Vue tableau de bord'),
                    ('progress_create', 'Création suivi'),
                    ('progress_update', 'Modification suivi'),
                    ('progress_delete', 'Suppression suivi'),
                    ('schedule_create', 'Création planning'),
                    ('schedule_update', 'Modification planning'),
                    ('schedule_delete', 'Suppression planning'),
                    ('attribution_create', 'Création attribution'),
                    ('attribution_update', 'Modification attribution'),
                    ('attribution_delete', 'Suppression attribution'),
                    ('other', 'Autre'),
                ],
                max_length=30,
                verbose_name='Type d\'action'
            ),
        ),
        
        # Add new indexes for better performance
        migrations.AddIndex(
            model_name='actionlog',
            index=models.Index(fields=['organisation'], name='tracking_act_org_idx'),
        ),
        
        migrations.AddIndex(
            model_name='actionlog',
            index=models.Index(fields=['-timestamp', 'organisation'], name='tracking_act_time_org_idx'),
        ),
    ]
