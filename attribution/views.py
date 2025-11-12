from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import AttributionForm, ScheduleEntryForm
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.conf import settings
from PIL import Image as PILImage, ImageDraw
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/images'))
from static.images.header import create_header_table
from .models import Cours_Attribution, Course, Teacher, Attribution, ScheduleEntry
from reglage.models import Grade, Departement, Section, AnneeAcademique
from django.db import transaction
from datetime import datetime
import json
import traceback

# Configuration de wkhtmltopdf
# config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

def attribution_list(request):
    teachers = Teacher.objects.all().order_by('nom_complet')
    cours_attributions = Cours_Attribution.objects.all().order_by('code_ue')
    courses = Course.objects.all().order_by('code_ue')
    
    # Récupérer la liste unique des départements
    departements = Cours_Attribution.objects.values_list('departement', flat=True).distinct().order_by('departement')
    
    # Récupérer l'année académique en cours depuis le modèle AnneeAcademique
    annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
    if annee_courante:
        academic_year = annee_courante.code
    else:
        # Fallback si aucune année en cours n'est définie
        current_year = datetime.now().year
        next_year = current_year + 1
        academic_year = f"{current_year}-{next_year}"
    
    # Créer la liste des éléments à ajouter au document
    elements = []
    
    # Ajouter l'en-tête institutionnelle
    header = create_header_table()
    elements.append(header)
    elements.append(Spacer(1, 10))
    
    # Calculer les totaux pour le tableau de bord
    total_cmi = sum(float(cours.cmi or 0) for cours in cours_attributions)
    total_td_tp = sum(float(cours.td_tp or 0) for cours in cours_attributions)
    total_combined = total_cmi + total_td_tp
    total_courses = cours_attributions.count()
    
    # Calculer le nombre d'enseignants qui ont une charge (attribution)
    teachers_with_assignments = Attribution.objects.values('matricule').distinct().count()
    
    context = {
        'teachers': teachers,
        'courses': courses,
        'available_courses': cours_attributions,
        'departements': departements,
        'academic_year': academic_year,
        'total_cmi': total_cmi,
        'total_td_tp': total_td_tp,
        'total_combined': total_combined,
        'total_courses': total_courses,
        'teachers_with_assignments': teachers_with_assignments,
    }
    return render(request, 'attribution/attribution_list.html', context)

@require_http_methods(['GET'])
def get_teacher_info(request):
    teacher_id = request.GET.get('teacher_id')
    try:
        teacher = Teacher.objects.get(id=teacher_id)
        return JsonResponse({
            'matricule': teacher.matricule,
            'grade': teacher.grade
        })
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Enseignant non trouvé'}, status=404)

@require_http_methods(['POST'])
def add_course_attribution(request):
    try:
        code_ue = request.POST.get('code_ue')
        if not code_ue:
            messages.error(request, 'Le code UE est requis')
            return redirect('attribution:attribution_list')
        
        # Chercher le cours dans la table Course
        course = Course.objects.filter(code_ue=code_ue).first()
        
        if not course:
            messages.error(request, f'Le cours {code_ue} n\'existe pas dans la table des cours')
            return redirect('attribution:attribution_list')
        
        # Créer une nouvelle entrée dans la table Cours_Attribution
        Cours_Attribution.objects.create(
            code_ue=course.code_ue,
            intitule_ue=course.intitule_ue,
            intitule_ec=course.intitule_ec,
            credit=course.credit,
            cmi=course.cmi,
            td_tp=course.td_tp,
            classe=course.classe,
            semestre=course.semestre,
            departement=course.departement
        )
        
        messages.success(request, f'Le cours {code_ue} a été ajouté avec succès')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'ajout du cours : {str(e)}')
    
    return redirect('attribution:attribution_list')

@require_http_methods(['POST'])
def delete_course(request, course_id):
    try:
        # Utiliser une transaction atomique pour garantir la cohérence
        with transaction.atomic():
            course = Cours_Attribution.objects.select_for_update().get(id=course_id)
            code_ue = course.code_ue
            
            # Supprimer le cours (les contraintes FK CASCADE s'occuperont des relations)
            course.delete()
        
        messages.success(request, f'Le cours {code_ue} a été supprimé avec succès')
    except Cours_Attribution.DoesNotExist:
        messages.error(request, "Le cours n'existe pas")
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
    
    return redirect('attribution:attribution_list')

@require_http_methods(['POST'])
def migrate_courses(request):
    try:
        with transaction.atomic():
            # Supprimer tous les cours existants dans Cours_Attribution
            Cours_Attribution.objects.all().delete()
            
            # Migrer tous les cours de Course vers Cours_Attribution
            courses = Course.objects.all()
            count = 0
            
            for course in courses:
                # Créer tous les cours (même avec des code_ue en double)
                Cours_Attribution.objects.create(
                    code_ue=course.code_ue,
                    intitule_ue=course.intitule_ue,
                    intitule_ec=course.intitule_ec or '',
                    credit=int(course.credit) if course.credit else 0,
                    cmi=float(course.cmi) if course.cmi else 0,
                    td_tp=float(course.td_tp) if course.td_tp else 0,
                    classe=course.classe,
                    semestre=course.semestre,
                    departement=course.departement,
                    section=course.section or ''
                )
                count += 1
            
            messages.success(request, f'{count} cours ont été migrés avec succès depuis la table Course')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la migration : {str(e)}')
    
    return redirect('attribution:attribution_list')

@require_http_methods(['POST'])
def vider_cours(request):
    try:
        count = Cours_Attribution.objects.count()
        Cours_Attribution.objects.all().delete()
        messages.success(request, f'{count} cours ont été supprimés avec succès')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
    return redirect('attribution:attribution_list')

@require_http_methods(['GET'])
def search_attributions(request):
    matricule = request.GET.get('teacher_matricule')
    annee_academique = request.GET.get('teacher_academic_year')
    type_charge = request.GET.get('type_charge')

    print(f"Débogage recherche - Matricule: {matricule}, Année: {annee_academique}, Type: {type_charge}")

    # Requête de jointure entre Teacher, Attribution et Cours_Attribution
    # Rendre la recherche plus flexible
    attributions = Attribution.objects.all()
    if matricule:
        attributions = attributions.filter(matricule__matricule=matricule)
    if annee_academique:
        attributions = attributions.filter(annee_academique=annee_academique)
    if type_charge:
        attributions = attributions.filter(type_charge=type_charge)
    
    attributions = attributions.select_related('matricule', 'code_ue')

    print(f"Nombre d'attributions trouvées : {attributions.count()}")
    for attr in attributions:
        print(f"Attribution: {attr.matricule.nom_complet}, {attr.code_ue.code_ue}, {attr.type_charge}")

    # Préparer le contexte pour le template
    context = {
        'attributions': attributions,
        'selected_teacher_name': attributions.first().matricule.nom_complet if attributions.exists() else '',
        'selected_year': annee_academique,
        'selected_type': type_charge,
        'teachers': Teacher.objects.all().order_by('nom_complet'),
        'academic_years': list(set(Attribution.objects.values_list('annee_academique', flat=True))),
    }

    return render(request, 'attribution/liste_attributions.html', context)

@require_http_methods(['GET'])
def get_filtered_courses(request):
    departement = request.GET.get('departement')
    semestre = request.GET.get('semestre')
    
    courses = Cours_Attribution.objects.all()
    
    if departement:
        courses = courses.filter(departement=departement)
    if semestre:
        courses = courses.filter(semestre=semestre)
    
    context = {
        'courses': courses
    }
    
    return render(request, 'attribution/courses_list.html', context)

@csrf_exempt
def create_attribution(request):
    if request.method == 'POST':
        try:
            # Log de la requête reçue
            print("Requête reçue:", request.body.decode('utf-8'))
            
            # Décodage du JSON
            data = json.loads(request.body.decode('utf-8'))
            
            # Extraction et validation des données
            selected_cours = data.get('selected_cours', [])
            matricule = data.get('teacher_matricule')
            annee = data.get('teacher_academic_year')
            type_charge = data.get('type_charge')

            # Validation des données requises
            if not all([matricule, annee, type_charge]):
                return JsonResponse({
                    'success': False,
                    'message': 'Données manquantes : matricule, année académique ou type de charge.'
                }, status=400)

            if not selected_cours:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun cours sélectionné.'
                }, status=400)

            attributions_created = []
            ids_to_delete = []  # Changement : collecter les IDs au lieu des code_ue
            skipped_courses = []
            errors = []

            # Démarrage d'une transaction atomique
            with transaction.atomic():
                for cours in selected_cours:
                    # Validation de la structure de chaque cours
                    if not isinstance(cours, dict) or 'id' not in cours or 'code_ue' not in cours:
                        return JsonResponse({
                            'success': False,
                            'message': f'Format de données incorrect pour le cours: {cours}'
                        }, status=400)

                    try:
                        # Récupération de l'enseignant
                        teacher = Teacher.objects.get(matricule=matricule)
                        
                        # Récupérer le cours depuis Cours_Attribution (table source)
                        cours_attr = Cours_Attribution.objects.get(id=cours['id'])
                        
                        # Créer/récupérer le cours dans Course avec get_or_create
                        # La clé unique : code_ue + intitule_ue + intitule_ec + credit + cmi + td_tp + classe
                        course, created = Course.objects.get_or_create(
                            code_ue=cours_attr.code_ue,
                            intitule_ue=cours_attr.intitule_ue,
                            intitule_ec=cours_attr.intitule_ec,
                            credit=cours_attr.credit,
                            cmi=cours_attr.cmi,
                            td_tp=cours_attr.td_tp,
                            classe=cours_attr.classe,
                            defaults={
                                'semestre': cours_attr.semestre,
                                'departement': cours_attr.departement,
                                'section': cours_attr.section,
                            }
                        )
                        
                        # Vérification si l'attribution existe déjà
                        existing_attribution = Attribution.objects.filter(
                            matricule=teacher,
                            code_ue=course,
                            annee_academique=annee
                        ).first()
                        
                        if existing_attribution:
                            # Si l'attribution existe déjà, on l'ignore et on continue
                            skipped_courses.append(f"{cours['code_ue']} (ID:{cours['id']})")
                            continue

                        # Création de l'attribution
                        attribution = Attribution.objects.create(
                            matricule=teacher,
                            code_ue=course,
                            annee_academique=annee,
                            type_charge=type_charge
                        )
                        attributions_created.append(attribution)

                        # Ajout de l'ID exact pour suppression précise dans Cours_Attribution
                        ids_to_delete.append(cours['id'])

                    except Teacher.DoesNotExist:
                        errors.append(f"Enseignant avec matricule {matricule} non trouvé")
                    except Course.DoesNotExist:
                        errors.append(f"Cours avec ID {cours['id']} (code_ue: {cours['code_ue']}) non trouvé")
                    except Exception as e:
                        errors.append(f"Erreur pour {cours['code_ue']} (ID:{cours['id']}): {str(e)}")

                # Suppression précise : uniquement les cours réellement attribués (par ID)
                if ids_to_delete:
                    Cours_Attribution.objects.filter(id__in=ids_to_delete).delete()

            # Construire le message de retour
            message_parts = []
            if attributions_created:
                message_parts.append(f'{len(attributions_created)} attribution(s) créée(s) avec succès')
            if skipped_courses:
                message_parts.append(f'{len(skipped_courses)} cours ignoré(s) (déjà attribué(s)): {", ".join(skipped_courses)}')
            if errors:
                message_parts.append(f'Erreurs: {"; ".join(errors)}')
            
            final_message = '. '.join(message_parts)
            
            # Si aucune attribution n'a été créée et qu'il y a des erreurs ou des cours ignorés
            if not attributions_created and (errors or skipped_courses):
                return JsonResponse({
                    'success': False,
                    'message': final_message
                }, status=400)
            
            # Retour succès
            return JsonResponse({
                'success': True,
                'message': final_message
            })

        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur de décodage JSON: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur serveur: {str(e)}'
            }, status=400)

    # Méthode non autorisée
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)


@require_http_methods(['POST'])
@csrf_exempt  # Temporairement pour debug
def delete_attribution(request, attribution_id):
    try:
        # Utiliser une transaction atomique pour garantir la cohérence
        with transaction.atomic():
            attribution = Attribution.objects.select_for_update().get(id=attribution_id)
            
            # Récupération sécurisée du code UE
            try:
                code_ue = attribution.code_ue.code_ue if attribution.code_ue else 'inconnu'
            except:
                code_ue = 'inconnu'
            
            # Récupération sécurisée du nom enseignant
            try:
                teacher_name = attribution.matricule.nom_complet if attribution.matricule else 'inconnu'
            except:
                teacher_name = 'inconnu'
            
            # Supprimer TOUS les horaires liés en désactivant temporairement les contraintes
            count_schedules = ScheduleEntry.objects.filter(attribution=attribution).count()
            ScheduleEntry.objects.filter(attribution=attribution).delete()
            
            # Supprimer l'attribution elle-même
            attribution.delete()
        
        # Ne pas utiliser messages.success dans une vue JSON
        return JsonResponse({
            'success': True, 
            'message': f'Attribution {code_ue} ({teacher_name}) et {count_schedules} horaire(s) supprimé(s) avec succès'
        })
    except Attribution.DoesNotExist:
        return JsonResponse({'success': False, 'error': "L'attribution n'existe pas"}, status=404)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"=== Erreur delete_attribution ID={attribution_id} ===")
        print(error_details)
        print("=" * 50)
        return JsonResponse({'success': False, 'error': f'{str(e)}'}, status=500)


def liste_attributions_view(request):
    try:
        teachers = Teacher.objects.all().order_by('nom_complet')
        courses = Course.objects.all().order_by('code_ue')
        academic_years = Attribution.objects.values_list('annee_academique', flat=True).distinct().order_by('-annee_academique')

        context = {
            'teachers': teachers,
            'courses': courses,
            'academic_years': academic_years,
            'attributions': None,  # Pas d'attributions par défaut
            'total_cmi': 0,
            'total_td_tp': 0,
            'total_combined': 0,
            'total_courses': 0
        }
        
        return render(request, 'attribution/liste_attributions.html', context)
    except Exception as e:
        messages.error(request, f'Erreur lors du chargement de la page : {str(e)}')
        return redirect('home')


@require_http_methods(['POST'])
@csrf_exempt
def create_new_attribution(request):
    try:
        # Récupérer les données JSON
        data = json.loads(request.body)
        matricule = data.get('teacher_matricule')
        annee_academique = data.get('teacher_academic_year')
        type_charge = data.get('type_charge')
        code_ue = data.get('code_ue')

        # Vérifier que toutes les données requises sont présentes
        if not all([matricule, annee_academique, type_charge, code_ue]):
            return JsonResponse({
                'success': False,
                'error': 'Tous les champs sont obligatoires'
            }, status=400)

        # Récupérer les objets liés
        try:
            teacher = Teacher.objects.get(matricule=matricule)
        except Teacher.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Enseignant avec matricule {matricule} non trouvé'
            }, status=404)
        
        # Chercher le cours (prendre le premier si plusieurs avec le même code_ue)
        course = Course.objects.filter(code_ue=code_ue).first()
        if not course:
            return JsonResponse({
                'success': False,
                'error': f'Cours avec code {code_ue} non trouvé'
            }, status=404)

        # Vérifier si l'attribution existe déjà
        if Attribution.objects.filter(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee_academique
        ).exists():
            return JsonResponse({
                'success': False,
                'error': f'Cette attribution existe déjà pour l\'année {annee_academique}'
            }, status=400)

        # Créer la nouvelle attribution
        Attribution.objects.create(
            matricule=teacher,
            code_ue=course,
            annee_academique=annee_academique,
            type_charge=type_charge
        )

        return JsonResponse({
            'success': True,
            'message': f'Attribution créée avec succès pour {teacher.nom_complet}, {course.code_ue}'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la création de l\'attribution : {str(e)}'
        }, status=500)


@require_http_methods(['GET', 'POST'])
def search_attributions(request):
    try:
        # Récupérer les critères de recherche
        teacher_name = request.GET.get('teacher_name') if request.method == 'GET' else request.POST.get('teacher_name')
        matricule = request.GET.get('teacher_matricule') if request.method == 'GET' else request.POST.get('teacher_matricule')
        annee_academique = request.GET.get('teacher_academic_year') if request.method == 'GET' else request.POST.get('teacher_academic_year')
        type_charge = request.GET.get('type_charge') if request.method == 'GET' else request.POST.get('type_charge')
        code_ue = request.GET.get('code_ue') if request.method == 'GET' else request.POST.get('code_ue')

        # Construire la requête de base
        query = Attribution.objects.select_related('matricule', 'code_ue')

        # Appliquer les filtres si les valeurs sont fournies
        if teacher_name:
            query = query.filter(matricule__id=teacher_name)
        if matricule:
            query = query.filter(matricule__matricule=matricule)
        if annee_academique:
            query = query.filter(annee_academique=annee_academique)
        if type_charge:
            # Convert type_charge to match model choices
            type_charge_normalized = type_charge.lower()
            if type_charge_normalized == 'reguliere':
                query = query.filter(type_charge='reguliere')
            elif type_charge_normalized == 'supplementaire':
                query = query.filter(type_charge='supplementaire')
        if code_ue:
            # Recherche par code exact ou intitulé partiel
            from django.db.models import Q
            query = query.filter(
                Q(code_ue__code_ue__icontains=code_ue) | 
                Q(code_ue__intitule_ue__icontains=code_ue)
            )

        # Récupérer les attributions filtrées
        attributions = query.values(
            'id',
            'code_ue__code_ue',
            'code_ue__intitule_ue',       
            'code_ue__intitule_ec',  
            'code_ue__credit',  
            'code_ue__cmi',       
            'code_ue__td_tp',       
            'code_ue__classe',      
            'code_ue__semestre',
            'type_charge',                 
        ).order_by('type_charge')

        # Calculer les totaux
        total_cmi = sum(float(attr['code_ue__cmi'] or 0) for attr in attributions)
        total_td_tp = sum(float(attr['code_ue__td_tp'] or 0) for attr in attributions)
        total_combined = total_cmi + total_td_tp
        total_courses = attributions.count()

        # Récupérer les données pour les listes déroulantes
        teachers = Teacher.objects.all().order_by('nom_complet')
        courses = Course.objects.all().order_by('code_ue')
        academic_years = Attribution.objects.values_list('annee_academique', flat=True).distinct().order_by('-annee_academique')

        context = {
            'attributions': attributions,
            'teachers': teachers,
            'courses': courses,
            'academic_years': academic_years,
            'total_cmi': total_cmi,
            'total_td_tp': total_td_tp,
            'total_combined': total_combined,
            'total_courses': total_courses,
            'selected_teacher_name': teacher_name,
            'selected_matricule': matricule,
            'selected_year': annee_academique,
            'selected_type': type_charge,
            'selected_code_ue': code_ue
        }

        if not attributions:
            messages.warning(request, 'Aucune attribution trouvée pour ces critères')
        else:
            messages.success(request, f'{attributions.count()} attribution(s) trouvée(s)')

        return render(request, 'attribution/liste_attributions.html', context)

    except Exception as e:
        import traceback
        messages.error(request, f'Erreur lors de la recherche : {str(e)}')
        # Log the full traceback for debugging
        print(traceback.format_exc())
        return redirect('attribution:list_attribution')

def liste_charges(request):
    # Vue pour afficher les attributions de charge avec filtrage
    from django.db.models import Q
    
    attributions = Attribution.objects.select_related('matricule', 'code_ue')
    
    # Récupérer les paramètres de filtrage
    teacher_matricule = request.GET.get('teacher_matricule')
    annee_academique = request.GET.get('teacher_academic_year')
    type_charge = request.GET.get('type_charge')
    code_ue = request.GET.get('code_ue')
    
    # Appliquer les filtres
    if teacher_matricule:
        attributions = attributions.filter(matricule__matricule=teacher_matricule)
    if annee_academique:
        attributions = attributions.filter(annee_academique=annee_academique)
    if type_charge:
        attributions = attributions.filter(type_charge=type_charge)
    if code_ue:
        # Recherche par code exact ou intitulé partiel
        attributions = attributions.filter(
            Q(code_ue__code_ue__icontains=code_ue) | 
            Q(code_ue__intitule_ue__icontains=code_ue)
        )
    
    # Calculer le nombre d'enseignants qui ont une charge (attribution)
    teachers_with_assignments = Attribution.objects.values('matricule').distinct().count()
    
    # Récupérer toutes les UEs avec leurs attributions
    cours_ues = Cours_Attribution.objects.all().order_by('code_ue')
    
    # Créer un dictionnaire UE -> Enseignants pour affichage rapide
    ue_enseignants = {}
    for attribution in Attribution.objects.select_related('code_ue', 'matricule').all():
        ue_code = attribution.code_ue.code_ue
        if ue_code not in ue_enseignants:
            ue_enseignants[ue_code] = []
        enseignant_info = f"{attribution.matricule.grade} {attribution.matricule.nom_complet}"
        if enseignant_info not in ue_enseignants[ue_code]:
            ue_enseignants[ue_code].append(enseignant_info)
    
    # Récupérer les années académiques depuis le modèle AnneeAcademique
    annees_academiques = AnneeAcademique.objects.all().order_by('-date_debut')
    annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
    
    # Fallback vers les années des attributions existantes si aucune année n'est configurée
    if not annees_academiques.exists():
        academic_years = list(set(Attribution.objects.values_list('annee_academique', flat=True)))
    else:
        academic_years = [annee.code for annee in annees_academiques]
    
    context = {
        'attributions': attributions,
        'teachers': Teacher.objects.all().order_by('nom_complet'),
        'academic_years': academic_years,
        'annee_courante': annee_courante.code if annee_courante else None,
        'selected_teacher_name': attributions.first().matricule.nom_complet if attributions.exists() else '',
        'selected_year': annee_academique,
        'selected_type': type_charge,
        'selected_code_ue': code_ue,
        'teachers_with_assignments': teachers_with_assignments,
        'cours_ues': cours_ues,
        'ue_enseignants': ue_enseignants,
    }
    
    return render(request, 'attribution/charge.html', context)

def detail_attribution(request, attribution_id):
    # Vue pour afficher les détails d'une attribution
    attribution = get_object_or_404(Attribution, id=attribution_id)
    
    context = {
        'attribution': attribution,
    }
    
    return render(request, 'attribution/detail_attribution.html', context)

def edit_attribution(request, attribution_id):
    # Vue pour modifier une attribution
    attribution = get_object_or_404(Attribution, id=attribution_id)
    
    if request.method == 'POST':
        # Logique de mise à jour de l'attribution
        form = AttributionForm(request.POST, instance=attribution)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attribution mise à jour avec succès')
            return redirect('attribution:liste_charges')
    else:
        form = AttributionForm(instance=attribution)
    
    context = {
        'form': form,
        'attribution': attribution,
    }
    
    return render(request, 'attribution/edit_attribution.html', context)

def generate_courses_pdf(request, cours_attribution_objects, departement=None):
    """Générer un PDF à partir d'objets Cours_Attribution (cours de la liste d'attribution)"""
    # Créer un buffer pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF avec l'orientation paysage
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )
    
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(landscape(A4)[0]-20, 10, text)
        canvas.restoreState()

    elements = []
    
    # Ajouter l'en-tête institutionnelle
    header = create_header_table()
    elements.append(header)
    elements.append(Spacer(1, 15))
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10,
        alignment=1
    )
    
    # Style pour le texte des cellules
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=1  # Centre le texte
    )
    
    # Titre du document
    current_year = datetime.now().year
    next_year = current_year + 1
    academic_year = f"{current_year}-{next_year}"
    
    if departement:
        title_text = f"LISTE DES COURS DU DÉPARTEMENT {departement.upper()} - ANNÉE ACADÉMIQUE {academic_year}"
    else:
        title_text = f"LISTE DES COURS - ANNÉE ACADÉMIQUE {academic_year}"
        
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 10))
    
    # Entêtes du tableau
    header_data = [
        ['Code UE', 'Intitulé UE', 'Intitulé EC', 'Crédit', 'CMI', 'TD+TP', 'Classe', 'Semestre', 'Département']
    ]
    
    # Préparer les données du tableau
    # Trier les cours par semestre (ordre croissant)
    cours_tries = sorted(cours_attribution_objects, key=lambda course: course.semestre)
    
    data = []
    for course in cours_tries:
        row = [
            course.code_ue,
            Paragraph(course.intitule_ue, cell_style),
            Paragraph(course.intitule_ec or '', cell_style),
            course.credit,
            course.cmi,
            course.td_tp,
            Paragraph(course.classe or '', cell_style),
            course.semestre,
            course.departement
        ]
        data.append(row)
    
    # Créer le tableau avec les entêtes et les données
    all_data = header_data + data
    col_widths = [60, 180, 120, 40, 40, 40, 60, 60, 100]  # Largeurs des colonnes ajustées
    table = Table(all_data, colWidths=col_widths)
    
    # Style du tableau
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Aligner le code UE à gauche
        ('ALIGN', (3, 1), (8, -1), 'CENTER'),  # Aligner les colonnes numériques au centre
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Alternance de couleurs pour les lignes
    for i in range(1, len(all_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Ajouter les informations de date et heure
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    date_text = f"Généré le {now}"
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(date_text, ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2)))  # Aligné à droite
    
    # Générer le PDF
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    
    # Préparer la réponse avec le PDF généré
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="liste_cours.pdf"'
    
    return response

def schedule_builder(request):
    """Redirige vers la page unifiée de gestion des horaires"""
    # Rediriger vers la vue unifiée au lieu de l'ancienne interface
    return redirect('attribution:schedule_entry_list')

def schedule_pdf(request):
    classe = request.GET.get('classe')  # Ex: L1BC ou juste L1
    annee = request.GET.get('annee')
    week_start = request.GET.get('semaine')  # YYYY-MM-DD
    chef_section_id = request.GET.get('chef_section')
    chef_adjoint_id = request.GET.get('chef_adjoint')
    attribution_id = request.GET.get('attribution_id')

    # Extraire le niveau (L1, L2, L3, M1, M2) de la classe
    import re
    from reportlab.platypus import PageBreak
    niveau_demande = None
    if classe:
        match = re.match(r'^(L[1-3]|M[1-2])', classe)
        if match:
            niveau_demande = match.group(1)
    
    # Récupérer toutes les attributions
    all_attributions = Attribution.objects.select_related('matricule', 'code_ue')
    if attribution_id:
        all_attributions = all_attributions.filter(id=attribution_id)
        if not classe and all_attributions.exists():
            classe = all_attributions.first().code_ue.classe
            match = re.match(r'^(L[1-3]|M[1-2])', classe)
            if match:
                niveau_demande = match.group(1)
    
    if annee:
        all_attributions = all_attributions.filter(annee_academique=annee)
    
    # Générer toutes les 5 pages si aucun niveau spécifique n'est demandé
    if niveau_demande:
        niveaux_a_generer = [niveau_demande]
    else:
        niveaux_a_generer = ['L1', 'L2', 'L3', 'M1', 'M2']  # Toutes les pages

    # Préparation PDF avec marges réduites pour optimiser l'espace
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10, leftMargin=10, topMargin=20, bottomMargin=15)
    
    # Colonnes fixes pour chaque niveau - définies exactement selon les besoins
    colonnes_par_niveau = {
        'L1': ['L1BC', 'L1CST', 'L1MI', 'L1PHY', 'L1IT', 'L1IG'],
        'L2': ['L2BC', 'L2CST', 'L2MI', 'L2PHY', 'L2IT', 'L2IG'],
        'L3': ['L3BC', 'L3CST', 'L3MI', 'L3PHY', 'L3IT', 'L3IG'],
        'M1': ['M1BC', 'M1CST', 'M1MI', 'M1PHY', 'M1IT', 'M1IG'],
        'M2': ['M2BC', 'M2CST', 'M2MI', 'M2PHY', 'M2IT', 'M2IG'],
    }

    def get_col_key_from_classe(classe_val):
        """Extraire la clé de colonne depuis le champ classe (ex: L1BC, L2MI, etc.)"""
        if not classe_val:
            return None
        
        classe_upper = classe_val.upper().strip()
        
        # Méthode 1: Format exact L1BC, L2MI, M1PHY, etc.
        match = re.match(r'^(L[1-3]|M[1-2])(BC|CST|MI|PHY|IT|IG)', classe_upper)
        if match:
            return match.group(0)  # Retourne L1BC, L2MI, etc.
        
        # Méthode 2: Extraire niveau + chercher suffixe dans le texte
        match_niveau = re.match(r'^(L[1-3]|M[1-2])', classe_upper)
        if match_niveau:
            niveau = match_niveau.group(1)
            # Chercher les suffixes courants dans le reste du texte
            suffixes = ['BC', 'CST', 'MI', 'PHY', 'IT', 'IG']
            for suffix in suffixes:
                if suffix in classe_upper:
                    return f"{niveau}{suffix}"
        
        # Méthode 3: Fallback - retourner tel quel si c'est un format valide
        if re.match(r'^(L[1-3]|M[1-2])[A-Z]+$', classe_upper):
            return classe_upper
        
        return None
    
    days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    
    # Récupérer toutes les entries
    if week_start and not annee:
        try:
            y, m, d = [int(x) for x in week_start.split('-')]
            semaine_date = datetime(y, m, d).date()
            all_entries = ScheduleEntry.objects.filter(semaine_debut=semaine_date)
        except Exception:
            all_entries = ScheduleEntry.objects.none()
    else:
        all_entries = ScheduleEntry.objects.filter(
            annee_academique=annee if annee else all_attributions.first().annee_academique if all_attributions.exists() else '',
        )
        if week_start:
            try:
                y, m, d = [int(x) for x in week_start.split('-')]
                semaine_date = datetime(y, m, d).date()
                all_entries = all_entries.filter(semaine_debut=semaine_date)
            except Exception:
                pass

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 8)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(landscape(A4)[0]-20, 10, text)
        canvas.restoreState()

    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('SchedTitle', parent=styles['Heading2'], fontSize=13, alignment=1, fontName='Times-Bold')
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9, leading=11, alignment=1, wordWrap='CJK', fontName='Times-Roman')
    
    # Calculer les dates de début et fin de semaine pour le titre
    from datetime import timedelta
    semaine_info = ""
    day_dates = {}
    
    # Si pas de semaine spécifiée, utiliser la semaine en cours
    if not week_start:
        # Trouver la semaine en cours
        from reglage.models import SemaineCours
        semaine_en_cours = SemaineCours.objects.filter(est_en_cours=True).first()
        if semaine_en_cours:
            week_start = semaine_en_cours.date_debut.strftime('%Y-%m-%d')
    
    if week_start:
        try:
            y, m, d = [int(x) for x in week_start.split('-')]
            date_debut = datetime(y, m, d).date()
            date_fin = date_debut + timedelta(days=5)  # Samedi (6 jours de cours)
            semaine_info = f"{date_debut.strftime('%d')} au {date_fin.strftime('%d %B %Y')}"
            
            # Calculer les dates pour chaque jour
            days_map = {
                'Lundi': 0, 'Mardi': 1, 'Mercredi': 2, 
                'Jeudi': 3, 'Vendredi': 4, 'Samedi': 5
            }
            for day, offset in days_map.items():
                day_dates[day] = date_debut + timedelta(days=offset)
        except:
            semaine_info = week_start
    
    # Récupérer les créneaux depuis la table Creneau si disponible
    from reglage.models import Creneau
    creneaux_actifs = Creneau.objects.filter(est_actif=True).order_by('ordre', 'heure_debut')
    
    if creneaux_actifs.exists():
        # Utiliser les créneaux de la table Réglage
        slots = [(c.get_format_court(), c.code) for c in creneaux_actifs]
    else:
        # Fallback sur les créneaux par défaut
        slots = [('08h00-12h00', 'AM'), ('13h00-17h00', 'PM')]
    
    # Boucle sur chaque niveau pour créer une page par niveau
    page_count = 0
    for niveau in niveaux_a_generer:
        # Filtrer les horaires pour ce niveau
        entries_niveau = all_entries.filter(attribution__code_ue__classe__startswith=niveau)
        
        # Debug: afficher le nombre d'horaires trouvés pour ce niveau
        print(f"\n=== Niveau {niveau} ===")
        print(f"Nombre d'horaires trouvés: {entries_niveau.count()}")
        for e in entries_niveau:
            print(f"  - {e.attribution.code_ue.classe} | {e.attribution.code_ue.code_ue} | {e.attribution.matricule.nom_complet} | {e.jour} {e.creneau}")
        
        # Générer la page même s'il n'y a pas d'horaires (tableau vide avec colonnes)
        # On ne saute plus les niveaux sans données
        
        # Ajouter un saut de page si ce n'est pas la première page
        if page_count > 0:
            elements.append(PageBreak())
        page_count += 1
        
        # Titre selon l'image - sans mention du niveau sur la première ligne
        titre = f"<b>SECTION DES SCIENCES & TECHNOLOGIES</b><br/>"\
                f"Horaires des Cours : semaine du {semaine_info}"
        titre_para = Paragraph(titre, ParagraphStyle('TitleCustom', parent=styles['Normal'], fontSize=12, alignment=1, fontName='Times-Bold', leading=14))
        elements.append(titre_para)
        elements.append(Spacer(1, 8))
        
        # Utiliser les colonnes fixes pour ce niveau comme base
        col_keys_predefinies = colonnes_par_niveau.get(niveau, [])
        
        # D'abord, parcourir les entries pour détecter toutes les colonnes réelles
        colonnes_detectees = set(col_keys_predefinies)  # Commencer avec les colonnes prédéfinies
        by_col = {}
        
        # Parcourir tous les horaires et les organiser par colonne
        for e in entries_niveau.select_related('attribution__matricule', 'attribution__code_ue'):
            a = e.attribution
            if not a:
                continue
            classe_val = a.code_ue.classe or ''
            col_key = get_col_key_from_classe(classe_val)
            
            if col_key:
                colonnes_detectees.add(col_key)
                if col_key not in by_col:
                    by_col[col_key] = []
                    if col_key not in col_keys_predefinies:
                        print(f"Colonne ajoutée dynamiquement: {col_key} pour le niveau {niveau}")
                by_col[col_key].append((e, a))
        
        # Finaliser la liste des colonnes triées
        col_keys = sorted(list(colonnes_detectees))
        
        # S'assurer que toutes les colonnes ont une liste (même vide)
        for col in col_keys:
            if col not in by_col:
                by_col[col] = []
        
        # En-tête colonnes - s'assurer qu'il n'y a pas de None
        table_header = ['Jour', 'Heures'] + [str(k) if k is not None else 'N/A' for k in col_keys]
        
        # Construire les lignes du tableau
        data = [table_header]
        for day in days:
            # Afficher le jour avec la date en dessous
            if day in day_dates:
                day_label = f"<b>{day}</b><br/>{day_dates[day].strftime('%d/%m')}"
            else:
                day_label = f"<b>{day}</b>"
            
            for i, (slot_label, slot_code) in enumerate(slots):
                row = []
                
                # Cellule Jour - seulement sur la première ligne du jour avec Paragraph pour formatage
                if i == 0:
                    row.append(Paragraph(day_label, cell_style))
                else:
                    row.append('')  # Vide car sera fusionné
                
                # Cellule Heures - avec Times New Roman
                row.append(Paragraph(slot_label, cell_style))
                
                # Ajouter une cellule pour chaque colonne de classe
                for col in col_keys:
                    items = []
                    for e, a in by_col.get(col, []):
                        jour_label = day.lower()
                        
                        # Vérifier que l'entry correspond au jour et créneau actuel
                        # Comparaison flexible : accepter e.creneau == slot_code OU e.creneau.upper() == slot_code
                        creneau_match = (
                            e.creneau == slot_code or 
                            e.creneau.upper() == slot_code or
                            e.creneau.upper() == slot_code.upper()
                        )
                        
                        if e.jour == jour_label and creneau_match:
                            code = a.code_ue.code_ue or ''
                            title = a.code_ue.intitule_ue or ''
                            teacher_name = a.matricule.nom_complet or ''
                            grade = a.matricule.grade or ''
                            if grade:
                                txt = f"<b>{code}</b><br/><i>({title})</i><br/>{grade} {teacher_name}"
                            else:
                                txt = f"<b>{code}</b><br/><i>({title})</i><br/>{teacher_name}"
                            items.append(txt)
                    
                    # Créer le contenu de la cellule - utiliser espace si vide
                    if items:
                        cell_content = '<br/><br/>'.join(items)
                    else:
                        cell_content = '&nbsp;'  # Espace insécable HTML
                    row.append(Paragraph(cell_content, cell_style))
                
                data.append(row)
        
        # Créer et styler le tableau
        # Calculer le nombre de colonnes
        nb_cols = len(col_keys)
        
        # Si pas de données, créer un tableau minimal
        if len(data) <= 1 or nb_cols == 0:
            # Tableau vide - afficher juste un message
            data = [['Jour', 'Heures', 'Aucun cours programmé']]
            col_widths = [60, 80, 400]
            table = Table(data, colWidths=col_widths)
            style = TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ])
            table.setStyle(style)
            elements.append(table)
            continue  # Passer au niveau suivant
        
        # Calculer la largeur disponible pour les colonnes de classe
        page_width = 842  # landscape(A4)[0]
        
        # 842 - 30 (marges) - 55 (jour) - 75 (heures) = 682 points disponibles
        largeur_disponible = 682
        largeur_colonne = int(largeur_disponible / nb_cols)
        # S'assurer qu'on a au moins 100 points par colonne pour la lisibilité
        if largeur_colonne < 100:
            largeur_colonne = 100
        
        col_widths = [50, 70] + [largeur_colonne] * nb_cols
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),  # TOP au lieu de MIDDLE pour plus d'espace
            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ])
        
        # Fusionner les cellules de la colonne Jour pour éviter la redondance
        nb_creneaux = len(slots)
        if nb_creneaux > 1:
            for day_idx in range(len(days)):
                row_start = 1 + (day_idx * nb_creneaux)  # +1 pour l'en-tête
                row_end = row_start + (nb_creneaux - 1)
                # Vérifier que les indices sont valides
                if row_start < len(data) and row_end < len(data):
                    style.add('SPAN', (0, row_start), (0, row_end))
        
        table.setStyle(style)
        elements.append(table)
        
        # Signatures en bas de chaque page
        elements.append(Spacer(1, 20))
        chef_section = Teacher.objects.filter(id=chef_section_id).first() if chef_section_id else None
        chef_adjoint = Teacher.objects.filter(id=chef_adjoint_id).first() if chef_adjoint_id else None

        # Fonction pour obtenir la désignation du grade
        def get_grade_designation(code_grade):
            if not code_grade:
                return ''
            try:
                from reglage.models import Grade
                grade_obj = Grade.objects.get(CodeGrade=code_grade)
                return grade_obj.DesignationGrade
            except:
                return code_grade  # Fallback sur le code si la désignation n'existe pas

        # Style pour les signatures avec Times New Roman
        sig_style = ParagraphStyle('SigStyle', parent=styles['Normal'], fontSize=10, alignment=0, fontName='Times-Roman')
        
        # Créer le contenu des signatures selon l'image
        chef_section_text = "LE CHEF DE SECTION<br/>"
        if chef_section:
            chef_section_text += f"<u>{chef_section.nom_complet}</u><br/>"
            if chef_section.grade:
                grade_designation = get_grade_designation(chef_section.grade)
                chef_section_text += f"<i>{grade_designation}</i>"
        
        chef_adjoint_text = "LE CHEF DE SECTION-ADJOINT / ENSEIGNEMENT<br/>"
        if chef_adjoint:
            chef_adjoint_text += f"<u>{chef_adjoint.nom_complet}</u><br/>"
            if chef_adjoint.grade:
                grade_designation = get_grade_designation(chef_adjoint.grade)
                chef_adjoint_text += f"<i>{grade_designation}</i>"
        
        sig_table_data = [[
            Paragraph(chef_section_text, sig_style),
            Paragraph(chef_adjoint_text, sig_style),
        ]]
        sig_table = Table(sig_table_data, colWidths=[landscape(A4)[0]/2-20, landscape(A4)[0]/2-20])
        sig_table.setStyle(TableStyle([
            ('ALIGN',(0,0),(0,0),'LEFT'),
            ('ALIGN',(1,0),(1,0),'RIGHT'),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        elements.append(sig_table)

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"horaire_{classe or 'classe'}_{annee or 'annee'}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@csrf_exempt
@require_http_methods(['POST'])
def save_schedule_entries(request):
    from .validators import ScheduleConflictValidator
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
        annee = payload.get('annee_academique')
        semaine = payload.get('semaine_debut')  # YYYY-MM-DD
        entries = payload.get('entries', [])
        if not annee or not semaine:
            return JsonResponse({'success': False, 'message': 'annee_academique et semaine_debut requis'}, status=400)

        y, m, d = [int(x) for x in semaine.split('-')]
        semaine_date = datetime(y, m, d).date()

        saved = 0
        errors = []
        
        for e in entries:
            attribution_id = e.get('attribution_id')
            jour = e.get('jour')  # 'lundi'...
            creneau = e.get('creneau')  # 'am'/'pm'
            salle = e.get('salle')
            remarques = e.get('remarques')
            if not all([attribution_id, jour, creneau]):
                continue
                
            try:
                a = Attribution.objects.get(id=attribution_id)
                
                # Vérifier s'il existe déjà (pour update)
                existing = ScheduleEntry.objects.filter(
                    attribution=a,
                    annee_academique=annee,
                    semaine_debut=semaine_date,
                    jour=jour,
                    creneau=creneau
                ).first()
                
                # *** VALIDATION DES CONFLITS ***
                validation_result = ScheduleConflictValidator.validate_schedule_entry(
                    attribution=a,
                    jour=jour,
                    creneau=creneau,
                    semaine=semaine_date,
                    salle=salle,
                    exclude_id=existing.id if existing else None
                )
                
                # Si conflit détecté, l'ajouter aux erreurs et passer au suivant
                if not validation_result['valid']:
                    errors.extend(validation_result['errors'])
                    continue
                
                # Pas de conflit, créer ou mettre à jour
                obj, _ = ScheduleEntry.objects.update_or_create(
                    attribution=a,
                    annee_academique=annee,
                    semaine_debut=semaine_date,
                    jour=jour,
                    creneau=creneau,
                    defaults={'salle': salle, 'remarques': remarques}
                )
                saved += 1
            except Attribution.DoesNotExist:
                errors.append(f"Attribution {attribution_id} introuvable")
                continue
        
        # Retourner le résultat
        if errors:
            return JsonResponse({
                'success': False if saved == 0 else True,
                'saved': saved,
                'message': f'{saved} horaire(s) créé(s). {len(errors)} conflit(s) détecté(s).',
                'errors': errors
            })
        
        return JsonResponse({'success': True, 'saved': saved, 'message': f'✅ {saved} horaire(s) créé(s) avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def generate_pdf(request):
    # Récupérer les paramètres de filtrage pour les attributions
    matricule = request.GET.get('matricule', '')
    annee_academique = request.GET.get('annee_academique', '')
    type_charge = request.GET.get('type_charge', '')
    departement = request.GET.get('departement', '')
    course_ids = request.GET.get('course_ids', '')
    
    # Filtrer les cours ou les attributions selon ce qui est demandé
    if course_ids:
        # Si nous avons des IDs de cours spécifiques (de la page attribution_list)
        course_id_list = course_ids.split(',')
        cours_attribution_objects = Cours_Attribution.objects.filter(id__in=course_id_list)
        
        # Créer un PDF directement à partir des objets Cours_Attribution
        return generate_courses_pdf(request, cours_attribution_objects, departement)
    else:
        # Filtrer les attributions (comportement original)
        attributions = Attribution.objects.select_related('matricule', 'code_ue')
        
        if matricule:
            attributions = attributions.filter(matricule__matricule=matricule)
        if annee_academique:
            attributions = attributions.filter(annee_academique=annee_academique)
    
    # Obtenir des informations sur l'enseignant (pour l'en-tête)
    enseignant_info = None
    if attributions.exists():
        enseignant_info = attributions.first().matricule
    
    # Séparer les attributions par type de charge
    attributions_regulieres = attributions.filter(type_charge='Reguliere')
    attributions_supplementaires = attributions.filter(type_charge='Supplementaire')
    
    # Créer un buffer pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF avec l'orientation paysage pour correspondre au format demandé
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )
    
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(landscape(A4)[0]-20, 10, text)
        canvas.restoreState()

    elements = []
    
    # Ajouter l'en-tête institutionnelle
    header = create_header_table()
    elements.append(header)
    elements.append(Spacer(1, 15))
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10,
        alignment=1
    )
    
    # Style pour le texte des cellules
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=1  # Centre le texte
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=0  # Aligné à gauche
    )
    
    # Informations de l'enseignant
    if enseignant_info:
        # Récupérer la désignation complète du grade
        grade_designation = ''
        try:
            if enseignant_info.grade:
                grade_obj = Grade.objects.get(CodeGrade=enseignant_info.grade)
                grade_designation = grade_obj.DesignationGrade
        except Grade.DoesNotExist:
            grade_designation = enseignant_info.grade
        except:
            grade_designation = 'Non spécifié'
        
        # Récupérer la désignation complète du département
        departement_designation = ''
        try:
            if enseignant_info.departement:
                dept_obj = Departement.objects.get(CodeDept=enseignant_info.departement)
                departement_designation = dept_obj.DesignationDept
        except Departement.DoesNotExist:
            departement_designation = enseignant_info.departement
        except:
            departement_designation = 'Non spécifié'
        
        # Récupérer la désignation complète de la section
        section_designation = ''
        try:
            if enseignant_info.section:
                section_obj = Section.objects.get(CodeSection=enseignant_info.section)
                section_designation = section_obj.DesignationSection
        except Section.DoesNotExist:
            section_designation = enseignant_info.section
        except:
            section_designation = 'Non spécifiée'
            
        # Fonction pour créer une image avec bords arrondis
        def create_rounded_image(image_path, size=(100, 100), radius=15):
            """Crée une image avec des bords arrondis"""
            try:
                # Ouvrir l'image
                img = PILImage.open(image_path).convert("RGB")
                
                # Redimensionner l'image
                img = img.resize(size, PILImage.Resampling.LANCZOS)
                
                # Créer un masque avec bords arrondis
                mask = PILImage.new('L', size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle([(0, 0), size], radius=radius, fill=255)
                
                # Appliquer le masque
                output = PILImage.new('RGB', size, (255, 255, 255))
                output.paste(img, (0, 0))
                output.putalpha(mask)
                
                # Sauvegarder dans un buffer
                img_buffer = BytesIO()
                output.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                return img_buffer
            except Exception as e:
                print(f"Erreur lors de la création de l'image arrondie: {e}")
                return None
        
        # Préparer la photo de l'enseignant
        photo_element = None
        if enseignant_info.photo:
            try:
                # Construire le chemin complet de la photo
                photo_path = os.path.join(settings.MEDIA_ROOT, str(enseignant_info.photo))
                if os.path.exists(photo_path):
                    # Créer l'image avec bords arrondis
                    rounded_img_buffer = create_rounded_image(photo_path, size=(100, 100), radius=15)
                    if rounded_img_buffer:
                        # Créer l'élément Image pour le PDF
                        photo_element = Image(rounded_img_buffer, width=100, height=100)
            except Exception as e:
                print(f"Erreur lors du chargement de la photo: {e}")
        
        # Si pas de photo, créer un placeholder
        if not photo_element:
            # Créer un paragraphe "Pas de photo" centré
            photo_placeholder = Paragraph("Pas de photo", ParagraphStyle(
                'PhotoPlaceholder',
                parent=styles['Normal'],
                fontSize=8,
                alignment=1,
                textColor=colors.grey
            ))
            photo_element = photo_placeholder
        
        # Créer le tableau d'informations
        enseignant_data = [
            ['Matricule en interne :', enseignant_info.matricule, '', '', '', ''],
            ['Nom et post-noms :', enseignant_info.nom_complet, '', '', '', ''],
            ['Grade :', grade_designation, '', '', '', ''],
            ['Département :', departement_designation, '', '', '', ''],
            ['Section :', section_designation, '', '', '', ''],
            ['Année académique :', annee_academique if annee_academique else 'Toutes les années', '', '', '', '']
        ]
        
        info_table = Table(enseignant_data, colWidths=[120, 280, 60, 60, 60, 60])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (1, -1), 0.5, colors.black),
        ]))
        
        # Créer un tableau global avec infos à gauche et photo à droite
        main_data = [[info_table, photo_element]]
        main_table = Table(main_data, colWidths=[610, 110])
        main_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            ('LEFTPADDING', (1, 0), (1, 0), 5),
            ('RIGHTPADDING', (1, 0), (1, 0), 5),
            ('TOPPADDING', (1, 0), (1, 0), 5),
            ('BOTTOMPADDING', (1, 0), (1, 0), 5),
        ]))
        
        elements.append(main_table)
        elements.append(Spacer(1, 10))
    
    # Fonction pour créer un tableau de charges (régulières ou supplémentaires)
    def creer_tableau_charges(attributions, titre):
        # Créer une cellule pour le titre avec fond gris
        titre_data = [[Paragraph(titre, cell_style)]]
        titre_table = Table(titre_data, colWidths=[720])
        titre_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(titre_table)
        
        # Entêtes du tableau principal
        headers = [
            'Code',
            'Intitulé U.E.',
            'Intitulé EC',
            'Présentiel',
            'TP - TD',
            'Total',
            'Classe',
            'Semestre'
        ]
        
        # Colonne double pour les heures prévues
        header_data = [
            ['Code', 'Intitulé U.E.', 'Intitulé EC', 'Heures prévues', '', 'Total', 'Classe', 'Semestre'],
            ['', '', '', 'Présentiel', 'TP - TD', '', '', '']
        ]
        
        # Préparer les données
        data = []
        
        # Totaux pour calcul
        total_presentiel = 0
        total_tp_td = 0
        total_heures = 0
        
        # Ajouter chaque attribution au tableau
        for attr in attributions:
            presentiel = attr.code_ue.cmi
            tp_td = attr.code_ue.td_tp
            total = presentiel + tp_td
            
            # Ajouter aux totaux
            total_presentiel += presentiel
            total_tp_td += tp_td
            total_heures += total
            
            # Utiliser Paragraph pour permettre le retour à la ligne automatique dans les cellules
            row = [
                attr.code_ue.code_ue,
                Paragraph(attr.code_ue.intitule_ue, cell_style),
                Paragraph(attr.code_ue.intitule_ec or '', cell_style),
                str(presentiel),
                str(tp_td),
                str(total),
                Paragraph(attr.code_ue.classe or '', cell_style),
                attr.code_ue.semestre
            ]
            data.append(row)
        
        # Ajouter ligne de sous-total
        sous_total_row = ['', '', 'Sous-total ' + ('1' if titre == 'Charge régulière' else '2'), 
                        str(total_presentiel), str(total_tp_td), str(total_heures), '', '']
        data.append(sous_total_row)
        
        # Combiner les en-têtes et les données
        all_data = header_data + data
        
        # Définir les largeurs de colonnes
        col_widths = [60, 150, 150, 80, 80, 80, 60, 60]
        
        # Créer le tableau
        table = Table(all_data, colWidths=col_widths, repeatRows=2)
        
        # Style du tableau
        style = TableStyle([
            # Style des entêtes
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
            ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (3, 0), (4, 0)),  # Fusion des cellules pour "Heures prévues"
            
            # Style des cellules de données
            ('ALIGN', (0, 2), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Style pour la ligne de sous-total
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (2, -1)),  # Fusion des 3 premières cellules pour le texte "Sous-total"
        ])
        
        table.setStyle(style)
        return table, total_presentiel, total_tp_td, total_heures
    
    # Générer et ajouter le tableau des charges régulières
    if attributions_regulieres.exists():
        table_regulieres, total_presentiel_reg, total_tp_td_reg, total_heures_reg = creer_tableau_charges(attributions_regulieres, 'Charge régulière')
        elements.append(table_regulieres)
        elements.append(Spacer(1, 10))
    else:
        total_presentiel_reg, total_tp_td_reg, total_heures_reg = 0, 0, 0
    
    # Générer et ajouter le tableau des charges supplémentaires
    if attributions_supplementaires.exists():
        table_supplementaires, total_presentiel_supp, total_tp_td_supp, total_heures_supp = creer_tableau_charges(attributions_supplementaires, 'Charge supplémentaire')
        elements.append(table_supplementaires)
        elements.append(Spacer(1, 10))
    else:
        total_presentiel_supp, total_tp_td_supp, total_heures_supp = 0, 0, 0
    
    # Ajouter le total général
    total_data = [
        ['Total', '', '', 
         str(total_presentiel_reg + total_presentiel_supp), 
         str(total_tp_td_reg + total_tp_td_supp), 
         str(total_heures_reg + total_heures_supp), 
         '', '']  # Colonnes vides pour classe et semestre
    ]
    
    total_table = Table(total_data, colWidths=[60, 150, 150, 80, 80, 80, 60, 60])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (5, 0), 0.5, colors.black),
        ('SPAN', (0, 0), (2, 0)),  # Fusion des 3 premières cellules pour le texte "Total"
    ]))
    
    elements.append(total_table)
    
    # Générer le PDF avec le footer
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    
    # Préparer la réponse
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"charge_horaire_{matricule if matricule else 'tous'}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response.write(pdf)
    
    return response


# ============= CRUD pour ScheduleEntry =============

class ScheduleEntryListView(ListView):
    """Liste unifiée des entrées d'horaire avec filtrage et ajout rapide"""
    model = ScheduleEntry
    template_name = 'attribution/schedule_unified.html'
    context_object_name = 'entries'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ScheduleEntry.objects.select_related(
            'attribution__matricule',
            'attribution__code_ue'
        ).order_by('-date_cours', 'creneau')
        
        # Filtrage
        annee = self.request.GET.get('annee')
        jour = self.request.GET.get('jour')
        creneau = self.request.GET.get('creneau')
        classe = self.request.GET.get('classe')
        semaine = self.request.GET.get('semaine')
        
        if annee:
            queryset = queryset.filter(annee_academique=annee)
        if jour:
            queryset = queryset.filter(jour=jour)
        if creneau:
            queryset = queryset.filter(creneau=creneau)
        if classe:
            queryset = queryset.filter(attribution__code_ue__classe__icontains=classe)
        if semaine:
            queryset = queryset.filter(semaine_debut=semaine)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique, Salle, Creneau, Classe, SemaineCours
        
        context = super().get_context_data(**kwargs)
        
        # Données depuis les modèles de réglage (PRIORITÉ)
        context['annees_reglage'] = AnneeAcademique.objects.all().order_by('-code')
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        context['salles_disponibles'] = Salle.objects.filter(est_disponible=True).order_by('code')
        context['creneaux_actifs'] = Creneau.objects.filter(est_actif=True).order_by('ordre', 'heure_debut')
        context['classes_reglage'] = Classe.objects.all().order_by('CodeClasse')
        context['semaines_cours'] = SemaineCours.objects.all().order_by('numero_semaine')
        context['semaine_courante'] = SemaineCours.objects.filter(est_en_cours=True).first()
        
        # Liste des enseignants pour les signataires du PDF (filtrés par fonction)
        context['teachers'] = Teacher.objects.all().order_by('nom_complet')
        context['chefs_section'] = Teacher.objects.filter(fonction='CS').order_by('nom_complet')
        context['chefs_adjoint'] = Teacher.objects.filter(fonction='CSAE').order_by('nom_complet')
        
        # Années académiques (fallback depuis les horaires existants si réglage vide)
        annees_existantes = ScheduleEntry.objects.values_list(
            'annee_academique', flat=True
        ).distinct().order_by('-annee_academique')
        
        # Utiliser les années de réglage si disponibles, sinon celles des horaires
        if context['annees_reglage'].exists():
            context['annees'] = [a.code for a in context['annees_reglage']]
        else:
            context['annees'] = list(annees_existantes)
        
        # Cours options pour l'ajout rapide
        attributions = Attribution.objects.select_related('matricule', 'code_ue').order_by('code_ue__classe', 'code_ue__code_ue')
        context['cours_options'] = [
            {
                'attribution_id': a.id,
                'code_ue': a.code_ue.code_ue,
                'intitule_ue': a.code_ue.intitule_ue,
                'classe': a.code_ue.classe,
                'enseignant': a.matricule.nom_complet,
                'grade': a.matricule.grade,
                'annee': a.annee_academique,
            }
            for a in attributions
        ]
        
        # Nombre de salles utilisées
        context['salles_count'] = ScheduleEntry.objects.exclude(
            salle__isnull=True
        ).exclude(salle='').values('salle').distinct().count()
        
        return context


class ScheduleEntryCreateView(CreateView):
    """Création d'une nouvelle entrée d'horaire"""
    model = ScheduleEntry
    form_class = ScheduleEntryForm
    template_name = 'attribution/schedule_entry_form.html'
    success_url = reverse_lazy('attribution:schedule_entry_list')
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique
        context = super().get_context_data(**kwargs)
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        return context
    
    def form_valid(self, form):
        from reglage.models import AnneeAcademique, SemaineCours
        from .validators import ScheduleConflictValidator
        
        # Insérer automatiquement l'année académique en cours
        annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
        if annee_courante:
            form.instance.annee_academique = annee_courante.code
        
        # Calculer et sauvegarder le jour depuis cleaned_data
        if 'jour' in form.cleaned_data and form.cleaned_data['jour']:
            form.instance.jour = form.cleaned_data['jour']
        
        # Sauvegarder la salle depuis cleaned_data
        if 'salle' in form.cleaned_data and form.cleaned_data['salle']:
            form.instance.salle = form.cleaned_data['salle']
        
        # Sauvegarder le créneau depuis cleaned_data
        if 'creneau' in form.cleaned_data and form.cleaned_data['creneau']:
            form.instance.creneau = form.cleaned_data['creneau']
        
        # Sauvegarder le numéro de semaine depuis SemaineCours
        if form.instance.semaine_debut:
            try:
                semaine_obj = SemaineCours.objects.get(date_debut=form.instance.semaine_debut)
                form.instance.numero_semaine = semaine_obj.numero_semaine
            except SemaineCours.DoesNotExist:
                pass
        
        # *** VALIDATION DES CONFLITS ***
        print(f"\n=== VALIDATION DES CONFLITS ===")
        print(f"Attribution: {form.instance.attribution}")
        print(f"Jour: {form.instance.jour}")
        print(f"Créneau: {form.instance.creneau}")
        print(f"Semaine: {form.instance.semaine_debut}")
        print(f"Salle: {form.instance.salle}")
        
        validation_result = ScheduleConflictValidator.validate_schedule_entry(
            attribution=form.instance.attribution,
            jour=form.instance.jour,
            creneau=form.instance.creneau,
            semaine=form.instance.semaine_debut,
            salle=form.instance.salle,
            exclude_id=None  # Pas d'exclusion pour création
        )
        
        print(f"Résultat validation: {validation_result}")
        print(f"Valid: {validation_result['valid']}")
        print(f"Errors: {validation_result['errors']}")
        
        # Si des conflits sont détectés, afficher les erreurs et bloquer
        if not validation_result['valid']:
            print(f"CONFLIT DÉTECTÉ! Ajout de {len(validation_result['errors'])} message(s) d'erreur")
            for error in validation_result['errors']:
                messages.error(self.request, error)
                print(f"  - {error}")
            return self.form_invalid(form)
        
        # Afficher les avertissements s'il y en a
        for warning in validation_result['warnings']:
            messages.warning(self.request, warning)
        
        messages.success(self.request, "✅ Horaire créé avec succès. Aucun conflit détecté.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la création de l'horaire. Vérifiez les données.")
        return super().form_invalid(form)


class ScheduleEntryUpdateView(UpdateView):
    """Modification d'une entrée d'horaire existante"""
    model = ScheduleEntry
    form_class = ScheduleEntryForm
    template_name = 'attribution/schedule_entry_form.html'
    success_url = reverse_lazy('attribution:schedule_entry_list')
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique
        context = super().get_context_data(**kwargs)
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        return context
    
    def form_valid(self, form):
        from reglage.models import SemaineCours
        from .validators import ScheduleConflictValidator
        
        # Calculer et sauvegarder le jour depuis cleaned_data
        if 'jour' in form.cleaned_data and form.cleaned_data['jour']:
            form.instance.jour = form.cleaned_data['jour']
        
        # Sauvegarder la salle depuis cleaned_data
        if 'salle' in form.cleaned_data and form.cleaned_data['salle']:
            form.instance.salle = form.cleaned_data['salle']
        
        # Sauvegarder le créneau depuis cleaned_data
        if 'creneau' in form.cleaned_data and form.cleaned_data['creneau']:
            form.instance.creneau = form.cleaned_data['creneau']
        
        # Sauvegarder le numéro de semaine depuis SemaineCours
        if form.instance.semaine_debut:
            try:
                semaine_obj = SemaineCours.objects.get(date_debut=form.instance.semaine_debut)
                form.instance.numero_semaine = semaine_obj.numero_semaine
            except SemaineCours.DoesNotExist:
                pass
        
        # *** VALIDATION DES CONFLITS ***
        validation_result = ScheduleConflictValidator.validate_schedule_entry(
            attribution=form.instance.attribution,
            jour=form.instance.jour,
            creneau=form.instance.creneau,
            semaine=form.instance.semaine_debut,
            salle=form.instance.salle,
            exclude_id=form.instance.id  # Exclure l'horaire actuel de la vérification
        )
        
        # Si des conflits sont détectés, afficher les erreurs et bloquer
        if not validation_result['valid']:
            for error in validation_result['errors']:
                messages.error(self.request, error)
            return self.form_invalid(form)
        
        # Afficher les avertissements s'il y en a
        for warning in validation_result['warnings']:
            messages.warning(self.request, warning)
        
        messages.success(self.request, "✅ Horaire modifié avec succès. Aucun conflit détecté.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la modification de l'horaire.")
        return super().form_invalid(form)


@require_GET
def autocomplete_ues(request):
    """Vue pour l'autocomplétion des UEs"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # Recherche dans les attributions existantes
    attributions = Attribution.objects.select_related('code_ue').filter(
        Q(code_ue__code_ue__icontains=query) |
        Q(code_ue__intitule_ue__icontains=query) |
        Q(code_ue__intitule_ec__icontains=query) |
        Q(code_ue__classe__icontains=query)
    ).distinct()[:10]  # Limiter à 10 résultats
    
    results = []
    for attr in attributions:
        results.append({
            'id': attr.id,
            'text': f"{attr.code_ue.code_ue} - {attr.code_ue.intitule_ue} - {attr.code_ue.intitule_ec or ''} - {attr.code_ue.classe}",
            'code_ue': attr.code_ue.code_ue,
            'intitule_ue': attr.code_ue.intitule_ue,
            'intitule_ec': attr.code_ue.intitule_ec,
            'classe': attr.code_ue.classe
        })
    
    return JsonResponse({'results': results})


def schedule_conflicts_report(request):
    """Affiche un rapport des conflits pour une semaine donnée"""
    from .validators import ScheduleConflictValidator
    from reglage.models import SemaineCours
    
    # Récupérer la semaine sélectionnée ou la semaine en cours
    semaine_param = request.GET.get('semaine')
    
    if semaine_param:
        try:
            y, m, d = [int(x) for x in semaine_param.split('-')]
            semaine_date = datetime(y, m, d).date()
        except:
            semaine_date = None
    else:
        # Utiliser la semaine en cours par défaut
        semaine_en_cours = SemaineCours.objects.filter(est_en_cours=True).first()
        semaine_date = semaine_en_cours.date_debut if semaine_en_cours else None
    
    conflicts_report = None
    if semaine_date:
        conflicts_report = ScheduleConflictValidator.get_conflicts_for_week(semaine_date)
    
    # Récupérer toutes les semaines pour le sélecteur
    semaines_cours = SemaineCours.objects.all().order_by('numero_semaine')
    
    context = {
        'conflicts_report': conflicts_report,
        'semaine_selectionnee': semaine_date,
        'semaines_cours': semaines_cours,
    }
    
    return render(request, 'attribution/conflicts_report.html', context)


@csrf_exempt
@require_http_methods(['POST'])
def schedule_entry_delete(request, pk):
    """Suppression d'une entrée d'horaire"""
    try:
        # Utiliser une transaction atomique pour garantir la cohérence
        with transaction.atomic():
            entry = ScheduleEntry.objects.select_for_update().get(pk=pk)
            
            # Récupération des infos pour le message
            info = f"{entry.attribution} - {entry.jour} {entry.creneau}"
            
            # Supprimer l'horaire
            entry.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Horaire {info} supprimé avec succès'
        })
    except ScheduleEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Horaire non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)


def generer_pdf_heures_supplementaires(request, attributions, annee_academique, section):
    """Générer un PDF des heures supplémentaires par grade et par section"""
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import PageBreak
    from reportlab.lib.units import inch
    
    # Ordre des grades pour le tri
    GRADE_ORDER = {
        'PE': 1, 'PO': 2, 'P': 3, 'PA': 4, 'CT': 5, 'ASS2': 6, 'ASS1': 7,
    }
    
    def get_grade_priority(grade):
        if not grade:
            return 999
        return GRADE_ORDER.get(grade.upper().strip(), 100)
    
    # Grouper par section puis par grade
    stats_par_section = {}
    
    for attribution in attributions:
        teacher_section = attribution.matricule.section or "Non définie"
        grade = attribution.matricule.grade or "Non spécifié"
        
        if teacher_section not in stats_par_section:
            stats_par_section[teacher_section] = {}
        
        if grade not in stats_par_section[teacher_section]:
            stats_par_section[teacher_section][grade] = {
                'grade': grade,
                'enseignants': set(),
                'nombre_cours': 0,
                'total_cmi': 0,
                'total_td_tp': 0,
                'total_heures': 0,
            }
        
        # Ajouter les statistiques
        stats_par_section[teacher_section][grade]['enseignants'].add(attribution.matricule.matricule)
        stats_par_section[teacher_section][grade]['nombre_cours'] += 1
        
        cmi = float(attribution.code_ue.cmi) if attribution.code_ue.cmi else 0
        td_tp = float(attribution.code_ue.td_tp) if attribution.code_ue.td_tp else 0
        
        stats_par_section[teacher_section][grade]['total_cmi'] += cmi
        stats_par_section[teacher_section][grade]['total_td_tp'] += td_tp
        stats_par_section[teacher_section][grade]['total_heures'] += (cmi + td_tp)
    
    # Créer le PDF en mode portrait
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,  # Portrait au lieu de landscape
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#181c34'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#495057'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#181c34'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # En-tête avec image
    from django.conf import settings
    import os
    from reportlab.platypus import Image
    
    entete_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    if os.path.exists(entete_path):
        img = Image(entete_path, width=doc.width, height=1.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 10))
    
    # Section d'abord
    if section and section != 'ALL':
        try:
            from reglage.models import Section as SectionModel
            section_obj = SectionModel.objects.filter(CodeSection=section).first()
            section_designation = section_obj.DesignationSection if section_obj else section
            section_text = f"SECTION : {section_designation.upper()}"
        except:
            section_text = f"SECTION : {section.upper()}"
        elements.append(Paragraph(section_text, section_style))
    
    # Année académique ensuite
    info_text = f"<b>Année Académique:</b> {annee_academique or 'Toutes'}"
    elements.append(Paragraph(info_text, subtitle_style))
    
    # Titre principal en dernier
    titre = "RAPPORT DES HEURES SUPPLÉMENTAIRES PAR GRADE"
    elements.append(Paragraph(titre, title_style))
    elements.append(Spacer(1, 15))
    
    # Parcourir chaque section
    for idx_section, (section_name, grades_stats) in enumerate(sorted(stats_par_section.items())):
        if idx_section > 0:
            elements.append(PageBreak())
        
        # Trier les grades
        grades_sorted = sorted(
            grades_stats.items(),
            key=lambda x: get_grade_priority(x[0])
        )
        
        # Tableau des statistiques (en-têtes raccourcis pour format portrait)
        data = [['Grade', 'Nb. Ens.', 'Nb. Cours', 'CMI (h)', 'TD/TP (h)', 'Total (h)']]
        
        section_total_enseignants = set()
        section_total_cours = 0
        section_total_cmi = 0
        section_total_td_tp = 0
        section_total_heures = 0
        
        for grade, stats in grades_sorted:
            nb_enseignants = len(stats['enseignants'])
            section_total_enseignants.update(stats['enseignants'])
            section_total_cours += stats['nombre_cours']
            section_total_cmi += stats['total_cmi']
            section_total_td_tp += stats['total_td_tp']
            section_total_heures += stats['total_heures']
            
            data.append([
                grade,
                str(nb_enseignants),
                str(stats['nombre_cours']),
                f"{stats['total_cmi']:.1f}",
                f"{stats['total_td_tp']:.1f}",
                f"{stats['total_heures']:.1f}",
            ])
        
        # Ligne de total
        data.append([
            Paragraph('<b>TOTAL</b>', styles['Normal']),
            Paragraph(f"<b>{len(section_total_enseignants)}</b>", styles['Normal']),
            Paragraph(f"<b>{section_total_cours}</b>", styles['Normal']),
            Paragraph(f"<b>{section_total_cmi:.1f}</b>", styles['Normal']),
            Paragraph(f"<b>{section_total_td_tp:.1f}</b>", styles['Normal']),
            Paragraph(f"<b>{section_total_heures:.1f}</b>", styles['Normal']),
        ])
        
        # Créer le tableau (largeurs ajustées pour format portrait)
        col_widths = [60, 100, 80, 70, 70, 80]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#495057')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
    
    # Générer le PDF
    doc.build(elements)
    
    # Retourner la réponse
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f'heures_supplementaires_grade_{annee_academique or "toutes"}.pdf'.replace(' ', '_')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


def heures_supplementaires_par_grade(request):
    """Vue pour afficher les heures supplémentaires attribuées par grade"""
    from django.db.models import Sum, Count, F
    from django.db.models.functions import Coalesce
    
    # Récupérer l'année académique sélectionnée (optionnel)
    annee_academique = request.GET.get('annee_academique')
    section = request.GET.get('section')
    format_pdf = request.GET.get('format') == 'pdf'
    
    # Filtrer les attributions de type "supplementaire"
    attributions = Attribution.objects.filter(type_charge='Supplementaire').select_related('matricule', 'code_ue')
    
    # Filtrer par année si spécifiée
    if annee_academique:
        attributions = attributions.filter(annee_academique=annee_academique)
    
    # Filtrer par section si spécifiée
    if section and section != 'ALL':
        from django.db.models import Q
        try:
            from reglage.models import Section as SectionModel
            section_obj = SectionModel.objects.filter(CodeSection=section).first()
            section_designation = section_obj.DesignationSection if section_obj else section
            
            attributions = attributions.filter(
                Q(matricule__section=section) | 
                Q(matricule__section=section_designation) |
                Q(matricule__section__icontains=section_designation)
            )
        except:
            attributions = attributions.filter(matricule__section=section)
    
    # Si format PDF demandé, générer le PDF
    if format_pdf:
        return generer_pdf_heures_supplementaires(request, attributions, annee_academique, section)
    
    # Grouper par grade et calculer les statistiques
    stats_par_grade = {}
    
    for attribution in attributions:
        grade = attribution.matricule.grade if attribution.matricule.grade else "Non spécifié"
        
        if grade not in stats_par_grade:
            stats_par_grade[grade] = {
                'grade': grade,
                'nombre_enseignants': set(),
                'nombre_cours': 0,
                'total_cmi': 0,
                'total_td_tp': 0,
                'total_heures': 0,
            }
        
        # Ajouter l'enseignant (set pour éviter les doublons)
        stats_par_grade[grade]['nombre_enseignants'].add(attribution.matricule.matricule)
        
        # Compter le cours
        stats_par_grade[grade]['nombre_cours'] += 1
        
        # Calculer les heures
        cmi = float(attribution.code_ue.cmi) if attribution.code_ue.cmi else 0
        td_tp = float(attribution.code_ue.td_tp) if attribution.code_ue.td_tp else 0
        
        stats_par_grade[grade]['total_cmi'] += cmi
        stats_par_grade[grade]['total_td_tp'] += td_tp
        stats_par_grade[grade]['total_heures'] += (cmi + td_tp)
    
    # Convertir les sets en nombres
    for grade in stats_par_grade:
        stats_par_grade[grade]['nombre_enseignants'] = len(stats_par_grade[grade]['nombre_enseignants'])
    
    # Convertir en liste pour le template et trier par grade
    stats_list = sorted(stats_par_grade.values(), key=lambda x: x['grade'])
    
    # Calculer les totaux généraux
    totaux = {
        'nombre_enseignants': sum(s['nombre_enseignants'] for s in stats_list),
        'nombre_cours': sum(s['nombre_cours'] for s in stats_list),
        'total_cmi': sum(s['total_cmi'] for s in stats_list),
        'total_td_tp': sum(s['total_td_tp'] for s in stats_list),
        'total_heures': sum(s['total_heures'] for s in stats_list),
    }
    
    # Récupérer les années académiques disponibles
    annees_disponibles = list(Attribution.objects.filter(
        type_charge='Supplementaire'
    ).values_list('annee_academique', flat=True).distinct().order_by('-annee_academique'))
    
    # Récupérer les sections disponibles
    from teachers.models import Teacher
    sections_disponibles = list(Teacher.objects.exclude(
        section__isnull=True
    ).exclude(
        section=''
    ).values_list('section', flat=True).distinct().order_by('section'))
    
    context = {
        'stats_par_grade': stats_list,
        'totaux': totaux,
        'annee_selectionnee': annee_academique,
        'annees_disponibles': annees_disponibles,
        'sections_disponibles': sections_disponibles,
        'section_selectionnee': section,
    }
    
    # Si la requête est en AJAX, retourner en JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context, safe=False)
    
    # Sinon, retourner le template HTML
    return render(request, 'attribution/heures_supplementaires_grade.html', context)

def imprimer_charges_section(request):
    """Générer un PDF des charges regroupées par section d'appartenance des enseignants"""
    from django.db.models import Q, Sum
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import PageBreak
    from reportlab.lib.units import inch
    from datetime import datetime
    from reglage.models import Departement
    
    # Récupérer les paramètres
    annee_academique = request.GET.get('annee_academique')
    section = request.GET.get('section')
    type_charge = request.GET.get('type_charge')
    
    if not annee_academique or not section:
        return HttpResponse("Paramètres manquants : année académique et section sont requis", status=400)
    
    # Filtrer les attributions
    attributions = Attribution.objects.select_related('matricule', 'code_ue').filter(
        annee_academique=annee_academique
    )
    
    if type_charge:
        attributions = attributions.filter(type_charge=type_charge)
    
    # Récupérer la désignation complète de la section
    section_designation = section
    section_code = section
    if section != 'ALL':
        try:
            from reglage.models import Section as SectionModel
            section_obj = SectionModel.objects.filter(CodeSection=section).first()
            if section_obj:
                section_designation = section_obj.DesignationSection
                section_code = section_obj.CodeSection
        except:
            pass
    
    # Filtrer par section d'appartenance des enseignants
    # Essayer à la fois par code et par désignation
    if section != 'ALL':
        from django.db.models import Q
        attributions = attributions.filter(
            Q(matricule__section=section_code) | 
            Q(matricule__section=section_designation) |
            Q(matricule__section__icontains=section_designation)
        )
    
    # Vérifier s'il y a des données
    if not attributions.exists():
        return HttpResponse(
            f"Aucune attribution trouvée pour la section '{section_designation}' ({section_code}) "
            f"et l'année académique {annee_academique}. "
            f"Vérifiez que les enseignants ont bien leur section renseignée dans leur fiche.",
            status=404
        )
    
    # Ordre des grades pour le tri
    GRADE_ORDER = {
        'PE': 1,
        'PO': 2,
        'P': 3,
        'PA': 4,
        'CT': 5,
        'ASS2': 6,
        'ASS1': 7,
    }
    
    def get_grade_priority(grade):
        """Retourne la priorité du grade pour le tri"""
        if not grade:
            return 999  # Les enseignants sans grade à la fin
        grade_upper = grade.upper().strip()
        return GRADE_ORDER.get(grade_upper, 100)  # Grade inconnu après les connus mais avant les None
    
    # Grouper par section puis par département des cours
    attributions_par_section = {}
    sections_order = []
    
    for attribution in attributions.order_by('code_ue__departement'):
        # Utiliser la section d'appartenance de l'enseignant
        teacher_section = attribution.matricule.section or "Non définie"
        
        if teacher_section not in attributions_par_section:
            attributions_par_section[teacher_section] = {}
            sections_order.append(teacher_section)
        
        # Grouper par département du cours
        dept = attribution.code_ue.departement or "Non défini"
        if dept not in attributions_par_section[teacher_section]:
            attributions_par_section[teacher_section][dept] = []
        
        attributions_par_section[teacher_section][dept].append(attribution)
    
    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Style pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#181c34'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#495057'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.white,
        spaceAfter=8,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    dept_title_style = ParagraphStyle(
        'DeptTitle',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#181c34'),
        spaceAfter=8,
        spaceBefore=8,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # En-tête avec image
    from django.conf import settings
    import os
    from reportlab.platypus import Image
    
    entete_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    if os.path.exists(entete_path):
        img = Image(entete_path, width=doc.width, height=1.5*inch)
        elements.append(img)
        elements.append(Spacer(1, 10))
    else:
        # Fallback si l'image n'existe pas
        header_data = [
            [Paragraph('<b>RÉPUBLIQUE DÉMOCRATIQUE DU CONGO</b>', ParagraphStyle('header', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER))],
            [Paragraph('<b>MINISTÈRE DE L\'ENSEIGNEMENT SUPÉRIEUR ET UNIVERSITAIRE</b>', ParagraphStyle('header', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER))],
        ]
        header_table = Table(header_data, colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 15))
    
    # Titre principal
    titre = "LISTE DES CHARGES HORAIRES PAR SECTION"
    if section != 'ALL':
        titre = f"LISTE DES CHARGES HORAIRES - SECTION {section_designation.upper()}"
    
    elements.append(Paragraph(titre, title_style))
    
    # Informations - uniquement l'année académique
    info_text = f"<b>Année Académique:</b> {annee_academique}"
    elements.append(Paragraph(info_text, subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Parcourir chaque section
    for idx_section, section_name in enumerate(sections_order):
        if idx_section > 0:
            elements.append(PageBreak())
        
        section_depts = attributions_par_section[section_name]
        
        # Compteurs pour la section
        section_nb_enseignants = set()
        section_nb_cours = 0
        
        # Parcourir chaque département de la section
        for dept_name in sorted(section_depts.keys()):
            dept_attributions = section_depts[dept_name]
            
            # En-tête département
            dept_header = Paragraph(f"🏛️ DÉPARTEMENT: {dept_name.upper()}", dept_title_style)
            elements.append(dept_header)
            elements.append(Spacer(1, 8))
            
            # Grouper par enseignant dans ce département
            enseignants_charges = {}
            for attr in dept_attributions:
                teacher_key = (attr.matricule.matricule, attr.matricule.nom_complet, attr.matricule.grade, attr.matricule.departement)
                if teacher_key not in enseignants_charges:
                    enseignants_charges[teacher_key] = []
                enseignants_charges[teacher_key].append(attr)
                section_nb_enseignants.add(attr.matricule.matricule)
            
            
            # Trier les enseignants par grade puis par nom
            enseignants_sorted = sorted(
                enseignants_charges.items(),
                key=lambda x: (get_grade_priority(x[0][2]), x[0][1])  # x[0][2] = grade, x[0][1] = nom
            )
            
            # Créer le tableau pour ce département
            for (matricule, nom, grade, dept), charges in enseignants_sorted:
                # En-tête enseignant
                teacher_header = f"{grade or ''} {nom}".strip()
                teacher_para = Paragraph(f"<b>{teacher_header}</b>", styles['Normal'])
                teacher_table = Table([[teacher_para]], colWidths=[doc.width])
                teacher_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e9ecef')),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(teacher_table)
                
                # Tableau des charges
                data = [['Code UE', 'Intitulé UE', 'Classe', 'Semestre', 'Crédit', 'Volume horaire (h)', 'Type de charge']]
                
                for charge in charges:
                    cmi = float(charge.code_ue.cmi or 0)
                    td_tp = float(charge.code_ue.td_tp or 0)
                    total = cmi + td_tp
                    
                    section_nb_cours += 1
                    
                    # Classe avec retours à la ligne
                    classe_text = (charge.code_ue.classe or '—').replace(',', '<br/>')
                    
                    data.append([
                        charge.code_ue.code_ue,
                        Paragraph(charge.code_ue.intitule_ue[:60], styles['Normal']),
                        Paragraph(classe_text, ParagraphStyle('classe', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER)),
                        charge.code_ue.semestre or '—',
                        str(charge.code_ue.credit or 0),
                        str(int(total)),
                        charge.type_charge if charge.type_charge else '—'
                    ])
                
                # Créer le tableau
                col_widths = [60, 220, 80, 50, 45, 70, 100]
                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#495057')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                    ('TOPPADDING', (0, 1), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 10))
            
            # Séparateur entre départements
            elements.append(Spacer(1, 12))
        
        # Fin de section
        elements.append(Spacer(1, 20))
    
    # Générer le PDF
    doc.build(elements)
    
    # Retourner la réponse
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f'charges_section_{section}_{annee_academique}.pdf'.replace(' ', '_')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response