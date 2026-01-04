from django.utils.deprecation import MiddlewareMixin
from .models import ActionLog


class ActionLoggingMiddleware(MiddlewareMixin):
    """
    Middleware pour enregistrer automatiquement les actions importantes
    """
    
    def process_request(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
            
        # Enregistrer l'accès au tableau de bord
        if request.path == '/tracking/' or request.path == '/':
            ActionLog.log_action(
                user=request.user,
                action_type='dashboard_view',
                description="Accès au tableau de bord du suivi",
                model_name='Dashboard',
                request=request
            )
        
        # Plus d'enregistrement des consultations (supprimé)
        
        # Enregistrer les exports PDF
        elif '/pdf' in request.path:
            ActionLog.log_action(
                user=request.user,
                action_type='export',
                description="Export PDF du tableau de bord",
                model_name='DashboardPDF',
                request=request
            )
        
        # Enregistrer les créations/modifications (POST requests)
        elif request.method == 'POST':
            path_parts = request.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                app_name = path_parts[0]
                action_name = path_parts[1] if len(path_parts) > 1 else ''
                
                # Créations et modifications d'attributions
                if app_name == 'attribution' and 'attribution' in action_name:
                    # Récupérer les données du formulaire pour une description détaillée
                    post_data = request.POST
                    
                    if 'create' in request.path or 'new' in request.path:
                        # Description détaillée pour la création
                        teacher_id = post_data.get('matricule', '')
                        course_code = post_data.get('code_ue', '')
                        description = f"Création d'attribution"
                        if teacher_id and course_code:
                            try:
                                from teachers.models import Teacher
                                from courses.models import Course
                                teacher = Teacher.objects.get(pk=teacher_id)
                                course = Course.objects.get(pk=course_code)
                                description = f"Création d'attribution: {course.code_ue} - {teacher.nom_complet}"
                            except:
                                description = f"Création d'attribution (ID: {course_code} - {teacher_id})"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='attribution_create',
                            description=description,
                            model_name='Attribution',
                            request=request
                        )
                    else:
                        # Description détaillée pour la modification
                        teacher_id = post_data.get('matricule', '')
                        course_code = post_data.get('code_ue', '')
                        description = f"Modification d'attribution"
                        if teacher_id and course_code:
                            try:
                                from teachers.models import Teacher
                                from courses.models import Course
                                teacher = Teacher.objects.get(pk=teacher_id)
                                course = Course.objects.get(pk=course_code)
                                description = f"Modification d'attribution: {course.code_ue} - {teacher.nom_complet}"
                            except:
                                description = f"Modification d'attribution (ID: {course_code} - {teacher_id})"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='attribution_update',
                            description=description,
                            model_name='Attribution',
                            request=request
                        )
                
                # Créations et modifications de planning
                elif app_name == 'attribution' and 'planning' in action_name:
                    post_data = request.POST
                    
                    if 'create' in request.path or 'new' in request.path:
                        # Description détaillée pour la création de planning
                        course_code = post_data.get('code_ue', '')
                        salle_id = post_data.get('salle', '')
                        jour = post_data.get('jour', '')
                        description = f"Création d'entrée de planning"
                        if course_code and salle_id and jour:
                            try:
                                from courses.models import Course
                                from attribution.models import Salle
                                course = Course.objects.get(pk=course_code)
                                salle = Salle.objects.get(pk=salle_id)
                                description = f"Création planning: {course.code_ue} - {salle.nom_salle} ({jour})"
                            except:
                                description = f"Création planning (ID: {course_code} - {salle_id} - {jour})"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='schedule_create',
                            description=description,
                            model_name='ScheduleEntry',
                            request=request
                        )
                    else:
                        # Description détaillée pour la modification de planning
                        course_code = post_data.get('code_ue', '')
                        salle_id = post_data.get('salle', '')
                        jour = post_data.get('jour', '')
                        description = f"Modification d'entrée de planning"
                        if course_code and salle_id and jour:
                            try:
                                from courses.models import Course
                                from attribution.models import Salle
                                course = Course.objects.get(pk=course_code)
                                salle = Salle.objects.get(pk=salle_id)
                                description = f"Modification planning: {course.code_ue} - {salle.nom_salle} ({jour})"
                            except:
                                description = f"Modification planning (ID: {course_code} - {salle_id} - {jour})"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='schedule_update',
                            description=description,
                            model_name='ScheduleEntry',
                            request=request
                        )
                
                # Suivi des enseignements
                elif app_name == 'tracking' and 'progress' in action_name:
                    post_data = request.POST
                    
                    if 'create' in request.path or 'new' in request.path:
                        # Description détaillée pour la création de suivi
                        teacher_id = post_data.get('teacher', '')
                        course_id = post_data.get('course', '')
                        week_id = post_data.get('week', '')
                        hours_done = post_data.get('hours_done', '0')
                        description = f"Création d'un suivi d'enseignement"
                        if teacher_id and course_id:
                            try:
                                from teachers.models import Teacher
                                from courses.models import Course
                                teacher = Teacher.objects.get(pk=teacher_id)
                                course = Course.objects.get(pk=course_id)
                                description = f"Création suivi: {course.code_ue} - {teacher.nom_complet} ({hours_done}h)"
                            except:
                                description = f"Création suivi (ID: {course_id} - {teacher_id} - {hours_done}h)"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='progress_create',
                            description=description,
                            model_name='TeachingProgress',
                            request=request
                        )
                    else:
                        # Description détaillée pour la modification de suivi
                        teacher_id = post_data.get('teacher', '')
                        course_id = post_data.get('course', '')
                        hours_done = post_data.get('hours_done', '0')
                        description = f"Modification d'un suivi d'enseignement"
                        if teacher_id and course_id:
                            try:
                                from teachers.models import Teacher
                                from courses.models import Course
                                teacher = Teacher.objects.get(pk=teacher_id)
                                course = Course.objects.get(pk=course_id)
                                description = f"Modification suivi: {course.code_ue} - {teacher.nom_complet} ({hours_done}h)"
                            except:
                                description = f"Modification suivi (ID: {course_id} - {teacher_id} - {hours_done}h)"
                        
                        ActionLog.log_action(
                            user=request.user,
                            action_type='progress_update',
                            description=description,
                            model_name='TeachingProgress',
                            request=request
                        )
        
        return None
    
    def process_response(self, request, response):
        # Enregistrer les impressions
        if 'print' in request.GET:
            if hasattr(request, 'user') and request.user.is_authenticated:
                ActionLog.log_action(
                    user=request.user,
                    action_type='print',
                    description="Impression d'une page",
                    model_name='Print',
                    request=request
                )
        
        return response
