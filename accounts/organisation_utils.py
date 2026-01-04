"""
Utilitaires pour gérer l'isolation des données par organisation
"""
from .models import Organisation

def get_user_organisation(user):
    """
    Récupère l'organisation de l'utilisateur connecté
    Retourne None si l'utilisateur n'a pas d'organisation ou si c'est un superuser
    """
    if not user.is_authenticated:
        return None
    
    # Les superusers voient toutes les données
    if user.is_superuser:
        return None
    
    if hasattr(user, 'profile') and user.profile.organisation:
        return user.profile.organisation
    
    return None

def is_org_user(user):
    """
    Vérifie si l'utilisateur est un utilisateur d'organisation (pas admin global)
    """
    return get_user_organisation(user) is not None

def get_organisation_filter(user):
    """
    Retourne un dictionnaire de filtre pour l'organisation de l'utilisateur
    Retourne un dict vide si l'utilisateur n'a pas d'organisation
    """
    organisation = get_user_organisation(user)
    if organisation:
        return {'organisation': organisation}
    return {}

def get_section_filter(user):
    """
    Retourne un dictionnaire de filtre par section (code de l'organisation)
    Pour les modèles qui utilisent 'section' au lieu de 'organisation'
    """
    organisation = get_user_organisation(user)
    if organisation:
        return {'section': organisation.code}
    return {}

def filter_queryset_by_organisation(queryset, user, field_name='organisation'):
    """
    Filtre un queryset par l'organisation de l'utilisateur
    Si l'utilisateur n'a pas d'organisation, retourne le queryset inchangé
    
    Args:
        queryset: Le queryset à filtrer
        user: L'utilisateur connecté
        field_name: Le nom du champ à utiliser pour le filtrage (par défaut 'organisation')
                   Peut être 'organisation', 'section', ou un chemin comme 'course__section'
    """
    organisation = get_user_organisation(user)
    if organisation:
        if field_name == 'organisation':
            return queryset.filter(organisation=organisation)
        elif field_name == 'section':
            return queryset.filter(section=organisation.code)
        else:
            # Pour les chemins personnalisés comme 'course__section'
            return queryset.filter(**{field_name: organisation.code})
    return queryset
