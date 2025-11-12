from django.contrib.auth.models import User
from .models import Role
from teachers.models import Teacher

def sync_user_roles_with_teacher_function(user_profile):
    """
    Synchronise les rôles d'un utilisateur en fonction de sa fonction d'enseignant.
    Cette fonction est appelée lorsqu'un enseignant est associé à un utilisateur ou
    lorsque la fonction d'un enseignant change.
    
    Args:
        user_profile: Le profil utilisateur à mettre à jour
    """
    # Vérifier si l'utilisateur est associé à un enseignant via son matricule
    if not user_profile.matricule_enseignant:
        return
    
    try:
        teacher = Teacher.objects.get(matricule=user_profile.matricule_enseignant)
    except Teacher.DoesNotExist:
        return
    
    # Récupérer la fonction de l'enseignant
    fonction = teacher.fonction.upper() if teacher.fonction else ''
    
    # Déterminer le rôle approprié en fonction de la fonction (nouvelle nomenclature)
    if fonction in ['DG']:
        role_name = Role.ADMIN
    elif fonction in ['CS', 'CSAE', 'CSR', 'SAAS', 'CD', 'SD', 'SGAC', 'SGR', 'SGAD', 'AB']:
        role_name = Role.GESTIONNAIRE
    else:
        role_name = Role.AGENT
    
    # Ajouter le rôle approprié s'il n'existe pas déjà
    try:
        role = Role.objects.get(name=role_name)
        # Vérifier si l'utilisateur a déjà ce rôle
        if not user_profile.roles.filter(name=role_name).exists():
            # Ne garder que les rôles dans le nouveau set
            for old_role in user_profile.roles.exclude(name__in=[Role.ADMIN, Role.GESTIONNAIRE, Role.AGENT]):
                user_profile.roles.remove(old_role)
            # Ajouter le nouveau rôle
            user_profile.roles.add(role)
    except Role.DoesNotExist:
        pass
