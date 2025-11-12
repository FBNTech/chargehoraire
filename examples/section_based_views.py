from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from teachers.models import Teacher
from accounts.permissions import check_admin_permission, check_section_role_permission


class SectionBasedTeachersListView(LoginRequiredMixin, ListView):
    """
    Vue exemple qui filtre les enseignants en fonction de la section de l'utilisateur.
    Les admins et rôles administratifs peuvent voir tous les enseignants.
    Les chefs de section ne peuvent voir que les enseignants de leur section.
    """
    model = Teacher
    template_name = 'examples/teachers_by_section.html'
    context_object_name = 'teachers'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Admins et rôles administratifs peuvent tout voir
        if check_admin_permission(self.request.user):
            return queryset
            
        # Les chefs de section ne peuvent voir que les enseignants de leur section
        if check_section_role_permission(self.request.user):
            user_section = self.request.user.profile.section
            if user_section:
                # Dans un système réel, vous auriez une relation directe entre enseignants et sections
                # ou vous utiliseriez une fonction pour déterminer si un enseignant appartient à une section
                # Pour cet exemple, nous supposons que la section est stockée dans un champ "section" du modèle Teacher
                return queryset.filter(section=user_section)
            else:
                # Si l'utilisateur a un rôle de section mais pas de section définie, ne montrer aucun enseignant
                return queryset.none()
        
        # Pour les autres utilisateurs, appliquer d'autres filtres selon les besoins
        # ...
        
        # Par défaut, retourner un queryset vide
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter des informations supplémentaires au contexte
        if check_section_role_permission(self.request.user):
            context['section_name'] = self.request.user.profile.section
            
        return context


def section_specific_action(request, section_code):
    """
    Exemple de vue fonction qui vérifie l'accès à une section spécifique
    avant d'effectuer une action.
    """
    # Vérifier si l'utilisateur peut accéder à cette section
    if request.user.profile.can_access_section(section_code):
        # Effectuer l'action spécifique à la section
        # ...
        
        messages.success(request, f"Action effectuée avec succès pour la section {section_code}")
        return redirect('dashboard')
    else:
        messages.error(request, f"Vous n'avez pas accès à la section {section_code}")
        return redirect('dashboard')
