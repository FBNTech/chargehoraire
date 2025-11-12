from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import login
from django.db import transaction

from .models import UserProfile, Role
from .forms import (
    UserRegistrationForm, UserProfileForm, StudentProfileForm, 
    TeacherProfileForm, UserRoleForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm, TeacherUserCreationForm
)

class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class CustomPasswordChangeView(PasswordChangeView):
    """Vue de changement de mot de passe personnalisée"""
    template_name = 'accounts/password_change.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:password_change_done')

class CustomPasswordResetView(PasswordResetView):
    """Vue de réinitialisation de mot de passe personnalisée"""
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Vue de confirmation de réinitialisation de mot de passe personnalisée"""
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')

class RegisterView(CreateView):
    """Vue d'inscription des utilisateurs"""
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Votre compte a été créé avec succès !")
        return redirect(self.success_url)

@method_decorator(login_required, name='dispatch')
class ProfileView(DetailView):
    """Vue du profil utilisateur"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user

@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    """Vue de mise à jour du profil utilisateur"""
    model = UserProfile
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user.profile
    
    def get_form_class(self):
        # Choisir le formulaire approprié en fonction des rôles de l'utilisateur
        if self.request.user.profile.is_etudiant:
            return StudentProfileForm
        elif self.request.user.profile.is_enseignant:
            return TeacherProfileForm
        return UserProfileForm
    
    def form_valid(self, form):
        messages.success(self.request, "Votre profil a été mis à jour avec succès !")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class UserListView(UserPassesTestMixin, ListView):
    """Vue de la liste des utilisateurs (admin seulement)"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.profile.is_admin

@method_decorator(login_required, name='dispatch')
class UserDetailView(UserPassesTestMixin, DetailView):
    """Vue des détails d'un utilisateur (admin seulement)"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'profile_user'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.profile.is_admin

from .utils import sync_user_roles_with_teacher_function
from teachers.models import Teacher

@login_required
def update_user_roles(request, pk):
    """Vue pour mettre à jour les rôles d'un utilisateur"""
    # Vérifier que l'utilisateur actuel est admin ou staff
    if not (request.user.is_staff or request.user.profile.is_admin):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('accounts:profile')
    
    user = get_object_or_404(User, pk=pk)
    
    # Récupérer l'enseignant associé s'il existe
    teacher = None
    if user.profile.matricule_enseignant:
        try:
            teacher = Teacher.objects.get(matricule=user.profile.matricule_enseignant)
        except Teacher.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user.profile)
        if form.is_valid():
            # Sauvegarder les rôles
            profile = form.save(commit=False)
            
            # Option pour synchroniser les rôles avec la fonction de l'enseignant
            sync_with_function = request.POST.get('sync_with_function') == 'on'
            
            if sync_with_function and teacher:
                # Appliquer les rôles en fonction de la fonction de l'enseignant
                sync_user_roles_with_teacher_function(profile)
                messages.success(
                    request, 
                    f"Les rôles de {user.username} ont été synchronisés avec sa fonction d'enseignant ({teacher.fonction})."
                )
            else:
                # Sauvegarder le rôle sélectionné manuellement (unique)
                selected_role = form.cleaned_data['roles']
                profile.save()
                profile.roles.set([selected_role])
                messages.success(request, f"Le rôle de {user.username} a été mis à jour avec succès !")
                
            return redirect('accounts:user_detail', pk=pk)
    else:
        form = UserRoleForm(instance=user.profile)
    
    return render(request, 'accounts/user_roles.html', {
        'form': form,
        'profile_user': user,
        'teacher': teacher
    })

@login_required
def activate_deactivate_user(request, pk):
    """Vue pour activer/désactiver un utilisateur"""
    # Vérifier que l'utilisateur actuel est admin ou staff
    if not (request.user.is_staff or request.user.profile.is_admin):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('accounts:profile')
    
    user = get_object_or_404(User, pk=pk)
    
    # Ne pas permettre de désactiver son propre compte
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('accounts:user_detail', pk=pk)
    
    user.is_active = not user.is_active
    user.save()
    
    action = "activé" if user.is_active else "désactivé"
    messages.success(request, f"Le compte de {user.username} a été {action} avec succès !")
    
    return redirect('accounts:user_detail', pk=pk)

@login_required
@transaction.atomic
def create_user(request):
    """Vue pour créer un nouvel utilisateur (admin seulement)"""
    # Vérifier que l'utilisateur actuel est admin ou staff
    if not (request.user.is_staff or request.user.profile.is_admin):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        role_form = UserRoleForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid() and role_form.is_valid():
            user = user_form.save()
            
            # Mettre à jour le profil
            profile = user.profile
            for field, value in profile_form.cleaned_data.items():
                setattr(profile, field, value)
            
            # Assigner un seul rôle depuis le formulaire radio
            selected_role = role_form.cleaned_data['roles']
            profile.roles.set([selected_role])
            profile.save()
            
            messages.success(request, f"Le compte pour {user.username} a été créé avec succès !")
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
        role_form = UserRoleForm()
    
    return render(request, 'accounts/user_create.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'role_form': role_form
    })

@login_required
@transaction.atomic
def create_teacher_user(request):
    """Vue pour créer un nouvel utilisateur à partir d'un enseignant existant"""
    # Vérifier que l'utilisateur actuel est admin ou staff
    if not (request.user.is_staff or request.user.profile.is_admin):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = TeacherUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            teacher = form.cleaned_data['teacher']
            
            # Synchroniser automatiquement les rôles avec la fonction de l'enseignant
            from .utils import sync_user_roles_with_teacher_function
            sync_user_roles_with_teacher_function(user.profile)
            
            messages.success(
                request, 
                f"Le compte utilisateur pour l'enseignant {teacher.nom_complet} ({user.username}) a été créé avec succès ! "
                f"Les privilèges ont été assignés en fonction de sa fonction : {teacher.fonction}."
            )
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = TeacherUserCreationForm()
    
    return render(request, 'accounts/teacher_user_create.html', {
        'form': form,
        'title': 'Créer un utilisateur depuis un enseignant'
    })

@login_required
@transaction.atomic
def delete_user(request, pk):
    """Vue pour supprimer un utilisateur"""
    # Vérifier que l'utilisateur actuel est admin ou staff
    if not (request.user.is_staff or request.user.profile.is_admin):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('accounts:profile')
    
    # Verrouiller l'utilisateur pour éviter les conflits concurrents
    user = get_object_or_404(User.objects.select_for_update(), pk=pk)
    
    # Ne pas permettre de supprimer son propre compte
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('accounts:user_detail', pk=pk)
    
    username = user.username
    # Les contraintes FK CASCADE supprimeront automatiquement le profil lié
    user.delete()
    
    messages.success(request, f"L'utilisateur {username} a été supprimé avec succès !")
    return redirect('accounts:user_list')
