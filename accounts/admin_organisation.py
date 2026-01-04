"""
Vues d'administration pour la gestion des organisations
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Organisation, UserProfile
from .permissions import check_admin_permission

@login_required
def organisation_list(request):
    """Liste des organisations"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisations = Organisation.objects.all().order_by('nom')
    
    context = {
        'organisations': organisations,
    }
    return render(request, 'accounts/organisation_list.html', context)

@login_required
@transaction.atomic
def organisation_create(request):
    """Créer une nouvelle organisation"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        
        if not nom or not code:
            messages.error(request, "Le nom et le code sont obligatoires.")
            return render(request, 'accounts/organisation_form.html')
        
        # Vérifier si le code existe déjà
        if Organisation.objects.filter(code=code).exists():
            messages.error(request, f"Une organisation avec le code '{code}' existe déjà.")
            return render(request, 'accounts/organisation_form.html')
        
        organisation = Organisation.objects.create(
            nom=nom,
            code=code,
            description=description,
            est_active=True
        )
        
        messages.success(request, f"L'organisation '{organisation.nom}' a été créée avec succès.")
        return redirect('accounts:organisation_list')
    
    return render(request, 'accounts/organisation_form.html')

@login_required
def organisation_detail(request, pk):
    """Afficher les détails d'une organisation"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisation = get_object_or_404(Organisation, pk=pk)
    
    # Calculer les statistiques exactes pour cette organisation
    from tracking.models import Course, Teacher
    from attribution.models import ScheduleEntry
    from reglage.models import Departement, Mention, Classe
    
    # Utilisateurs de l'organisation
    users_count = UserProfile.objects.filter(organisation=organisation).count()
    
    # Cours de l'organisation (filtrés par section = code organisation)
    courses_count = Course.objects.filter(section=organisation.code).count()
    
    # Enseignants de l'organisation (filtrés par section = code organisation)
    teachers_count = Teacher.objects.filter(section=organisation.code).count()
    
    # Horaires de l'organisation
    schedules_count = ScheduleEntry.objects.filter(organisation=organisation).count()
    
    # Étudiants de l'organisation (ceux qui ont un matricule_etudiant)
    students_count = UserProfile.objects.filter(organisation=organisation, matricule_etudiant__isnull=False).exclude(matricule_etudiant='').count()
    
    # Départements de l'organisation (via section)
    from reglage.models import Section
    try:
        section_obj = Section.objects.get(CodeSection=organisation.code)
        departments_count = Departement.objects.filter(section=section_obj).count()
        mentions_count = Mention.objects.filter(departement__section=section_obj).count()
        classes_count = Classe.objects.filter(mention__departement__section=section_obj).count()
    except Section.DoesNotExist:
        departments_count = 0
        mentions_count = 0
        classes_count = 0
    
    context = {
        'organisation': organisation,
        'users_count': users_count,
        'courses_count': courses_count,
        'teachers_count': teachers_count,
        'schedules_count': schedules_count,
        'students_count': students_count,
        'departments_count': departments_count,
        'mentions_count': mentions_count,
        'classes_count': classes_count,
    }
    return render(request, 'accounts/organisation_detail.html', context)

@login_required
@transaction.atomic
def organisation_edit(request, pk):
    """Modifier une organisation"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisation = get_object_or_404(Organisation, pk=pk)
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        est_active = request.POST.get('est_active') == 'on'
        
        if not nom or not code:
            messages.error(request, "Le nom et le code sont obligatoires.")
            return render(request, 'accounts/organisation_form.html', {'organisation': organisation})
        
        # Vérifier si le code existe déjà (sauf pour cette organisation)
        if Organisation.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, f"Une autre organisation avec le code '{code}' existe déjà.")
            return render(request, 'accounts/organisation_form.html', {'organisation': organisation})
        
        organisation.nom = nom
        organisation.code = code
        organisation.description = description
        organisation.est_active = est_active
        organisation.save()
        
        messages.success(request, f"L'organisation '{organisation.nom}' a été modifiée avec succès.")
        return redirect('accounts:organisation_list')
    
    context = {
        'organisation': organisation,
    }
    return render(request, 'accounts/organisation_form.html', context)

@login_required
@transaction.atomic
def organisation_delete(request, pk):
    """Supprimer une organisation"""
    if not check_admin_permission(request.user):
        messages.error(request, "Vous n'avez pas les permissions nécessaires.")
        return redirect('home')
    
    organisation = get_object_or_404(Organisation, pk=pk)
    
    if request.method == 'POST':
        # Vérifier s'il y a des utilisateurs liés
        users_count = organisation.users.count()
        if users_count > 0:
            messages.error(request, f"Impossible de supprimer cette organisation car {users_count} utilisateur(s) y sont rattachés.")
            return redirect('accounts:organisation_list')
        
        nom = organisation.nom
        organisation.delete()
        messages.success(request, f"L'organisation '{nom}' a été supprimée avec succès.")
        return redirect('accounts:organisation_list')
    
    context = {
        'organisation': organisation,
        'users_count': organisation.users.count(),
    }
    return render(request, 'accounts/organisation_confirm_delete.html', context)
