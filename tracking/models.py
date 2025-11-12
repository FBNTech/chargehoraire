from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from courses.models import Course
from teachers.models import Teacher
from reglage.models import Semestre, SemaineCours

class AcademicWeek(models.Model):
    """Modèle pour définir les semaines académiques"""
    codesemaine = models.CharField(max_length=20, verbose_name="Code semaine", default="S-001")
    semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, related_name='semaines', verbose_name="Semestre", null=True, blank=True)
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    academic_year = models.CharField(max_length=20, verbose_name="Année académique")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Semaine académique"
        verbose_name_plural = "Semaines académiques"
        ordering = ['-academic_year', 'codesemaine']
        unique_together = ['codesemaine', 'academic_year']
        
    def __str__(self):
        if self.semestre:
            return f"{self.codesemaine} - {self.semestre.DesignationSemestre} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"
        else:
            return f"{self.codesemaine} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"

class TeachingProgress(models.Model):
    """Modèle pour enregistrer les heures d'enseignement effectuées par semaine"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress_records', verbose_name="UE")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='progress_records', verbose_name="Enseignant")
    week = models.ForeignKey(SemaineCours, on_delete=models.CASCADE, related_name='progress_records', verbose_name="Semaine")
    hours_done = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Heures effectuées")
    comment = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planifié'),
        ('completed', 'Terminé'),
        ('canceled', 'Annulé'),
        ('rescheduled', 'Reporté')
    ], default='planned', verbose_name="Statut")
    
    class Meta:
        verbose_name = "Suivi d'enseignement"
        verbose_name_plural = "Suivi des enseignements"
        ordering = ['-week__annee_academique', 'week__numero_semaine', 'course__code_ue']
        unique_together = ['course', 'teacher', 'week']
        
    def __str__(self):
        return f"{self.course.code_ue} - {self.teacher.nom_complet} - {self.week.designation}"
    
    def save(self, *args, **kwargs):
        # Vérifie si c'est un nouvel enregistrement
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Mettre à jour les statistiques de progression
        if is_new or kwargs.get('update_stats', True):
            self.update_progress_stats()
    
    def update_progress_stats(self):
        """Mettre à jour les statistiques de progression pour ce cours"""
        try:
            # Récupérer ou créer les statistiques de progression
            stats, created = ProgressStats.objects.get_or_create(
                course=self.course,
                teacher=self.teacher,
                academic_year=self.week.academic_year
            )
            
            # Calculer le total des heures effectuées
            total_hours = TeachingProgress.objects.filter(
                course=self.course,
                teacher=self.teacher,
                week__academic_year=self.week.academic_year
            ).aggregate(models.Sum('hours_done'))['hours_done__sum'] or 0
            
            # Mettre à jour les statistiques
            stats.total_hours_done = total_hours
            stats.last_update = timezone.now()
            stats.save()
            
        except Exception as e:
            # Gérer les erreurs silencieusement mais les logger
            # En production, il faudrait utiliser un logger
            print(f"Erreur lors de la mise à jour des statistiques: {e}")

class ProgressStats(models.Model):
    """Modèle pour les statistiques de progression des enseignements"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress_stats', verbose_name="UE")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='progress_stats', verbose_name="Enseignant")
    academic_year = models.CharField(max_length=20, verbose_name="Année académique")
    total_hours_done = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Total heures effectuées")
    last_update = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Statistiques de progression"
        verbose_name_plural = "Statistiques de progression"
        unique_together = ['course', 'teacher', 'academic_year']
        
    def __str__(self):
        return f"{self.course.code_ue} - {self.teacher.nom_complet} - {self.academic_year}"
    
    @property
    def total_hours_allocated(self):
        """Retourne le nombre total d'heures allouées pour ce cours et cet enseignant"""
        # Le volume horaire total est la somme des heures CMI et TD+TP
        return (self.course.cmi or 0) + (self.course.td_tp or 0)
    
    @property
    def hours_remaining(self):
        """Retourne le nombre d'heures restantes"""
        return max(0, self.total_hours_allocated - self.total_hours_done)
    
    @property
    def progress_percentage(self):
        """Retourne le pourcentage de progression"""
        if self.total_hours_allocated <= 0:
            return 100  # Éviter une division par zéro
        return min(100, (self.total_hours_done / self.total_hours_allocated) * 100)


class ActionLog(models.Model):
    """Modèle pour enregistrer l'historique des actions des utilisateurs"""
    ACTION_TYPES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('view', 'Consultation'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('export', 'Exportation'),
        ('import', 'Importation'),
        ('print', 'Impression'),
        ('other', 'Autre'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utilisateur")
    username = models.CharField(max_length=150, verbose_name="Nom d'utilisateur")  # Garde le nom si l'utilisateur est supprimé
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Type d'action")
    model_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modèle concerné")
    object_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de l'objet")
    object_repr = models.TextField(blank=True, null=True, verbose_name="Représentation de l'objet")
    description = models.TextField(verbose_name="Description")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure", db_index=True)
    
    class Meta:
        verbose_name = "Historique d'action"
        verbose_name_plural = "Historique des actions"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['model_name']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_action_type_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def log_action(cls, user, action_type, description, model_name=None, object_id=None, object_repr=None, request=None):
        """Méthode helper pour créer un log d'action"""
        ip_address = None
        user_agent = None
        
        if request:
            # Récupérer l'IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Récupérer le user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limiter la taille
        
        return cls.objects.create(
            user=user if user and user.is_authenticated else None,
            username=user.username if user and user.is_authenticated else 'Anonyme',
            action_type=action_type,
            model_name=model_name,
            object_id=str(object_id) if object_id else None,
            object_repr=str(object_repr) if object_repr else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
