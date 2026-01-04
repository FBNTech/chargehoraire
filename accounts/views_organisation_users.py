"""
Vues pour la gestion des utilisateurs par organisation
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from .models import Organisation, UserProfile, Role
from .forms import UserRegistrationForm, UserProfileForm
from .permissions import check_admin_permission

@login_required
@transaction.atomic
def organisation_user_create(request, org_id):
    """Créer un utilisateur pour une organisation spécifique"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisation = get_object_or_404(Organisation, pk=org_id)
    
    # Récupérer les enseignants dont la section correspond au code de l'organisation
    from teachers.models import Teacher
    from django.db.models import Q
    
    # Filtrer les enseignants par le code de l'organisation qui correspond à leur section
    teachers = Teacher.objects.filter(section=organisation.code).order_by('section', 'nom_complet')
    
    # Grouper les enseignants par section
    teachers_by_section = {}
    for teacher in teachers:
        section = teacher.section or 'Sans section'
        if section not in teachers_by_section:
            teachers_by_section[section] = []
        teachers_by_section[section].append(teacher)
    
    # Récupérer les sections disponibles
    sections = list(teachers_by_section.keys())
    
    if request.method == 'POST':
        # Vérifier si un enseignant a été sélectionné
        teacher_id = request.POST.get('teacher_id')
        
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        # Récupérer le rôle sélectionné
        role_id = request.POST.get('role')
        
        # Debug: afficher les erreurs de formulaire
        if not user_form.is_valid():
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur {field}: {error}")
        
        if not profile_form.is_valid():
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur profil {field}: {error}")
        
        if user_form.is_valid():
            # Créer l'utilisateur
            user = user_form.save()
            
            # Mettre à jour le profil (créé automatiquement par le signal)
            profile = user.profile
            profile.organisation = organisation  # Assigner l'organisation
            
            # Récupérer les données du profil depuis le POST (les noms peuvent être préfixés)
            phone_number = request.POST.get('phone_number') or request.POST.get('profile-phone_number', '')
            address = request.POST.get('address') or request.POST.get('profile-address', '')
            section = request.POST.get('section') or request.POST.get('profile-section', '')
            
            profile.phone_number = phone_number
            profile.address = address
            profile.section = section
            
            # Gérer la photo de profil
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            elif 'profile-profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile-profile_picture']
            
            # Assigner le rôle
            if role_id:
                try:
                    role = Role.objects.get(id=role_id)
                    profile.roles.set([role])
                except Role.DoesNotExist:
                    pass
            
            profile.save()
            
            messages.success(request, f"L'utilisateur '{user.username}' a été créé avec succès pour l'organisation '{organisation.nom}'.")
            return redirect('accounts:organisation_detail', pk=org_id)
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm(initial={'organisation': organisation})
    
    # Récupérer tous les rôles disponibles
    roles = Role.objects.all()
    
    context = {
        'organisation': organisation,
        'user_form': user_form,
        'profile_form': profile_form,
        'roles': roles,
        'teachers': teachers,
        'teachers_by_section': teachers_by_section,
        'sections': sections,
    }
    return render(request, 'accounts/organisation_user_create.html', context)

@login_required
def organisation_users_list(request, org_id):
    """Liste des utilisateurs d'une organisation"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisation = get_object_or_404(Organisation, pk=org_id)
    users = organisation.users.select_related('user').all()
    
    context = {
        'organisation': organisation,
        'users': users,
    }
    return render(request, 'accounts/organisation_users_list.html', context)
