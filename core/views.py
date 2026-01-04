from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum
from reglage.models import AnneeAcademique, SemaineCours
from attribution.models import ScheduleEntry
from django.contrib import messages

@login_required
def home(request):
    """
    Vue pour la page d'accueil du tableau de bord
    Affiche un aperçu des informations importantes
    """
    from accounts.models import Organisation
    from accounts.permissions import check_admin_permission, check_administrative_role_permission
    
    # Récupérer les organisations dès le début
    organisations = Organisation.objects.all().order_by('nom')
    
    is_admin = check_admin_permission(request.user)
    is_administrative = check_administrative_role_permission(request.user)
    
    context = {
        'current_year': timezone.now().year,
        'active_year': AnneeAcademique.objects.filter(est_en_cours=True).first(),
        'current_week': SemaineCours.objects.filter(est_en_cours=True).first(),
        'is_admin': is_admin or is_administrative,
        'organisations': organisations,
        'total_organisations': organisations.count(),
        'organisations_actives': organisations.filter(est_active=True).count(),
    }
    
    # Statistiques rapides (si l'utilisateur a les permissions)
    if request.user.has_perm('attribution.view_scheduleentry'):
        context['total_cours'] = ScheduleEntry.objects.count()
        
    return render(request, 'home.html', context)
