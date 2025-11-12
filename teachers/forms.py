from django import forms
from .models import Teacher
from reglage.models import Fonction, Grade, CategorieEnseignant, Departement

class TeacherForm(forms.ModelForm):    
    class Meta:
        model = Teacher
        fields = ['photo', 'matricule', 'nom_complet', 'fonction', 'grade', 'categorie', 'departement', 'section']
        labels = {
            'photo': '',
            'matricule': '',
            'nom_complet': '',
            'fonction': '',
            'grade': '',
            'categorie': '',
            'departement': '',
            'section': ''
        }
        widgets = {
            'matricule': forms.TextInput(attrs={'placeholder': 'Matricule', 'class': 'form-control'}),
            'nom_complet': forms.TextInput(attrs={'placeholder': 'Nom complet', 'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'fonction': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionner une fonction'
            }),
            'grade': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionner un grade'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionner une catégorie'
            }),
            'departement': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionner un département'
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Section (automatique)',
                'readonly': 'readonly',
                'style': 'background-color: #e9ecef; cursor: not-allowed;'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        
        # Ajouter des classes Bootstrap aux champs
        for field_name, field in self.fields.items():
            if field_name != 'photo':
                if isinstance(field.widget, forms.TextInput):
                    field.widget.attrs.update({
                        'class': 'form-control'
                    })
        
        # Méthode drastique pour éliminer les doublons dans les listes déroulantes
        # Réinitialiser complètement les choix des champs de sélection avec des ensembles pour garantir l'unicité
        
        # Fonctions - Utilisation d'un set pour garantir l'unicité absolue
        unique_fonctions = set()
        fonction_choices = [('', 'Sélectionner une fonction')]
        for f in Fonction.objects.all().order_by('DesignationFonction'):
            if f.CodeFonction and f.CodeFonction not in unique_fonctions:
                fonction_choices.append((f.CodeFonction, f.DesignationFonction))
                unique_fonctions.add(f.CodeFonction)
        self.fields['fonction'].choices = fonction_choices
        
        # Grades - Même principe
        unique_grades = set()
        grade_choices = [('', 'Sélectionner un grade')]
        for g in Grade.objects.all().order_by('DesignationGrade'):
            if g.CodeGrade and g.CodeGrade not in unique_grades:
                grade_choices.append((g.CodeGrade, g.DesignationGrade))
                unique_grades.add(g.CodeGrade)
        self.fields['grade'].choices = grade_choices
        
        # Catégories - Même principe
        unique_categories = set()
        categorie_choices = [('', 'Sélectionner une catégorie')]
        for c in CategorieEnseignant.objects.all().order_by('DesignationCategorie'):
            if c.CodeCategorie and c.CodeCategorie not in unique_categories:
                categorie_choices.append((c.CodeCategorie, c.DesignationCategorie))
                unique_categories.add(c.CodeCategorie)
        self.fields['categorie'].choices = categorie_choices
        
        # Départements - Même principe
        unique_departements = set()
        departement_choices = [('', 'Sélectionner un département')]
        
        for d in Departement.objects.all().order_by('DesignationDept'):
            if d.CodeDept and d.CodeDept not in unique_departements:
                departement_choices.append((d.CodeDept, d.DesignationDept))
                unique_departements.add(d.CodeDept)
                    
        self.fields['departement'].choices = departement_choices
        
        # Afficher un décompte des options dans chaque liste (pour débogage)
        print(f"Nombre d'options - Fonction: {len(fonction_choices)-1}, Grade: {len(grade_choices)-1}, Catégorie: {len(categorie_choices)-1}, Département: {len(departement_choices)-1}")
        
        # Si nous sommes en mode édition, sélectionner les valeurs actuelles
        if instance:
            for field_name in ['fonction', 'grade', 'categorie', 'departement']:
                self.initial[field_name] = getattr(instance, field_name, '')
            
            if instance.section:
                self.initial['section'] = instance.section
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Récupérer automatiquement la section du département
        departement_code = self.cleaned_data.get('departement')
        if departement_code:
            try:
                dept = Departement.objects.get(CodeDept=departement_code)
                instance.section = dept.section.CodeSection
            except Departement.DoesNotExist:
                instance.section = None
        else:
            instance.section = None
        
        if commit:
            instance.save()
        
        return instance
