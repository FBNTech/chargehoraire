from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_roles(sender, **kwargs):
    """Créer les rôles par défaut après les migrations"""
    from .models import Role
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Créer les rôles de base s'ils n'existent pas
            roles = [
                {'name': Role.ADMIN, 'description': 'Administrateur du système'},
                {'name': Role.GESTIONNAIRE, 'description': 'Gestionnaire'},
                {'name': Role.AGENT, 'description': 'Agent'},
            ]
            
            for role_data in roles:
                Role.objects.get_or_create(
                    name=role_data['name'],
                    defaults={'description': role_data['description']}
                )
    except Exception as e:
        # Gérer silencieusement les erreurs lors de la création des rôles
        pass


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        # Connecter le signal post_migrate pour créer les rôles par défaut
        post_migrate.connect(create_default_roles, sender=self)
