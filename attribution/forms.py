from django import forms
from .models import Attribution, Course, ScheduleEntry
from teachers.models import Teacher
from reglage.models import AnneeAcademique, Salle, Creneau, SemaineCours
from datetime import datetime

class AttributionForm(forms.ModelForm):
    class Meta:
        model = Attribution
        fields = ['matricule', 'code_ue', 'annee_academique', 'type_charge']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['matricule'].queryset = Teacher.objects.all().order_by('matricule')
        self.fields['code_ue'].queryset = Course.objects.all().order_by('code_ue')
        
        # Personnalisation des widgets
        self.fields['matricule'].widget.attrs.update({'class': 'form-control'})
        self.fields['code_ue'].widget.attrs.update({'class': 'form-control'})
        self.fields['annee_academique'].widget.attrs.update({'class': 'form-control'})
        self.fields['type_charge'].widget.attrs.update({'class': 'form-control'})


class ScheduleEntryForm(forms.ModelForm):
    # Champs personnalisés pour utiliser les modèles de réglage
    annee_academique_select = forms.ModelChoiceField(
        queryset=AnneeAcademique.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Année académique',
        help_text='Sélectionner depuis les années enregistrées'
    )
    
    semaine_select = forms.ModelChoiceField(
        queryset=SemaineCours.objects.all().order_by('numero_semaine'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Semaine de cours',
        help_text='Sélectionner la semaine'
    )
    
    # Champ pour la date de début
    date_debut = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Date de début'
        }),
        label='Date de début',
    )
    
    # Champ pour la date de fin de la plage
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date',
            'placeholder': 'Date de fin (optionnel)'
        }),
        label='Date de fin',
    )
    
    # Champ pour la sélection du créneau
    creneau_select = forms.ModelChoiceField(
        queryset=Creneau.objects.filter(est_actif=True).order_by('heure_debut'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Créneau horaire',
        help_text='Sélectionner un créneau horaire. Laissez vide pour un cours ponctuel'
    )
    
    # Champ pour la sélection de la salle
    salle_select = forms.ModelChoiceField(
        queryset=Salle.objects.filter(est_disponible=True).order_by('code'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Salle',
        help_text='Sélectionner une salle disponible'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer les données pour les listes déroulantes
        from reglage.models import SemaineCours, Creneau, Salle
        
        # Champ pour la sélection de la semaine
        self.fields['semaine_select'] = forms.ModelChoiceField(
            queryset=SemaineCours.objects.all().order_by('-date_debut'),
            label='Semaine de cours',
            widget=forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_semaine_select'
            }),
            required=False
        )
        
        # Configuration du champ date_fin
        self.fields['date_fin'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Date de fin (optionnel)'
        })
        
        # Configuration du champ date_cours (caché)
        self.fields['date_cours'].widget = forms.HiddenInput()
        
        # Configuration du champ année académique
        self.fields['annee_academique'].widget = forms.HiddenInput()
        
        # Configuration du champ remarques
        self.fields['remarques'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Remarques optionnelles',
            'maxlength': '500'
        })
    
    class Meta:
        model = ScheduleEntry
        fields = [
            'attribution', 'annee_academique', 'semaine_debut', 
            'date_fin', 'date_cours', 'creneau', 'salle', 'remarques'
        ]
        
        widgets = {
            'attribution': forms.Select(attrs={'class': 'form-select'}),
            'annee_academique': forms.HiddenInput(),
            'semaine_debut': forms.HiddenInput(),
            'creneau': forms.Select(attrs={'class': 'form-select'}),
            'salle': forms.Select(attrs={'class': 'form-select'}),
            'date_cours': forms.HiddenInput(),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Date de fin (optionnel)'
            }),
            'remarques': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Remarques optionnelles',
                'maxlength': '500'
            }),
        }
        labels = {
            'attribution': 'Cours (UE + Enseignant)',
            'annee_academique': 'Année académique (saisie manuelle)',
            'semaine_debut': 'Semaine (date de début)',
            'date_cours': 'Date du cours',
            'creneau': 'Créneau (code)',
            'salle': 'Salle (saisie manuelle)',
            'remarques': 'Remarques',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre les champs du modèle non requis car nous utilisons les champs personnalisés
        self.fields['annee_academique'].required = False
        self.fields['creneau'].required = False
        self.fields['semaine_debut'].required = True  # Maintenant requis pour la plage de dates
        self.fields['date_cours'].required = False
        
        # Définir la date minimale pour les champs de date (aujourd'hui par défaut)
        today = datetime.now().date()
        self.fields['semaine_debut'].widget.attrs['min'] = today
        self.fields['date_fin'].widget.attrs['min'] = today
        self.fields['date_cours'].widget.attrs['min'] = today
        
        # Personnaliser l'affichage des attributions avec intitulés UE/EC concis
        self.fields['attribution'].queryset = Attribution.objects.select_related(
            'matricule', 'code_ue'
        ).order_by('code_ue__code_ue', 'code_ue__classe')
        
        # Rendre le champ d'attribution désactivé par défaut (sera activé après sélection de la classe)
        self.fields['attribution'].disabled = True
        self.fields['attribution'].widget.attrs['disabled'] = 'disabled'
        
        def format_ue_label(attribution):
            ue = attribution.code_ue
            # Raccourcir l'intitulé UE à 20 caractères max
            intitule_ue = (ue.intitule_ue[:17] + '...') if ue.intitule_ue and len(ue.intitule_ue) > 20 else (ue.intitule_ue or '')
            # Raccourcir l'intitulé EC à 15 caractères max si présent
            intitule_ec = ''
            if ue.intitule_ec:
                intitule_ec = ' | ' + ((ue.intitule_ec[:12] + '...') if len(ue.intitule_ec) > 15 else ue.intitule_ec)
            
            return f"{ue.code_ue} - {ue.classe} - {intitule_ue}{intitule_ec} - {attribution.matricule.nom_complet}"
        
        self.fields['attribution'].label_from_instance = format_ue_label
        
        # Pré-remplir avec l'année en cours si elle existe
        if not self.instance.pk:  # Nouveau formulaire
            annee_courante = AnneeAcademique.objects.filter(est_en_cours=True).first()
            if annee_courante:
                self.fields['annee_academique'].initial = annee_courante.code
                self.fields['annee_academique_select'].initial = annee_courante
            
            # Pré-remplir avec la semaine en cours
            semaine_courante = SemaineCours.objects.filter(est_en_cours=True).first()
            if semaine_courante:
                self.fields['semaine_select'].initial = semaine_courante
                self.fields['semaine_debut'].initial = semaine_courante.date_debut
        
        # Personnaliser l'affichage des semaines
        self.fields['semaine_select'].label_from_instance = lambda obj: (
            f"S{obj.numero_semaine} : {obj.date_debut.strftime('%d/%m')} - {obj.date_fin.strftime('%d/%m')}"
            f"{' ★' if obj.est_en_cours else ''}"
        )
        
        # Personnaliser l'affichage des créneaux avec placeholder
        self.fields['creneau_select'].label_from_instance = lambda obj: (
            f"{obj.designation} ({obj.get_format_court()})"
        )
        # Placeholder créneau
        premier_creneau = Creneau.objects.filter(est_actif=True).first()
        if premier_creneau:
            self.fields['creneau_select'].empty_label = f"{premier_creneau.designation} ({premier_creneau.get_format_court()})"
        
        # Personnaliser l'affichage des salles avec placeholder
        premiere_salle = Salle.objects.filter(est_disponible=True).first()
        if premiere_salle:
            if premiere_salle.capacite:
                self.fields['salle_select'].empty_label = f"{premiere_salle.code} - {premiere_salle.designation} ({premiere_salle.capacite} places)"
            else:
                self.fields['salle_select'].empty_label = f"{premiere_salle.code} - {premiere_salle.designation}"
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Si année sélectionnée depuis le combo, utiliser son code
        annee_select = cleaned_data.get('annee_academique_select')
        if annee_select:
            cleaned_data['annee_academique'] = annee_select.code
        
        # Si semaine sélectionnée depuis le combo, utiliser sa date_debut
        semaine_select = cleaned_data.get('semaine_select')
        if semaine_select:
            cleaned_data['semaine_debut'] = semaine_select.date_debut
        
        # Si date_cours fournie, calculer automatiquement le jour
        date_cours = cleaned_data.get('date_cours')
        if date_cours:
            # Mapper weekday() vers les noms de jours
            jours_map = {
                0: 'lundi',
                1: 'mardi',
                2: 'mercredi',
                3: 'jeudi',
                4: 'vendredi',
                5: 'samedi',
                6: 'dimanche'
            }
            cleaned_data['jour'] = jours_map[date_cours.weekday()]
        
        # Si salle sélectionnée depuis le combo, utiliser son code
        salle_select = cleaned_data.get('salle_select')
        if salle_select:
            cleaned_data['salle'] = salle_select.code
        
        # Si créneau sélectionné depuis le combo, utiliser son code
        creneau_select = cleaned_data.get('creneau_select')
        if creneau_select:
            cleaned_data['creneau'] = creneau_select.code
        
        return cleaned_data
