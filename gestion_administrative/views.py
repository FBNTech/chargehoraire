from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.templatetags.static import static
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import AutorisationAbsenceEnseignantForm, EtudiantForm, ImportExcelForm, AutorisationAbsenceEtudiantForm, InscriptionForm, ImportInscriptionsForm
from .models import AbsenceEnseignant, Etudiant, AutorisationAbsenceEtudiant, Annonce, Inscription
from teachers.models import Teacher
from reglage.models import Departement, Grade, Fonction
import pandas as pd
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse


def dashboard(request):
    # Vue simple affichant uniquement un titre
    return render(request, 'gestion_administrative/dashboard.html')


def liste_absences(request):
    """Affiche la liste des absences enregistrées"""
    absences = AbsenceEnseignant.objects.all()
    
    # Enrichir avec les noms des enseignants
    for absence in absences:
        try:
            teacher = Teacher.objects.get(matricule=absence.MatriculeEnseignant)
            absence.nom_enseignant = teacher.nom_complet
        except Teacher.DoesNotExist:
            absence.nom_enseignant = "Enseignant introuvable"
    
    # Vérifier si la demande est pour un PDF
    if request.GET.get('format') == 'pdf':
        # Utiliser la fonction commune pour trouver l'entête
        header_path = _absolute_static_path('images/entete.PNG')
        
        # Contexte pour le PDF
        context = {
            'absences': absences,
            'date_impression': datetime.now(),
            'header_path': header_path
        }
        
        # Générer le PDF
        template_path = 'gestion_administrative/absence_enseignant_pdf.html'
        template = get_template(template_path)
        html = template.render(context)
        
        # Créer la réponse HTTP avec le PDF pour affichage dans le navigateur
        response = HttpResponse(content_type='application/pdf')
        nom_fichier = f"liste_absences_enseignants_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
        
        # Générer le PDF avec xhtml2pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Erreur lors de la génération du PDF', status=400)
        
        return response
    
    return render(request, 'gestion_administrative/liste_absences.html', {
        'absences': absences
    })


def modifier_absence(request, absence_id):
    """Modifie une absence existante"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    absence = get_object_or_404(AbsenceEnseignant, id=absence_id)
    
    if request.method == 'POST':
        absence.dateDebut = request.POST.get('dateDebut')
        absence.dateFin = request.POST.get('dateFin')
        absence.Destination = request.POST.get('destination')
        absence.Motif = request.POST.get('motif')
        absence.save()
        
        return JsonResponse({'success': True, 'message': 'Absence modifiée avec succès'})
    
    # GET: retourner les données pour le formulaire
    return JsonResponse({
        'id': absence.id,
        'matricule': absence.MatriculeEnseignant,
        'dateDebut': absence.dateDebut.strftime('%Y-%m-%d'),
        'dateFin': absence.dateFin.strftime('%Y-%m-%d'),
        'destination': absence.Destination,
        'motif': absence.Motif
    })


def supprimer_absence(request, absence_id):
    """Supprime une absence"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    if request.method == 'POST':
        absence = get_object_or_404(AbsenceEnseignant, id=absence_id)
        absence.delete()
        return JsonResponse({'success': True, 'message': 'Absence supprimée avec succès'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


# ==================== GESTION DES ÉTUDIANTS ====================

def liste_etudiants(request):
    """Liste tous les étudiants avec recherche et filtrage"""
    etudiants = Etudiant.objects.all()
    
    # Recherche
    from django.db import models
    search = request.GET.get('search')
    if search:
        etudiants = etudiants.filter(
            models.Q(matricule__icontains=search) |
            models.Q(nom_complet__icontains=search) |
            models.Q(classe__icontains=search)
        )
    
    # Filtrage par statut
    statut = request.GET.get('statut')
    if statut:
        etudiants = etudiants.filter(statut=statut)
    
    return render(request, 'gestion_administrative/etudiants/liste.html', {
        'etudiants': etudiants,
        'search': search,
        'statut_filter': statut,
    })


def ajouter_etudiant(request):
    """Ajouter un nouvel étudiant"""
    if request.method == 'POST':
        form = EtudiantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Étudiant ajouté avec succès!')
            return redirect('gestion_administrative:liste_etudiants')
    else:
        form = EtudiantForm()
    
    return render(request, 'gestion_administrative/etudiants/form.html', {
        'form': form,
        'title': 'Ajouter un étudiant'
    })


def modifier_etudiant(request, etudiant_id):
    """Modifier un étudiant existant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    
    if request.method == 'POST':
        form = EtudiantForm(request.POST, instance=etudiant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Étudiant modifié avec succès!')
            return redirect('gestion_administrative:liste_etudiants')
    else:
        # Initialiser le formulaire avec l'instance existante
        form = EtudiantForm(instance=etudiant)
        # Si l'étudiant a une classe, la définir dans le formulaire
        if etudiant.classe:
            form.fields['classe'].initial = etudiant.classe
    
    return render(request, 'gestion_administrative/etudiants/form.html', {
        'form': form,
        'title': 'Modifier l\'étudiant',
        'etudiant': etudiant
    })


def supprimer_etudiant(request, etudiant_id):
    """Supprimer un étudiant"""
    if request.method == 'POST':
        etudiant = get_object_or_404(Etudiant, id=etudiant_id)
        etudiant.delete()
        return JsonResponse({'success': True, 'message': 'Étudiant supprimé avec succès'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


def importer_etudiants_excel(request):
    """Importer des étudiants depuis un fichier Excel"""
    if request.method == 'POST':
        form = ImportExcelForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                fichier = request.FILES['fichier_excel']
                df = pd.read_excel(fichier)
                
                # Colonnes attendues
                colonnes_requises = ['matricule', 'nom_complet']
                colonnes_optionnelles = [
                    'date_naissance', 'sexe', 'telephone', 'departement', 'classe', 'annee_academique'
                ]
                
                # Vérifier les colonnes requises
                for col in colonnes_requises:
                    if col not in df.columns:
                        messages.error(request, f'Colonne requise manquante: {col}')
                        return render(request, 'gestion_administrative/etudiants/import.html', {'form': form})
                
                etudiants_crees = 0
                etudiants_modifies = 0
                erreurs = []
                
                for index, row in df.iterrows():
                    try:
                        # Préparer les données
                        data = {
                            'matricule': str(row['matricule']).strip(),
                            'nom_complet': str(row['nom_complet']).strip(),
                        }
                        
                        # Ajouter les colonnes optionnelles si présentes
                        for col in colonnes_optionnelles:
                            if col in df.columns and pd.notna(row[col]):
                                if col == 'date_naissance':
                                    data[col] = pd.to_datetime(row[col]).date()
                                else:
                                    data[col] = str(row[col]).strip()
                        
                        # Créer ou mettre à jour l'étudiant
                        etudiant, created = Etudiant.objects.update_or_create(
                            matricule=data['matricule'],
                            defaults=data
                        )
                        
                        if created:
                            etudiants_crees += 1
                        else:
                            etudiants_modifies += 1
                            
                    except Exception as e:
                        erreurs.append(f'Ligne {index + 2}: {str(e)}')
                
                # Messages de résultat
                if etudiants_crees > 0:
                    messages.success(request, f'{etudiants_crees} étudiants créés')
                if etudiants_modifies > 0:
                    messages.info(request, f'{etudiants_modifies} étudiants modifiés')
                if erreurs:
                    for erreur in erreurs[:5]:  # Limiter à 5 erreurs
                        messages.error(request, erreur)
                    if len(erreurs) > 5:
                        messages.error(request, f'... et {len(erreurs) - 5} autres erreurs')
                
                return redirect('gestion_administrative:liste_etudiants')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'importation: {str(e)}')
    else:
        form = ImportExcelForm()
    
    return render(request, 'gestion_administrative/etudiants/import.html', {'form': form})


def supprimer_absence_etudiant(request, absence_id):
    """Supprimer une autorisation d'absence étudiant"""
    if request.method == 'POST':
        absence = get_object_or_404(AutorisationAbsenceEtudiant, id=absence_id)
        # Sauvegarder les informations pour le message de réussite
        etudiant_nom = absence.etudiant.nom_complet
        # Supprimer l'autorisation
        absence.delete()
        return JsonResponse({'success': True, 'message': f"L'autorisation d'absence pour {etudiant_nom} a été supprimée avec succès."})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


def liste_absences_etudiants(request):
    """Affiche la liste des autorisations d'absence pour les étudiants"""
    absences = AutorisationAbsenceEtudiant.objects.all().select_related('etudiant', 'chef_departement')
    
    # Recherche par nom ou matricule
    search = request.GET.get('search')
    if search:
        from django.db.models import Q
        absences = absences.filter(
            Q(etudiant__matricule__icontains=search) | 
            Q(etudiant__nom_complet__icontains=search)
        )
    
    # Filtrer par période
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if date_debut:
        absences = absences.filter(periode_debut__gte=date_debut)
    if date_fin:
        absences = absences.filter(periode_fin__lte=date_fin)
        
    return render(request, 'gestion_administrative/etudiants/liste_absences.html', {
        'absences': absences,
        'search': search,
        'date_debut': date_debut,
        'date_fin': date_fin,
    })


def autorisation_absence_etudiant(request):
    """Formulaire d'autorisation d'absence pour étudiant avec génération de PDF"""
    # Vérifier si on a une demande pour générer un PDF à partir d'un ID existant
    absence_id = request.GET.get('id')
    if absence_id:
        # Récupérer l'autorisation existante
        try:
            autorisation = AutorisationAbsenceEtudiant.objects.select_related('etudiant', 'chef_departement').get(id=absence_id)
            etudiant = autorisation.etudiant
            
            # Utiliser la fonction commune pour trouver l'entête
            header_path = _absolute_static_path('images/entete.PNG')
            
            # Récupérer le chef de département
            from reglage.models import Grade
            
            # Utiliser le chef de département enregistré
            try:
                dept_chef = autorisation.chef_departement
                departement_chef = dept_chef.nom_complet
                try:
                    grade_obj = Grade.objects.get(pk=dept_chef.grade)
                    departement_chef_grade = grade_obj.DesignationGrade
                except Grade.DoesNotExist:
                    departement_chef_grade = dept_chef.grade
            except:
                # Fallback si pour une raison quelconque le chef n'est pas disponible
                departement_chef = "Chef de Département"
                departement_chef_grade = ""
            
            # Contexte pour le PDF
            context = {
                'etudiant': etudiant,
                'periode_debut': autorisation.periode_debut,
                'periode_fin': autorisation.periode_fin,
                'motif': autorisation.motif,
                'destination': autorisation.destination if autorisation.destination else '',
                'disposition_cours': autorisation.disposition_cours if autorisation.disposition_cours else '',
                'date_aujourdhui': datetime.now(),
                'header_path': header_path,
                'departement_chef': departement_chef,
                'departement_chef_grade': departement_chef_grade,
                'autorisation_id': autorisation.id,  # Ajouter l'ID pour référence
            }
            
            # Générer le PDF
            template_path = 'gestion_administrative/etudiants/autorisation_absence_pdf.html'
            template = get_template(template_path)
            html = template.render(context)
            
            # Créer la réponse HTTP avec le PDF pour affichage dans le navigateur
            response = HttpResponse(content_type='application/pdf')
            nom_fichier = f"autorisation_absence_{etudiant.matricule}_{autorisation.periode_debut.strftime('%Y%m%d')}.pdf"
            
            # Toujours afficher le PDF directement dans le navigateur
            response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
            
            # Générer le PDF avec xhtml2pdf
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Erreur lors de la génération du PDF', status=400)
            
            return response
            
        except AutorisationAbsenceEtudiant.DoesNotExist:
            messages.error(request, "Cette autorisation d'absence n'existe pas.")
            return redirect('gestion_administrative:liste_absences_etudiants')
    
    if request.method == 'POST':
        form = AutorisationAbsenceEtudiantForm(request.POST)
        if form.is_valid():
            # Sauvegarder l'autorisation d'absence dans la base de données
            autorisation = form.save(commit=False)  # Ne pas sauvegarder immédiatement
            autorisation.chef_departement = form.cleaned_data['chef_departement']  # Ajouter le chef de département
            autorisation.save()  # Sauvegarder l'entrée dans la base de données
            
            # Récupérer les données pour le PDF
            etudiant = autorisation.etudiant
            
            # Utiliser la fonction commune pour trouver l'entête
            header_path = _absolute_static_path('images/entete.PNG')
            
            # Récupérer le chef de département sélectionné dans le formulaire
            from teachers.models import Teacher
            from reglage.models import Grade
            
            # Utiliser le chef de département enregistré
            try:
                dept_chef = autorisation.chef_departement
                departement_chef = dept_chef.nom_complet
                try:
                    grade_obj = Grade.objects.get(pk=dept_chef.grade)
                    departement_chef_grade = grade_obj.DesignationGrade
                except Grade.DoesNotExist:
                    departement_chef_grade = dept_chef.grade
            except:
                # Fallback si pour une raison quelconque le chef n'est pas disponible
                departement_chef = "Chef de Département"
                departement_chef_grade = ""
            
            # Contexte pour le PDF
            context = {
                'etudiant': etudiant,
                'periode_debut': autorisation.periode_debut,
                'periode_fin': autorisation.periode_fin,
                'motif': autorisation.motif,
                'destination': autorisation.destination if autorisation.destination else '',
                'disposition_cours': autorisation.disposition_cours if autorisation.disposition_cours else '',
                'date_aujourdhui': datetime.now(),
                'header_path': header_path,
                'departement_chef': departement_chef,
                'departement_chef_grade': departement_chef_grade,
                'autorisation_id': autorisation.id,  # Ajouter l'ID pour référence
            }
            
            # Générer le PDF
            template_path = 'gestion_administrative/etudiants/autorisation_absence_pdf.html'
            template = get_template(template_path)
            html = template.render(context)
            
            # Créer la réponse HTTP avec le PDF pour affichage dans le navigateur
            response = HttpResponse(content_type='application/pdf')
            nom_fichier = f"autorisation_absence_{etudiant.matricule}_{autorisation.periode_debut.strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
            
            # Générer le PDF avec xhtml2pdf
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Erreur lors de la génération du PDF', status=400)
            
            return response
    else:
        form = AutorisationAbsenceEtudiantForm()
    
    return render(request, 'gestion_administrative/etudiants/autorisation_absence.html', {
        'form': form,
        'title': 'Autorisation d\'absence étudiant'
    })


def autorisation_absence_enseignant(request):
    """Affiche le formulaire, enregistre les données, puis génère un PDF."""
    # Vérifier si on a une demande pour générer un PDF à partir d'un ID existant
    absence_id = request.GET.get('id')
    if absence_id:
        try:
            # Essayer d'abord de trouver une autorisation d'absence dans la table AbsenceEnseignant
            absence = AbsenceEnseignant.objects.get(id=absence_id)
            
            # Récupérer l'enseignant
            try:
                teacher = Teacher.objects.get(matricule=absence.MatriculeEnseignant)
            except Teacher.DoesNotExist:
                return HttpResponse('Enseignant non trouvé', status=404)
            
            # Générer le contexte pour le PDF
            departement_designation = _resolve_departement_designation(teacher.departement)
            grade_designation = _resolve_grade_designation(teacher.grade)
            fonction_designation = _resolve_fonction_designation(teacher.fonction)
            debut_fr = _date_fr(absence.dateDebut)
            fin_fr = _date_fr(absence.dateFin)
            
            context = {
                'teacher': teacher,
                'periode_debut': absence.dateDebut,
                'periode_fin': absence.dateFin,
                'periode_debut_fr': debut_fr,
                'periode_fin_fr': fin_fr,
                'motif': absence.Motif,
                'destination': absence.Destination,
                'disposition_cours': '',  # Pas disponible dans AbsenceEnseignant
                'disposition_stage': '',   # Pas disponible dans AbsenceEnseignant
                'departement_designation': departement_designation,
                'grade_designation': grade_designation,
                'fonction_designation': fonction_designation,
                'header_path': _absolute_static_path('images/entete.PNG'),
            }
            
            # Générer le PDF
            pdf_response = _render_to_pdf('gestion_administrative/autorisation_absence_enseignant_pdf.html', context)
            return pdf_response
        except AbsenceEnseignant.DoesNotExist:
            try:
                # Essayer ensuite de trouver dans AutorisationAbsenceEnseignant
                autorisation = AutorisationAbsenceEnseignant.objects.select_related('teacher').get(id=absence_id)
                
                departement_designation = _resolve_departement_designation(autorisation.teacher.departement)
                grade_designation = _resolve_grade_designation(autorisation.teacher.grade)
                fonction_designation = _resolve_fonction_designation(autorisation.teacher.fonction)
                debut_fr = _date_fr(autorisation.periode_debut)
                fin_fr = _date_fr(autorisation.periode_fin)
                
                context = {
                    'teacher': autorisation.teacher,
                    'periode_debut': autorisation.periode_debut,
                    'periode_fin': autorisation.periode_fin,
                    'periode_debut_fr': debut_fr,
                    'periode_fin_fr': fin_fr,
                    'motif': autorisation.motif,
                    'destination': autorisation.destination,
                    'disposition_cours': autorisation.disposition_cours,
                    'disposition_stage': autorisation.disposition_stage,
                    'departement_designation': departement_designation,
                    'grade_designation': grade_designation,
                    'fonction_designation': fonction_designation,
                    'header_path': _absolute_static_path('images/entete.PNG'),
                }
                
                # Générer le PDF
                pdf_response = _render_to_pdf('gestion_administrative/autorisation_absence_enseignant_pdf.html', context)
                return pdf_response
            except AutorisationAbsenceEnseignant.DoesNotExist:
                messages.error(request, "Cette autorisation d'absence n'existe pas.")
                return redirect('gestion_administrative:liste_absences')
    
    if request.method == 'POST':
        form = AutorisationAbsenceEnseignantForm(request.POST)
        if form.is_valid():
            # 1) Enregistrer les données AVANT la génération du PDF
            instance = form.save()

            # 1.1) Enregistrer aussi dans la table AbsenceEnseignant
            AbsenceEnseignant.objects.create(
                MatriculeEnseignant=instance.teacher.matricule,
                dateDebut=instance.periode_debut,
                dateFin=instance.periode_fin,
                Destination=instance.destination,
                Motif=instance.motif
            )

            # 2) Contexte pour le PDF basé sur l'instance enregistrée
            departement_designation = _resolve_departement_designation(instance.teacher.departement)
            grade_designation = _resolve_grade_designation(instance.teacher.grade)
            fonction_designation = _resolve_fonction_designation(instance.teacher.fonction)
            debut_fr = _date_fr(instance.periode_debut)
            fin_fr = _date_fr(instance.periode_fin)
            context = {
                'teacher': instance.teacher,
                'periode_debut': instance.periode_debut,
                'periode_fin': instance.periode_fin,
                'periode_debut_fr': debut_fr,
                'periode_fin_fr': fin_fr,
                'motif': instance.motif,
                'destination': instance.destination,
                'disposition_cours': instance.disposition_cours,
                'disposition_stage': instance.disposition_stage,
                'departement_designation': departement_designation,
                'grade_designation': grade_designation,
                'fonction_designation': fonction_designation,
                'header_path': _absolute_static_path('images/entete.PNG'),
            }

            # 3) Générer le PDF
            pdf_response = _render_to_pdf('gestion_administrative/autorisation_absence_enseignant_pdf.html', context)
            return pdf_response
    else:
        form = AutorisationAbsenceEnseignantForm()

    # Fournir les informations d'identité des enseignants pour l'aperçu côté client
    teachers_info = list(
        Teacher.objects.all().values(
            'id', 'nom_complet', 'matricule', 'grade', 'fonction', 'section', 'departement'
        )
    )
    # Map des désignations de département (éviter d'afficher le code)
    dept_map = {
        d['CodeDept']: d['DesignationDept']
        for d in Departement.objects.all().values('CodeDept', 'DesignationDept')
    }
    # Map des désignations de grade et de fonction
    grade_map = { g['CodeGrade']: g['DesignationGrade'] for g in Grade.objects.all().values('CodeGrade', 'DesignationGrade') }
    fonction_map = { f['CodeFonction']: f['DesignationFonction'] for f in Fonction.objects.all().values('CodeFonction', 'DesignationFonction') }
    for t in teachers_info:
        dept_code_or_name = t.get('departement')
        t['departement_designation'] = dept_map.get(dept_code_or_name, dept_code_or_name)
        grade_code_or_name = t.get('grade')
        t['grade_designation'] = grade_map.get(grade_code_or_name, grade_code_or_name)
        fonction_code_or_name = t.get('fonction')
        t['fonction_designation'] = fonction_map.get(fonction_code_or_name, fonction_code_or_name)

    return render(request, 'gestion_administrative/autorisation_absence_enseignant.html', {
        'form': form,
        'teachers_info': teachers_info,
    })


def _absolute_static_path(relative_static_path: str) -> str:
    """Retourne un chemin ou URL pour un asset static (utile pour xhtml2pdf)."""
    # Générer l'URL statique
    url = static(relative_static_path)
    
    # Priorité au STATIC_ROOT si collectstatic a été fait, sinon dossier static/
    candidate_paths = []
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        candidate_paths.append(os.path.join(settings.STATIC_ROOT, relative_static_path))
    # Dossier static de l'app
    candidate_paths.append(os.path.join(settings.BASE_DIR, 'static', relative_static_path))
    # Dossier staticfiles
    candidate_paths.append(os.path.join(settings.BASE_DIR, 'staticfiles', relative_static_path))

    for p in candidate_paths:
        if os.path.exists(p):
            return p
    # Fallback: essayer via static URL mais xhtml2pdf préfère les chemins locaux
    return os.path.join(settings.BASE_DIR, 'static', relative_static_path)


def _render_to_pdf(template_src: str, context: dict) -> HttpResponse:
    template = get_template(template_src)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = "inline; filename=autorisation_absence_enseignant.pdf"

    pisa_status = pisa.CreatePDF(
        src=html,
        dest=response,
        encoding='UTF-8',
        link_callback=lambda uri, rel: uri  # On fournit des chemins absolus dans le template
    )

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    return response


def _resolve_departement_designation(dept_code_or_name: str) -> str:
    """Retourne la désignation complète du département depuis son code.
    Si aucune correspondance n'est trouvée, retourne la valeur d'entrée.
    """
    if not dept_code_or_name:
        return ''
    try:
        # Essai par CodeDept
        dept = Departement.objects.filter(CodeDept=dept_code_or_name).first()
        if dept:
            return dept.DesignationDept
        # Essai par DesignationDept (si déjà une désignation est stockée)
        dept = Departement.objects.filter(DesignationDept=dept_code_or_name).first()
        if dept:
            return dept.DesignationDept
    except Exception:
        pass
    return dept_code_or_name


def _resolve_grade_designation(code_or_name: str) -> str:
    if not code_or_name:
        return ''
    try:
        g = Grade.objects.filter(CodeGrade=code_or_name).first()
        if g:
            return g.DesignationGrade
        g = Grade.objects.filter(DesignationGrade=code_or_name).first()
        if g:
            return g.DesignationGrade
    except Exception:
        pass
    return code_or_name


def _resolve_fonction_designation(code_or_name: str) -> str:
    if not code_or_name:
        return ''
    try:
        f = Fonction.objects.filter(CodeFonction=code_or_name).first()
        if f:
            return f.DesignationFonction
        f = Fonction.objects.filter(DesignationFonction=code_or_name).first()
        if f:
            return f.DesignationFonction
    except Exception:
        pass
    return code_or_name


def _date_fr(d):
    """Retourne une date formatée en français: Lundi 1 janvier 2025.
    Compatible xhtml2pdf en évitant les locales système.
    """
    if not d:
        return ''
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    # Python weekday(): Monday=0
    try:
        wd = d.weekday()
        jour = jours[wd]
        return f"{jour} {d.day} {mois[d.month-1]} {d.year}"
    except Exception:
        try:
            # Si d est un string parseable, fallback simple
            return str(d)
        except Exception:
            return ''


# ==================== GESTION DES ANNONCES ET COMMUNIQUÉS ====================

def liste_annonces(request):
    """Liste des annonces et communiqués avec filtrage et recherche"""
    # Récupérer toutes les annonces par défaut
    annonces = Annonce.objects.all()
    
    # Filtrage par type
    type_filtre = request.GET.get('type', '')
    if type_filtre:
        annonces = annonces.filter(type=type_filtre)
    
    # Filtrage par cible
    cible_filtre = request.GET.get('cible', '')
    if cible_filtre:
        annonces = annonces.filter(cible=cible_filtre)
    
    # Filtrage par statut de publication
    statut_filtre = request.GET.get('statut', '')
    if statut_filtre == 'publie':
        annonces = annonces.filter(publie=True)
    elif statut_filtre == 'non_publie':
        annonces = annonces.filter(publie=False)
    
    # Recherche textuelle
    recherche = request.GET.get('recherche', '')
    if recherche:
        annonces = annonces.filter(
            Q(titre__icontains=recherche) | 
            Q(contenu__icontains=recherche)
        )
    
    # Pagination
    paginator = Paginator(annonces, 15)  # 15 annonces par page
    page = request.GET.get('page', 1)
    annonces_page = paginator.get_page(page)
    
    context = {
        'annonces': annonces_page,
        'type_filtre': type_filtre,
        'cible_filtre': cible_filtre,
        'statut_filtre': statut_filtre,
        'recherche': recherche,
        'types': Annonce.TYPE_CHOICES,
        'cibles': Annonce.CIBLE_CHOICES,
    }
    
    return render(request, 'gestion_administrative/annonces/liste.html', context)


def ajouter_annonce(request):
    """Ajouter une nouvelle annonce ou communiqué"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        titre = request.POST.get('titre')
        contenu = request.POST.get('contenu')
        type_annonce = request.POST.get('type')
        cible = request.POST.get('cible')
        date_publication = request.POST.get('date_publication')
        date_expiration = request.POST.get('date_expiration')
        important = 'important' in request.POST
        publie = 'publie' in request.POST
        
        # Récupérer l'enseignant qui publie (à adapter selon votre logique d'authentification)
        # Ici on suppose qu'on reçoit l'ID de l'enseignant dans le formulaire
        publie_par_id = request.POST.get('publie_par')
        publie_par = None
        if publie_par_id:
            try:
                publie_par = Teacher.objects.get(id=publie_par_id)
            except Teacher.DoesNotExist:
                pass
        
        # Créer l'annonce
        annonce = Annonce(
            titre=titre,
            contenu=contenu,
            type=type_annonce,
            cible=cible,
            publie=publie,
            important=important,
            publie_par=publie_par
        )
        
        # Gérer les dates
        if date_publication:
            annonce.date_publication = date_publication
        else:
            annonce.date_publication = timezone.now()
        
        if date_expiration:
            annonce.date_expiration = date_expiration
        
        # Gérer la pièce jointe
        if 'piece_jointe' in request.FILES:
            annonce.piece_jointe = request.FILES['piece_jointe']
        
        # Sauvegarder l'annonce
        annonce.save()
        
        messages.success(request, 'Annonce créée avec succès.')
        return redirect('gestion_administrative:annonces')
    
    # Récupérer la liste des enseignants pour le champ publie_par
    teachers = Teacher.objects.all().order_by('nom_complet')
    
    context = {
        'types': Annonce.TYPE_CHOICES,
        'cibles': Annonce.CIBLE_CHOICES,
        'teachers': teachers,
    }
    
    return render(request, 'gestion_administrative/annonces/form.html', context)


def modifier_annonce(request, annonce_id):
    """Modifier une annonce existante"""
    annonce = get_object_or_404(Annonce, id=annonce_id)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        annonce.titre = request.POST.get('titre')
        annonce.contenu = request.POST.get('contenu')
        annonce.type = request.POST.get('type')
        annonce.cible = request.POST.get('cible')
        annonce.important = 'important' in request.POST
        annonce.publie = 'publie' in request.POST
        
        # Gérer les dates
        date_publication = request.POST.get('date_publication')
        if date_publication:
            annonce.date_publication = date_publication
        
        date_expiration = request.POST.get('date_expiration')
        if date_expiration:
            annonce.date_expiration = date_expiration
        
        # Récupérer l'enseignant qui publie
        publie_par_id = request.POST.get('publie_par')
        if publie_par_id:
            try:
                annonce.publie_par = Teacher.objects.get(id=publie_par_id)
            except Teacher.DoesNotExist:
                pass
        
        # Gérer la pièce jointe
        if 'piece_jointe' in request.FILES:
            annonce.piece_jointe = request.FILES['piece_jointe']
        
        # Sauvegarder l'annonce
        annonce.save()
        
        messages.success(request, 'Annonce modifiée avec succès.')
        return redirect('gestion_administrative:annonces')
    
    # Récupérer la liste des enseignants pour le champ publie_par
    teachers = Teacher.objects.all().order_by('nom_complet')
    
    context = {
        'annonce': annonce,
        'types': Annonce.TYPE_CHOICES,
        'cibles': Annonce.CIBLE_CHOICES,
        'teachers': teachers,
    }
    
    return render(request, 'gestion_administrative/annonces/form.html', context)


def supprimer_annonce(request, annonce_id):
    """Supprimer une annonce"""
    if request.method == 'POST':
        annonce = get_object_or_404(Annonce, id=annonce_id)
        titre = annonce.titre  # Sauvegarder le titre pour le message
        annonce.delete()
        return JsonResponse({'success': True, 'message': f'Annonce "{titre}" supprimée avec succès.'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# Vues pour la gestion des inscriptions
def liste_inscriptions(request):
    """Affiche la liste des inscriptions"""
    inscriptions = Inscription.objects.all().order_by('-date_inscription')
    
    # Pagination
    paginator = Paginator(inscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'gestion_administrative/inscriptions_list.html', {
        'page_obj': page_obj
    })


def ajouter_inscription(request):
    """Ajoute une nouvelle inscription"""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription ajoutée avec succès.")
            return redirect('gestion_administrative:liste_inscriptions')
    else:
        form = InscriptionForm()
    
    return render(request, 'gestion_administrative/inscription_form.html', {
        'form': form,
        'title': 'Ajouter une inscription'
    })


def modifier_inscription(request, inscription_id):
    """Modifie une inscription existante"""
    inscription = get_object_or_404(Inscription, id=inscription_id)
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST, instance=inscription)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription modifiée avec succès.")
            return redirect('gestion_administrative:liste_inscriptions')
    else:
        form = InscriptionForm(instance=inscription)
    
    return render(request, 'gestion_administrative/inscription_form.html', {
        'form': form,
        'title': 'Modifier une inscription',
        'inscription': inscription
    })


def supprimer_inscription(request, inscription_id):
    """Supprime une inscription"""
    if request.method == 'POST':
        inscription = get_object_or_404(Inscription, id=inscription_id)
        inscription.delete()
        messages.success(request, "Inscription supprimée avec succès.")
        return redirect('gestion_administrative:liste_inscriptions')
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


def importer_inscriptions_excel(request):
    """Importe des inscriptions depuis un fichier Excel"""
    if request.method == 'POST':
        form = ImportInscriptionsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                print('DEBUG importer_inscriptions_excel: using pandas + *_id assignment')
                fichier = request.FILES['excel_file']
                df = pd.read_excel(fichier)
                
                # Colonnes attendues
                colonnes_requises = ['matricule', 'code_classe', 'annee_academique']
                
                # Vérifier les colonnes requises
                for col in colonnes_requises:
                    if col not in df.columns:
                        messages.error(request, f'Colonne requise manquante: {col}')
                        return render(request, 'gestion_administrative/import_inscriptions.html', {'form': form})
                
                inscriptions_crees = 0
                inscriptions_modifiees = 0
                erreurs = []
                
                for index, row in df.iterrows():
                    try:
                        # Récupérer les données
                        matricule = str(row['matricule']).strip()
                        code_classe = str(row['code_classe']).strip()
                        annee_academique = str(row['annee_academique']).strip()
                        
                        # Vérifier l'étudiant
                        try:
                            etudiant = Etudiant.objects.get(matricule=matricule)
                        except Etudiant.DoesNotExist:
                            erreurs.append(f'Ligne {index + 2}: Étudiant {matricule} non trouvé')
                            continue
                        
                        # Vérifier la classe
                        try:
                            classe_id = Classe.objects.only('id').get(CodeClasse=code_classe).id
                        except Classe.DoesNotExist:
                            erreurs.append(f'Ligne {index + 2}: Classe {code_classe} non trouvée')
                            continue
                        
                        # Créer ou mettre à jour l'inscription
                        inscription, created = Inscription.objects.update_or_create(
                            etudiant_id=etudiant.id,
                            code_classe_id=classe_id,
                            annee_academique=annee_academique,
                            defaults={'est_actif': True}
                        )
                        
                        if created:
                            inscriptions_crees += 1
                        else:
                            inscriptions_modifiees += 1
                            
                    except Exception as e:
                        erreurs.append(f'Ligne {index + 2}: {str(e)}')
                
                # Messages de résultat
                if inscriptions_crees > 0:
                    messages.success(request, f'{inscriptions_crees} inscriptions créées')
                if inscriptions_modifiees > 0:
                    messages.info(request, f'{inscriptions_modifiees} inscriptions modifiées')
                if erreurs:
                    for erreur in erreurs[:5]:  # Limiter à 5 erreurs
                        messages.error(request, erreur)
                    if len(erreurs) > 5:
                        messages.error(request, f'... et {len(erreurs) - 5} autres erreurs')
                
                return redirect('gestion_administrative:liste_inscriptions')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'importation: {str(e)}')
    else:
        form = ImportInscriptionsForm()
    
    return render(request, 'gestion_administrative/import_inscriptions.html', {'form': form})
