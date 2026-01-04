from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from accounts.models import Role
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from .models import Teacher
from .forms import TeacherForm
import pandas as pd
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from reglage.models import Departement
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Create your views here.

class TeacherListView(ListView):
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'
    
    def get_queryset(self):
        from accounts.organisation_utils import filter_queryset_by_organisation
        
        queryset = Teacher.objects.all()
        
        # Filtrer par organisation de l'utilisateur (via section)
        queryset = filter_queryset_by_organisation(queryset, self.request.user, field_name='section')
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(matricule__icontains=search_query) |
                Q(nom_complet__icontains=search_query) |
                Q(fonction__icontains=search_query) |
                Q(grade__icontains=search_query) |
                Q(categorie__icontains=search_query) |
                Q(departement__icontains=search_query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        from accounts.organisation_utils import filter_queryset_by_organisation
        
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales (filtrées par organisation)
        filtered_teachers = filter_queryset_by_organisation(Teacher.objects, self.request.user, field_name='section')
        context['total_teachers'] = filtered_teachers.count()
        
        # Statistiques par grade (filtrées)
        grades = filtered_teachers.values_list('grade', flat=True).distinct()
        context['stats_by_grade'] = {grade: filtered_teachers.filter(grade=grade).count() for grade in grades}
        
        return context

class TeacherCreateView(UserPassesTestMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teachers:list')

    def form_valid(self, form):
        from accounts.organisation_utils import get_user_organisation
        
        # Assigner automatiquement la section de l'organisation de l'utilisateur
        user_org = get_user_organisation(self.request.user)
        if user_org:
            form.instance.section = user_org.code
        messages.success(self.request, 'Enseignant ajouté avec succès!')
        return super().form_valid(form)

    def test_func(self):
        from accounts.organisation_utils import is_org_user
        user = self.request.user
        return user.is_authenticated and (
            user.is_staff or
            is_org_user(user) or
            user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists()
        )

class TeacherUpdateView(UserPassesTestMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teachers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Enseignant modifié avec succès!')
        return super().form_valid(form)

    def test_func(self):
        from accounts.organisation_utils import get_user_organisation, is_org_user
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Admin global peut tout modifier
        if user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists():
            return True
        # Utilisateur d'organisation ne peut modifier que ses enseignants
        user_org = get_user_organisation(user)
        if user_org and is_org_user(user):
            teacher = self.get_object()
            return teacher.section == user_org.code
        return False

class TeacherDeleteView(UserPassesTestMixin, DeleteView):
    model = Teacher
    success_url = reverse_lazy('teachers:list')
    template_name = 'teachers/teacher_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        teacher = self.get_object()
        teacher_name = teacher.nom_complet
        
        try:
            # Utiliser une transaction atomique pour garantir la cohérence
            with transaction.atomic():
                # Verrouiller l'enseignant pour éviter les conflits concurrents
                teacher = Teacher.objects.select_for_update().get(pk=teacher.pk)
                
                # IMPORTANT: Supprimer MANUELLEMENT les objets liés pour éviter les problèmes SQLite CASCADE
                # 1. D'abord les horaires liés aux attributions de cet enseignant
                from attribution.models import Attribution, ScheduleEntry
                
                attributions = Attribution.objects.filter(matricule=teacher.matricule)
                for attribution in attributions:
                    # Supprimer les horaires de cette attribution
                    ScheduleEntry.objects.filter(attribution=attribution).delete()
                
                # 2. Ensuite les attributions de cet enseignant
                attributions_count = attributions.count()
                attributions.delete()
                
                # 3. Enfin l'enseignant lui-même
                teacher.delete()
            
            message = f"L'enseignant {teacher_name} a été supprimé avec succès."
            if attributions_count > 0:
                message += f" ({attributions_count} attribution(s) supprimée(s))"
            
            messages.success(request, message)
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('teachers:list')

    def test_func(self):
        from accounts.organisation_utils import get_user_organisation, is_org_user
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Admin global peut tout supprimer
        if user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists():
            return True
        # Utilisateur d'organisation ne peut supprimer que ses enseignants
        user_org = get_user_organisation(user)
        if user_org and is_org_user(user):
            teacher = self.get_object()
            return teacher.section == user_org.code
        return False

@csrf_exempt
def import_excel(request):
    # Restreindre l'import aux administrateurs/gestionnaires et utilisateurs d'organisation
    from accounts.organisation_utils import get_user_organisation, is_org_user
    user = request.user
    user_org = get_user_organisation(user)
    if not (user.is_authenticated and (user.is_staff or is_org_user(user) or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                return JsonResponse({'error': 'Aucun fichier sélectionné'}, status=400)

            # Créer un dossier temporaire s'il n'existe pas
            temp_dir = os.path.join(tempfile.gettempdir(), 'excel_imports')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Sauvegarder le fichier temporairement
            temp_path = os.path.join(temp_dir, excel_file.name)
            with open(temp_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            # Lire le fichier Excel
            df = pd.read_excel(temp_path)
            
            # Normaliser les noms de colonnes
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Vérifier les colonnes requises
            required_columns = ['matricule', 'nom_complet', 'fonction', 'grade', 'section', 'categorie', 'departement']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                os.remove(temp_path)  # Nettoyer le fichier temporaire
                return JsonResponse({
                    'error': f'Colonnes manquantes : {", ".join(missing_columns)}'
                }, status=400)

            # Envoyer le nombre total de lignes et le chemin du fichier
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'total': len(df),
                    'status': 'starting',
                    'temp_file': temp_path
                })

        except Exception as e:
            # Nettoyer en cas d'erreur
            if 'temp_path' in locals():
                os.remove(temp_path)
            return JsonResponse({
                'error': f"Erreur lors de l'import: {str(e)}"
            }, status=500)

    elif request.method == 'GET' and request.headers.get('X-Progress'):
        try:
            current_progress = int(request.GET.get('current', 0))
            total = int(request.GET.get('total', 0))
            temp_path = request.GET.get('temp_file')
            
            if not temp_path or not os.path.exists(temp_path) or current_progress >= total:
                return JsonResponse({'error': 'Fichier temporaire non trouvé ou paramètres invalides'}, status=400)

            # Lire le fichier Excel
            df = pd.read_excel(temp_path)
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Traiter le prochain lot de lignes (5 lignes à la fois)
            batch_size = 5
            end_index = min(current_progress + batch_size, total)
            
            for index in range(current_progress, end_index):
                row = df.iloc[index]
                try:
                    teacher_data = {
                        'matricule': str(row['matricule']).strip(),
                        'nom_complet': str(row['nom_complet']).strip(),
                        'fonction': str(row['fonction']).strip(),
                        'grade': str(row['grade']).strip(),
                        'categorie': str(row['categorie']).strip(),
                        'departement': str(row['departement']).strip()
                    }
                    
                    # Assigner automatiquement la section de l'organisation
                    if user_org:
                        teacher_data['section'] = user_org.code

                    Teacher.objects.update_or_create(
                        matricule=teacher_data['matricule'],
                        defaults=teacher_data
                    )

                except Exception as e:
                    # Nettoyer en cas d'erreur
                    os.remove(temp_path)
                    return JsonResponse({
                        'error': f"Erreur à la ligne {index + 1}: {str(e)}"
                    }, status=500)

            progress = (end_index / total) * 100
            
            # Si c'est la dernière itération, supprimer le fichier temporaire
            if end_index >= total:
                os.remove(temp_path)
                return JsonResponse({
                    'current': end_index,
                    'total': total,
                    'progress': 100,
                    'status': 'completed',
                    'message': f"{end_index} enseignants importés avec succès!"
                })
            
            return JsonResponse({
                'current': end_index,
                'total': total,
                'progress': progress,
                'status': 'processing',
                'temp_file': temp_path
            })

        except Exception as e:
            # Nettoyer en cas d'erreur
            if 'temp_path' in locals():
                os.remove(temp_path)
            return JsonResponse({
                'error': f"Erreur lors du traitement: {str(e)}"
            }, status=500)

def import_teachers(request):
    """Importe des enseignants à partir d'un fichier Excel."""
    # Restreindre l'import aux administrateurs/gestionnaires
    user = request.user
    if not (user.is_authenticated and (user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        messages.error(request, 'Permission refusée')
        return redirect('teachers:list')

    if request.method == 'POST' and 'file' in request.FILES:
        try:
            file = request.FILES['file']
            df = pd.read_excel(file)
            
            # Normaliser les noms de colonnes
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Vérifier les colonnes requises
            required_columns = ['matricule', 'nom_complet', 'fonction', 'grade', 'section', 'categorie', 'departement']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, f'Colonnes manquantes dans le fichier: {", ".join(missing_columns)}')
                return redirect('teachers:list')
            
            # Compter les enseignants ajoutés ou mis à jour
            added = 0
            updated = 0
            
            for _, row in df.iterrows():
                teacher_data = {
                    'matricule': str(row['matricule']).strip(),
                    'nom_complet': str(row['nom_complet']).strip(),
                    'fonction': str(row['fonction']).strip(),
                    'grade': str(row['grade']).strip(),
                    'section': str(row['section']).strip(),
                    'categorie': str(row['categorie']).strip(),
                    'departement': str(row['departement']).strip()
                }
                
                # Mettre à jour ou créer l'enseignant
                teacher, created = Teacher.objects.update_or_create(
                    matricule=teacher_data['matricule'],
                    defaults=teacher_data
                )
                
                if created:
                    added += 1
                else:
                    updated += 1
            
            messages.success(request, f'Import terminé : {added} enseignants ajoutés, {updated} enseignants mis à jour.')
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'import : {str(e)}')
        
        return redirect('teachers:list')
    
    return render(request, 'teachers/teacher_list.html')

def delete_all_teachers(request):
    """Supprime tous les enseignants de la base de données"""
    from django.db import connection
    
    # Vérifier les permissions
    user = request.user
    if not (user.is_authenticated and (user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        messages.error(request, 'Permission refusée. Vous n\'avez pas les droits pour supprimer tous les enseignants.')
        return redirect('teachers:list')
    
    try:
        # Compter le nombre d'enseignants avant suppression
        count = Teacher.objects.count()
        
        # Désactiver temporairement les contraintes de clés étrangères pour SQLite
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')
        
        try:
            # Supprimer tous les enseignants
            Teacher.objects.all().delete()
            
            messages.success(request, f'✅ {count} enseignant(s) ont été supprimé(s) avec succès.')
        finally:
            # Réactiver les contraintes de clés étrangères
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')
        
    except Exception as e:
        messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')
    
    return redirect('teachers:list')

def get_section_by_departement(request):
    """Retourne la section associée à un département donné"""
    departement_code = request.GET.get('departement')
    
    if not departement_code:
        return JsonResponse({'error': 'Code département manquant'}, status=400)
    
    try:
        dept = Departement.objects.get(CodeDept=departement_code)
        return JsonResponse({
            'section_code': dept.section.CodeSection,
            'section_designation': dept.section.DesignationSection
        })
    except Departement.DoesNotExist:
        return JsonResponse({'error': 'Département non trouvé'}, status=404)
