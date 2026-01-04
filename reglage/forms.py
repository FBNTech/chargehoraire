from django import forms
from .models import SemaineCours, AnneeAcademique, Creneau, Section


class SemaineCoursForm(forms.ModelForm):
    """Formulaire personnalisé pour les semaines de cours"""
    
    class Meta:
        model = SemaineCours
        fields = ['numero_semaine', 'date_debut', 'date_fin', 'annee_academique', 'est_en_cours', 'remarques']
        widgets = {
            'numero_semaine': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1, 2, 3...'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'jj/mm/aaaa'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'jj/mm/aaaa'
            }),
            'annee_academique': forms.Select(attrs={
                'class': 'form-select'
            }),
            'est_en_cours': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Remarques optionnelles...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer toutes les années académiques
        annees = AnneeAcademique.objects.all().order_by('-code')
        annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
        
        # Créer les choix pour le combo année académique
        choix_annees = [('', '-- Sélectionner une année --')]
        for annee in annees:
            label = f"{annee.code}"
            if annee.est_en_cours:
                label += " ★ (En cours)"
            choix_annees.append((annee.code, label))
        
        # Remplacer le champ par un Select avec les choix
        self.fields['annee_academique'] = forms.ChoiceField(
            choices=choix_annees,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Pré-remplir avec l'année en cours si création (pas de pk)
        if not self.instance.pk and annee_courante:
            self.initial['annee_academique'] = annee_courante.code


class CreneauForm(forms.ModelForm):
    """Formulaire personnalisé pour les créneaux horaires"""
    
    class Meta:
        model = Creneau
        fields = ['code', 'designation', 'type_creneau', 'section', 'heure_debut', 'heure_fin', 'est_actif', 'ordre']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: AM, PM, S1, S2...'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Matinée, Après-midi...'
            }),
            'type_creneau': forms.Select(attrs={
                'class': 'form-select'
            }),
            'section': forms.Select(attrs={
                'class': 'form-select',
                'id': 'section_select'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'est_actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ordre d\'affichage'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer toutes les sections
        sections = Section.objects.all().order_by('DesignationSection')
        
        # Créer les choix pour le combo section (uniquement les codes)
        choix_sections = [('', '-- Sélectionner une section --')]
        for section in sections:
            choix_sections.append((section.CodeSection, section.CodeSection))
        
        # Remplacer le champ par un Select avec les choix de codes uniquement
        self.fields['section'] = forms.ModelChoiceField(
            queryset=sections,
            required=False,
            empty_label="Toutes les sections",
            to_field_name='CodeSection',
            widget=forms.Select(attrs={'class': 'form-select', 'id': 'section_select'})
        )
        
        # Personnaliser l'affichage pour montrer uniquement les codes
        self.fields['section'].label_from_instance = lambda obj: obj.CodeSection
        
        # Ajouter des classes pour le style
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'Select', 'NumberInput', 'TimeInput']:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
