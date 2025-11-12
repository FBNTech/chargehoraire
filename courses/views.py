from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from accounts.models import Role
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from .models import Course
from .forms import CourseForm
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

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        queryset = Course.objects.all()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(code_ue__icontains=search_query) |
                Q(intitule_ue__icontains=search_query) |
                Q(intitule_ec__icontains=search_query) |
                Q(classe__icontains=search_query) |
                Q(semestre__icontains=search_query) |
                Q(departement__icontains=search_query)
            )
        return queryset

class CourseCreateView(UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:list')

    def form_invalid(self, form):
        logger.error(f"Erreurs de validation du formulaire: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Erreur dans le champ {field}: {error}")
        return super().form_invalid(form)

    def form_valid(self, form):
        logger.info("Formulaire valide, sauvegarde du cours...")
        messages.success(self.request, 'Cours ajouté avec succès!')
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_staff or
            user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists()
        )

class CourseUpdateView(UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:list')

    def form_invalid(self, form):
        logger.error(f"Erreurs de validation du formulaire: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Erreur dans le champ {field}: {error}")
        return super().form_invalid(form)

    def form_valid(self, form):
        logger.info("Formulaire valide, mise à jour du cours...")
        messages.success(self.request, 'Cours modifié avec succès!')
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_staff or
            user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists()
        )

class CourseDeleteView(UserPassesTestMixin, DeleteView):
    model = Course
    success_url = reverse_lazy('courses:list')
    template_name = 'courses/course_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        course_name = course.code_ue + ' - ' + course.intitule_ue
        
        try:
            # Utiliser une transaction atomique pour garantir la cohérence
            with transaction.atomic():
                # Verrouiller le cours pour éviter les conflits concurrents
                course = Course.objects.select_for_update().get(pk=course.pk)
                
                # IMPORTANT: Supprimer MANUELLEMENT les objets liés pour éviter les problèmes SQLite CASCADE
                # 1. D'abord les horaires liés aux attributions de ce cours
                from attribution.models import Attribution, ScheduleEntry
                
                attributions = Attribution.objects.filter(code_ue=course)
                for attribution in attributions:
                    # Supprimer les horaires de cette attribution
                    ScheduleEntry.objects.filter(attribution=attribution).delete()
                
                # 2. Ensuite les attributions de ce cours
                attributions_count = attributions.count()
                attributions.delete()
                
                # 3. Enfin le cours lui-même
                course.delete()
            
            message = f"Le cours {course_name} a été supprimé avec succès."
            if attributions_count > 0:
                message += f" ({attributions_count} attribution(s) supprimée(s))"
            
            messages.success(request, message)
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('courses:list')

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_staff or
            user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists()
        )

@csrf_exempt
def import_excel(request):
    # Restreindre l'import aux administrateurs/gestionnaires
    user = request.user
    if not (user.is_authenticated and (user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        return JsonResponse({'error': "Permission refusée"}, status=403)

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
            required_columns = ['code_ue', 'intitule_ue', 'intitule_ec', 'credit', 'cmi', 'td_tp', 'classe', 'semestre', 'departement']
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
                    course_data = {
                        'code_ue': str(row['code_ue']).strip(),
                        'intitule_ue': str(row['intitule_ue']).strip(),
                        'intitule_ec': str(row['intitule_ec']).strip(),
                        'credit': int(row['credit']),
                        'cmi': int(row['cmi']),
                        'td_tp': int(row['td_tp']),
                        'classe': str(row['classe']).strip(),
                        'semestre': str(row['semestre']).strip(),
                        'departement': str(row['departement']).strip()
                    }

                    Course.objects.update_or_create(
                        code_ue=course_data['code_ue'],
                        defaults=course_data
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
                    'message': f"{end_index} cours importés avec succès!"
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

def import_courses(request):
    """Importe des cours à partir d'un fichier Excel."""
    # Restreindre l'import aux administrateurs/gestionnaires
    user = request.user
    if not (user.is_authenticated and (user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        messages.error(request, "Permission refusée")
        return redirect('courses:list')

    if request.method == 'POST' and 'file' in request.FILES:
        session_id = request.POST.get('session_id', None)
        try:
            file = request.FILES['file']
            df = pd.read_excel(file)
            
            # Normaliser les noms de colonnes
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Vérifier les colonnes requises
            required_columns = ['code_ue', 'intitule_ue', 'intitule_ec', 'credit', 'cmi', 'td_tp', 'classe', 'semestre', 'departement']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, f'Colonnes manquantes dans le fichier: {", ".join(missing_columns)}')
                return redirect('courses:list')
            
            # Compter les cours ajoutés et ignorés
            added = 0
            skipped = 0
            total = len(df)
            
            # Initialiser la progression dans la session si session_id existe
            if session_id:
                request.session[f'import_progress_{session_id}'] = {
                    'status': 'processing',
                    'total': total,
                    'current': 0,
                    'added': 0,
                    'skipped': 0
                }
                request.session.save()
            
            for index, row in df.iterrows():
                try:
                    # Vérifier que les champs obligatoires ne sont pas vides
                    if pd.isna(row['code_ue']) or pd.isna(row['intitule_ue']):
                        skipped += 1
                        # Mettre à jour la progression pour les lignes ignorées
                        if session_id and ((index + 1) % 5 == 0 or (index + 1) == total):
                            request.session[f'import_progress_{session_id}'] = {
                                'status': 'processing',
                                'total': total,
                                'current': index + 1,
                                'added': added,
                                'skipped': skipped
                            }
                            request.session.save()
                        continue
                    
                    course_data = {
                        'code_ue': str(row['code_ue']).strip(),
                        'intitule_ue': str(row['intitule_ue']).strip(),
                        'intitule_ec': str(row['intitule_ec']).strip() if pd.notna(row['intitule_ec']) else '',
                        'credit': float(row['credit']) if pd.notna(row['credit']) else 0,
                        'cmi': float(row['cmi']) if pd.notna(row['cmi']) else 0,
                        'td_tp': float(row['td_tp']) if pd.notna(row['td_tp']) else 0,
                        'classe': str(row['classe']).strip() if pd.notna(row['classe']) else '',
                        'semestre': str(row['semestre']).strip() if pd.notna(row['semestre']) else '',
                        'departement': str(row['departement']).strip() if pd.notna(row['departement']) else ''
                    }
                except Exception as e:
                    skipped += 1
                    # Mettre à jour la progression pour les erreurs
                    if session_id and ((index + 1) % 5 == 0 or (index + 1) == total):
                        request.session[f'import_progress_{session_id}'] = {
                            'status': 'processing',
                            'total': total,
                            'current': index + 1,
                            'added': added,
                            'skipped': skipped
                        }
                        request.session.save()
                    continue
                
                # Gérer la section (optionnelle dans le fichier Excel)
                if 'section' in df.columns and pd.notna(row['section']):
                    course_data['section'] = str(row['section']).strip()
                else:
                    # Récupérer automatiquement la section du département
                    dept_code = course_data['departement']
                    try:
                        dept = Departement.objects.get(CodeDept=dept_code)
                        course_data['section'] = dept.section.CodeSection
                    except:
                        course_data['section'] = None
                
                # Créer le cours (même si le code_ue existe déjà)
                course = Course.objects.create(**course_data)
                added += 1
                
                # Mettre à jour la progression dans la session
                if session_id:
                    # Mettre à jour toutes les 5 lignes ou sur la dernière ligne
                    if (index + 1) % 5 == 0 or (index + 1) == total:
                        request.session[f'import_progress_{session_id}'] = {
                            'status': 'processing',
                            'total': total,
                            'current': index + 1,
                            'added': added,
                            'skipped': skipped
                        }
                        request.session.save()
            
            # Finaliser la progression
            if session_id:
                request.session[f'import_progress_{session_id}'] = {
                    'status': 'completed',
                    'total': total,
                    'current': total,
                    'added': added,
                    'skipped': skipped
                }
                request.session.save()
            
            # Message de résumé
            summary_parts = [f'{added} cours ajoutés']
            if skipped > 0:
                summary_parts.append(f'{skipped} lignes ignorées')
            messages.success(request, f'✅ Import terminé : {", ".join(summary_parts)}.')
        
        except Exception as e:
            # Marquer la progression comme erreur
            if session_id:
                request.session[f'import_progress_{session_id}'] = {
                    'status': 'error',
                    'message': str(e)
                }
                request.session.save()
            messages.error(request, f'Erreur lors de l\'import : {str(e)}')
        
        return redirect('courses:list')
    
    return render(request, 'courses/course_list.html')

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

def import_progress(request):
    """Retourne la progression de l'importation"""
    session_id = request.GET.get('session_id', None)
    
    if not session_id:
        return JsonResponse({'error': 'Session ID manquant'}, status=400)
    
    progress_key = f'import_progress_{session_id}'
    progress_data = request.session.get(progress_key, None)
    
    if not progress_data:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Session de progression non trouvée'
        })
    
    return JsonResponse(progress_data)

def delete_all_courses(request):
    """Supprime tous les cours de la base de données"""
    from django.db import connection
    
    # Vérifier les permissions
    user = request.user
    if not (user.is_authenticated and (user.is_staff or user.profile.roles.filter(name__in=[Role.ADMIN, Role.GESTIONNAIRE]).exists())):
        messages.error(request, 'Permission refusée. Vous n\'avez pas les droits pour supprimer tous les cours.')
        return redirect('courses:list')
    
    try:
        # Compter le nombre de cours avant suppression
        count = Course.objects.count()
        
        # Désactiver temporairement les contraintes de clés étrangères pour SQLite
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')
        
        try:
            # Supprimer tous les cours
            Course.objects.all().delete()
            
            messages.success(request, f'✅ {count} cours ont été supprimés avec succès.')
        finally:
            # Réactiver les contraintes de clés étrangères
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')
        
    except Exception as e:
        messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')
    
    return redirect('courses:list')
