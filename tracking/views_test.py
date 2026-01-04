from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ActionLog

@login_required
def test_actions(request):
    """Vue de test pour générer différentes actions"""
    
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        
        if action_type == 'create':
            ActionLog.log_action(
                user=request.user,
                action_type='create',
                description="Test de création",
                model_name='TestModel',
                request=request
            )
        elif action_type == 'update':
            ActionLog.log_action(
                user=request.user,
                action_type='update',
                description="Test de modification",
                model_name='TestModel',
                request=request
            )
        elif action_type == 'delete':
            ActionLog.log_action(
                user=request.user,
                action_type='delete',
                description="Test de suppression",
                model_name='TestModel',
                request=request
            )
        elif action_type == 'export':
            ActionLog.log_action(
                user=request.user,
                action_type='export',
                description="Test d'export",
                model_name='TestModel',
                request=request
            )
        elif action_type == 'print':
            ActionLog.log_action(
                user=request.user,
                action_type='print',
                description="Test d'impression",
                model_name='TestModel',
                request=request
            )
    
    # Afficher les 10 dernières actions
    recent_actions = ActionLog.objects.all().order_by('-timestamp')[:10]
    
    return render(request, 'tracking/test_actions.html', {
        'recent_actions': recent_actions
    })
