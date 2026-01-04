"""
Mixins pour associer automatiquement l'organisation aux objets créés
"""
from django.core.exceptions import ValidationError
from .organisation_utils import get_user_organisation

class OrganisationFormMixin:
    """
    Mixin pour les formulaires qui doivent associer automatiquement l'organisation
    """
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        
        # Associer l'organisation de l'utilisateur si elle n'est pas déjà définie
        if user and not instance.organisation:
            organisation = get_user_organisation(user)
            if organisation:
                instance.organisation = organisation
        
        if commit:
            instance.save()
            # Sauvegarder les relations many-to-many si nécessaire
            if hasattr(self, 'save_m2m'):
                self.save_m2m()
        
        return instance

class OrganisationViewMixin:
    """
    Mixin pour les vues qui doivent associer automatiquement l'organisation
    """
    def form_valid(self, form):
        # Associer l'organisation avant de sauvegarder
        if hasattr(form, 'save'):
            form.instance.organisation = get_user_organisation(self.request.user)
        return super().form_valid(form)
    
    def get_queryset(self):
        """Filtrer automatiquement par organisation"""
        from .organisation_utils import filter_queryset_by_organisation
        queryset = super().get_queryset()
        return filter_queryset_by_organisation(queryset, self.request.user)
