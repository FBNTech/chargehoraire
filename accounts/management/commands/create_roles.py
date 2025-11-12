from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = 'Crée les rôles de base nécessaires au fonctionnement de l\'application'

    def handle(self, *args, **kwargs):
        # Définition des rôles
        roles = [
            (Role.ADMIN, 'Administrateur avec accès complet à toutes les fonctionnalités'),
            (Role.GESTIONNAIRE, 'Gestionnaire - Accès administratif étendu'),
            (Role.AGENT, 'Agent - Accès opérationnel de base'),
        ]
        
        # Création des rôles
        roles_created = 0
        roles_updated = 0
        
        for name, description in roles:
            role, created = Role.objects.update_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                roles_created += 1
                self.stdout.write(self.style.SUCCESS(f'Rôle créé: {name}'))
            else:
                roles_updated += 1
                self.stdout.write(self.style.WARNING(f'Rôle mis à jour: {name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Terminé! {roles_created} rôles créés, {roles_updated} rôles mis à jour.'
        ))
