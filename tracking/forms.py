from django import forms
from django.utils import timezone
from .models import TeachingProgress, AcademicWeek
from courses.models import Course
from teachers.models import Teacher
from reglage.models import SemaineCours

class AcademicWeekForm(forms.ModelForm):
    """Formulaire pour la gestion des semaines académiques"""
    class Meta:
        model = AcademicWeek
        fields = ['codesemaine', 'semestre', 'start_date', 'end_date', 'academic_year', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'codesemaine': forms.TextInput(attrs={'class': 'form-control'}),
            'semestre': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir l'année académique par défaut
        if not self.instance.pk:
            current_year = timezone.now().year
            academic_year = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
            self.initial['academic_year'] = academic_year
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Vérifier que la date de fin est postérieure à la date de début
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'La date de fin doit être postérieure à la date de début')
        
        # Assurer que l'année académique est présente
        if not cleaned_data.get('academic_year'):
            # Si l'année académique est manquante, utiliser la valeur par défaut
            current_year = timezone.now().year
            cleaned_data['academic_year'] = f"{current_year-1}-{current_year}" if timezone.now().month < 9 else f"{current_year}-{current_year+1}"
        
        return cleaned_data

class TeachingProgressForm(forms.ModelForm):
    """Formulaire pour l'enregistrement du suivi des enseignements"""
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),  # Include all courses for validation
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Sélectionner une UE",
        label="UE"
    )
    
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all().order_by('nom_complet'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Sélectionner un enseignant",
        label="Enseignant"
    )
    
    week = forms.ModelChoiceField(
        queryset=SemaineCours.objects.none(),  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Sélectionner une semaine",
        label="Semaine de cours"
    )
    

    
    class Meta:
        model = TeachingProgress
        fields = ['course', 'teacher', 'week', 'hours_done', 'status', 'comment']
        widgets = {
            'hours_done': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0', 'placeholder': "Nombre d'heures réalisées"}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pour filtrer les choix en fonction de l'utilisateur ou des droits d'accès
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les enseignants par organisation si l'utilisateur appartient à une organisation
        if user:
            from accounts.organisation_utils import get_user_organisation
            user_organisation = get_user_organisation(user)
            if user_organisation:
                # Filtrer les enseignants par section de l'organisation
                teachers_queryset = Teacher.objects.filter(
                    section=user_organisation.code
                ).order_by('nom_complet')
                self.fields['teacher'].queryset = teachers_queryset
        
        # Charger les semaines depuis le module réglage
        # Afficher toutes les semaines enregistrées, triées par année académique et numéro de semaine
        weeks_queryset = SemaineCours.objects.all().order_by('-annee_academique', 'numero_semaine')
        
        self.fields['week'].queryset = weeks_queryset
        self.fields['week'].empty_label = "Sélectionner une semaine"
        
        # Personnaliser l'affichage des options du dropdown de semaines
        # Format: "S-001 - Semaine X (date_debut - date_fin)"
        self.fields['week'].label_from_instance = lambda obj: f"{obj.designation} ({obj.date_debut.strftime('%d/%m/%Y')} - {obj.date_fin.strftime('%d/%m/%Y')})"
        
        # Initialiser le queryset des cours pour inclure tous les cours
        # Cela permet la validation même si le cours est sélectionné dynamiquement
        self.fields['course'].queryset = Course.objects.all()
        
        # Si on modifie un enregistrement existant, s'assurer que le cours est inclus
        if self.instance and self.instance.pk and self.instance.course:
            # Le cours est déjà inclus dans le queryset complet
            pass

class ProgressFilterForm(forms.Form):
    """Formulaire pour filtrer les suivis d'enseignement"""
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Tous les enseignants"
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Tous les cours"
    )
    
    academic_year = forms.ChoiceField(
        choices=[],  # Sera rempli dynamiquement
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=""
    )
    
    week_start = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Semaine début'})
    )
    
    week_end = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Semaine fin'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(dict(TeachingProgress.status.field.choices).items()),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Générer les choix pour les années académiques
        current_year = timezone.now().year
        years = []
        
        # Ajouter les 5 dernières années académiques
        for i in range(5):
            year = current_year - i
            academic_year = f"{year-1}-{year}"
            years.append((academic_year, academic_year))
        
        self.fields['academic_year'].choices = [('', 'Toutes les années')] + years
