from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import AttributionForm, ScheduleEntryForm
from .views_schedule import get_ues_by_classe
from teachers.models import Teacher
from reglage.models import Classe
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
import re
import traceback

# Fonction pour ne garder que le nom de famille
def truncate_teacher_name(full_name):
    if not full_name:
        return ''
    # Prendre uniquement le premier mot (nom de famille)
    return full_name.split()[0] if full_name.strip() else ''

# Fonction pour tronquer les intitulés des UE
def truncate_ue_title(title):
    if not title:
        return ''
        
    # Dictionnaire d'abréviations courantes
    abbreviations = {
        'didactique': 'Didact.',
        'informatique': 'Info',
        'introduction': 'Intro.',
        'programmation': 'Prog.',
        'développement': 'Dév.',
        'application': 'Appli.',
        'technologie': 'Techno.',
        'système': 'Sys.',
        'réseau': 'Réseau',
        'base de données': 'BD',
        'mathématique': 'Math.',
        'physique': 'Phys.',
        'chimie': 'Chimie',
        # 'chimie analytique': 'Chimie An.',  # Ne plus abréger chimie analytique
        'biologie': 'Bio.',
        'économie': 'Éco.',
        'gestion': 'Gest.',
        'communication': 'Com.',
        'langue': 'Lang.',
        'français': 'Fr.',
        'anglais': 'Angl.',
        'espagnol': 'Esp.',
        'allemand': 'All.',
        'histoire': 'Hist.',
        'géographie': 'Géo.',
        'philosophie': 'Philo.',
        'psychologie': 'Psy.',
        'sociologie': 'Socio.',
        'pédagogie': 'Pédago.',
        'méthodologie': 'Méthodo.'
    }
    
    # Remplacer les expressions complètes (les plus longues d'abord)
    lower_title = title.lower()
    
    # Trier les clés par longueur décroissante pour remplacer les expressions les plus longues d'abord
    sorted_abbr = sorted(abbreviations.items(), key=lambda x: -len(x[0]))
    
    # Faire une passe pour les remplacements en respectant la casse
    for word, abbr in sorted_abbr:
        if word in lower_title:
            # Remplacer en respectant la casse d'origine
            title = re.sub(r'\b' + re.escape(word) + r'\b', 
                          abbr, 
                          title, 
                          flags=re.IGNORECASE)
            # Mettre à jour la version en minuscules pour les prochaines vérifications
            lower_title = title.lower()
    
    # Retourner le titre avec les abréviations mais sans troncature
    return title


# Configuration de wkhtmltopdf
# config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

def attribution_list(request):
    from accounts.organisation_utils import filter_queryset_by_organisation, get_user_organisation
    
    teachers = Teacher.objects.all().order_by('nom_complet')
    
    # Debug: Vérifier l'organisation de l'utilisateur
    user_org = get_user_organisation(request.user)
    print(f"DEBUG - User: {request.user.username}, Organisation: {user_org}, Is superuser: {request.user.is_superuser}")
    print(f"DEBUG - Total cours avant filtre: {Cours_Attribution.objects.count()}")
    
    # Afficher la répartition des cours par organisation et section
    from django.db.models import Count
    repartition = Cours_Attribution.objects.values('organisation__code', 'organisation__nom').annotate(count=Count('id'))
    print("DEBUG - Répartition des cours par organisation:")
    for r in repartition:
        print(f"  {r['organisation__code']} ({r['organisation__nom']}): {r['count']} cours")
    
    repartition_section = Cours_Attribution.objects.values('section').annotate(count=Count('id'))
    print("DEBUG - Répartition des cours par section:")
    for r in repartition_section:
        print(f"  Section {r['section']}: {r['count']} cours")
    
    # Filtrer les cours par organisation (via le champ section)
    cours_attributions = filter_queryset_by_organisation(Cours_Attribution.objects, request.user, field_name='section').order_by('code_ue')
    print(f"DEBUG - Total cours après filtre: {cours_attributions.count()}")
    print(f"DEBUG - Code section recherché: {user_org.code if user_org else 'None'}")
    
    # Filtrer la liste déroulante des cours par organisation (via le champ section)
    if user_org:
        courses = Course.objects.filter(section=user_org.code).order_by('code_ue')
    else:
        courses = Course.objects.all().order_by('code_ue')
    
    # Récupérer la liste unique des départements (filtrée par organisation via section)
    departements = filter_queryset_by_organisation(Cours_Attribution.objects, request.user, field_name='section').values_list('departement', flat=True).distinct().order_by('departement')
    
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

from django.http import JsonResponse

@require_http_methods(['POST'])
def add_course_attribution(request):
    import logging
    import traceback
    from django.views.decorators.csrf import csrf_exempt
    
    logger = logging.getLogger(__name__)
    response_data = {'success': False, 'error': None}
    
    try:
        # Afficher toutes les données POST reçues
        logger.info(f"Données POST reçues : {dict(request.POST)}")
        
        code_ue = request.POST.get('code_ue')
        logger.info(f"Tentative d'ajout du cours : {code_ue}")
        
        # Vérifier les en-têtes de la requête
        logger.info(f"En-têtes de la requête : {dict(request.headers)}")
        
        if not code_ue:
            error_msg = 'Le code UE est requis'
            logger.error(error_msg)
            response_data['error'] = error_msg
            return JsonResponse(response_data, status=400)
        
        # Chercher le cours dans la table Course
        course = Course.objects.filter(code_ue=code_ue).first()
        logger.info(f"Cours trouvé : {course}")
        
        if not course:
            error_msg = f'Le cours {code_ue} n\'existe pas dans la table des cours'
            logger.error(error_msg)
            response_data['error'] = error_msg
            return JsonResponse(response_data, status=404)
        
        # Vérifier si le cours existe déjà dans Cours_Attribution
        existing = Cours_Attribution.objects.filter(code_ue=code_ue).first()
        if existing:
            error_msg = f'Le cours {code_ue} existe déjà dans la liste des attributions (ID: {existing.id})'
            logger.warning(error_msg)
            response_data['error'] = error_msg
            return JsonResponse(response_data, status=409)  # 409 Conflict
            
        # Vérifier les données du cours source
        logger.info(f"Détails du cours source - Code: {course.code_ue}, Intitulé: {course.intitule_ue}, Classe: {course.classe}, Semestre: {course.semestre}")
        
        # Vérifier les champs obligatoires du modèle Cours_Attribution
        required_fields = ['code_ue', 'intitule_ue', 'classe', 'semestre']
        for field in required_fields:
            if not getattr(course, field, None):
                error_msg = f'Le champ {field} est manquant ou vide dans le cours source'
                logger.error(error_msg)
                messages.error(request, error_msg)
                return redirect('attribution:attribution_list')
        
        # Créer une nouvelle entrée dans la table Cours_Attribution
        try:
            # Préparer les données avec des valeurs par défaut
            # Si intitule_ec est vide, utiliser 'Non spécifié' comme valeur par défaut
            intitule_ec = course.intitule_ec if course.intitule_ec else f"EC - {course.intitule_ue}"
            
            cours_data = {
                'code_ue': course.code_ue,
                'intitule_ue': course.intitule_ue,
                'intitule_ec': intitule_ec,  # Utilisation de la valeur par défaut si vide
                'credit': course.credit or 0,
                'cmi': course.cmi or 0,
                'td_tp': course.td_tp or 0,
                'classe': course.classe or 'N/A',
                'semestre': course.semestre or 'S1',
                'departement': course.departement or 'N/A',
                'section': course.section,
                'organisation': course.organisation
            }
            
            logger.info(f"Données du cours préparées : {cours_data}")
            
            logger.info(f"Données du cours à créer : {cours_data}")
            
            # Créer l'instance avec les données préparées
            cours_attribution = Cours_Attribution(**cours_data)
            
            # Valider le modèle avant sauvegarde
            try:
                cours_attribution.full_clean()
                logger.info("Validation du modèle réussie")
                
                # Essayer de sauvegarder avec des informations détaillées
                try:
                    cours_attribution.save()
                    logger.info(f"Cours sauvegardé avec succès. ID: {cours_attribution.id}")
                    
                    # Succès - renvoyer une réponse JSON
                    response_data.update({
                        'success': True,
                        'message': f'Le cours {code_ue} a été ajouté avec succès',
                        'course_id': cours_attribution.id
                    })
                    return JsonResponse(response_data)
                    
                except Exception as save_error:
                    error_msg = f'Erreur lors de la sauvegarde : {str(save_error)}'
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    response_data['error'] = error_msg
                    return JsonResponse(response_data, status=500)
                    
            except Exception as validation_error:
                error_msg = f'Erreur de validation du modèle : {str(validation_error)}'
                logger.error(error_msg)
                
                # Ajouter les erreurs de validation détaillées à la réponse
                if hasattr(validation_error, 'error_dict'):
                    validation_errors = {}
                    for field, errors in validation_error.error_dict.items():
                        validation_errors[field] = [str(e) for e in errors]
                        logger.error(f"Erreur champ {field}: {errors}")
                    response_data['validation_errors'] = validation_errors
                
                response_data['error'] = error_msg
                return JsonResponse(response_data, status=400)
            
        except Exception as e:
            error_msg = f'Erreur lors de la création du cours : {str(e)}'
            logger.error(f"{error_msg} - Détails : {e.__class__.__name__} - {str(e)}")
            response_data['error'] = error_msg
            return JsonResponse(response_data, status=500)
            
    except Exception as e:
        error_msg = f'Erreur inattendue : {str(e)}'
        logger.error(f"{error_msg} - Détails : {e.__class__.__name__} - {str(e)}")
        response_data['error'] = error_msg
        return JsonResponse(response_data, status=500)

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
    from accounts.organisation_utils import get_user_organisation
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Récupérer l'organisation de l'utilisateur
        user_org = get_user_organisation(request.user)
        
        with transaction.atomic():
            # Supprimer tous les cours existants dans Cours_Attribution
            deleted_count = Cours_Attribution.objects.all().count()
            Cours_Attribution.objects.all().delete()
            logger.info(f"{deleted_count} cours supprimés de Cours_Attribution")
            
            # Migrer tous les cours de Course vers Cours_Attribution
            courses = Course.objects.all()
            count = 0
            errors = []
            
            for course in courses:
                try:
                    # Créer tous les cours avec l'organisation de l'utilisateur
                    Cours_Attribution.objects.create(
                        organisation=user_org,
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
                except Exception as e:
                    errors.append(f"Erreur pour {course.code_ue}: {str(e)}")
                    logger.error(f"Erreur migration cours {course.code_ue}: {str(e)}")
            
            if errors:
                messages.warning(request, f'{count} cours migrés avec {len(errors)} erreurs. Consultez les logs pour plus de détails.')
            else:
                messages.success(request, f'{count} cours ont été migrés avec succès depuis la table Course')
            
    except Exception as e:
        logger.error(f'Erreur lors de la migration : {str(e)}')
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

    print(f"Debogage recherche - Matricule: {matricule}, Annee: {annee_academique}, Type: {type_charge}")

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

    print(f"Nombre d'attributions trouvees : {attributions.count()}")
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
            
            # Dédupliquer les cours sélectionnés par code_ue
            seen_codes = set()
            unique_cours = []
            for cours in selected_cours:
                code_ue = cours.get('code_ue')
                if code_ue and code_ue not in seen_codes:
                    seen_codes.add(code_ue)
                    unique_cours.append(cours)
            
            selected_cours = unique_cours
            print(f"Cours après déduplication: {selected_cours}")

            attributions_created = []
            ids_to_delete = []  # Collecter les IDs des cours attribués pour suppression dans Cours_Attribution
            skipped_courses = []
            errors = []

            # Démarrage d'une transaction atomique
            with transaction.atomic():
                for cours in selected_cours:
                    # Validation de la structure de chaque cours
                    if not isinstance(cours, dict) or 'code_ue' not in cours:
                        return JsonResponse({
                            'success': False,
                            'message': f'Format de données incorrect pour le cours: {cours}'
                        }, status=400)

                    try:
                        # Récupération de l'enseignant
                        teacher = Teacher.objects.get(matricule=matricule)
                        
                        # Récupérer le cours depuis Cours_Attribution (table source) par code_ue
                        # Filtrer par organisation de l'utilisateur
                        from accounts.organisation_utils import get_user_organisation
                        user_org = get_user_organisation(request.user)
                        
                        print(f"DEBUG - User org: {user_org}, Code: {user_org.code if user_org else 'None'}")
                        print(f"DEBUG - Recherche cours: {cours['code_ue']}")
                        
                        if user_org:
                            cours_attr = Cours_Attribution.objects.filter(
                                code_ue=cours['code_ue'],
                                section=user_org.code
                            ).first()
                            print(f"DEBUG - Cours trouvé avec filtre org: {cours_attr}")
                        else:
                            cours_attr = Cours_Attribution.objects.filter(code_ue=cours['code_ue']).first()
                            print(f"DEBUG - Cours trouvé sans filtre: {cours_attr}")
                        
                        if not cours_attr:
                            error_msg = f"Cours avec code_ue {cours['code_ue']} non trouvé dans Cours_Attribution pour l'organisation {user_org.code if user_org else 'N/A'}"
                            print(f"ERROR - {error_msg}")
                            errors.append(error_msg)
                            continue
                        
                        # Récupérer le cours existant dans Course par code_ue et section
                        # Ne pas créer de doublon
                        try:
                            course = Course.objects.get(
                                code_ue=cours_attr.code_ue,
                                section=cours_attr.section
                            )
                            print(f"DEBUG - Cours existant trouvé: {course.code_ue}")
                        except Course.DoesNotExist:
                            # Si le cours n'existe pas, le créer
                            course = Course.objects.create(
                                code_ue=cours_attr.code_ue,
                                intitule_ue=cours_attr.intitule_ue,
                                intitule_ec=cours_attr.intitule_ec,
                                credit=cours_attr.credit,
                                cmi=cours_attr.cmi,
                                td_tp=cours_attr.td_tp,
                                classe=cours_attr.classe,
                                semestre=cours_attr.semestre,
                                departement=cours_attr.departement,
                                section=cours_attr.section,
                                organisation=cours_attr.organisation
                            )
                            print(f"DEBUG - Nouveau cours créé: {course.code_ue}")
                        except Course.MultipleObjectsReturned:
                            # Si plusieurs cours existent avec le même code_ue et section, prendre le premier
                            course = Course.objects.filter(
                                code_ue=cours_attr.code_ue,
                                section=cours_attr.section
                            ).first()
                            print(f"DEBUG - Plusieurs cours trouvés, utilisation du premier: {course.code_ue}")
                        
                        # Vérification si l'attribution existe déjà
                        existing_attribution = Attribution.objects.filter(
                            matricule=teacher,
                            code_ue=course,
                            annee_academique=annee
                        ).first()
                        
                        if existing_attribution:
                            # Si l'attribution existe déjà, on l'ignore et on continue
                            skipped_courses.append(f"{cours['code_ue']}")
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
                        ids_to_delete.append(cours_attr.id)

                    except Teacher.DoesNotExist:
                        errors.append(f"Enseignant avec matricule {matricule} non trouvé")
                    except Exception as e:
                        print(f"Erreur détaillée pour {cours['code_ue']}: {type(e).__name__}: {str(e)}")
                        errors.append(f"Erreur pour {cours['code_ue']}: {str(e)}")

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
        # Afficher tous les enseignants et cours sans filtrage par organisation
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
        from accounts.organisation_utils import get_user_organisation
        
        # Récupérer les données JSON
        data = json.loads(request.body)
        matricule = data.get('teacher_matricule')
        annee_academique = data.get('teacher_academic_year')
        type_charge = data.get('type_charge')
        code_ue = data.get('code_ue')
        
        # Récupérer l'organisation de l'utilisateur
        user_org = get_user_organisation(request.user)

        # Vérifier que toutes les données requises sont présentes
        if not all([matricule, annee_academique, type_charge, code_ue]):
            return JsonResponse({
                'success': False,
                'error': 'Tous les champs sont obligatoires'
            }, status=400)

        # Récupérer les objets liés - filtrer par organisation si applicable
        try:
            teacher_qs = Teacher.objects.all()
            if user_org:
                teacher_qs = teacher_qs.filter(section=user_org.code)
            teacher = teacher_qs.get(matricule=matricule)
        except Teacher.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Enseignant avec matricule {matricule} non trouvé dans votre organisation'
            }, status=404)
        
        # Chercher le cours (filtrer par organisation si applicable)
        course_qs = Course.objects.all()
        if user_org:
            course_qs = course_qs.filter(section=user_org.code)
        course = course_qs.filter(code_ue=code_ue).first()
        if not course:
            return JsonResponse({
                'success': False,
                'error': f'Cours avec code {code_ue} non trouvé dans votre organisation'
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
    from accounts.organisation_utils import get_user_organisation, filter_queryset_by_organisation
    
    # Vérifier si l'utilisateur appartient à une organisation
    user_org = get_user_organisation(request.user)
    
    attributions = Attribution.objects.select_related('matricule', 'code_ue')
    
    # Filtrer par organisation de l'utilisateur
    if user_org:
        # Filtrer les attributions par section de l'enseignant ou du cours
        attributions = attributions.filter(
            Q(matricule__section=user_org.code) | Q(code_ue__section=user_org.code)
        )
    
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
    
    # Calculer le nombre d'enseignants qui ont une charge (attribution) - filtré par organisation
    base_attributions = Attribution.objects.all()
    if user_org:
        base_attributions = base_attributions.filter(
            Q(matricule__section=user_org.code) | Q(code_ue__section=user_org.code)
        )
    teachers_with_assignments = base_attributions.values('matricule').distinct().count()
    
    # Récupérer toutes les UEs avec leurs attributions - filtrées par organisation
    cours_ues = Cours_Attribution.objects.all().order_by('code_ue')
    if user_org:
        cours_ues = cours_ues.filter(section=user_org.code)
    
    # Créer un dictionnaire UE -> Enseignants pour affichage rapide - filtré par organisation
    ue_enseignants = {}
    all_attributions = Attribution.objects.select_related('code_ue', 'matricule').all()
    if user_org:
        all_attributions = all_attributions.filter(
            Q(matricule__section=user_org.code) | Q(code_ue__section=user_org.code)
        )
    for attribution in all_attributions:
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
    
    # Récupérer les années et sections pour le modal heures supplémentaires
    from reglage.models import Section as SectionReglage
    annees_modal = list(AnneeAcademique.objects.all().order_by('-date_debut'))
    sections_modal = list(SectionReglage.objects.all().order_by('CodeSection'))
    if user_org:
        sections_modal = [s for s in sections_modal if s.CodeSection == user_org.code]
    
    # Filtrer les enseignants par organisation
    teachers = Teacher.objects.all().order_by('nom_complet')
    if user_org:
        teachers = teachers.filter(section=user_org.code)
    
    context = {
        'attributions': attributions,
        'teachers': teachers,
        'academic_years': academic_years,
        'annee_courante': annee_courante.code if annee_courante else None,
        'selected_teacher_name': attributions.first().matricule.nom_complet if attributions.exists() else '',
        'selected_year': annee_academique,
        'selected_type': type_charge,
        'selected_code_ue': code_ue,
        'teachers_with_assignments': teachers_with_assignments,
        'cours_ues': cours_ues,
        'ue_enseignants': ue_enseignants,
        'annees_modal': annees_modal,
        'sections_modal': sections_modal,
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
        canvas.drawRightString(A4[0]-20, 10, text)
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
    
    # Ajouter ligne de sous-total
    sous_total_row = ['', '', 'Sous-total', 
                    str(sum(float(attr.cmi or 0) for attr in cours_tries)), 
                    str(sum(float(attr.td_tp or 0) for attr in cours_tries)), 
                    str(sum(float(attr.cmi or 0) for attr in cours_tries) + sum(float(attr.td_tp or 0) for attr in cours_tries)), 
                    '', '']
    data.append(sous_total_row)
    
    # Combiner les en-têtes et les données
    all_data = header_data + data
    
    # Définir les largeurs de colonnes
    col_widths = [60, 180, 120, 40, 40, 40, 60, 60, 100]  # Largeurs des colonnes ajustées
    
    # Créer le tableau
    table = Table(all_data, colWidths=col_widths, repeatRows=1)
    
    # Style du tableau
    table_style = TableStyle([
        # Style des entêtes
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (3, 1), (4, 1)),  # Fusion des cellules pour "Heures prévues"
        
        # Style des cellules de données
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Style pour la ligne de sous-total
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('SPAN', (0, -1), (2, -1)),  # Fusion des 3 premières cellules pour le texte "Sous-total"
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
    from datetime import datetime, timedelta
    import locale
    from accounts.models import Role
    from accounts.organisation_utils import get_user_organisation
    from reglage.models import Classe as ClasseModel
    
    # Configurer la locale en français pour les noms de mois
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'French_France.1252')
        except:
            pass  # Si la locale française n'est pas disponible, continuer avec la locale par défaut
    
    # Récupérer le type d'horaire (cours ou examens)
    type_horaire = request.GET.get('type', 'cours')  # Par défaut: cours
    
    classe = request.GET.get('classe')  # Ex: L1BC ou juste L1
    annee = request.GET.get('annee')
    week_start = request.GET.get('semaine')  # YYYY-MM-DD
    chef_section_id = request.GET.get('chef_section')
    chef_adjoint_id = request.GET.get('chef_adjoint')
    section_code = request.GET.get('section', '')  # Code de la section
    attribution_id = request.GET.get('attribution_id')
    
    # Récupérer l'organisation de l'utilisateur
    user = request.user
    user_org = get_user_organisation(user)
    
    # Récupérer la désignation complète de la section depuis la base de données
    section_designation = ""
    if section_code:
        from reglage.models import Section
        try:
            section_obj = Section.objects.get(CodeSection=section_code)
            section_designation = section_obj.DesignationSection
        except Section.DoesNotExist:
            section_designation = section_code  # Fallback sur le code si non trouvé
    elif user_org:
        # Si pas de section_code spécifié, utiliser celle de l'organisation
        section_code = user_org.code
        section_designation = user_org.nom

    # Extraire le niveau (L1, L2, L3, M1, M2) de la classe
    import re
    from reportlab.platypus import PageBreak
    niveau_demande = None
    if classe:
        match = re.match(r'^(L[1-3]|M[1-2])', classe)
        if match:
            niveau_demande = match.group(1)
    
    # Récupérer les classes autorisées dynamiquement depuis la base de données
    if user_org:
        # Filtrer les classes par section de l'organisation (via mention -> departement -> section)
        classes_autorisees = list(ClasseModel.objects.filter(
            mention__departement__section__CodeSection=user_org.code
        ).values_list('CodeClasse', flat=True))
    else:
        # Admin: toutes les classes
        classes_autorisees = list(ClasseModel.objects.all().values_list('CodeClasse', flat=True))
    
    # Récupérer toutes les attributions
    all_attributions = Attribution.objects.select_related('matricule', 'code_ue')
    
    # Appliquer le filtre de section si l'utilisateur appartient à une organisation
    if user_org:
        if classes_autorisees:
            all_attributions = all_attributions.filter(code_ue__classe__in=classes_autorisees)
    
    if attribution_id:
        all_attributions = all_attributions.filter(id=attribution_id)
        if not classe and all_attributions.exists():
            classe = all_attributions.first().code_ue.classe
            match = re.match(r'^(L[1-3]|M[1-2])', classe)
            if match:
                niveau_demande = match.group(1)
    
    if annee:
        all_attributions = all_attributions.filter(annee_academique=annee)
    
    # Générer uniquement les pages pour les niveaux qui ont des cours
    if niveau_demande:
        niveaux_a_generer = [niveau_demande]
    else:
        # L'ordre des niveaux sera déterminé après avoir identifié ceux avec des cours
        niveaux_a_generer = ['L1', 'L2', 'L3', 'M1', 'M2']

    # Préparation PDF avec marges réduites pour optimiser l'espace
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10, leftMargin=10, topMargin=20, bottomMargin=15)
    
    # Colonnes pour chaque niveau - basées sur les classes autorisées (dynamique depuis la BDD)
    colonnes_par_niveau = {
        'L1': sorted([c for c in classes_autorisees if c.startswith('L1')]),
        'L2': sorted([c for c in classes_autorisees if c.startswith('L2')]),
        'L3': sorted([c for c in classes_autorisees if c.startswith('L3')]),
        'M1': sorted([c for c in classes_autorisees if c.startswith('M1')]),
        'M2': sorted([c for c in classes_autorisees if c.startswith('M2')]),
    }

    def get_col_key_from_classe(classe_val):
        """Extraire la clé de colonne depuis le champ classe (ex: L1BC, L2MI, L1PHYTO, etc.)"""
        if not classe_val:
            return None
        
        # Supprimer tous les espaces et convertir en majuscules
        classe_upper = classe_val.upper().strip().replace(' ', '')
        
        # Retourner la classe telle quelle si elle correspond au format niveau + mention
        # Format: L1, L2, L3, M1, M2 suivi de lettres (ex: L1PHYTO, L1BC, M1INFO)
        if re.match(r'^(L[1-3]|M[1-2])[A-Z]+$', classe_upper):
            return classe_upper
        
        return None
    
    days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    
    # Récupérer toutes les entries
    # Si aucune semaine ni année n'est spécifiée, afficher TOUTES les entrées (comme la liste)
    print(f"PDF: Paramètres reçus - week_start='{week_start}', annee='{annee}'")
    
    # Base queryset - filtré par organisation si applicable (via section du cours ou enseignant)
    base_queryset = ScheduleEntry.objects.select_related('attribution__code_ue', 'attribution__matricule')
    if user_org:
        from django.db.models import Q
        base_queryset = base_queryset.filter(
            Q(attribution__matricule__section=user_org.code) | 
            Q(attribution__code_ue__section=user_org.code)
        )
    
    if not week_start and not annee:
        print("PDF: Branche 1 - Aucun filtre")
        all_entries = base_queryset.all()
        print(f"PDF: Aucun filtre - Affichage de TOUTES les {all_entries.count()} entrées")
    elif week_start and not annee:
        print("PDF: Branche 2 - Filtre par semaine uniquement")
        try:
            y, m, d = [int(x) for x in week_start.split('-')]
            semaine_date = datetime(y, m, d).date()
            # Inclure toutes les entrées de la semaine (du lundi au samedi)
            semaine_fin = semaine_date + timedelta(days=5)  # 6 jours de cours
            # CORRECTION: Utiliser date_cours au lieu de semaine_debut
            all_entries = base_queryset.filter(
                date_cours__gte=semaine_date,
                date_cours__lte=semaine_fin
            )
            print(f"PDF: Filtre semaine du {semaine_date} au {semaine_fin}, trouvé {all_entries.count()} entrées")
            if all_entries.exists():
                print("Entrées trouvées:")
                for e in all_entries[:10]:
                    print(f"  - {e.attribution.code_ue.classe} | {e.attribution.code_ue.code_ue} | {e.jour} | date_cours={e.date_cours}")
        except Exception as ex:
            print(f"PDF: ERREUR dans branche 2 - {ex}")
            all_entries = ScheduleEntry.objects.none()
    else:
        print("PDF: Branche 3 - Filtre par année")
        all_entries = base_queryset.filter(
            annee_academique=annee if annee else all_attributions.first().annee_academique if all_attributions.exists() else '',
        )
        print(f"PDF: Après filtre année: {all_entries.count()} entrées")
        if week_start:
            try:
                y, m, d = [int(x) for x in week_start.split('-')]
                semaine_date = datetime(y, m, d).date()
                # Inclure toutes les entrées de la semaine (du lundi au samedi)
                semaine_fin = semaine_date + timedelta(days=5)  # 6 jours de cours
                # CORRECTION: Utiliser date_cours au lieu de semaine_debut
                all_entries = all_entries.filter(
                    date_cours__gte=semaine_date,
                    date_cours__lte=semaine_fin
                )
                print(f"PDF: Après filtre semaine: {all_entries.count()} entrées")
            except Exception as ex:
                print(f"PDF: ERREUR filtre semaine - {ex}")
                pass

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 8)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(A4[0]-20, 10, text)
        canvas.restoreState()

    # Debug: Afficher le nombre total d'entrées après filtrage
    print(f"\n=== TOTAL ENTREES APRES FILTRAGE ===")
    print(f"Nombre total d'entrées: {all_entries.count()}")
    if all_entries.exists():
        print("Exemples d'entrees:")
        for e in all_entries[:5]:
            creneau_info = f"{e.creneau.code}" if e.creneau else "None"
            print(f"  - ID={e.id} | classe={e.attribution.code_ue.classe} | code={e.attribution.code_ue.code_ue} | jour={e.jour} | creneau={creneau_info} | date_cours={e.date_cours}")
    else:
        # Si aucune entrée trouvée, afficher TOUTES les entrées de la base
        print("\n[ATTENTION] AUCUNE ENTREE TROUVEE AVEC LES FILTRES!")
        all_in_db = ScheduleEntry.objects.all()
        print(f"Total dans la base de donnees: {all_in_db.count()}")
        if all_in_db.exists():
            print("Toutes les entrees disponibles:")
            for e in all_in_db[:10]:
                creneau_info = f"{e.creneau.code}" if e.creneau else "None"
                print(f"  - ID={e.id} | classe={e.attribution.code_ue.classe} | code={e.attribution.code_ue.code_ue} | jour={e.jour} | creneau={creneau_info} | date_cours={e.date_cours} | semaine_debut={e.semaine_debut}")

    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('SchedTitle', parent=styles['Heading2'], fontSize=8, alignment=1, fontName='Times-Bold')
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10, alignment=1, wordWrap='CJK', fontName='Times-Roman')
    # Styles personnalisés
    ue_title_style = ParagraphStyle('UETitle', parent=styles['Normal'], fontSize=8, alignment=1, wordWrap=None, fontName='Times-Italic')
    teacher_style = ParagraphStyle('Teacher', parent=styles['Normal'], fontSize=8, alignment=1, wordWrap=None, fontName='Times-Roman')
    code_style = ParagraphStyle('Code', parent=styles['Normal'], fontSize=8, alignment=1, wordWrap=None, fontName='Times-Bold')
    
    # Calculer les dates de début et fin de semaine pour le titre
    semaine_info = ""
    numero_semaine_str = ""
    day_dates = {}
    
    # Si pas de semaine spécifiée, utiliser toutes les entrées
    if not week_start and all_entries.exists():
        # Trouver la plage de dates des entrées
        premiere_entree = all_entries.order_by('date_cours').first()
        derniere_entree = all_entries.order_by('-date_cours').first()
        
        if premiere_entree and derniere_entree and premiere_entree.date_cours and derniere_entree.date_cours:
            # Utiliser la première date comme référence pour le week_start
            week_start = premiere_entree.date_cours.strftime('%Y-%m-%d')
            
            # Calculer le numéro de semaine à partir de la première entrée
            from reglage.models import SemaineCours
            semaine_obj = SemaineCours.objects.filter(
                date_debut__lte=premiere_entree.date_cours,
                date_fin__gte=premiere_entree.date_cours
            ).first()
            if semaine_obj:
                numero_semaine_str = f"S{semaine_obj.numero_semaine}"
            
            print(f"PDF: Plage automatique detectee du {premiere_entree.date_cours} au {derniere_entree.date_cours}")
        else:
            # Fallback : utiliser la semaine en cours
            semaine_en_cours = SemaineCours.objects.filter(est_en_cours=True).first()
            if semaine_en_cours:
                week_start = semaine_en_cours.date_debut.strftime('%Y-%m-%d')
                numero_semaine_str = f"S{semaine_en_cours.numero_semaine}"
    
    if week_start:
        try:
            y, m, d = [int(x) for x in week_start.split('-')]
            date_reference = datetime(y, m, d).date()
            
            # Trouver le lundi de la semaine contenant cette date
            # weekday(): lundi=0, mardi=1, ..., dimanche=6
            jours_depuis_lundi = date_reference.weekday()
            date_debut = date_reference - timedelta(days=jours_depuis_lundi)  # Lundi
            date_fin = date_debut + timedelta(days=5)  # Samedi
            
            print(f"PDF: Date reference {date_reference}, Lundi de la semaine: {date_debut}, Samedi: {date_fin}")
            
            # Récupérer le numéro de semaine depuis SemaineCours
            from reglage.models import SemaineCours
            # Chercher la semaine qui contient le lundi
            semaine_obj = SemaineCours.objects.filter(
                date_debut__lte=date_debut,
                date_fin__gte=date_debut
            ).first()
            if semaine_obj:
                numero_semaine_str = f"S{semaine_obj.numero_semaine}"
            
            # Créer l'info avec le numéro de semaine si disponible
            if numero_semaine_str:
                semaine_info = f"{numero_semaine_str} : {date_debut.strftime('%d')} au {date_fin.strftime('%d %B %Y')}"
            else:
                semaine_info = f"{date_debut.strftime('%d')} au {date_fin.strftime('%d %B %Y')}"
            
            # Calculer les dates pour chaque jour
            days_map = {
                'Lundi': 0, 'Mardi': 1, 'Mercredi': 2, 
                'Jeudi': 3, 'Vendredi': 4, 'Samedi': 5
            }
            for day, offset in days_map.items():
                day_dates[day] = date_debut + timedelta(days=offset)
                print(f"PDF: {day} = {day_dates[day]}")
        except:
            semaine_info = week_start
    
    # Récupérer les créneaux depuis la table Creneau si disponible
    from reglage.models import Creneau
    
    # Filtrer les créneaux selon le type d'horaire et la section
    # IMPORTANT: Exclure le créneau 'TJ' car il ne doit jamais apparaître dans le PDF
    # TJ est juste un raccourci pour créer des entrées AM et PM
    if type_horaire == 'cours':
        # Pour les cours, filtrer par type_creneau
        creneaux_actifs = Creneau.objects.filter(
            est_actif=True, 
            type_creneau__in=['cours', 'les_deux']
        ).exclude(code='TJ').order_by('ordre', 'heure_debut')
    elif type_horaire == 'examens':
        # Pour les examens, filtrer par type_creneau et section
        if section_code:
            creneaux_actifs = Creneau.objects.filter(
                est_actif=True, 
                type_creneau__in=['examen', 'les_deux'],
                section__CodeSection=section_code
            ).exclude(code='TJ').order_by('ordre', 'heure_debut')
        else:
            # Si pas de section spécifiée, tous les créneaux d'examens
            creneaux_actifs = Creneau.objects.filter(
                est_actif=True, 
                type_creneau__in=['examen', 'les_deux']
            ).exclude(code='TJ').order_by('ordre', 'heure_debut')
    else:
        # Par défaut, tous les créneaux actifs (sauf TJ)
        creneaux_actifs = Creneau.objects.filter(est_actif=True).exclude(code='TJ').order_by('ordre', 'heure_debut')
    
    if creneaux_actifs.exists():
        # Utiliser les créneaux de la table Réglage
        slots = [(c.get_format_court(), c.code) for c in creneaux_actifs]
    else:
        # Fallback sur les créneaux par défaut
        slots = [('08h00-12h00', 'AM'), ('13h00-17h00', 'PM')]
    
    # Vérifier s'il y a des entrées avant de générer le PDF
    if not all_entries.exists():
        from django.contrib import messages
        messages.warning(request, "[ATTENTION] Aucun horaire trouvé avec les critères sélectionnés. Veuillez vérifier vos filtres.")
        from django.shortcuts import redirect
        return redirect('attribution:schedule_entry_list')
    
    # Boucle sur chaque niveau pour créer une page par niveau
    page_count = 0
    for niveau in niveaux_a_generer:
        # Filtrer les horaires pour ce niveau - utiliser startswith pour être précis
        entries_niveau = all_entries.filter(attribution__code_ue__classe__istartswith=niveau)
        
        # Debug: afficher le nombre d'horaires trouvés pour ce niveau
        print(f"\n=== Niveau {niveau} ===")
        print(f"Nombre d'horaires trouves: {entries_niveau.count()}")
        for e in entries_niveau:
            print(f"  - {e.attribution.code_ue.classe} | {e.attribution.code_ue.code_ue} | {e.attribution.matricule.nom_complet} | {e.jour} {e.creneau}")
        
        # Ne générer la page que si des horaires existent pour ce niveau
        if not entries_niveau.exists():
            print(f"Niveau {niveau} ignore : aucun cours programme")
            continue
        
        # Ajouter un saut de page si ce n'est pas la première page
        if page_count > 0:
            elements.append(PageBreak())
        page_count += 1
        
        # Titre selon l'image - avec la désignation complète de la section si fournie
        if section_designation:
            # Si la désignation commence déjà par "SECTION", ne pas le dupliquer
            if section_designation.upper().startswith("SECTION"):
                section_title = section_designation.upper()
            else:
                section_title = f"SECTION {section_designation.upper()}"
        else:
            section_title = "SECTION DES SCIENCES & TECHNOLOGIES"
        
        # Adapter le titre selon le type d'horaire
        if type_horaire == 'examens':
            titre_type = "Horaire des Examens"
        else:
            titre_type = "Horaire des Enseignements"
        
        titre = f"<b>{section_title}</b><br/>"\
                f"{titre_type} : semaine du {semaine_info}"
        titre_para = Paragraph(titre, ParagraphStyle('TitleCustom', parent=styles['Normal'], fontSize=8, alignment=1, fontName='Times-Bold', leading=10))
        elements.append(titre_para)
        elements.append(Spacer(1, 8))
        
        # Déterminer le semestre selon le niveau
        semestres_par_niveau = {
            'L1': 'Semestre 1',
            'L2': 'Semestre 3',
            'L3': 'Semestre 5',
            'M1': 'Semestre 1',
            'M2': 'Semestre 3'
        }
        
        # Afficher le semestre pour tous les niveaux
        semestre_display = semestres_par_niveau.get(niveau, 'Semestre 1')
        semestre_info = f"({semestre_display})"
        
        info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=7, alignment=1, fontName='Times-Roman', leading=9)
        semestre_para = Paragraph(semestre_info, info_style)
        elements.append(semestre_para)
        elements.append(Spacer(1, 4))
        
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
                by_col[col_key].append((e, a))
        
        # Finaliser la liste des colonnes triées
        col_keys = sorted(list(colonnes_detectees))
        
        # S'assurer que toutes les colonnes ont une liste (même vide)
        for col in col_keys:
            if col not in by_col:
                by_col[col] = []
        
        # Debug: afficher le nombre d'entrées par colonne
        print(f"PDF Niveau {niveau}: {len(col_keys)} colonnes detectees: {col_keys}")
        for col in col_keys:
            print(f"  Colonne {col}: {len(by_col[col])} entrées")
        
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
                        # e.creneau est maintenant un objet Creneau (ForeignKey) ou None
                        # Obtenir le code du créneau
                        creneau_code = e.creneau.code if e.creneau else None
                        
                        # Si le créneau est vide, afficher dans le premier créneau (AM) par défaut
                        if not creneau_code or creneau_code.strip() == '':
                            creneau_match = (slot_code == 'AM' or i == 0)
                        else:
                            # Comparaison flexible du code du créneau
                            creneau_match = (
                                creneau_code == slot_code or 
                                creneau_code.upper() == slot_code or
                                creneau_code.upper() == slot_code.upper()
                            )
                        
                        if e.jour == jour_label and creneau_match:
                            code = a.code_ue.code_ue or ''
                            title = truncate_ue_title(a.code_ue.intitule_ue or '')
                            ec = a.code_ue.intitule_ec or ''
                            teacher_name = truncate_teacher_name(a.matricule.nom_complet or '')
                            grade = a.matricule.grade or ''
                            
                            # Construire le texte avec EC si présent
                            if ec:
                                # Si EC existe, l'afficher après le titre de l'UE
                                ec_truncated = truncate_ue_title(ec)
                                if grade:
                                    txt = f"<b>{code}</b><br/><i>{title}</i><br/><i>{ec_truncated}</i><br/>{grade} {teacher_name}"
                                else:
                                    txt = f"<b>{code}</b><br/><i>{title}</i><br/><i>{ec_truncated}</i><br/>{teacher_name}"
                            else:
                                # Pas d'EC, affichage normal
                                if grade:
                                    txt = f"<b>{code}</b><br/><i>{title}</i><br/>{grade} {teacher_name}"
                                else:
                                    txt = f"<b>{code}</b><br/>{title}<br/>{teacher_name}"
                            items.append(txt)
                    
                    # Créer le contenu de la cellule - utiliser espace si vide
                    if items:
                        # Créer un style personnalisé pour le contenu de la cellule
                        style = ParagraphStyle(
                            'CellContent',
                            parent=styles['Normal'],
                            fontSize=7,  # Taille de police légèrement réduite
                            leading=8,   # Espacement entre les lignes réduit
                            alignment=1,
                            wordWrap='CJK',
                            fontName='Times-Roman',
                            splitLongWords=False,
                            spaceShrinkage=0.85,  # Réduit encore plus l'espacement
                            maxSpace=20,  # Largeur maximale avant troncature
                            ellipsis='...',
                            # Réduire les marges
                            leftIndent=0,
                            rightIndent=0,
                            firstLineIndent=0,
                            spaceBefore=0,
                            spaceAfter=0,
                            # Espacement entre les paragraphes
                            paragraphSpaceBefore=0,
                            paragraphSpaceAfter=0
                        )
                        # Joindre les éléments avec des sauts de ligne et créer un seul Paragraph
                        cell_content = '<br/><br/>'.join(items)
                        row.append(Paragraph(cell_content, style))
                    else:
                        row.append(Paragraph('&nbsp;', cell_style))  # Espace insécable HTML
                
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
        
        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),  # Lignes plus fines
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 7),  # Taille de police réduite pour l'en-tête
            # Réduire les marges et espacements
            ('LEFTPADDING', (0,0), (-1,-1), 1),  # Marge gauche réduite
            ('RIGHTPADDING', (0,0), (-1,-1), 1),  # Marge droite réduite
            ('TOPPADDING', (0,0), (-1,-1), 1),    # Marge haute réduite
            ('BOTTOMPADDING', (0,0), (-1,-1), 1), # Marge basse réduite
            # Hauteur de ligne réduite
            ('LEADING', (0,0), (-1,-1), 7),      # Espacement entre les lignes réduit
            ('FONTSIZE', (0,1), (-1,-1), 7),     # Taille de police réduite pour les données
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
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
        elements.append(Spacer(1, 10))  # Réduire l'espace avant les signatures
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
        sig_style = ParagraphStyle('SigStyle', parent=styles['Normal'], fontSize=8, alignment=0, fontName='Times-Roman')
        
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
        
        return JsonResponse({'success': True, 'saved': saved, 'message': f'[OK] {saved} horaire(s) cree(s) avec succes'})
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
    csae_info = None
    sgac_info = None
    if attributions.exists():
        enseignant_info = attributions.first().matricule
        
        # Récupérer le CSAE de la section de l'enseignant
        try:
            from teachers.models import Teacher
            csae_info = Teacher.objects.filter(
                fonction='CSAE',
                section=enseignant_info.section
            ).first()
        except:
            csae_info = None
        
        # Récupérer le SGAC (Secrétaire Général Académique)
        try:
            from teachers.models import Teacher
            sgac_info = Teacher.objects.filter(fonction='SGAC').first()
        except:
            sgac_info = None
    
    # Séparer les attributions par type de charge
    attributions_regulieres = attributions.filter(type_charge='Reguliere')
    attributions_supplementaires = attributions.filter(type_charge='Supplementaire')
    
    # Créer un buffer pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF avec l'orientation portrait
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
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
        canvas.drawRightString(A4[0]-20, 10, text)
        canvas.restoreState()

    elements = []
    
    # Ajouter l'en-tête institutionnelle
    header = create_header_table()
    elements.append(header)
    elements.append(Spacer(1, 2))
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=11,
        spaceAfter=10,
        alignment=1
    )
    
    # Style pour le texte des cellules
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
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
                print(f"Erreur lors de la creation de l'image arrondie: {e}")
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
        
        # Créer le tableau d'informations adapté au portrait (6 lignes x 2 colonnes)
        enseignant_data = [
            [Paragraph('Matricule en interne :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), enseignant_info.matricule],
            [Paragraph('Nom et post-noms :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), enseignant_info.nom_complet],
            [Paragraph('Grade :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), grade_designation],
            [Paragraph('Département :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), departement_designation],
            [Paragraph('Section :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), section_designation],
            [Paragraph('Année académique :', ParagraphStyle('LabelStyle', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=9)), annee_academique if annee_academique else 'Toutes les années']
        ]
        
        # Largeurs adaptées au portrait (première colonne 120px, deuxième colonne réduite de 2cm total: 358 - 56 ≈ 302px)
        info_table = Table(enseignant_data, colWidths=[120, 302])
        info_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # Deuxième colonne alignée à gauche
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Ajouter le titre "DESCRIPTION DE LA CHARGE HORAIRE POUR L'ANNEE ACADEMIQUE" responsive
        annee_display = annee_academique if annee_academique else 'Toutes les années'
        title_text = f"<u>DESCRIPTION DE LA CHARGE HORAIRE POUR L'ANNEE ACADEMIQUE  {annee_display}</u>"
        title_para = Paragraph(title_text, title_style)
        
        elements.append(title_para)
        elements.append(Spacer(1, 1))
        
        # Créer un tableau global avec infos à gauche alignées et photo à droite
        main_data = [[info_table, photo_element]]
        main_table = Table(main_data, colWidths=[422, 120])  # Total 542px pour s'adapter au tableau d'informations réduit de 2cm
        main_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),   # Tableau d'informations aligné à gauche
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('RIGHTPADDING', (0, 0), (0, 0), 5),
            ('TOPPADDING', (0, 0), (0, 0), 5),
            ('BOTTOMPADDING', (0, 0), (0, 0), 5),
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
        titre_table = Table(titre_data, colWidths=[529])  # Même largeur que le tableau de données augmenté
        titre_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
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
            'Crédits',
            'Classe',
            'Semestre'
        ]
        
        # Colonne double pour les heures prévues
        header_data = [
            ['Code', 'Intitulé U.E.', 'Intitulé EC', 'Heures prévues', '', 'Total', 'Crédits', 'Classe', 'Semestre'],
            ['', '', '', 'Présentiel', 'TP - TD', '', '', '', '']
        ]
        
        # Préparer les données
        data = []
        
        # Totaux pour calcul
        total_presentiel = 0
        total_tp_td = 0
        total_heures = 0
        total_credits = 0
        
        # Ajouter chaque attribution au tableau
        for attr in attributions:
            presentiel = attr.code_ue.cmi
            tp_td = attr.code_ue.td_tp
            total = presentiel + tp_td
            
            # Ajouter aux totaux
            total_presentiel += presentiel
            total_tp_td += tp_td
            total_heures += total
            total_credits += attr.code_ue.credit if attr.code_ue.credit else 0
            
            # Utiliser Paragraph pour permettre le retour à la ligne automatique dans les cellules
            row = [
                attr.code_ue.code_ue,
                Paragraph(attr.code_ue.intitule_ue, cell_style),
                Paragraph(attr.code_ue.intitule_ec or '', cell_style),
                str(presentiel),
                str(tp_td),
                str(total),
                str(attr.code_ue.credit) if attr.code_ue.credit else '0',
                Paragraph(attr.code_ue.classe or '', cell_style),
                attr.code_ue.semestre
            ]
            data.append(row)
        
        # Ajouter ligne de sous-total
        sous_total_row = ['', '', 'Sous-total ' + ('1' if titre == 'Charge régulière' else '2'), 
                        str(total_presentiel), str(total_tp_td), str(total_heures), str(total_credits), '', '']
        data.append(sous_total_row)
        
        # Combiner les en-têtes et les données
        all_data = header_data + data
        
        # Définir les largeurs de colonnes adaptées au portrait (total 529px = 501px + 28px)
        col_widths = [42, 95, 95, 58, 58, 58, 42, 42, 39]
        
        # Créer le tableau
        table = Table(all_data, colWidths=col_widths, repeatRows=2)
        
        # Style du tableau
        style = TableStyle([
            # Style des entêtes
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
            ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 7),  # Entêtes aussi à taille 7
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (3, 0), (4, 0)),  # Fusion des cellules pour "Heures prévues"
            
            # Style des cellules de données
            ('ALIGN', (0, 2), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 2), (-1, -1), 7),  # Toutes les données à taille 7
            
            # Style pour la colonne des codes (première colonne)
            ('ALIGN', (0, 2), (0, -1), 'LEFT'),  # Aligné à gauche pour mieux gérer le retour à la ligne
            
            # Style pour la ligne de sous-total
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 7),  # Sous-total aussi à taille 7
            ('SPAN', (0, -1), (2, -1)),  # Fusion des 3 premières cellules pour le texte "Sous-total"
        ])
        
        table.setStyle(style)
        return table, total_presentiel, total_tp_td, total_heures, total_credits
    
    # Générer et ajouter le tableau des charges régulières
    if attributions_regulieres.exists():
        table_regulieres, total_presentiel_reg, total_tp_td_reg, total_heures_reg, total_credits_reg = creer_tableau_charges(attributions_regulieres, 'Charge régulière')
        elements.append(table_regulieres)
        elements.append(Spacer(1, 10))
    else:
        total_presentiel_reg, total_tp_td_reg, total_heures_reg, total_credits_reg = 0, 0, 0, 0
    
    # Générer et ajouter le tableau des charges supplémentaires
    if attributions_supplementaires.exists():
        table_supplementaires, total_presentiel_supp, total_tp_td_supp, total_heures_supp, total_credits_supp = creer_tableau_charges(attributions_supplementaires, 'Charge supplémentaire')
        elements.append(table_supplementaires)
        elements.append(Spacer(1, 10))
    else:
        total_presentiel_supp, total_tp_td_supp, total_heures_supp, total_credits_supp = 0, 0, 0, 0
    
    # Ajouter le total général
    total_data = [
        ['Total', '', '', 
         str(total_presentiel_reg + total_presentiel_supp), 
         str(total_tp_td_reg + total_tp_td_supp), 
         str(total_heures_reg + total_heures_supp), 
         str(total_credits_reg + total_credits_supp),
         '', '']  # Colonnes vides pour classe et semestre
    ]
    
    total_table = Table(total_data, colWidths=[42, 95, 95, 58, 58, 58, 42, 42, 39])
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
    
    # Ajouter la section des signatures
    elements.append(Spacer(1, 14))
    
    # Styles pour les signatures
    styles = getSampleStyleSheet()
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,  # Centre
        leading=11
    )
    
    signature_style_italic = ParagraphStyle(
        'SignatureStyleItalic',
        parent=styles['Normal'],
        fontSize=9,
        alignment=2,  # Aligné à droite
        leading=11,
        fontName='Helvetica-Oblique'
    )
    
    # Date et lieu à droite + "Signature de l'intéressé"
    from datetime import datetime
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=10, alignment=2)  # Aligné à droite
    elements.append(Paragraph(f"Fait à Mbanza-Ngungu, le  {date_du_jour}", date_style))
    elements.append(Paragraph("<i>Signature de l'intéressé</i>", signature_style_italic))
    elements.append(Spacer(1, 20))
    
    # Titre "Pour accord :" centré
    pour_accord_style = ParagraphStyle('PourAccord', parent=styles['Normal'], fontSize=11, alignment=1, fontName='Helvetica-BoldOblique')
    elements.append(Paragraph("<i><b>Pour accord :</b></i>", pour_accord_style))
    elements.append(Spacer(1, 15))
    
    # Récupérer les grades
    enseignant_grade = enseignant_info.get_grade_designation() if enseignant_info and hasattr(enseignant_info, 'get_grade_designation') else ''
    csae_grade = csae_info.get_grade_designation() if csae_info and hasattr(csae_info, 'get_grade_designation') else ''
    sgac_grade = sgac_info.get_grade_designation() if sgac_info and hasattr(sgac_info, 'get_grade_designation') else ''
    
    # Ligne des signatures: CSAE (gauche) et SGAC (droite)
    signature_left_style = ParagraphStyle('SignatureLeft', parent=styles['Normal'], fontSize=9, alignment=0, leading=11)
    signature_right_style = ParagraphStyle('SignatureRight', parent=styles['Normal'], fontSize=9, alignment=2, leading=11)
    
    if csae_info:
        csae_text = f"<i>Date et signature du Chef de Section/Adjoint<br/>Chargé de l'Enseignement</i><br/><br/><br/><br/><b><u>{csae_info.nom_complet}</u></b><br/><i>{csae_grade}</i>"
    else:
        csae_text = "<i>Date et signature du Chef de Section/Adjoint<br/>Chargé de l'Enseignement</i><br/><br/><br/><br/>"
    
    if sgac_info:
        sgac_text = f"<i>Date et signature du Secrétaire Général Académique</i><br/><br/><br/><br/><b><u>{sgac_info.nom_complet}</u></b><br/><i>{sgac_grade}</i>"
    else:
        sgac_text = "<i>Date et signature du Secrétaire Général Académique</i><br/><br/><br/><br/>"
    
    signature_data = [[
        Paragraph(csae_text, signature_left_style),
        Paragraph(sgac_text, signature_right_style),
    ]]
    
    signature_table = Table(signature_data, colWidths=[280, 280])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(signature_table)
    
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
        from accounts.organisation_utils import get_user_organisation
        from django.db.models import Q
        
        # Récupérer le queryset de base avec les jointures nécessaires
        queryset = ScheduleEntry.objects.select_related(
            'attribution__matricule',
            'attribution__code_ue',
            'creneau'
        ).order_by('-date_cours', 'jour')
        
        # Filtrer par organisation de l'utilisateur (via section du cours)
        user_org = get_user_organisation(self.request.user)
        if user_org:
            queryset = queryset.filter(
                Q(attribution__matricule__section=user_org.code) | 
                Q(attribution__code_ue__section=user_org.code)
            )
        
        # Pour le superuser, filtrer par chef de section sélectionné
        elif self.request.user.is_superuser:
            chef_section_id = self.request.GET.get('chef_section')
            chef_adjoint_id = self.request.GET.get('chef_adjoint')
            
            if chef_section_id:
                try:
                    chef_section = Teacher.objects.get(id=chef_section_id)
                    queryset = queryset.filter(
                        Q(attribution__matricule__section=chef_section.section) | 
                        Q(attribution__code_ue__section=chef_section.section)
                    )
                except Teacher.DoesNotExist:
                    pass
            
            elif chef_adjoint_id:
                try:
                    chef_adjoint = Teacher.objects.get(id=chef_adjoint_id)
                    queryset = queryset.filter(
                        Q(attribution__matricule__section=chef_adjoint.section) | 
                        Q(attribution__code_ue__section=chef_adjoint.section)
                    )
                except Teacher.DoesNotExist:
                    pass
        
        # Récupérer les paramètres GET
        annee = self.request.GET.get('annee')
        jour = self.request.GET.get('jour')
        creneau = self.request.GET.get('creneau')
        classe = self.request.GET.get('classe')
        type_horaire = self.request.GET.get('type_horaire', '')  # Vide par défaut = tous les types
        
        # Appliquer les filtres
        if annee:
            queryset = queryset.filter(annee_academique=annee)
            
        if jour:
            queryset = queryset.filter(jour=jour)
            
        if creneau:
            # Filtrer par code de créneau (au lieu de l'ID)
            queryset = queryset.filter(creneau__code=creneau)
            
        if classe:
            queryset = queryset.filter(attribution__code_ue__classe__icontains=classe)
        elif self.request.user.is_superuser:
            # Pour le superuser, filtrer automatiquement par section si un chef est sélectionné
            chef_section_id = self.request.GET.get('chef_section')
            chef_adjoint_id = self.request.GET.get('chef_adjoint')
            
            if chef_section_id:
                try:
                    chef_section = Teacher.objects.get(id=chef_section_id)
                    # Récupérer les classes de cette section
                    classes_section = Classe.objects.filter(
                        mention__departement__section__CodeSection=chef_section.section
                    ).values_list('CodeClasse', flat=True)
                    
                    if classes_section:
                        # Filtrer par les classes de cette section
                        class_filter = Q()
                        for classe_code in classes_section:
                            class_filter |= Q(attribution__code_ue__classe__icontains=classe_code)
                        queryset = queryset.filter(class_filter)
                except Teacher.DoesNotExist:
                    pass
            
            elif chef_adjoint_id:
                try:
                    chef_adjoint = Teacher.objects.get(id=chef_adjoint_id)
                    # Récupérer les classes de cette section
                    classes_section = Classe.objects.filter(
                        mention__departement__section__CodeSection=chef_adjoint.section
                    ).values_list('CodeClasse', flat=True)
                    
                    if classes_section:
                        # Filtrer par les classes de cette section
                        class_filter = Q()
                        for classe_code in classes_section:
                            class_filter |= Q(attribution__code_ue__classe__icontains=classe_code)
                        queryset = queryset.filter(class_filter)
                except Teacher.DoesNotExist:
                    pass
        
        # Filtrer par type d'horaire (cours vs examens) - utiliser le champ type_horaire du modèle
        if type_horaire:
            queryset = queryset.filter(type_horaire=type_horaire)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique, Salle, Creneau, Classe, SemaineCours, Section
        from accounts.organisation_utils import get_user_organisation
        from django.db.models import Q
        
        context = super().get_context_data(**kwargs)
        user_org = get_user_organisation(self.request.user)
        
        # Données depuis les modèles de réglage (PRIORITÉ)
        context['annees_reglage'] = AnneeAcademique.objects.all().order_by('-code')
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        context['salles_disponibles'] = Salle.objects.filter(est_disponible=True).order_by('code')
        
        # Filtrer les créneaux selon le type d'horaire sélectionné
        type_horaire = self.request.GET.get('type_horaire', 'cours')
        if type_horaire == 'cours':
            context['creneaux_actifs'] = Creneau.objects.filter(
                est_actif=True, 
                type_creneau__in=['cours', 'les_deux']
            ).order_by('ordre', 'heure_debut')
        elif type_horaire == 'examen':
            # Pour les examens, filtrer par section de l'utilisateur ou toutes les sections
            if user_org:
                context['creneaux_actifs'] = Creneau.objects.filter(
                    est_actif=True, 
                    type_creneau__in=['examen', 'les_deux'],
                    section__CodeSection=user_org.code
                ).order_by('ordre', 'heure_debut')
            else:
                # Superuser voit tous les créneaux d'examens
                context['creneaux_actifs'] = Creneau.objects.filter(
                    est_actif=True, 
                    type_creneau__in=['examen', 'les_deux']
                ).order_by('ordre', 'heure_debut')
        else:
            context['creneaux_actifs'] = Creneau.objects.filter(est_actif=True).order_by('ordre', 'heure_debut')
        
        # Filtrer les classes par section de l'organisation ou par chef de section sélectionné
        if user_org:
            context['classes_reglage'] = Classe.objects.filter(
                mention__departement__section__CodeSection=user_org.code
            ).order_by('CodeClasse')
        elif self.request.user.is_superuser:
            # Pour le superuser, filtrer par chef de section sélectionné
            chef_section_id = self.request.GET.get('chef_section')
            chef_adjoint_id = self.request.GET.get('chef_adjoint')
            
            if chef_section_id:
                try:
                    chef_section = Teacher.objects.get(id=chef_section_id)
                    # Debug: afficher la section du chef
                    print(f"DEBUG: Chef section = {chef_section.nom_complet}, Section = '{chef_section.section}'")
                    
                    # Vérifier si la section existe dans la table Section
                    from reglage.models import Section
                    try:
                        section_obj = Section.objects.get(CodeSection=chef_section.section)
                        print(f"DEBUG: Section trouvée = {section_obj.DesignationSection}")
                    except Section.DoesNotExist:
                        print(f"DEBUG: ERREUR - Section '{chef_section.section}' n'existe pas dans la table Section!")
                    
                    # Filtrer les classes par section
                    classes_filtrees = Classe.objects.filter(
                        mention__departement__section__CodeSection=chef_section.section
                    ).order_by('CodeClasse')
                    
                    # Debug: afficher les classes trouvées
                    print(f"DEBUG: Nombre de classes trouvées pour section '{chef_section.section}' = {classes_filtrees.count()}")
                    if classes_filtrees.count() > 0:
                        for c in classes_filtrees[:5]:  # Afficher les 5 premières
                            print(f"  - {c.CodeClasse} (Section: {c.mention.departement.section.CodeSection})")
                    else:
                        print(f"DEBUG: AUCUNE classe trouvée pour la section '{chef_section.section}'")
                        # Afficher toutes les sections disponibles
                        sections_disponibles = Section.objects.all().values_list('CodeSection', flat=True)
                        print(f"DEBUG: Sections disponibles dans la BD = {list(sections_disponibles)}")
                    
                    context['classes_reglage'] = classes_filtrees
                    context['selected_section'] = chef_section.section
                except Teacher.DoesNotExist:
                    print(f"DEBUG: Chef de section avec ID {chef_section_id} non trouvé")
                    context['classes_reglage'] = Classe.objects.all().order_by('CodeClasse')
            
            elif chef_adjoint_id:
                try:
                    chef_adjoint = Teacher.objects.get(id=chef_adjoint_id)
                    context['classes_reglage'] = Classe.objects.filter(
                        mention__departement__section__CodeSection=chef_adjoint.section
                    ).order_by('CodeClasse')
                except Teacher.DoesNotExist:
                    context['classes_reglage'] = Classe.objects.all().order_by('CodeClasse')
            
            else:
                context['classes_reglage'] = Classe.objects.all().order_by('CodeClasse')
        else:
            context['classes_reglage'] = Classe.objects.all().order_by('CodeClasse')
        
        context['semaines_cours'] = SemaineCours.objects.all().order_by('numero_semaine')
        context['semaine_courante'] = SemaineCours.objects.filter(est_en_cours=True).first()
        
        # Sections disponibles pour les créneaux d'examens
        if user_org:
            context['sections'] = [user_org]
        else:
            # Superuser voit toutes les sections
            context['sections'] = Section.objects.all().order_by('DesignationSection')
        
        # Liste des enseignants filtrés par organisation
        teachers = Teacher.objects.all().order_by('nom_complet')
        if user_org:
            teachers = teachers.filter(section=user_org.code)
        context['teachers'] = teachers
        context['chefs_section'] = teachers.filter(fonction='CS').order_by('nom_complet')
        context['chefs_adjoint'] = teachers.filter(fonction='CSAE').order_by('nom_complet')
        
        # Années académiques (fallback depuis les horaires existants si réglage vide)
        annees_existantes = ScheduleEntry.objects.values_list(
            'annee_academique', flat=True
        ).distinct().order_by('-annee_academique')
        
        # Utiliser les années de réglage si disponibles, sinon celles des horaires
        if context['annees_reglage'].exists():
            context['annees'] = [a.code for a in context['annees_reglage']]
        else:
            context['annees'] = list(annees_existantes)
        
        # Cours options pour l'ajout rapide - filtrés par organisation
        attributions = Attribution.objects.select_related('matricule', 'code_ue').order_by('code_ue__classe', 'code_ue__code_ue')
        if user_org:
            attributions = attributions.filter(
                Q(matricule__section=user_org.code) | Q(code_ue__section=user_org.code)
            )
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
        
        # Nombre de salles utilisées (version corrigée pour les clés étrangères)
        context['salles_count'] = ScheduleEntry.objects.filter(
            salle__isnull=False
        ).values('salle').distinct().count()
        
        return context


class ScheduleEntryCreateView(CreateView):
    """Création d'une nouvelle entrée d'horaire"""
    model = ScheduleEntry
    form_class = ScheduleEntryForm
    template_name = 'attribution/schedule_entry_form.html'
    success_url = reverse_lazy('attribution:schedule_entry_list')
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique, Classe
        from accounts.organisation_utils import get_user_organisation
        
        context = super().get_context_data(**kwargs)
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        
        # Filtrer les classes par section de l'organisation
        user_org = get_user_organisation(self.request.user)
        if user_org:
            context['classes'] = Classe.objects.filter(
                mention__departement__section__CodeSection=user_org.code
            ).order_by('CodeClasse')
        else:
            context['classes'] = Classe.objects.all().order_by('CodeClasse')
        return context
    
    def form_valid(self, form):
        print("\n" + "="*60)
        print("FORM_VALID APPELE - Le formulaire est valide")
        print("="*60)
        
        from datetime import timedelta
        from reglage.models import AnneeAcademique, SemaineCours
        from .validators import ScheduleConflictValidator
        
        force_conflicts = form.cleaned_data.get('force_conflicts')

        # Récupérer la date de fin de la plage (si spécifiée)
        date_fin = form.cleaned_data.get('date_fin')
        date_debut = form.cleaned_data.get('semaine_debut')
        
        # Debug: afficher les dates reçues
        print(f"\n=== DEBUG CRÉATION HORAIRE ===")
        print(f"Date début (semaine_debut): {date_debut}")
        print(f"Date fin (date_fin): {date_fin}")
        print(f"Type date_debut: {type(date_debut)}")
        print(f"Type date_fin: {type(date_fin)}")
        
        # Vérifier si une plage de dates est spécifiée et valide
        if date_fin and date_debut:
            if date_fin < date_debut:
                form.add_error('date_fin', "La date de fin doit être postérieure ou égale à la date de début.")
                return self.form_invalid(form)
            
            # Calculer le nombre de jours dans la plage
            delta = date_fin - date_debut
            jours_plage = delta.days + 1  # +1 pour inclure le jour de début
            
            if jours_plage > 31:  # Limiter à 1 mois pour des raisons de performance
                form.add_error('date_fin', "La plage de dates ne peut pas dépasser 31 jours.")
                return self.form_invalid(form)
        
        # Insérer automatiquement l'année académique en cours
        annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
        if annee_courante:
            form.instance.annee_academique = annee_courante.code
        
        # Calculer et sauvegarder le jour depuis la date de début (en français)
        if date_debut:
            # Mapper les jours en français
            jours_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
            form.instance.jour = jours_fr[date_debut.weekday()]
        
        # Sauvegarder la salle depuis cleaned_data (les deux champs pour compatibilité)
        if 'salle' in form.cleaned_data and form.cleaned_data['salle']:
            form.instance.salle = form.cleaned_data['salle']
        if 'salle_link' in form.cleaned_data and form.cleaned_data['salle_link']:
            form.instance.salle_link = form.cleaned_data['salle_link']
        
        # Sauvegarder le créneau depuis cleaned_data (déjà une instance)
        if 'creneau' in form.cleaned_data and form.cleaned_data['creneau']:
            form.instance.creneau = form.cleaned_data['creneau']
        
        # Déduire automatiquement le type_horaire depuis le type_creneau du créneau sélectionné
        if form.instance.creneau:
            creneau_obj = form.instance.creneau
            # Si type_creneau est 'les_deux', on utilise 'cours' par défaut
            if creneau_obj.type_creneau == 'examen':
                form.instance.type_horaire = 'examen'
            else:
                # Pour 'cours' ou 'les_deux', on utilise 'cours'
                form.instance.type_horaire = 'cours'
        else:
            # Par défaut si pas de créneau
            form.instance.type_horaire = 'cours'
        
        # Détecter si la case "Toute la journée" est cochée
        toute_la_journee = form.cleaned_data.get('toute_la_journee', False)
        creneau_toute_journee = False
        creneaux_a_creer = [form.instance.creneau]  # Par défaut, un seul créneau
        
        print(f"\n{'='*60}")
        print(f"DETECTION TOUTE LA JOURNEE")
        print(f"{'='*60}")
        print(f"Case 'Toute la journee' cochee: {toute_la_journee}")
        print(f"Creneau selectionne: {form.instance.creneau}")
        
        if toute_la_journee:
            print(f"[OK] TOUTE LA JOURNEE DETECTEE !")
            creneau_toute_journee = True
            # Récupérer les créneaux matin et après-midi
            from reglage.models import Creneau
            creneau_matin = Creneau.objects.filter(code='AM').first()
            creneau_apres_midi = Creneau.objects.filter(code='PM').first()
            
            print(f"Creneau AM trouve: {creneau_matin}")
            print(f"Creneau PM trouve: {creneau_apres_midi}")
            
            if creneau_matin and creneau_apres_midi:
                creneaux_a_creer = [creneau_matin, creneau_apres_midi]
                print(f"[OK] Les 2 creneaux AM et PM seront crees:")
                print(f"  1. Creneau AM: {creneau_matin.code} - {creneau_matin.designation} ({creneau_matin.heure_debut}-{creneau_matin.heure_fin})")
                print(f"  2. Creneau PM: {creneau_apres_midi.code} - {creneau_apres_midi.designation} ({creneau_apres_midi.heure_debut}-{creneau_apres_midi.heure_fin})")
            else:
                print(f"[ERREUR] Les creneaux AM ou PM n'existent pas !")
                messages.warning(self.request, "Les creneaux AM et PM n'existent pas. Veuillez les creer d'abord.")
                # Si AM/PM n'existent pas, utiliser le créneau sélectionné
                if form.instance.creneau:
                    creneaux_a_creer = [form.instance.creneau]
                else:
                    form.add_error(None, "Veuillez selectionner un creneau ou creer les creneaux AM et PM.")
                    return self.form_invalid(form)
        else:
            print(f"[INFO] Creneau normal - Une seule entree sera creee")
            if not form.instance.creneau:
                form.add_error('creneau', "Veuillez selectionner un creneau ou cocher 'Toute la journee'.")
                return self.form_invalid(form)
        
        print(f"Nombre de creneaux a creer: {len(creneaux_a_creer)}")
        print(f"{'='*60}\n")
        
        # Liste pour stocker toutes les entrées créées (pour les messages de confirmation)
        created_entries = []
        
        # Si une plage de dates est spécifiée, créer plusieurs entrées
        # Note: On utilise >= au lieu de > pour permettre une plage d'un seul jour
        if date_fin and date_debut and date_fin >= date_debut:
            print(f"CRÉATION D'UNE PLAGE DE {date_debut} à {date_fin}")
            current_date = date_debut
            entry_count = 0
            while current_date <= date_fin:
                # Mapper les jours en français
                jours_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
                
                # Trouver la semaine correspondant à cette date
                from reglage.models import SemaineCours
                semaine_obj = SemaineCours.objects.filter(
                    date_debut__lte=current_date,
                    date_fin__gte=current_date
                ).first()
                numero_semaine = semaine_obj.numero_semaine if semaine_obj else None
                
                # Créer une entrée pour chaque créneau (1 ou 2 selon si c'est "Toute la journée")
                for creneau in creneaux_a_creer:
                    entry_count += 1
                    print(f"  -> Création entrée #{entry_count} pour {current_date} ({current_date.strftime('%A')})")
                    print(f"     Semaine trouvée: S{numero_semaine} pour {current_date}")
                    
                    # Créer une copie du formulaire pour chaque date et créneau
                    entry = ScheduleEntry(
                        attribution=form.instance.attribution,
                        type_horaire=form.instance.type_horaire,  # Type: cours ou examen
                        annee_academique=form.instance.annee_academique,
                        semaine_debut=current_date,
                        date_cours=current_date,  # Utiliser la date du jour comme date de cours
                        numero_semaine=numero_semaine,  # Numéro de semaine correspondant à la date
                        jour=jours_fr[current_date.weekday()],  # Jour en français
                        creneau=creneau,  # Utiliser le créneau de la boucle (AM ou PM si TJ)
                        salle=form.instance.salle,
                        salle_link=form.instance.salle_link,
                        remarques=form.instance.remarques
                    )
                    
                    # Valider l'entrée pour cette date et ce créneau
                    validation_result = self._validate_entry(entry)
                    if not validation_result['valid']:
                        if force_conflicts:
                            for error in validation_result['errors']:
                                messages.warning(self.request, f"Le {current_date.strftime('%d/%m/%Y')} - {error}")
                        else:
                            for error in validation_result['errors']:
                                form.add_error(None, f"Le {current_date.strftime('%d/%m/%Y')} - {error}")
                            return self.form_invalid(form)
                    
                    # Sauvegarder l'entrée
                    entry.save()
                    created_entries.append(entry)
                
                # Passer au jour suivant
                current_date += timedelta(days=1)
            
            # Message de succès avec le nombre d'entrées créées
            messages.success(
                self.request, 
                f"[OK] {len(created_entries)} entrees d'horaire creees avec succes dans la plage du "
                f"{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}."
            )
            # Définir self.object pour get_success_url (utiliser la dernière entrée créée)
            self.object = created_entries[-1] if created_entries else None
            return redirect(self.success_url)
        
        # Si pas de plage de dates, créer une ou plusieurs entrées selon le créneau
        else:
            print(f"CRÉATION D'UNE SEULE ENTRÉE pour {date_debut}")
            
            # Sauvegarder le numéro de semaine depuis SemaineCours
            numero_semaine = None
            if form.instance.semaine_debut:
                try:
                    # Chercher la semaine qui contient cette date
                    semaine_obj = SemaineCours.objects.filter(
                        date_debut__lte=form.instance.semaine_debut,
                        date_fin__gte=form.instance.semaine_debut
                    ).first()
                    if semaine_obj:
                        numero_semaine = semaine_obj.numero_semaine
                except SemaineCours.DoesNotExist:
                    pass
            
            # Créer une entrée pour chaque créneau (1 ou 2 selon si c'est "Toute la journée")
            for idx, creneau in enumerate(creneaux_a_creer):
                print(f"\n=== Création entrée {idx+1}/{len(creneaux_a_creer)} ===")
                print(f"Créneau: {creneau.code} - {creneau.designation}")
                
                # Créer une nouvelle entrée pour ce créneau
                entry = ScheduleEntry(
                    attribution=form.instance.attribution,
                    type_horaire=form.instance.type_horaire,  # Type: cours ou examen
                    annee_academique=form.instance.annee_academique,
                    semaine_debut=form.instance.semaine_debut,
                    date_cours=form.instance.semaine_debut,
                    numero_semaine=numero_semaine,
                    jour=form.instance.jour,
                    creneau=creneau,  # Utiliser le créneau de la boucle (AM ou PM si TJ)
                    salle=form.instance.salle,
                    salle_link=form.instance.salle_link,
                    remarques=form.instance.remarques
                )
                
                # Valider l'entrée
                validation_result = self._validate_entry(entry)
                if not validation_result['valid']:
                    print(f"[WARN] Validation echouee pour {creneau.code}: {validation_result['errors']}")
                    if force_conflicts:
                        for error in validation_result['errors']:
                            messages.warning(self.request, f"[{creneau.code}] {error}")
                        # Continuer même si validation échoue avec force_conflicts
                        entry.save()
                        created_entries.append(entry)
                        print(f"[OK] Entree {creneau.code} sauvegardee malgre les conflits (force_conflicts=True)")
                    else:
                        for error in validation_result['errors']:
                            form.add_error(None, f"[{creneau.code}] {error}")
                        # Ne pas arrêter la boucle, continuer avec le prochain créneau
                        print(f"[ERREUR] Entree {creneau.code} non creee (validation echouee)")
                        continue
                else:
                    # Sauvegarder l'entrée
                    entry.save()
                    created_entries.append(entry)
                    print(f"[OK] Entree {creneau.code} creee avec succes")
            
            # Message de succès
            if creneau_toute_journee:
                messages.success(self.request, f"{len(created_entries)} horaires crees avec succes (Matin + Apres-midi). Aucun conflit detecte.")
            else:
                messages.success(self.request, "Horaire cree avec succes. Aucun conflit detecte.")
            
            # Définir self.object pour get_success_url
            self.object = created_entries[-1] if created_entries else None
            return redirect(self.success_url)
    
    def _validate_entry(self, entry):
        """Valide une entrée d'horaire et retourne le résultat de la validation."""
        from .validators import ScheduleConflictValidator
        
        print(f"\n=== VALIDATION DES CONFLITS ===")
        print(f"Attribution: {entry.attribution}")
        print(f"Jour: {entry.jour}")
        print(f"Créneau: {entry.creneau}")
        print(f"Date: {entry.semaine_debut}")
        print(f"Salle: {entry.salle}")
        
        validation_result = ScheduleConflictValidator.validate_schedule_entry(
            attribution=entry.attribution,
            jour=entry.jour,
            creneau=entry.creneau,
            semaine=entry.semaine_debut,
            salle=entry.salle,
            exclude_id=entry.pk if entry.pk else None
        )
        
        print(f"Résultat validation: {validation_result}")
        print(f"Valid: {validation_result['valid']}")
        print(f"Errors: {validation_result['errors']}")
        
        return validation_result
    
    def form_invalid(self, form):
        print("\n" + "="*60)
        print("FORM_INVALID APPELE - Le formulaire contient des erreurs")
        print("="*60)
        print("Erreurs du formulaire:")
        for field, errors in form.errors.items():
            print(f"  - {field}: {errors}")
        print("="*60 + "\n")
        
        messages.error(self.request, "Erreur lors de la création de l'horaire. Vérifiez les données.")
        return super().form_invalid(form)


class ScheduleEntryUpdateView(UpdateView):
    """Modification d'une entrée d'horaire existante"""
    model = ScheduleEntry
    form_class = ScheduleEntryForm
    template_name = 'attribution/schedule_entry_form.html'
    success_url = reverse_lazy('attribution:schedule_entry_list')
    
    def get_context_data(self, **kwargs):
        from reglage.models import AnneeAcademique, Classe
        from accounts.organisation_utils import get_user_organisation
        
        context = super().get_context_data(**kwargs)
        context['annee_courante'] = AnneeAcademique.objects.filter(est_en_cours=True).first()
        
        # Filtrer les classes par section de l'organisation
        user_org = get_user_organisation(self.request.user)
        if user_org:
            context['classes'] = Classe.objects.filter(
                mention__departement__section__CodeSection=user_org.code
            ).order_by('CodeClasse')
        else:
            context['classes'] = Classe.objects.all().order_by('CodeClasse')
        return context
    
    def form_valid(self, form):
        from reglage.models import SemaineCours
        from .validators import ScheduleConflictValidator
        
        force_conflicts = form.cleaned_data.get('force_conflicts')
        
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
        
        # Si des conflits sont détectés
        if not validation_result['valid']:
            if force_conflicts:
                for error in validation_result['errors']:
                    messages.warning(self.request, error)
            else:
                for error in validation_result['errors']:
                    messages.error(self.request, error)
                return self.form_invalid(form)
        
        # Afficher les avertissements s'il y en a
        for warning in validation_result['warnings']:
            messages.warning(self.request, warning)
        
        messages.success(self.request, "[OK] Horaire modifie avec succes. Aucun conflit detecte.")
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


@csrf_exempt
@require_http_methods(['POST'])
def schedule_entry_bulk_delete(request):
    """Suppression en masse d'entrées d'horaire"""
    import json
    
    try:
        # Récupérer les données JSON
        data = json.loads(request.body)
        entry_ids = data.get('entry_ids', [])
        
        if not entry_ids:
            return JsonResponse({
                'success': False,
                'error': 'Aucun horaire sélectionné'
            }, status=400)
        
        # Utiliser une transaction atomique pour garantir la cohérence
        with transaction.atomic():
            # Supprimer les entrées sélectionnées
            deleted_count = ScheduleEntry.objects.filter(id__in=entry_ids).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} horaire(s) supprimé(s) avec succès',
            'deleted_count': deleted_count
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
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
    title_style = ParagraphStyle('SchedTitle', parent=styles['Heading2'], fontSize=12, alignment=1, fontName='Times-Bold')
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=11, leading=13, alignment=1, wordWrap='CJK', fontName='Times-Roman')
    
    # Fonction pour tronquer le texte
    def truncate_text(text, length=20):
        return (text[:length] + '...') if len(text) > length else text
    
    # En-tête avec image
    from django.conf import settings
    import os
    from reportlab.platypus import Image
    from PIL import Image as PILImage
    
    entete_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    if os.path.exists(entete_path):
        try:
            # Lire les dimensions originales de l'image
            with PILImage.open(entete_path) as pil_img:
                original_width, original_height = pil_img.size
                aspect_ratio = original_width / original_height
            
            # Calculer la hauteur proportionnelle
            calculated_height = doc.width / aspect_ratio
            img = Image(entete_path, width=doc.width, height=calculated_height)
        except:
            # En cas d'erreur, utiliser une hauteur par défaut
            img = Image(entete_path, width=doc.width, height=1.2*inch)
        
        elements.append(img)
        elements.append(Spacer(1, 10))
    
    # Section d'abord
    if section and section != 'ALL':
        try:
            from reglage.models import Section as SectionModel
            section_obj = SectionModel.objects.filter(CodeSection=section).first()
            section_designation = section_obj.DesignationSection if section_obj else section
            
            section_text = f"{section_designation.upper()}"
        except:
            section_text = f"{section.upper()}"
        elements.append(Paragraph(section_text, ParagraphStyle('SectionStyle', parent=styles['Normal'], fontSize=14, alignment=1, fontName='Helvetica-Bold')))
    
    # Année académique ensuite avec un peu d'espace au-dessus
    elements.append(Spacer(1, 10))
    info_text = f"<b>Année Académique:</b> {annee_academique or 'Toutes'}"
    elements.append(Paragraph(info_text, ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=12, alignment=1)))
    
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
        col_widths = [70, 90, 85, 75, 75, 85]
        
        # Créer le tableau avec les données
        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
        style = TableStyle([
            # En-tête avec fond gris foncé et texte blanc
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),  # Taille de police augmentée pour l'en-tête
            # Padding pour l'en-tête
            ('LEFTPADDING', (0, 0), (-1, 0), 8),
            ('RIGHTPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            # Padding pour les données
            ('LEFTPADDING', (0, 1), (-1, -1), 6),
            ('RIGHTPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#34495e')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),
            # Police des données
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),  # Taille de police augmentée pour les données
            # Ligne de total en gras avec fond gris clair
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#34495e')),
            # Alternance de couleurs pour les lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        ])
        
        table.setStyle(style)
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
    import traceback
    
    try:
        # Récupérer l'année académique sélectionnée (optionnel)
        annee_academique = request.GET.get('annee_academique')
        section = request.GET.get('section')
        format_pdf = request.GET.get('format') == 'pdf'
        
        # Valider et nettoyer l'année académique
        if annee_academique and (not annee_academique.strip() or annee_academique.startswith(':')):
            annee_academique = None
        
        # DEBUG: Vérifier les types de charge disponibles
        types_charges = Attribution.objects.values_list('type_charge', flat=True).distinct()
        print(f"Types de charge disponibles: {list(types_charges)}")
        print(f"Année académique reçue: '{annee_academique}'")
        print(f"Section reçue: '{section}'")
        
        # Filtrer les attributions de type "supplementaire" (insensible à la casse)
        attributions = Attribution.objects.filter(type_charge__iexact='supplementaire').select_related('matricule', 'code_ue')
        print(f"Nombre d'attributions supplémentaires trouvées: {attributions.count()}")
        
        # DEBUG: Afficher les sections uniques des enseignants
        sections_enseignants = set(attr.matricule.section for attr in attributions if attr.matricule and attr.matricule.section)
        print(f"Sections des enseignants dans les attributions: {sections_enseignants}")
        
        # Filtrer par année si spécifiée
        if annee_academique:
            attributions = attributions.filter(annee_academique=annee_academique)
            print(f"Après filtrage par année: {attributions.count()}")
        
        # Filtrer par section si spécifiée
        if section and section != 'ALL':
            from django.db.models import Q
            try:
                from reglage.models import Section as SectionModel
                # Essayer de trouver la section par désignation ou code
                section_obj = SectionModel.objects.filter(
                    Q(DesignationSection=section) | Q(CodeSection=section)
                ).first()
                
                if section_obj:
                    # Filtrer par code ET désignation pour couvrir tous les cas
                    attributions = attributions.filter(
                        Q(matricule__section=section_obj.CodeSection) | 
                        Q(matricule__section=section_obj.DesignationSection) |
                        Q(matricule__section__icontains=section_obj.DesignationSection) |
                        Q(matricule__section__icontains=section_obj.CodeSection)
                    )
                    print(f"Filtrage par section: {section_obj.DesignationSection} ({section_obj.CodeSection})")
                else:
                    # Si la section n'est pas trouvée, filtrer directement par la valeur fournie
                    attributions = attributions.filter(
                        Q(matricule__section=section) |
                        Q(matricule__section__icontains=section)
                    )
                    print(f"Filtrage par section (direct): {section}")
                
                print(f"Après filtrage par section: {attributions.count()}")
            except Exception as e:
                print(f"Erreur filtrage section: {e}")
                import traceback
                print(traceback.format_exc())
                attributions = attributions.filter(matricule__section__icontains=section)
        
        # Si format PDF demandé, générer le PDF
        if format_pdf:
            return generer_pdf_heures_supplementaires(request, attributions, annee_academique, section)
        
        # Grouper par grade et calculer les statistiques
        stats_par_grade = {}
        
        for attribution in attributions:
            try:
                # Vérifier que l'attribution a un matricule et un code_ue
                if not attribution.matricule or not attribution.code_ue:
                    print(f"Attribution {attribution.id} sans matricule ou code_ue")
                    continue
                
                grade = attribution.matricule.grade if attribution.matricule.grade else "Non spécifié"
                
                if grade not in stats_par_grade:
                    stats_par_grade[grade] = {
                        'grade': grade,
                        'enseignants': set(),
                        'nombre_cours': 0,
                        'total_cmi': 0,
                        'total_td_tp': 0,
                        'total_heures': 0,
                    }
                
                # Ajouter l'enseignant (set pour éviter les doublons)
                stats_par_grade[grade]['enseignants'].add(attribution.matricule.matricule)
                
                # Compter le cours
                stats_par_grade[grade]['nombre_cours'] += 1
                
                # Calculer les heures
                cmi = float(attribution.code_ue.cmi) if attribution.code_ue.cmi else 0
                td_tp = float(attribution.code_ue.td_tp) if attribution.code_ue.td_tp else 0
                
                stats_par_grade[grade]['total_cmi'] += cmi
                stats_par_grade[grade]['total_td_tp'] += td_tp
                stats_par_grade[grade]['total_heures'] += (cmi + td_tp)
            except Exception as e:
                print(f"Erreur traitement attribution {attribution.id}: {e}")
                continue
        
        # Convertir les sets en nombres
        for grade in stats_par_grade:
            stats_par_grade[grade]['nombre_enseignants'] = len(stats_par_grade[grade]['enseignants'])
            # Supprimer le set pour éviter les problèmes de sérialisation JSON
            del stats_par_grade[grade]['enseignants']
        
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
        
        # Récupérer les années académiques depuis reglage/AnneeAcademique
        from reglage.models import AnneeAcademique, Section as SectionReglage
        annees_disponibles = list(AnneeAcademique.objects.all().order_by('-date_debut').values_list('code', flat=True))
        
        # Récupérer les sections depuis reglage/Section
        sections_disponibles = list(SectionReglage.objects.all().order_by('CodeSection').values_list('DesignationSection', flat=True))
        
        # DEBUG
        print(f"=== HEURES SUPPLEMENTAIRES DEBUG ===")
        print(f"Années disponibles: {annees_disponibles}")
        print(f"Sections disponibles: {sections_disponibles}")
        print(f"Nombre de stats: {len(stats_list)}")
        print(f"Stats par grade: {[s['grade'] for s in stats_list]}")
        print(f"Total enseignants: {totaux['nombre_enseignants']}, Total cours: {totaux['nombre_cours']}")
        
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
            print(f"Retour AJAX avec {len(annees_disponibles)} années et {len(sections_disponibles)} sections")
            return JsonResponse(context)
        
        # Sinon, retourner le template HTML
        return render(request, 'attribution/heures_supplementaires_grade.html', context)
        
    except Exception as e:
        print(f"=== ERREUR HEURES SUPPLEMENTAIRES ===")
        print(f"Erreur: {e}")
        print(traceback.format_exc())
        
        # Retourner une réponse d'erreur appropriée
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': str(e),
                'stats_par_grade': [],
                'totaux': {
                    'nombre_enseignants': 0,
                    'nombre_cours': 0,
                    'total_cmi': 0,
                    'total_td_tp': 0,
                    'total_heures': 0,
                },
                'annees_disponibles': [],
                'sections_disponibles': [],
            }, status=500)
        else:
            return HttpResponse(f"Erreur lors du chargement des données: {str(e)}", status=500)

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
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=1, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=12, alignment=1)
    section_title_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontSize=13, alignment=1, fontName='Helvetica-Bold')
    dept_title_style = ParagraphStyle('DeptTitle', parent=styles['Heading3'], fontSize=11, alignment=1, fontName='Helvetica-Bold')
    
    # En-tête avec image
    from django.conf import settings
    import os
    from reportlab.platypus import Image
    from PIL import Image as PILImage
    
    entete_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    if os.path.exists(entete_path):
        try:
            # Lire les dimensions originales de l'image
            with PILImage.open(entete_path) as pil_img:
                original_width, original_height = pil_img.size
                aspect_ratio = original_width / original_height
            
            # Calculer la hauteur proportionnelle
            calculated_height = doc.width / aspect_ratio
            img = Image(entete_path, width=doc.width, height=calculated_height)
        except:
            # En cas d'erreur, utiliser une hauteur par défaut
            img = Image(entete_path, width=doc.width, height=1.2*inch)
        
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
        elements.append(Paragraph(section_text, section_title_style))
    
    # Année académique ensuite
    info_text = f"<b>Année Académique:</b> {annee_academique}"
    elements.append(Paragraph(info_text, subtitle_style))
    
    # Titre principal en dernier
    titre = "LISTE DES CHARGES HORAIRES PAR SECTION"
    if section != 'ALL':
        titre = f"LISTE DES CHARGES HORAIRES - SECTION {section_designation.upper()}"
    
    elements.append(Paragraph(titre, title_style))
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
                        Paragraph(classe_text, ParagraphStyle('classe', parent=styles['Normal'], fontSize=7, alignment=1)),
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