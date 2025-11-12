from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import UserProfile, Role
from django.utils.translation import gettext_lazy as _
from teachers.models import Teacher

class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription des utilisateurs"""
    email = forms.EmailField(required=True, label=_('Email'))
    first_name = forms.CharField(required=True, label=_('Prénom'))
    last_name = forms.CharField(required=True, label=_('Nom'))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Formulaire pour le profil utilisateur"""
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'address', 'profile_picture', 'section')
        labels = {
            'phone_number': _('Numéro de téléphone'),
            'address': _('Adresse'),
            'profile_picture': _('Photo de profil'),
        }
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class StudentProfileForm(forms.ModelForm):
    """Formulaire spécifique pour les étudiants"""
    class Meta:
        model = UserProfile
        fields = ('matricule_etudiant', 'classe')
        labels = {
            'matricule_etudiant': _('Matricule'),
            'classe': _('Classe'),
        }

class TeacherProfileForm(forms.ModelForm):
    """Formulaire spécifique pour les enseignants"""
    class Meta:
        model = UserProfile
        fields = ('matricule_enseignant', 'departement', 'grade')
        labels = {
            'matricule_enseignant': _('Matricule'),
            'departement': _('Département'),
            'grade': _('Grade'),
        }

class UserRoleForm(forms.ModelForm):
    """Formulaire pour la gestion des rôles"""
    roles = forms.ModelChoiceField(
        queryset=Role.objects.filter(name__in=['admin', 'gestionnaire', 'agent']),
        widget=forms.RadioSelect,
        required=True,
        empty_label=None,
        label=_('Rôle')
    )
    
    class Meta:
        model = UserProfile
        fields = ('roles', 'section')
        labels = {
            'section': _('Section (si applicable)')
        }
        help_texts = {
            'section': _('Renseignez si nécessaire.')
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].widget.attrs.update({
            'placeholder': 'Code de la section (ex: INFO, GESTION)',
            'class': 'form-control'
        })

class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé pour le changement de mot de passe"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomPasswordResetForm(PasswordResetForm):
    """Formulaire personnalisé pour la réinitialisation du mot de passe"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

class CustomSetPasswordForm(SetPasswordForm):
    """Formulaire personnalisé pour définir un nouveau mot de passe"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class TeacherUserCreationForm(UserCreationForm):
    """Formulaire pour créer un utilisateur à partir d'un enseignant existant.
    Le rôle sera automatiquement assigné en fonction de la fonction de l'enseignant.
    """
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        label=_('Enseignant'),
        required=True,
        help_text=_('Sélectionnez un enseignant existant pour créer un compte utilisateur. '
                  'Les privilèges seront automatiquement assignés selon sa fonction.')
    )
    
    class Meta:
        model = User
        fields = ('teacher', 'username', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser l'affichage du champ de sélection d'enseignant
        self.fields['teacher'].widget.attrs.update({
            'class': 'form-control select2',
            'data-placeholder': 'Sélectionnez un enseignant...'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        teacher = self.cleaned_data['teacher']
        
        # Définir les informations utilisateur à partir de l'enseignant
        user.first_name = teacher.prenom if hasattr(teacher, 'prenom') else teacher.nom_complet.split(' ')[0]
        user.last_name = teacher.nom if hasattr(teacher, 'nom') else ' '.join(teacher.nom_complet.split(' ')[1:])
        user.email = teacher.email if hasattr(teacher, 'email') and teacher.email else f"{user.username}@example.com"
        
        if commit:
            user.save()
            
            # Créer le profil avec les informations de l'enseignant
            profile = user.profile
            profile.matricule_enseignant = teacher.matricule
            profile.departement = teacher.departement
            profile.grade = teacher.grade
            profile.save()
            
        return user
