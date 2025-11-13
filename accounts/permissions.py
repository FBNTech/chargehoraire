from functools import wraps
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from .models import Role

# Décorateurs pour les vues basées sur des fonctions
def admin_required(view_func):
    """Décorateur pour restreindre l'accès aux administrateurs uniquement."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.profile.is_admin):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def administrative_role_required(view_func):
    """Décorateur pour restreindre l'accès aux rôles administratifs (Administrateur, Gestionnaire)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_administrative_role:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def section_role_required(view_func):
    """Décorateur historique (désactivé si aucun rôle de section)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_section_role:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def department_role_required(view_func):
    """Décorateur historique (désactivé si aucun rôle de département)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_department_role:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def enseignant_required(view_func):
    """Décorateur historique (rôle enseignant supprimé)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_enseignant:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def etudiant_required(view_func):
    """Décorateur historique (rôle étudiant supprimé)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_etudiant:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

def personnel_admin_required(view_func):
    """Décorateur historique (rôle personnel administratif supprimé)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_personnel_admin:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
    return _wrapped_view

# Mixins pour les vues basées sur des classes
class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux administrateurs uniquement."""
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.profile.is_admin)
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
        
class AdministrativeRoleMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux rôles administratifs (Administrateur, Gestionnaire)."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_administrative_role
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
        
class SectionRoleMixin(UserPassesTestMixin):
    """Mixin historique (aucun rôle de section actif)."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_section_role
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')
        
class DepartmentRoleMixin(UserPassesTestMixin):
    """Mixin historique (aucun rôle de département actif)."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_department_role
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')

class EnseignantRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux enseignants uniquement."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_enseignant
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')

class EtudiantRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux étudiants uniquement."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_etudiant
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')

class PersonnelAdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès au personnel administratif uniquement."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.is_personnel_admin
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('accounts:login')

# Fonctions utilitaires pour vérifier les permissions
def check_admin_permission(user):
    """Vérifie si l'utilisateur a des permissions d'administrateur (Administrateur uniquement, pas Gestionnaire)."""
    if not user.is_authenticated:
        return False
        
    # Staff ou rôle admin traditionnel
    if user.is_staff or user.profile.is_admin:
        return True
        
    # Seul le rôle ADMIN a tous les privilèges (pas le gestionnaire)
    if user.profile.roles.filter(name=Role.ADMIN).exists():
        return True
        
    return False

def check_administrative_role_permission(user):
    """Vérifie si l'utilisateur a un rôle administratif (Administrateur, Gestionnaire)."""
    return user.is_authenticated and user.profile.is_administrative_role

def check_section_role_permission(user):
    """Historique: pas de rôle de section actif."""
    return user.is_authenticated and user.profile.is_section_role

def check_department_role_permission(user):
    """Historique: pas de rôle de département actif."""
    return user.is_authenticated and user.profile.is_department_role

def check_enseignant_permission(user):
    """Historique: rôle enseignant supprimé."""
    return user.is_authenticated and user.profile.is_enseignant

def check_etudiant_permission(user):
    """Historique: rôle étudiant supprimé."""
    return user.is_authenticated and user.profile.is_etudiant

def check_personnel_admin_permission(user):
    """Historique: rôle personnel administratif supprimé."""
    return user.is_authenticated and user.profile.is_personnel_admin

# Fonctions spécifiques pour les contrôles d'accès basés sur les fonctions
def has_finance_access(user):
    """Vérifie si l'utilisateur a accès aux fonctionnalités financières (Administrateur, Gestionnaire)."""
    if not user.is_authenticated:
        return False
    
    # Staff traditionnel
    if user.is_staff:
        return True
    
    # Administrateur et Gestionnaire ont accès
    if user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists():
        return True
        
    return False

def has_user_creation_access(user):
    """Vérifie si l'utilisateur peut créer d'autres utilisateurs (Administrateur, Gestionnaire)."""
    if not user.is_authenticated:
        return False
    
    # Staff traditionnel
    if user.is_staff:
        return True
    
    # Les rôles administratifs spécifiques ont aussi accès
    if user.profile.roles.filter(name__in=Role.ADMIN_ROLES).exists():
        return True
        
    return False

def has_reglage_access(user):
    """Vérifie si l'utilisateur a accès aux réglages système (Administrateur, Gestionnaire)."""
    if not user.is_authenticated:
        return False
    
    # Staff ou rôle admin traditionnel
    if user.is_staff or user.profile.is_admin:
        return True
    
    # Gestionnaire a aussi accès aux réglages
    if user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists():
        return True
        
    return False

def has_view_all_access(user):
    """Vérifie si l'utilisateur peut tout voir (sauf restrictions spécifiques)."""
    return user.is_authenticated and (user.is_staff or user.profile.is_admin or user.profile.is_administrative_role)

def can_view_department_data(user, department):
    """Vérifie si l'utilisateur peut voir les données d'un département spécifique."""
    if not user.is_authenticated:
        return False
        
    # Administrateurs et rôles administratifs peuvent tout voir
    if user.is_staff or user.profile.is_admin or user.profile.is_administrative_role:
        return True
        
    # Rôles historiques supprimés: on retire ces branches
        
    return False

def can_view_section_data(user, section):
    """Vérifie si l'utilisateur peut voir les données d'une section spécifique."""
    if not user.is_authenticated:
        return False
        
    # Administrateurs et rôles administratifs peuvent voir toutes les sections
    if user.is_staff or user.profile.is_admin or user.profile.is_administrative_role:
        return True
        
    # Rôles historiques supprimés: pas d'accès basé sur section
    
    # Les autres rôles ne peuvent pas accéder aux données de section directement
    return False

def check_department_belongs_to_section(department, section):
    """Vérifie si un département appartient à une section spécifique.
    Cette fonction devrait être adaptée pour utiliser votre modèle de données réel.
    """
    # Dans une implémentation réelle, vous feriez une requête à la base de données
    # pour vérifier la relation entre département et section.
    # Pour cet exemple, nous retournons simplement True.
    return True

def can_edit_courses_teachers(user):
    """Vérifie si l'utilisateur peut modifier des cours ou des enseignants (Administrateur, Gestionnaire)."""
    if not user.is_authenticated:
        return False
    
    return (user.is_staff or 
            user.profile.is_admin or 
            user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())

def can_delete_all(user):
    """Vérifie si l'utilisateur peut utiliser le bouton 'Supprimer tout' (Administrateur uniquement)."""
    if not user.is_authenticated:
        return False
    
    # Seul l'administrateur peut supprimer tout
    return user.is_staff or user.profile.roles.filter(name=Role.ADMIN).exists()
