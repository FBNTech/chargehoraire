from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
# Temporairement commenté pour permettre l'accès sans authentification
# from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Case, When, Value, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
import re

from .models import TeachingProgress, AcademicWeek, ProgressStats, ActionLog
from .forms import TeachingProgressForm, AcademicWeekForm, ProgressFilterForm
from courses.models import Course
from teachers.models import Teacher
from attribution.models import Attribution
from reglage.models import AnneeAcademique, SemaineCours
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from datetime import datetime, timedelta


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
        from attribution.models import ScheduleEntry
        context['total_cours'] = ScheduleEntry.objects.count()
        
    return render(request, 'home.html', context)


class DashboardView(TemplateView):
    """Vue du tableau de bord pour le suivi des enseignements"""
    template_name = 'tracking/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Année académique actuelle
        current_year = timezone.now().year
        academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
        
        # Heures effectuées (total de tous les enregistrements)
        total_hours_done = TeachingProgress.objects.aggregate(total=Sum('hours_done'))['total'] or 0
        
        # Heures allouées (basé sur les charges des enseignants)
        total_hours_allocated = Attribution.objects.select_related('code_ue').filter(
            code_ue__isnull=False
        ).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('code_ue__cmi') + F('code_ue__td_tp'),
                    output_field=FloatField()
                )
            )
        )['total'] or 0
        
        # Calcul du pourcentage
        global_progress_percentage = 0
        if total_hours_allocated > 0:
            global_progress_percentage = (float(total_hours_done) / float(total_hours_allocated)) * 100
        
        # Statistiques pour la carte
        stats = {
            'current_week': None,  # Sera déterminé par est_en_cours dans SemaineCours,
            'total_hours_done': total_hours_done,
            'total_hours_allocated': total_hours_allocated,
            'global_progress_percentage': round(global_progress_percentage, 1),
            'total_courses': Course.objects.count(),
            'total_teachers': Teacher.objects.count(),
        }
        
        # Progression des cours depuis TeachingProgress avec jointure Course
        course_progress = TeachingProgress.objects.filter(
            week__annee_academique=academic_year
        ).select_related('course').values(
            'course__code_ue',
            'course__intitule_ue', 
            'course__classe',
            'course__semestre',
            'course__cmi',
            'course__td_tp',
            'course__id'
        ).annotate(
            total_hours_done=Sum('hours_done'),
            total_volume=ExpressionWrapper(
                F('course__cmi') + F('course__td_tp'),
                output_field=FloatField()
            ),
            progression_percentage=Case(
                When(total_volume__gt=0, then=(F('total_hours_done') * 100.0) / F('total_volume')),
                default=Value(0),
                output_field=FloatField()
            )
        ).order_by('course__semestre', 'course__code_ue')
        
        # Grouper les cours par semestre
        courses_by_semester = {}
        for course in course_progress:
            semester = course['course__semestre']
            if semester not in courses_by_semester:
                courses_by_semester[semester] = []
            courses_by_semester[semester].append(course)
        
        context['courses_by_semester'] = courses_by_semester
        
        
        # Progression des enseignants par type de charge
        teacher_progress = []
        
        # Récupérer toutes les combinaisons uniques enseignant-type_charge
        teacher_charge_combinations = Attribution.objects.filter(
            matricule__matricule__in=TeachingProgress.objects.filter(
                week__annee_academique=academic_year
            ).values_list('teacher__matricule', flat=True).distinct()
        ).values('matricule__matricule', 'matricule__nom_complet', 'type_charge').distinct()
        
        for combination in teacher_charge_combinations:
            teacher_matricule = combination['matricule__matricule']
            teacher_name = combination['matricule__nom_complet']
            charge_type = combination['type_charge']
            
            if not charge_type:
                continue
                
            # Filtrer les cours selon le type de charge
            courses_for_charge = Attribution.objects.filter(
                matricule__matricule=teacher_matricule,
                type_charge=charge_type
            ).values_list('code_ue__id', flat=True)
            
            # Calculer les heures réalisées pour ce type de charge spécifique
            hours_done_for_charge = TeachingProgress.objects.filter(
                teacher__matricule=teacher_matricule,
                week__annee_academique=academic_year,
                course__id__in=courses_for_charge
            ).aggregate(total=Sum('hours_done'))['total'] or 0
            
            # Calculer les heures allouées pour ce type de charge spécifique
            hours_allocated_for_charge = Course.objects.filter(
                id__in=courses_for_charge
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('cmi') + F('td_tp'),
                        output_field=FloatField()
                    )
                )
            )['total'] or 0
            
            # Calculer le pourcentage de progression
            progression_percentage = 0
            if hours_allocated_for_charge > 0:
                progression_percentage = (float(hours_done_for_charge) * 100.0) / float(hours_allocated_for_charge)
            
            teacher_progress.append({
                'teacher__nom_complet': teacher_name,
                'teacher__matricule': teacher_matricule,
                'type_charge': charge_type.capitalize(),
                'total_hours_done': hours_done_for_charge,
                'total_hours_allocated': hours_allocated_for_charge,
                'progression_percentage': progression_percentage,
                'hours_display': f"{hours_done_for_charge}/{hours_allocated_for_charge}"
            })
        
        # Trier par nom d'enseignant puis par type de charge
        teacher_progress.sort(key=lambda x: (x['teacher__nom_complet'], x['type_charge']))
        
        context['teacher_progress'] = teacher_progress
        
        # Progression des classes
        class_progress = Course.objects.values(
            'classe', 'semestre'
        ).annotate(
            nombre_ue=Count('id'),
            total_hours_allocated=Sum(
                ExpressionWrapper(
                    F('cmi') + F('td_tp'),
                    output_field=FloatField()
                )
            ),
            total_hours_done=Sum(
                Case(
                    When(
                        progress_records__week__annee_academique=academic_year,
                        then='progress_records__hours_done'
                    ),
                    default=Value(0),
                    output_field=FloatField()
                )
            ),
            progression_percentage=Case(
                When(
                    total_hours_allocated__gt=0,
                    then=(F('total_hours_done') * 100.0) / F('total_hours_allocated')
                ),
                default=Value(0),
                output_field=FloatField()
            )
        ).order_by('classe', 'semestre')
        
        context['class_progress'] = class_progress
        context['stats'] = stats
        
        # Formulaire de filtre
        context['filter_form'] = ProgressFilterForm(self.request.GET or None)
        
        # Récupérer les enseignants avec la fonction CSAE
        context['csae_teachers'] = Teacher.objects.filter(fonction='CSAE').order_by('nom_complet')
        
        # Récupérer les semaines disponibles pour le filtre du PDF
        context['semaines_disponibles'] = SemaineCours.objects.filter(
            annee_academique=academic_year
        ).order_by('numero_semaine')
        
        return context

class TeachingProgressListView(ListView):
    """Liste des enregistrements de suivi des enseignements"""
    model = TeachingProgress
    template_name = 'tracking/progress_list.html'
    context_object_name = 'progress_entries'
    paginate_by = 20

class TeachingProgressPrintView(ListView):
    """Vue d'impression des enregistrements de suivi des enseignements"""
    model = TeachingProgress
    template_name = 'tracking/progress_print.html'
    context_object_name = 'progress_entries'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer selon les paramètres de requête
        filter_form = ProgressFilterForm(self.request.GET or None)
        
        if filter_form.is_valid():
            filters = {}
            
            if teacher_id := filter_form.cleaned_data.get('teacher'):
                filters['teacher'] = teacher_id
            
            if course_id := filter_form.cleaned_data.get('course'):
                filters['course'] = course_id
            
            if academic_year := filter_form.cleaned_data.get('academic_year'):
                filters['week__annee_academique'] = academic_year
            
            if week_start := filter_form.cleaned_data.get('week_start'):
                filters['week__numero_semaine__gte'] = week_start
            
            if week_end := filter_form.cleaned_data.get('week_end'):
                filters['week__numero_semaine__lte'] = week_end
            
            if status := filter_form.cleaned_data.get('status'):
                filters['status'] = status
            
            if filters:
                queryset = queryset.filter(**filters)
        
        return queryset.select_related('teacher', 'course', 'week').order_by('-week__annee_academique', '-week__numero_semaine')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajout de la date courante pour le rapport
        context['current_date'] = timezone.now()
        
        # Informations de filtrage
        filter_form = ProgressFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        # Calcul des statistiques pour les données filtrées
        queryset = self.get_queryset()
        
        context['total_hours'] = queryset.aggregate(total=Sum('hours_done'))['total'] or 0
        context['total_entries'] = queryset.count()
        
        # Extraire les informations de filtre pour le titre
        if filter_form.is_valid():
            teacher = filter_form.cleaned_data.get('teacher')
            course = filter_form.cleaned_data.get('course')
            academic_year = filter_form.cleaned_data.get('academic_year')
            
            if teacher:
                context['filtered_teacher'] = teacher
            if course:
                context['filtered_course'] = course
            if academic_year:
                context['filtered_academic_year'] = academic_year
        
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ProgressFilterForm(self.request.GET or None)
        
        # Calcul des totaux pour les résultats filtrés
        queryset = self.get_queryset()
        total_hours = queryset.aggregate(Sum('hours_done'))['hours_done__sum'] or 0
        context['total_hours'] = total_hours
        context['total_entries'] = queryset.count()
        
        return context

class TeachingProgressCreateView(CreateView):
    """Création d'un nouvel enregistrement de suivi"""
    model = TeachingProgress
    form_class = TeachingProgressForm
    template_name = 'tracking/progress_form.html'
    success_url = reverse_lazy('tracking:progress_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Enregistrement du suivi créé avec succès.")
        return super().form_valid(form)

class TeachingProgressUpdateView(UpdateView):
    """Modification d'un enregistrement de suivi existant"""
    model = TeachingProgress
    form_class = TeachingProgressForm
    template_name = 'tracking/progress_form.html'
    success_url = reverse_lazy('tracking:progress_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Enregistrement du suivi mis à jour avec succès.")
        return super().form_valid(form)

class TeachingProgressDeleteView(DeleteView):
    """Suppression d'un enregistrement de suivi"""
    model = TeachingProgress
    template_name = 'tracking/progress_confirm_delete.html'
    success_url = reverse_lazy('tracking:progress_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Enregistrement du suivi supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

class TeachingProgressDetailView(DetailView):
    """Détails d'un enregistrement de suivi"""
    model = TeachingProgress
    template_name = 'tracking/progress_detail.html'
    context_object_name = 'progress'

class AcademicWeekListView(ListView):
    """Liste des semaines académiques"""
    model = AcademicWeek
    template_name = 'tracking/week_list.html'
    context_object_name = 'weeks'
    paginate_by = 20
    
    def get_queryset(self):
        # Filtrer par année académique si spécifiée
        academic_year = self.request.GET.get('academic_year', '')
        queryset = AcademicWeek.objects.all()
        
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        # Précharger la relation semestre pour éviter les requêtes N+1
        return queryset.select_related('semestre').order_by('-academic_year', 'codesemaine')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des années académiques disponibles
        academic_years = AcademicWeek.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
        context['academic_years'] = academic_years
        
        # Année académique sélectionnée
        context['selected_year'] = self.request.GET.get('academic_year', '')
        
        return context

class AcademicWeekCreateView(CreateView):
    """Création d'une nouvelle semaine académique"""
    model = AcademicWeek
    form_class = AcademicWeekForm
    template_name = 'tracking/week_form.html'
    success_url = reverse_lazy('tracking:week_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Semaine académique créée avec succès.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Débogage des erreurs de validation
        errors = form.errors
        print(f"DEBUG - Erreurs de validation: {errors}")
        messages.error(self.request, f"Erreur de validation du formulaire: {errors}")
        return super().form_invalid(form)

class AcademicWeekUpdateView(UpdateView):
    """Modification d'une semaine académique existante"""
    model = AcademicWeek
    form_class = AcademicWeekForm
    template_name = 'tracking/week_form.html'
    success_url = reverse_lazy('tracking:week_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Semaine académique mise à jour avec succès.")
        return super().form_valid(form)
        
    def form_invalid(self, form):
        # Débogage des erreurs de validation
        errors = form.errors
        print(f"DEBUG - Erreurs de validation (update): {errors}")
        messages.error(self.request, f"Erreur de validation du formulaire: {errors}")
        return super().form_invalid(form)

class AcademicWeekDeleteView(DeleteView):
    """Suppression d'une semaine académique"""
    model = AcademicWeek
    template_name = 'tracking/week_confirm_delete.html'
    success_url = reverse_lazy('tracking:week_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Semaine académique supprimée avec succès.")
        return super().delete(request, *args, **kwargs)

class TeacherProgressView(DetailView):
    """Vue détaillée de la progression d'un enseignant"""
    model = Teacher
    template_name = 'tracking/teacher_progress.html'
    context_object_name = 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        
        # Année académique actuelle ou sélectionnée
        academic_year = self.request.GET.get('academic_year', '')
        if not academic_year:
            current_year = timezone.now().year
            academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
        
        # Récupérer les stats pour cet enseignant
        stats = ProgressStats.objects.filter(
            teacher=teacher,
            academic_year=academic_year
        ).select_related('course')
        
        context['stats'] = stats
        context['academic_year'] = academic_year
        
        # Progression hebdomadaire
        weekly_progress = TeachingProgress.objects.filter(
            teacher=teacher,
            week__annee_academique=academic_year
        ).order_by('week__numero_semaine').values('week__numero_semaine').annotate(
            total_hours=Sum('hours_done')
        )
        
        context['weekly_progress'] = list(weekly_progress)
        
        # Calculer les totaux
        total_allocated = sum(stat.total_hours_allocated for stat in stats)
        total_done = sum(stat.total_hours_done for stat in stats)
        
        context['total_allocated'] = total_allocated
        context['total_done'] = total_done
        context['total_remaining'] = max(0, total_allocated - total_done)
        
        if total_allocated > 0:
            context['overall_percentage'] = min(100, (total_done / total_allocated) * 100)
        else:
            context['overall_percentage'] = 100
        
        # Années académiques disponibles
        context['academic_years'] = ProgressStats.objects.filter(
            teacher=teacher
        ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
        
        return context

class CourseProgressView(DetailView):
    """Vue détaillée de la progression d'un cours"""
    model = Course
    template_name = 'tracking/course_progress.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Année académique actuelle ou sélectionnée
        academic_year = self.request.GET.get('academic_year', '')
        if not academic_year:
            current_year = timezone.now().year
            academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
        
        # Récupérer les stats pour ce cours
        stats = ProgressStats.objects.filter(
            course=course,
            academic_year=academic_year
        ).select_related('teacher')
        
        context['stats'] = stats
        context['academic_year'] = academic_year
        
        # Progression hebdomadaire
        weekly_progress = TeachingProgress.objects.filter(
            course=course,
            week__annee_academique=academic_year
        ).order_by('week__numero_semaine').values('week__numero_semaine').annotate(
            total_hours=Sum('hours_done')
        )
        
        context['weekly_progress'] = list(weekly_progress)
        
        # Calculer les totaux
        total_done = sum(stat.total_hours_done for stat in stats)
        # Calculer le volume horaire total en additionnant cmi et td_tp
        total_allocated = course.cmi + course.td_tp
        
        context['total_allocated'] = total_allocated
        context['total_done'] = total_done
        context['total_remaining'] = max(0, total_allocated - total_done)
        
        if total_allocated > 0:
            context['overall_percentage'] = min(100, (total_done / total_allocated) * 100)
        else:
            context['overall_percentage'] = 100
        
        # Années académiques disponibles
        context['academic_years'] = ProgressStats.objects.filter(
            course=course
        ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
        
        return context

# API pour les graphiques
def progress_chart_data(request):
    """Fournit les données pour les graphiques de suivi"""
    # Année académique actuelle ou sélectionnée
    academic_year = request.GET.get('academic_year', '')
    if not academic_year:
        current_year = timezone.now().year
        academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
    
    # Type de graphique demandé
    chart_type = request.GET.get('type', 'weekly')
    
    data = {}
    
    if chart_type == 'weekly':
        # Progression hebdomadaire globale
        weekly_data = TeachingProgress.objects.filter(
            week__annee_academique=academic_year
        ).values('week__numero_semaine').annotate(
            hours=Sum('hours_done')
        ).order_by('week__numero_semaine')
        
        weeks = [item['week__numero_semaine'] for item in weekly_data]
        hours = [float(item['hours']) for item in weekly_data]
        
        data = {
            'labels': weeks,
            'datasets': [{
                'label': 'Heures effectuées par semaine',
                'data': hours,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        }
    
    elif chart_type == 'course':
        # Progression par cours (top 10)
        course_data = ProgressStats.objects.filter(
            academic_year=academic_year
        ).values('course__code_ue').annotate(
            total=Sum('total_hours_done')
        ).order_by('-total')[:10]
        
        courses = [item['course__code_ue'] for item in course_data]
        hours = [float(item['total']) for item in course_data]
        
        data = {
            'labels': courses,
            'datasets': [{
                'label': 'Heures effectuées par cours',
                'data': hours,
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }]
        }
    
    elif chart_type == 'teacher':
        # Progression par enseignant (top 10)
        teacher_data = ProgressStats.objects.filter(
            academic_year=academic_year
        ).values('teacher__nom_complet').annotate(
            total=Sum('total_hours_done')
        ).order_by('-total')[:10]
        
        teachers = [item['teacher__nom_complet'] for item in teacher_data]
        hours = [float(item['total']) for item in teacher_data]
        
        data = {
            'labels': teachers,
            'datasets': [{
                'label': 'Heures effectuées par enseignant',
                'data': hours,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        }
    
    return JsonResponse(data)

@require_http_methods(['GET'])
def get_teacher_courses(request, teacher_id):
    """API endpoint pour récupérer les cours attribués à un enseignant"""
    try:
        teacher = Teacher.objects.get(id=teacher_id)
        
        # Récupérer les cours attribués à cet enseignant via le modèle Attribution
        attributions = Attribution.objects.filter(matricule=teacher).select_related('code_ue')
        
        courses_data = []
        for attribution in attributions:
            if attribution.code_ue:
                courses_data.append({
                    'id': attribution.code_ue.id,
                    'code_ue': attribution.code_ue.code_ue,
                    'intitule_ue': attribution.code_ue.intitule_ue,
                    'display_name': f"{attribution.code_ue.code_ue} - {attribution.code_ue.intitule_ue}"
                })
        
        return JsonResponse({
            'success': True,
            'courses': courses_data
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Enseignant non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def dashboard_pdf_view(request):
    """Vue pour générer le PDF du rapport de suivi des enseignements avec filtres"""
    
    # Récupérer les paramètres de filtrage
    semester_filter = request.GET.get('semester_filter', 'all')
    charge_type_filter = request.GET.get('charge_type_filter', 'all')
    class_semester_filter = request.GET.get('class_semester_filter', 'all')
    semaine_date_debut = request.GET.get('semaine_date_debut', '')
    type_semestre = request.GET.get('type_semestre', '')
    
    # Année académique actuelle
    current_year = timezone.now().year
    academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
    
    # Heures effectuées (total de tous les enregistrements)
    total_hours_done = TeachingProgress.objects.aggregate(total=Sum('hours_done'))['total'] or 0
    
    # Heures allouées (basé sur les charges des enseignants)
    total_hours_allocated = Attribution.objects.select_related('code_ue').filter(
        code_ue__isnull=False
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('code_ue__cmi') + F('code_ue__td_tp'),
                output_field=FloatField()
            )
        )
    )['total'] or 0
    
    # Calcul du pourcentage
    global_progress_percentage = 0
    if total_hours_allocated > 0:
        global_progress_percentage = (float(total_hours_done) / float(total_hours_allocated)) * 100
    
    # Statistiques pour le rapport  
    from reglage.models import SemaineCours
    stats = {
        'current_week': SemaineCours.objects.filter(est_en_cours=True, annee_academique=academic_year).first(),
        'total_hours_done': total_hours_done,
        'total_hours_allocated': total_hours_allocated,
        'global_progress_percentage': round(global_progress_percentage, 1),
        'total_courses': Course.objects.count(),
        'total_teachers': Teacher.objects.count(),
    }
    
    # Progression des cours groupés par département avec filtrage
    course_progress_filter = {'week__annee_academique': academic_year}
    
    # Ajouter le filtre par semaine si spécifié
    if semaine_date_debut:
        course_progress_filter['week__date_debut'] = semaine_date_debut
    
    # Ajouter le filtre par type de semestre (impair/pair)
    if type_semestre == 'impair':
        course_progress_filter['course__semestre__in'] = ['S1', 'S3', 'S5', 'S7']
    elif type_semestre == 'pair':
        course_progress_filter['course__semestre__in'] = ['S2', 'S4', 'S6', 'S8']
    
    course_progress_query = TeachingProgress.objects.filter(
        **course_progress_filter
    ).select_related('course').values(
        'course__code_ue',
        'course__intitule_ue',
        'course__intitule_ec',
        'course__classe',
        'course__semestre',
        'course__departement',
        'course__cmi',
        'course__td_tp',
        'course__id'
    ).annotate(
        total_hours_done=Sum('hours_done'),
        total_volume=ExpressionWrapper(
            F('course__cmi') + F('course__td_tp'),
            output_field=FloatField()
        ),
        progression_percentage=Case(
            When(total_volume__gt=0, then=(F('total_hours_done') * 100.0) / F('total_volume')),
            default=Value(0),
            output_field=FloatField()
        )
    ).order_by('course__departement', 'course__code_ue')
    
    # Appliquer le filtre de semestre pour les cours
    course_progress = []
    for course in course_progress_query:
        semester = course['course__semestre']
        if semester:
            semester_match = re.search(r'S(\d+)', semester)
            if semester_match:
                semester_number = int(semester_match.group(1))
                if semester_filter == 'all':
                    course_progress.append(course)
                elif semester_filter == 'odd' and semester_number % 2 == 1:
                    course_progress.append(course)
                elif semester_filter == 'even' and semester_number % 2 == 0:
                    course_progress.append(course)
    
    # Grouper les cours par département puis par semestre avec statistiques
    courses_by_department = {}
    for course in course_progress:
        department = course.get('course__departement', 'Non spécifié')
        if not department:
            department = 'Non spécifié'
        semester = course.get('course__semestre', 'Non spécifié')
        
        if department not in courses_by_department:
            courses_by_department[department] = {
                'semesters': {},
                'total_hours': 0,
                'course_count': 0
            }
        
        if semester not in courses_by_department[department]['semesters']:
            courses_by_department[department]['semesters'][semester] = {
                'courses': [],
                'total_hours': 0,
                'course_count': 0
            }
        
        courses_by_department[department]['semesters'][semester]['courses'].append(course)
        courses_by_department[department]['semesters'][semester]['total_hours'] += float(course.get('total_hours_done', 0) or 0)
        courses_by_department[department]['semesters'][semester]['course_count'] += 1
        courses_by_department[department]['total_hours'] += float(course.get('total_hours_done', 0) or 0)
        courses_by_department[department]['course_count'] += 1
    
    # Progression des enseignants
    teacher_progress = []
    
    # Filtrer les enseignants avec le filtre de semaine et type semestre
    teacher_progress_filter = {'week__annee_academique': academic_year}
    if semaine_date_debut:
        teacher_progress_filter['week__date_debut'] = semaine_date_debut
    if type_semestre == 'impair':
        teacher_progress_filter['course__semestre__in'] = ['S1', 'S3', 'S5', 'S7']
    elif type_semestre == 'pair':
        teacher_progress_filter['course__semestre__in'] = ['S2', 'S4', 'S6', 'S8']
    
    teacher_charge_combinations = Attribution.objects.filter(
        matricule__matricule__in=TeachingProgress.objects.filter(
            **teacher_progress_filter
        ).values_list('teacher__matricule', flat=True).distinct()
    ).values('matricule__matricule', 'matricule__nom_complet', 'type_charge').distinct()
    
    for combination in teacher_charge_combinations:
        teacher_matricule = combination['matricule__matricule']
        teacher_name = combination['matricule__nom_complet']
        charge_type = combination['type_charge']
        
        if not charge_type:
            continue
        
        # Appliquer le filtre de type de charge
        if charge_type_filter != 'all' and charge_type != charge_type_filter:
            continue
            
        courses_for_charge = Attribution.objects.filter(
            matricule__matricule=teacher_matricule,
            type_charge=charge_type
        ).values_list('code_ue__id', flat=True)
        
        # Appliquer le filtre par semaine et type semestre aux heures effectuées
        teacher_hours_filter = {
            'teacher__matricule': teacher_matricule,
            'week__annee_academique': academic_year,
            'course__id__in': courses_for_charge
        }
        if semaine_date_debut:
            teacher_hours_filter['week__date_debut'] = semaine_date_debut
        if type_semestre == 'impair':
            teacher_hours_filter['course__semestre__in'] = ['S1', 'S3', 'S5', 'S7']
        elif type_semestre == 'pair':
            teacher_hours_filter['course__semestre__in'] = ['S2', 'S4', 'S6', 'S8']
        
        hours_done_for_charge = TeachingProgress.objects.filter(
            **teacher_hours_filter
        ).aggregate(total=Sum('hours_done'))['total'] or 0
        
        hours_allocated_for_charge = Course.objects.filter(
            id__in=courses_for_charge
        ).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('cmi') + F('td_tp'),
                    output_field=FloatField()
                )
            )
        )['total'] or 0
        
        progression_percentage = 0
        if hours_allocated_for_charge > 0:
            progression_percentage = (float(hours_done_for_charge) * 100.0) / float(hours_allocated_for_charge)
        
        teacher_progress.append({
            'teacher__nom_complet': teacher_name,
            'teacher__matricule': teacher_matricule,
            'type_charge': charge_type.capitalize(),
            'total_hours_done': hours_done_for_charge,
            'total_hours_allocated': hours_allocated_for_charge,
            'progression_percentage': progression_percentage,
            'hours_display': f"{hours_done_for_charge}/{hours_allocated_for_charge}"
        })
    
    teacher_progress.sort(key=lambda x: (x['teacher__nom_complet'], x['type_charge']))
    
    # Chemin absolu pour les images dans le PDF
    from django.conf import settings
    import os
    static_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    
    # Récupérer l'enseignant CSAE sélectionné avec la désignation de sa section
    csae_teacher = None
    csae_section_designation = None
    csae_id = request.GET.get('csae_id')
    if csae_id:
        try:
            csae_teacher = Teacher.objects.get(id=csae_id)
            # Récupérer la désignation complète de la section
            if csae_teacher.departement:
                from reglage.models import Departement
                try:
                    dept = Departement.objects.get(CodeDept=csae_teacher.departement)
                    csae_section_designation = dept.section.DesignationSection
                except Departement.DoesNotExist:
                    pass
        except Teacher.DoesNotExist:
            pass
    
    # Récupérer la semaine sélectionnée
    selected_week = None
    if semaine_date_debut:
        try:
            from datetime import datetime
            date_debut = datetime.strptime(semaine_date_debut, '%Y-%m-%d').date()
            selected_week = SemaineCours.objects.get(date_debut=date_debut, annee_academique=academic_year)
        except (SemaineCours.DoesNotExist, ValueError):
            pass
    
    context = {
        'stats': stats,
        'courses_by_department': courses_by_department,
        'teacher_progress': teacher_progress,
        'academic_year': academic_year,
        'current_date': timezone.now(),
        'static_root': settings.BASE_DIR,
        'entete_path': static_path,
        'csae_teacher': csae_teacher,
        'csae_section_designation': csae_section_designation,
        'selected_week': selected_week,
    }
    
    # Générer le PDF
    template = get_template('tracking/dashboard_pdf.html')
    html = template.render(context)
    
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="rapport_suivi_enseignements_{academic_year}.pdf"'
        return response
    
    return HttpResponse('Erreur lors de la génération du PDF', status=500)


@user_passes_test(lambda u: u.is_superuser, login_url='/admin/login/')
def action_history_view(request):
    """Vue pour afficher l'historique des actions (réservé aux administrateurs)"""
    # Enregistrer la consultation de l'historique
    ActionLog.log_action(
        user=request.user,
        action_type='view',
        description="Consultation de l'historique des actions",
        model_name='ActionLog',
        request=request
    )
    
    # Récupérer tous les logs
    logs = ActionLog.objects.all().select_related('user')
    
    # Filtres
    action_type = request.GET.get('action_type')
    username = request.GET.get('username')
    model_name = request.GET.get('model_name')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    if username:
        logs = logs.filter(username__icontains=username)
    
    if model_name:
        logs = logs.filter(model_name__icontains=model_name)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except ValueError:
            pass
    
    if search:
        logs = logs.filter(description__icontains=search)
    
    # Statistiques
    stats = {
        'total_actions': logs.count(),
        'actions_today': logs.filter(timestamp__date=timezone.now().date()).count(),
        'actions_this_week': logs.filter(timestamp__gte=timezone.now() - timedelta(days=7)).count(),
        'unique_users': logs.values('username').distinct().count(),
        'actions_by_type': logs.values('action_type').annotate(count=Count('id')).order_by('-count')
    }
    
    # Pagination
    paginator = Paginator(logs, 50)  # 50 actions par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Liste des types d'actions pour le filtre
    action_types = ActionLog.ACTION_TYPES
    
    # Liste des utilisateurs uniques
    unique_users = ActionLog.objects.values_list('username', flat=True).distinct().order_by('username')
    
    # Liste des modèles uniques
    unique_models = ActionLog.objects.exclude(model_name__isnull=True).values_list('model_name', flat=True).distinct().order_by('model_name')
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'action_types': action_types,
        'unique_users': unique_users,
        'unique_models': unique_models,
        'filters': {
            'action_type': action_type,
            'username': username,
            'model_name': model_name,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'tracking/action_history.html', context)
