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
    context = {
        'current_year': timezone.now().year,
        'active_year': AnneeAcademique.objects.filter(est_en_cours=True).first(),
        'current_week': SemaineCours.objects.filter(est_en_cours=True).first(),
    }
    
    # Statistiques rapides (si l'utilisateur a les permissions)
    if request.user.has_perm('attribution.view_scheduleentry'):
        context['total_cours'] = ScheduleEntry.objects.count()
        
    return render(request, 'home.html', context)
