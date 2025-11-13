from .models import Role
from .permissions import (
    check_admin_permission, check_administrative_role_permission,
    check_section_role_permission, check_department_role_permission,
    can_view_department_data, can_view_section_data, has_reglage_access, has_finance_access, 
    has_user_creation_access, can_edit_courses_teachers, can_delete_all
)

def user_roles(request):
    """Ajoute les rôles de l'utilisateur au contexte de tous les templates."""
    if request.user.is_authenticated:
        return {
            # Rôles généraux
            'is_admin': check_admin_permission(request.user),
            'is_administrative_role': check_administrative_role_permission(request.user),
            'is_gestionnaire': request.user.profile.roles.filter(name='gestionnaire').exists(),
            'is_section_role': check_section_role_permission(request.user),
            'is_department_role': check_department_role_permission(request.user),
            'is_enseignant': request.user.profile.is_enseignant,
            'is_etudiant': request.user.profile.is_etudiant,
            'is_personnel_admin': request.user.profile.is_personnel_admin,
            
            # Permissions fonctionnelles
            'can_access_reglage': has_reglage_access(request.user),
            'can_access_finance': has_finance_access(request.user),
            'can_create_users': has_user_creation_access(request.user),
            'can_edit_courses_teachers': can_edit_courses_teachers(request.user),
            'can_delete_all': can_delete_all(request.user),
            
            # Fonctions utiles pour les templates
            'can_view_department_data': lambda dept: can_view_department_data(request.user, dept),
            'can_view_section_data': lambda section: can_view_section_data(request.user, section),
            
            # Tous les rôles de l'utilisateur
            'user_roles': request.user.profile.roles.all(),
            
            # Informations supplémentaires sur l'utilisateur
            'user_department': request.user.profile.departement,
        }
    return {
        # Rôles généraux
        'is_admin': False,
        'is_administrative_role': False,
        'is_gestionnaire': False,
        'is_section_role': False,
        'is_department_role': False,
        'is_enseignant': False,
        'is_etudiant': False,
        'is_personnel_admin': False,
        
        # Permissions fonctionnelles
        'can_access_reglage': False,
        'can_access_finance': False,
        'can_create_users': False,
        'can_delete_all': False,
        
        # Fonctions utiles pour les templates
        'can_view_department_data': lambda dept: False,
        'can_view_section_data': lambda section: False,
        
        # Tous les rôles de l'utilisateur
        'user_roles': [],
        
        # Informations supplémentaires sur l'utilisateur
        'user_department': None,
    }
