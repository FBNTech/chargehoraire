from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from django.conf import settings
from .permissions import (
    check_admin_permission, check_administrative_role_permission,
    check_section_role_permission, check_department_role_permission,
    check_enseignant_permission, check_etudiant_permission
)

class RoleBasedAccessMiddleware:
    """
    Middleware pour gérer les restrictions d'accès basées sur les rôles des utilisateurs.
    Applique les règles suivantes:
    
    - DG, SGAC, SGR, SGAD, AB: Accès complet à toutes les fonctionnalités (comme les administrateurs)
    - CS, CSAE, CSR, SAAS: Accès limité à leur section et départements d'attache
    - CD, SD: Accès limité à leur département
    - Enseignant: Accès très limité (profil, liste enseignants, liste UE)
    - Étudiant: Accès uniquement à la liste des UE de leur département
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs pour les différents niveaux d'accès
        self.admin_only_urls = [
            '/admin/',
            '/reglage/',
            '/finance/',
            '/accounts/register/',
            '/accounts/user/add/'
        ]
        
        self.admin_and_direction_urls = [
            '/gestion/',
            '/tracking/dashboard/',
            '/teachers/import/',
            '/courses/import/',
        ]
        
        self.restricted_for_basic_enseignant = [
            '/attribution/',
            '/charge/',
            '/tracking/',
            '/reglage/',
            '/gestion/',
        ]
        
        self.restricted_for_etudiant = [
            '/teachers/',
            '/attribution/',
            '/charge/',
            '/tracking/',
            '/reglage/',
            '/gestion/',
            '/accounts/profile/',  # L'étudiant ne peut pas modifier son profil
        ]
        
        # URLs publiques, toujours accessibles
        self.public_urls = [
            reverse('accounts:login'), 
            reverse('accounts:logout'),
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        current_url = request.path_info
        
        # Vérifier si l'URL est publique
        for url in self.public_urls:
            if current_url.startswith(url):
                return self.get_response(request)
        
        # URLs réservées aux administrateurs et aux rôles administratifs spécifiés (DG, SGAC, SGR, SGAD, AB)
        if any(current_url.startswith(url) for url in self.admin_only_urls):
            # Vérifier si l'utilisateur a des droits d'administration
            # La fonction check_admin_permission inclut déjà la vérification des rôles DG, SGAC, SGR, SGAD, AB
            if not check_admin_permission(request.user):
                messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette fonctionnalité.")
                return redirect('dashboard')
        
        # URLs réservées aux administrateurs et à la direction
        # Note: Cette condition reste pour la forme, mais avec nos modifications à check_admin_permission,
        # les rôles DG, SGAC, SGR, SGAD, AB passent déjà la première vérification
        if any(current_url.startswith(url) for url in self.admin_and_direction_urls):
            if not (check_admin_permission(request.user) or check_administrative_role_permission(request.user)):
                messages.error(request, "Cette fonctionnalité est réservée à l'administration.")
                return redirect('dashboard')
        
        # Restrictions pour les enseignants de base
        if check_enseignant_permission(request.user) and not (check_section_role_permission(request.user) or check_department_role_permission(request.user)):
            if any(current_url.startswith(url) for url in self.restricted_for_basic_enseignant):
                messages.warning(request, "En tant qu'enseignant, votre accès est limité à certaines fonctionnalités.")
                return redirect('dashboard')
            
            # Empêcher les actions d'ajout, modification et suppression pour les cours (UEs)
            if current_url.startswith('/courses/'):
                # Permettre uniquement la vue liste et détail
                if any(action in current_url for action in ['/add/', '/edit/', '/delete/', '/create/', '/update/']):
                    messages.warning(request, "En tant qu'enseignant, vous pouvez consulter les cours mais pas les modifier.")
                    return redirect('courses:list')
            
            # Empêcher les actions d'ajout, modification et suppression pour les enseignants
            if current_url.startswith('/teachers/'):
                # Permettre uniquement la vue liste et détail
                if any(action in current_url for action in ['/add/', '/edit/', '/delete/', '/create/', '/update/']):
                    messages.warning(request, "En tant qu'enseignant, vous pouvez consulter la liste des enseignants mais pas la modifier.")
                    return redirect('teachers:list')
        
        # Restrictions pour les étudiants
        if check_etudiant_permission(request.user):
            if any(current_url.startswith(url) for url in self.restricted_for_etudiant):
                messages.warning(request, "En tant qu'étudiant, votre accès est limité à certaines fonctionnalités.")
                return redirect('dashboard')
        
        # Si l'utilisateur a un rôle de département, vérifier qu'il accède uniquement aux données de son département
        if check_department_role_permission(request.user):
            # Logique pour vérifier que l'utilisateur n'accède qu'aux données de son département
            # À compléter selon la structure de l'application
            pass
        
        # Si l'utilisateur a un rôle de section, vérifier qu'il accède uniquement aux données de sa section
        if check_section_role_permission(request.user) and not check_admin_permission(request.user):
            # Récupérer la section de l'utilisateur
            user_section = request.user.profile.section
            
            # Si l'utilisateur essaie d'accéder à des données de section
            if 'section' in request.GET:
                section_code = request.GET.get('section')
                if section_code and user_section and section_code.lower() != user_section.lower():
                    messages.warning(request, f"En tant que responsable de section, vous ne pouvez accéder qu'aux données de votre section: {user_section}")
                    return redirect('dashboard')
            
            # Pour les URL qui contiennent un identifiant de section
            if '/section/' in current_url:
                try:
                    # Essayer d'extraire l'identifiant de la section de l'URL
                    # Par exemple /sections/CS001/details/ -> CS001
                    parts = current_url.split('/')
                    for i, part in enumerate(parts):
                        if part == 'section' and i + 1 < len(parts):
                            section_code = parts[i + 1]
                            if section_code and user_section and section_code.lower() != user_section.lower():
                                messages.warning(request, f"En tant que responsable de section, vous ne pouvez accéder qu'aux données de votre section: {user_section}")
                                return redirect('dashboard')
                except Exception as e:
                    # En cas d'erreur lors de l'analyse de l'URL, laissez passer et laissez la vue gérer
                    pass
                    
            # Pour certaines URL spécifiques qui doivent être limitées par section
            restricted_section_urls = [
                '/teachers/', 
                '/courses/', 
                '/attribution/', 
                '/charge/',
                '/tracking/'
            ]
            
            if any(current_url.startswith(url) for url in restricted_section_urls):
                # Ajoutez ici des vérifications spécifiques pour les vues qui peuvent nécessiter
                # des contraintes de section, mais qui ne les incluent pas dans l'URL
                # Ceci est un placeholder, et vous devrez adapter cette logique en fonction
                # de la structure spécifique de votre application
                pass
        
        response = self.get_response(request)
        return response
