from django import forms
from teachers.models import Teacher
from .models import AutorisationAbsenceEnseignant, Etudiant, AutorisationAbsenceEtudiant
from reglage.models import Classe


class AutorisationAbsenceEnseignantForm(forms.ModelForm):
    """Formulaire de saisie pour l'autorisation d'absence enseignant (ModelForm)"""
    class Meta:
        model = AutorisationAbsenceEnseignant
        fields = [
            'teacher',
            'periode_debut',
            'periode_fin',
            'motif',
            'destination',
            'disposition_cours',
            'disposition_stage',
        ]
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Sélectionnez un enseignant'}),
            'periode_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periode_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Motif de l\'absence'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Destination'}),
            'disposition_cours': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Disposition prise pour l\'occupation des étudiants'}),
            'disposition_stage': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Disposition prise pour les stages'}),
        }
        labels = {
            'teacher': "",
            'periode_debut': "Début de période",
            'periode_fin': "Fin de période",
            'motif': "",
            'destination': "",
            'disposition_cours': "",
            'disposition_stage': "",
        }


class EtudiantForm(forms.ModelForm):
    classe = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remplir le combo avec les CodeClasse
        classes = Classe.objects.all()
        choices = [('', 'Sélectionnez une classe')]
        choices.extend([(classe.CodeClasse, classe.CodeClasse) for classe in classes])
        self.fields['classe'].choices = choices
    
    class Meta:
        model = Etudiant
        fields = [
            'matricule', 'nom_complet', 'date_naissance',
            'sexe', 'telephone', 'departement', 'classe', 
            'annee_academique'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricule de l\'étudiant'}),
            'nom_complet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'annee_academique': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Année académique (ex: 2023-2024)'}),
        }
        labels = {
            'matricule': '',
            'nom_complet': '',
            'date_naissance': 'Date de naissance',
            'sexe': 'Sexe',
            'telephone': '',
            'departement': 'Département',
            'classe': 'Classe',
            'annee_academique': '',
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('classe'):
            instance.classe = self.cleaned_data['classe']
        if commit:
            instance.save()
        return instance


class ImportExcelForm(forms.Form):
    fichier_excel = forms.FileField(
        label="Fichier Excel",
        help_text="Sélectionnez un fichier Excel (.xlsx, .xls) contenant les données des étudiants",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )


class AutorisationAbsenceEtudiantForm(forms.ModelForm):
    class Meta:
        model = AutorisationAbsenceEtudiant
        fields = ['etudiant', 'periode_debut', 'periode_fin', 'motif', 'destination', 'disposition_cours']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'periode_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periode_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Motif de l\'absence'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Destination (optionnel)'}),
            'disposition_cours': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Disposition prise pour les cours (optionnel)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from teachers.models import Teacher
        
        # Rendre certains champs optionnels
        self.fields['destination'].required = False
        self.fields['disposition_cours'].required = False
        
        # Récupérer tous les chefs de département
        dept_chiefs = Teacher.objects.filter(fonction='CD')
        if not dept_chiefs.exists():
            # Si aucun chef avec code 'CD', essayer d'autres codes possibles
            dept_chiefs = Teacher.objects.filter(fonction__icontains='CHEF')
        
        # Ajouter le champ de sélection de chef de département
        self.fields['chef_departement'] = forms.ModelChoiceField(
            queryset=dept_chiefs,
            label='Chef de Département (signature)',
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True
        )
