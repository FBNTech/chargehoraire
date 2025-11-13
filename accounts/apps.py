from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        # Import ici pour éviter les problèmes de chargement circulaire
        from .models import Role
        from django.db import transaction
        
        # Créer les rôles par défaut si nécessaire
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
            # Cela peut se produire si la base de données n'est pas encore configurée
            pass
