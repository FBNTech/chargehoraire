from .models import ActionLog


class ActionLoggingMixin:
    """
    Mixin à ajouter aux vues pour enregistrer automatiquement les actions
    """
    
    def log_action(self, action_type, description, model_name=None, object_id=None, object_repr=None):
        """Enregistrer une action avec l'utilisateur courant"""
        ActionLog.log_action(
            user=self.request.user if hasattr(self, 'request') else None,
            action_type=action_type,
            description=description,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            request=getattr(self, 'request', None)
        )
    
    def log_create_action(self, obj, description=None):
        """Enregistrer une action de création"""
        if description is None:
            description = f"Création de {obj.__class__.__name__}: {str(obj)}"
        
        self.log_action(
            action_type='create',
            description=description,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj)
        )
    
    def log_update_action(self, obj, description=None):
        """Enregistrer une action de modification"""
        if description is None:
            description = f"Modification de {obj.__class__.__name__}: {str(obj)}"
        
        self.log_action(
            action_type='update',
            description=description,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj)
        )
    
    def log_delete_action(self, obj, description=None):
        """Enregistrer une action de suppression"""
        if description is None:
            description = f"Suppression de {obj.__class__.__name__}: {str(obj)}"
        
        self.log_action(
            action_type='delete',
            description=description,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj)
        )
    
    def log_view_action(self, model_name, description=None):
        """Enregistrer une action de consultation"""
        if description is None:
            description = f"Consultation de {model_name}"
        
        self.log_action(
            action_type='view',
            description=description,
            model_name=model_name
        )
    
    def log_export_action(self, description=None):
        """Enregistrer une action d'export"""
        if description is None:
            description = "Export de données"
        
        self.log_action(
            action_type='export',
            description=description
        )
    
    def log_print_action(self, description=None):
        """Enregistrer une action d'impression"""
        if description is None:
            description = "Impression de données"
        
        self.log_action(
            action_type='print',
            description=description
        )
