from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import TeachingProgress, AcademicWeek, ActionLog
from attribution.models import Attribution, ScheduleEntry
from django.db.models.signals import pre_delete

# Importer les fonctions du middleware
try:
    from .middleware_user import get_current_user
except ImportError:
    # Fallback si le middleware n'est pas encore disponible
    def get_current_user():
        return None


@receiver(post_save, sender=TeachingProgress)
def log_teaching_progress_save(sender, instance, created, **kwargs):
    """Enregistrer la création ou modification d'un suivi d'enseignement"""
    user = get_current_user()
    if created:
        ActionLog.log_action(
            user=user,
            action_type='progress_create',
            description=f"Création suivi: {instance.course.code_ue} - {instance.teacher.nom_complet} ({instance.hours_done}h/{instance.total_hours}h) - Semaine {instance.week}",
            model_name='TeachingProgress',
            object_id=instance.id,
            object_repr=str(instance)
        )
    else:
        ActionLog.log_action(
            user=user,
            action_type='progress_update',
            description=f"Modification suivi: {instance.course.code_ue} - {instance.teacher.nom_complet} ({instance.hours_done}h/{instance.total_hours}h) - Semaine {instance.week}",
            model_name='TeachingProgress',
            object_id=instance.id,
            object_repr=str(instance)
        )


@receiver(post_delete, sender=TeachingProgress)
def log_teaching_progress_delete(sender, instance, **kwargs):
    """Enregistrer la suppression d'un suivi d'enseignement"""
    user = get_current_user()
    ActionLog.log_action(
        user=user,
        action_type='progress_delete',
        description=f"Suppression suivi: {instance.course.code_ue} - {instance.teacher.nom_complet} ({instance.hours_done}h) - Semaine {instance.week}",
        model_name='TeachingProgress',
        object_id=instance.id,
        object_repr=str(instance)
    )


@receiver(post_save, sender=Attribution)
def log_attribution_save(sender, instance, created, **kwargs):
    """Enregistrer la création ou modification d'une attribution"""
    user = get_current_user()
    if created:
        ActionLog.log_action(
            user=user,
            action_type='attribution_create',
            description=f"Création attribution: {instance.code_ue.code_ue} ({instance.code_ue.intitule_ue}) - {instance.matricule.nom_complet} - {instance.nombre_heures}h",
            model_name='Attribution',
            object_id=instance.id,
            object_repr=str(instance)
        )
    else:
        ActionLog.log_action(
            user=user,
            action_type='attribution_update',
            description=f"Modification attribution: {instance.code_ue.code_ue} ({instance.code_ue.intitule_ue}) - {instance.matricule.nom_complet} - {instance.nombre_heures}h",
            model_name='Attribution',
            object_id=instance.id,
            object_repr=str(instance)
        )


@receiver(post_delete, sender=Attribution)
def log_attribution_delete(sender, instance, **kwargs):
    """Enregistrer la suppression d'une attribution"""
    user = get_current_user()
    ActionLog.log_action(
        user=user,
        action_type='attribution_delete',
        description=f"Suppression attribution: {instance.code_ue.code_ue} ({instance.code_ue.intitule_ue}) - {instance.matricule.nom_complet} - {instance.nombre_heures}h",
        model_name='Attribution',
        object_id=instance.id,
        object_repr=str(instance)
    )


@receiver(post_save, sender=ScheduleEntry)
def log_schedule_entry_save(sender, instance, created, **kwargs):
    """Enregistrer la création ou modification d'une entrée de planning"""
    user = get_current_user()
    course_code = instance.attribution.code_ue.code_ue if instance.attribution and instance.attribution.code_ue else 'N/A'
    salle = instance.salle_link.nom_salle if instance.salle_link else (instance.salle if instance.salle else 'N/A')
    creneau = f"{instance.creneau.heure_debut}-{instance.creneau.heure_fin}" if instance.creneau else 'N/A'
    
    if created:
        ActionLog.log_action(
            user=user,
            action_type='schedule_create',
            description=f"Création planning: {course_code} - {salle} ({instance.jour} {creneau})",
            model_name='ScheduleEntry',
            object_id=instance.id,
            object_repr=str(instance)
        )
    else:
        ActionLog.log_action(
            user=user,
            action_type='schedule_update',
            description=f"Modification planning: {course_code} - {salle} ({instance.jour} {creneau})",
            model_name='ScheduleEntry',
            object_id=instance.id,
            object_repr=str(instance)
        )


@receiver(post_delete, sender=ScheduleEntry)
def log_schedule_entry_delete(sender, instance, **kwargs):
    """Enregistrer la suppression d'une entrée de planning"""
    user = get_current_user()
    course_code = instance.attribution.code_ue.code_ue if instance.attribution and instance.attribution.code_ue else 'N/A'
    salle = instance.salle_link.nom_salle if instance.salle_link else (instance.salle if instance.salle else 'N/A')
    creneau = f"{instance.creneau.heure_debut}-{instance.creneau.heure_fin}" if instance.creneau else 'N/A'
    
    ActionLog.log_action(
        user=user,
        action_type='schedule_delete',
        description=f"Suppression planning: {course_code} - {salle} ({instance.jour} {creneau})",
        model_name='ScheduleEntry',
        object_id=instance.id,
        object_repr=str(instance)
    )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Enregistrer la connexion de l'utilisateur"""
    ActionLog.log_action(
        user=user,
        action_type='login',
        description=f"Connexion de l'utilisateur: {user.username}",
        model_name='User',
        request=request
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Enregistrer la déconnexion de l'utilisateur"""
    if user:
        ActionLog.log_action(
            user=user,
            action_type='logout',
            description=f"Déconnexion de l'utilisateur: {user.username}",
            model_name='User',
            request=request
        )
