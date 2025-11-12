from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from .models import (Section, Departement, Mention, Niveau, Classe, Grade, 
                     CategorieEnseignant, Semestre, Fonction, AnneeAcademique, Salle, Creneau, SemaineCours)
from .forms import SemaineCoursForm
import openpyxl
from django.db import transaction


class SafeDeleteView(DeleteView):
    """
    Classe de base pour toutes les vues de suppression avec transaction atomique.
    Utilise le pattern robuste avec select_for_update() pour éviter les problèmes SQLite.
    """
    def delete(self, request, *args, **kwargs):
        try:
            # Utiliser une transaction atomique pour garantir la cohérence
            with transaction.atomic():
                # Récupérer et verrouiller l'objet pour éviter les conflits concurrents
                self.object = self.get_queryset().select_for_update().get(pk=kwargs['pk'])
                success_url = self.get_success_url()
                
                # Supprimer l'objet (les contraintes FK CASCADE s'occuperont des relations)
                self.object.delete()
            
            # Message de succès (optionnel, peut être surchargé par les sous-classes)
            if hasattr(self, 'success_message'):
                messages.success(request, self.success_message)
            
            return redirect(success_url)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect(self.success_url)


def gestion_entites(request):
    """Affiche la page de gestion des entités."""
    return render(request, 'reglage/gestion_entites.html')

# Vues pour Section
class SectionListView(ListView):
    model = Section
    template_name = 'reglage/section_list.html'
    context_object_name = 'sections'

class SectionCreateView(CreateView):
    model = Section
    template_name = 'reglage/section_form.html'
    fields = ['CodeSection', 'DesignationSection']
    success_url = reverse_lazy('reglage:section_list')

class SectionUpdateView(UpdateView):
    model = Section
    template_name = 'reglage/section_form.html'
    fields = ['CodeSection', 'DesignationSection']
    success_url = reverse_lazy('reglage:section_list')

class SectionDeleteView(SafeDeleteView):
    model = Section
    template_name = 'reglage/section_confirm_delete.html'
    success_url = reverse_lazy('reglage:section_list')

# Vues pour Departement
class DepartementListView(ListView):
    model = Departement
    template_name = 'reglage/departement_list.html'
    context_object_name = 'departements'

class DepartementCreateView(CreateView):
    model = Departement
    template_name = 'reglage/departement_form.html'
    fields = ['CodeDept', 'DesignationDept', 'section']
    success_url = reverse_lazy('reglage:departement_list')

class DepartementUpdateView(UpdateView):
    model = Departement
    template_name = 'reglage/departement_form.html'
    fields = ['CodeDept', 'DesignationDept', 'section']
    success_url = reverse_lazy('reglage:departement_list')

class DepartementDeleteView(SafeDeleteView):
    model = Departement
    template_name = 'reglage/departement_confirm_delete.html'
    success_url = reverse_lazy('reglage:departement_list')

# Vues pour Mention
class MentionListView(ListView):
    model = Mention
    template_name = 'reglage/mention_list.html'
    context_object_name = 'mentions'

class MentionCreateView(CreateView):
    model = Mention
    template_name = 'reglage/mention_form.html'
    fields = ['CodeMention', 'DesignationMention']
    success_url = reverse_lazy('reglage:mention_list')

class MentionUpdateView(UpdateView):
    model = Mention
    template_name = 'reglage/mention_form.html'
    fields = ['CodeMention', 'DesignationMention']
    success_url = reverse_lazy('reglage:mention_list')

class MentionDeleteView(SafeDeleteView):
    model = Mention
    template_name = 'reglage/mention_confirm_delete.html'
    success_url = reverse_lazy('reglage:mention_list')

# Vues pour Niveau
class NiveauListView(ListView):
    model = Niveau
    template_name = 'reglage/niveau_list.html'
    context_object_name = 'niveaux'

class NiveauCreateView(CreateView):
    model = Niveau
    template_name = 'reglage/niveau_form.html'
    fields = ['CodeNiveau', 'DesignationNiveau']
    success_url = reverse_lazy('reglage:niveau_list')

class NiveauUpdateView(UpdateView):
    model = Niveau
    template_name = 'reglage/niveau_form.html'
    fields = ['CodeNiveau', 'DesignationNiveau']
    success_url = reverse_lazy('reglage:niveau_list')

class NiveauDeleteView(SafeDeleteView):
    model = Niveau
    template_name = 'reglage/niveau_confirm_delete.html'
    success_url = reverse_lazy('reglage:niveau_list')

# Vues pour Classe
class ClasseListView(ListView):
    model = Classe
    template_name = 'reglage/classe_list.html'
    context_object_name = 'classes'

class ClasseCreateView(CreateView):
    model = Classe
    template_name = 'reglage/classe_form.html'
    fields = ['niveau', 'mention']
    success_url = reverse_lazy('reglage:classe_list')

class ClasseUpdateView(UpdateView):
    model = Classe
    template_name = 'reglage/classe_form.html'
    fields = ['niveau', 'mention']
    success_url = reverse_lazy('reglage:classe_list')

class ClasseDeleteView(SafeDeleteView):
    model = Classe
    template_name = 'reglage/classe_confirm_delete.html'
    success_url = reverse_lazy('reglage:classe_list')

def classe_import_excel(request):
    """Importer des classes depuis un fichier Excel"""
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            replace_all = request.POST.get('replace_all') == 'on'
            
            if not excel_file:
                messages.error(request, 'Aucun fichier sélectionné')
                return redirect('reglage:classe_list')
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Format de fichier invalide. Utilisez .xlsx ou .xls')
                return redirect('reglage:classe_list')
            
            # Charger le fichier Excel
            try:
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
            except Exception as e:
                messages.error(request, f'Erreur lors de la lecture du fichier Excel: {str(e)}')
                return redirect('reglage:classe_list')
            
            # Compter les lignes (en excluant l'en-tête)
            total_rows = sheet.max_row - 1
            
            if total_rows < 1:
                messages.warning(request, 'Le fichier Excel est vide')
                return redirect('reglage:classe_list')
            
            classes_created = 0
            classes_updated = 0
            errors = []
            
            with transaction.atomic():
                # Supprimer toutes les classes si demandé
                if replace_all:
                    deleted_count = Classe.objects.all().delete()[0]
                    messages.info(request, f'{deleted_count} classe(s) supprimée(s)')
                
                # Parcourir les lignes (en sautant l'en-tête)
                for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    try:
                        # Vérifier que la ligne contient des données
                        if not any(row):
                            continue
                        
                        code_classe = str(row[0]).strip() if row[0] else None
                        designation = str(row[1]).strip() if row[1] else None
                        niveau = str(row[2]).strip() if row[2] else None
                        mention = str(row[3]).strip() if row[3] else None
                        
                        # Validation
                        if not code_classe:
                            errors.append(f"Ligne {row_num}: CodeClasse manquant")
                            continue
                        
                        if not designation:
                            errors.append(f"Ligne {row_num}: DesignationClasse manquant")
                            continue
                        
                        if not niveau:
                            errors.append(f"Ligne {row_num}: Niveau manquant")
                            continue
                        
                        # Récupérer ou créer les objets Niveau et Mention
                        try:
                            # Tenter par désignation
                            niveau_obj = Niveau.objects.filter(DesignationNiveau=niveau).first()
                            if not niveau_obj:
                                # Tenter par code (si un code identique existe déjà)
                                niveau_obj = Niveau.objects.filter(CodeNiveau=niveau).first()
                                if niveau_obj:
                                    # Mettre à jour la désignation si différente
                                    if niveau_obj.DesignationNiveau != niveau:
                                        niveau_obj.DesignationNiveau = niveau
                                        niveau_obj.save(update_fields=["DesignationNiveau"]) 
                                else:
                                    niveau_obj = Niveau.objects.create(CodeNiveau=niveau, DesignationNiveau=niveau)
                        except Exception as e:
                            errors.append(f"Ligne {row_num}: Erreur niveau - {str(e)}")
                            continue
                        
                        mention_obj = None
                        if mention:
                            try:
                                mention_obj = Mention.objects.filter(DesignationMention=mention).first()
                                if not mention_obj:
                                    mention_obj = Mention.objects.filter(CodeMention=mention).first()
                                    if mention_obj:
                                        if mention_obj.DesignationMention != mention:
                                            mention_obj.DesignationMention = mention
                                            mention_obj.save(update_fields=["DesignationMention"]) 
                                    else:
                                        mention_obj = Mention.objects.create(CodeMention=mention, DesignationMention=mention)
                            except Exception as e:
                                errors.append(f"Ligne {row_num}: Erreur mention - {str(e)}")
                                continue
                        
                        # Créer ou mettre à jour la classe
                        classe, created = Classe.objects.update_or_create(
                            CodeClasse=code_classe,
                            defaults={
                                'DesignationClasse': designation,
                                'niveau': niveau_obj,
                                'mention': mention_obj
                            }
                        )
                        
                        if created:
                            classes_created += 1
                        else:
                            classes_updated += 1
                            
                    except Exception as e:
                        errors.append(f"Ligne {row_num}: {str(e)}")
                        continue
            
            # Messages de résultat
            if classes_created > 0:
                messages.success(request, f'✅ {classes_created} classe(s) créée(s) avec succès')
            
            if classes_updated > 0:
                messages.info(request, f'ℹ️ {classes_updated} classe(s) mise(s) à jour')
            
            if errors:
                messages.warning(request, f'⚠️ {len(errors)} erreur(s) rencontrée(s):')
                for error in errors[:10]:  # Limiter à 10 erreurs affichées
                    messages.error(request, error)
                if len(errors) > 10:
                    messages.error(request, f'... et {len(errors) - 10} autre(s) erreur(s)')
            
            if classes_created == 0 and classes_updated == 0:
                messages.warning(request, 'Aucune classe importée')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'importation: {str(e)}')
        
        return redirect('reglage:classe_list')
    
    return redirect('reglage:classe_list')

# Vues pour Grade
class GradeListView(ListView):
    model = Grade
    template_name = 'reglage/grade_list.html'
    context_object_name = 'grades'

class GradeCreateView(CreateView):
    model = Grade
    template_name = 'reglage/grade_form.html'
    fields = ['CodeGrade', 'DesignationGrade']
    success_url = reverse_lazy('reglage:grade_list')

class GradeUpdateView(UpdateView):
    model = Grade
    template_name = 'reglage/grade_form.html'
    fields = ['CodeGrade', 'DesignationGrade']
    success_url = reverse_lazy('reglage:grade_list')

class GradeDeleteView(SafeDeleteView):
    model = Grade
    template_name = 'reglage/grade_confirm_delete.html'
    success_url = reverse_lazy('reglage:grade_list')

# Vues pour CategorieEnseignant
class CategorieListView(ListView):
    model = CategorieEnseignant
    template_name = 'reglage/categorie_list.html'
    context_object_name = 'categories'

class CategorieCreateView(CreateView):
    model = CategorieEnseignant
    template_name = 'reglage/categorie_form.html'
    fields = ['CodeCategorie', 'DesignationCategorie']
    success_url = reverse_lazy('reglage:categorie_list')

class CategorieUpdateView(UpdateView):
    model = CategorieEnseignant
    template_name = 'reglage/categorie_form.html'
    fields = ['CodeCategorie', 'DesignationCategorie']
    success_url = reverse_lazy('reglage:categorie_list')

class CategorieDeleteView(SafeDeleteView):
    model = CategorieEnseignant
    template_name = 'reglage/categorie_confirm_delete.html'
    success_url = reverse_lazy('reglage:categorie_list')

# Vues pour Semestre
class SemestreListView(ListView):
    model = Semestre
    template_name = 'reglage/semestre_list.html'
    context_object_name = 'semestres'

class SemestreCreateView(CreateView):
    model = Semestre
    template_name = 'reglage/semestre_form.html'
    fields = ['CodeSemestre', 'DesignationSemestre']
    success_url = reverse_lazy('reglage:semestre_list')

class SemestreUpdateView(UpdateView):
    model = Semestre
    template_name = 'reglage/semestre_form.html'
    fields = ['CodeSemestre', 'DesignationSemestre']
    success_url = reverse_lazy('reglage:semestre_list')

class SemestreDeleteView(SafeDeleteView):
    model = Semestre
    template_name = 'reglage/semestre_confirm_delete.html'
    success_url = reverse_lazy('reglage:semestre_list')

# Vues pour Fonction
class FonctionListView(ListView):
    model = Fonction
    template_name = 'reglage/fonction_list.html'
    context_object_name = 'fonctions'

class FonctionCreateView(CreateView):
    model = Fonction
    template_name = 'reglage/fonction_form.html'
    fields = ['CodeFonction', 'DesignationFonction']
    success_url = reverse_lazy('reglage:fonction_list')

class FonctionUpdateView(UpdateView):
    model = Fonction
    template_name = 'reglage/fonction_form.html'
    fields = ['CodeFonction', 'DesignationFonction']
    success_url = reverse_lazy('reglage:fonction_list')

class FonctionDeleteView(SafeDeleteView):
    model = Fonction
    template_name = 'reglage/fonction_confirm_delete.html'
    success_url = reverse_lazy('reglage:fonction_list')


# ==================== NOUVELLES VUES ====================

# Vues pour AnneeAcademique
class AnneeAcademiqueListView(ListView):
    model = AnneeAcademique
    template_name = 'reglage/annee_list.html'
    context_object_name = 'annees'

class AnneeAcademiqueCreateView(CreateView):
    model = AnneeAcademique
    template_name = 'reglage/annee_form.html'
    fields = ['code', 'designation', 'date_debut', 'date_fin', 'est_en_cours']
    success_url = reverse_lazy('reglage:annee_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Année académique créée avec succès.")
        return super().form_valid(form)

class AnneeAcademiqueUpdateView(UpdateView):
    model = AnneeAcademique
    template_name = 'reglage/annee_form.html'
    fields = ['code', 'designation', 'date_debut', 'date_fin', 'est_en_cours']
    success_url = reverse_lazy('reglage:annee_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Année académique modifiée avec succès.")
        return super().form_valid(form)

class AnneeAcademiqueDeleteView(SafeDeleteView):
    model = AnneeAcademique
    template_name = 'reglage/annee_confirm_delete.html'
    success_url = reverse_lazy('reglage:annee_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Année académique supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# Vues pour Salle
class SalleListView(ListView):
    model = Salle
    template_name = 'reglage/salle_list.html'
    context_object_name = 'salles'
    
    def get_queryset(self):
        queryset = Salle.objects.all()
        type_filtre = self.request.GET.get('type')
        if type_filtre:
            queryset = queryset.filter(type_salle=type_filtre)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types_salle'] = Salle._meta.get_field('type_salle').choices
        return context

class SalleCreateView(CreateView):
    model = Salle
    template_name = 'reglage/salle_form.html'
    fields = ['code', 'designation', 'capacite', 'type_salle', 'est_disponible', 'remarques']
    success_url = reverse_lazy('reglage:salle_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Salle créée avec succès.")
        return super().form_valid(form)

class SalleUpdateView(UpdateView):
    model = Salle
    template_name = 'reglage/salle_form.html'
    fields = ['code', 'designation', 'capacite', 'type_salle', 'est_disponible', 'remarques']
    success_url = reverse_lazy('reglage:salle_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Salle modifiée avec succès.")
        return super().form_valid(form)

class SalleDeleteView(SafeDeleteView):
    model = Salle
    template_name = 'reglage/salle_confirm_delete.html'
    success_url = reverse_lazy('reglage:salle_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Salle supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# Vues pour Creneau
class CreneauListView(ListView):
    model = Creneau
    template_name = 'reglage/creneau_list.html'
    context_object_name = 'creneaux'

class CreneauCreateView(CreateView):
    model = Creneau
    template_name = 'reglage/creneau_form.html'
    fields = ['code', 'designation', 'heure_debut', 'heure_fin', 'est_actif', 'ordre']
    success_url = reverse_lazy('reglage:creneau_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Créneau créé avec succès.")
        return super().form_valid(form)

class CreneauUpdateView(UpdateView):
    model = Creneau
    template_name = 'reglage/creneau_form.html'
    fields = ['code', 'designation', 'heure_debut', 'heure_fin', 'est_actif', 'ordre']
    success_url = reverse_lazy('reglage:creneau_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Créneau modifié avec succès.")
        return super().form_valid(form)

class CreneauDeleteView(SafeDeleteView):
    model = Creneau
    template_name = 'reglage/creneau_confirm_delete.html'
    success_url = reverse_lazy('reglage:creneau_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Créneau supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


# Vues pour SemaineCours
class SemaineCoursListView(ListView):
    model = SemaineCours
    template_name = 'reglage/semaine_list.html'
    context_object_name = 'semaines'
    
    def get_queryset(self):
        queryset = SemaineCours.objects.all()
        annee = self.request.GET.get('annee')
        if annee:
            queryset = queryset.filter(annee_academique=annee)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupérer les années académiques pour le filtre
        context['annees'] = SemaineCours.objects.values_list(
            'annee_academique', flat=True
        ).distinct().order_by('-annee_academique')
        return context

class SemaineCoursCreateView(CreateView):
    model = SemaineCours
    template_name = 'reglage/semaine_form.html'
    form_class = SemaineCoursForm
    success_url = reverse_lazy('reglage:semaine_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Semaine de cours créée avec succès.")
        return super().form_valid(form)

class SemaineCoursUpdateView(UpdateView):
    model = SemaineCours
    template_name = 'reglage/semaine_form.html'
    form_class = SemaineCoursForm
    success_url = reverse_lazy('reglage:semaine_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Semaine de cours modifiée avec succès.")
        return super().form_valid(form)

class SemaineCoursDeleteView(SafeDeleteView):
    model = SemaineCours
    template_name = 'reglage/semaine_confirm_delete.html'
    success_url = reverse_lazy('reglage:semaine_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Semaine de cours supprimée avec succès.")
        return super().delete(request, *args, **kwargs)
