from django import forms
from .models import Course
from reglage.models import Classe, Semestre, Departement, Section
import logging

logger = logging.getLogger(__name__)

class CourseForm(forms.ModelForm):
    # Définition explicite des champs de sélection
    classe = forms.ChoiceField(
        choices=[], 
        required=True, 
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Classe'}),
        label=''
    )
    semestre = forms.ChoiceField(
        choices=[], 
        required=True, 
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Semestre'}),
        label=''
    )
    departement = forms.ChoiceField(
        choices=[], 
        required=True, 
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Département'}),
        label=''
    )
    section = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Section (automatique)',
            'readonly': 'readonly',
            'style': 'background-color: #e9ecef; cursor: not-allowed;'
        }),
        label=''
    )

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        
        try:
            # Remplir les choix pour les classes à partir du modèle Classe
            classes = Classe.objects.all().order_by('CodeClasse')
            classe_choices = [('', 'Sélectionner une classe')] + [(classe.CodeClasse, classe.DesignationClasse) for classe in classes]
            self.fields['classe'].choices = classe_choices
            
            # Remplir les choix pour les semestres à partir du modèle Semestre
            semestres = Semestre.objects.all().order_by('CodeSemestre')
            semestre_choices = [('', 'Sélectionner un semestre')] + [(semestre.CodeSemestre, semestre.DesignationSemestre) for semestre in semestres]
            self.fields['semestre'].choices = semestre_choices
            
            # Remplir les choix pour les départements à partir du modèle Departement
            departements = Departement.objects.all().order_by('CodeDept')
            departement_choices = [('', 'Sélectionner un département')] + [(dept.CodeDept, dept.DesignationDept) for dept in departements]
            self.fields['departement'].choices = departement_choices
            
            # Définir les valeurs initiales si l'instance existe
            if self.instance.pk:
                # Pour une instance existante, nous devons faire correspondre les valeurs des champs 
                # avec les options disponibles dans les menus déroulants
                try:
                    # Trouver le code correspondant pour la classe existante
                    classes_map = {c.DesignationClasse: c.CodeClasse for c in classes}
                    if self.instance.classe in classes_map:
                        self.fields['classe'].initial = classes_map[self.instance.classe]
                    
                    # Le semestre est déjà enregistré sous forme de code, donc pas besoin de conversion
                    self.fields['semestre'].initial = self.instance.semestre
                    
                    # Trouver le code correspondant pour le département existant
                    depts_map = {d.DesignationDept: d.CodeDept for d in departements}
                    if self.instance.departement in depts_map:
                        self.fields['departement'].initial = depts_map[self.instance.departement]
                    
                    # Pré-remplir la section si elle existe
                    if self.instance.section:
                        self.fields['section'].initial = self.instance.section
                except Exception as e:
                    logger.error(f"Erreur lors de l'initialisation des valeurs: {e}")
        except Exception as e:
            print(f"Erreur lors de l'initialisation du formulaire: {e}")
            
    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"Données nettoyées du formulaire: {cleaned_data}")
        return cleaned_data
        
    def save(self, commit=True):
        try:
            logger.info(f"Début de la sauvegarde du formulaire. Données: {self.cleaned_data}")
            instance = super().save(commit=False)
            
            # Récupérer les codes des champs sélectionnés
            classe_code = self.cleaned_data.get('classe', '')
            semestre_code = self.cleaned_data.get('semestre', '')
            departement_code = self.cleaned_data.get('departement', '')
            
            # Enregistrer les codes dans le modèle
            instance.classe = classe_code
            instance.semestre = semestre_code
            instance.departement = departement_code
            
            # Récupérer automatiquement la section du département
            if departement_code:
                try:
                    dept = Departement.objects.get(CodeDept=departement_code)
                    instance.section = dept.section.CodeSection
                except Departement.DoesNotExist:
                    instance.section = None
            else:
                instance.section = None
            
            logger.info(f"Valeurs assignées: classe={instance.classe}, semestre={instance.semestre}, departement={instance.departement}")
            
            if commit:
                instance.save()
                logger.info(f"Cours sauvegardé avec succès. ID: {instance.pk}")
                
            return instance
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du formulaire: {e}")
            raise
    
    class Meta:
        model = Course
        fields = ['code_ue', 'intitule_ue', 'intitule_ec', 'credit', 'cmi', 'td_tp', 'classe', 'semestre', 'departement', 'section']
        labels = {
            'code_ue': '',
            'intitule_ue': '',
            'intitule_ec': '',
            'credit': '',
            'cmi': '',
            'td_tp': '',
            'classe': '',
            'semestre': '',
            'departement': '',
            'section': '',
        }
        widgets = {
            'code_ue': forms.TextInput(attrs={'placeholder': 'Code UE', 'class': 'form-control'}),
            'intitule_ue': forms.TextInput(attrs={'placeholder': 'Intitulé UE', 'class': 'form-control'}),
            'intitule_ec': forms.TextInput(attrs={'placeholder': 'Intitulé EC', 'class': 'form-control'}),
            'credit': forms.NumberInput(attrs={'placeholder': 'Crédit', 'class': 'form-control'}),
            'cmi': forms.NumberInput(attrs={'placeholder': 'CMI', 'class': 'form-control'}),
            'td_tp': forms.NumberInput(attrs={'placeholder': 'TD+TP', 'class': 'form-control'}),
        }
