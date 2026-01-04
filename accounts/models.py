from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Organisation(models.Model):
    """Modèle pour l'isolation des données par organisation/compte"""
    nom = models.CharField(_('Nom de l\'organisation'), max_length=200, unique=True)
    code = models.CharField(_('Code'), max_length=50, unique=True, help_text="Code unique de l'organisation")
    description = models.TextField(_('Description'), blank=True, null=True)
    est_active = models.BooleanField(_('Active'), default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Organisation')
        verbose_name_plural = _('Organisations')
        ordering = ['nom']
    
    def __str__(self):
        return self.nom

class Role(models.Model):
    """Modèle pour les rôles utilisateurs"""
    ADMIN = 'admin'                # Accès complet
    GESTIONNAIRE = 'gestionnaire'  # Gestionnaire
    AGENT = 'agent'                # Agent
    
    # Groupes de rôles pour faciliter les vérifications
    ADMIN_ROLES = [ADMIN]  # Seul Administrateur est niveau admin
    SECTION_ROLES = []
    DEPT_ROLES = []
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrateur'),
        (GESTIONNAIRE, 'Gestionnaire'),
        (AGENT, 'Agent'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return dict(self.ROLE_CHOICES).get(self.name, self.name)

class UserProfile(models.Model):
    """Extension du modèle utilisateur Django standard"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='users', verbose_name=_('Organisation'), null=True, blank=True)
    phone_number = models.CharField(_('Numéro de téléphone'), max_length=20, blank=True, null=True)
    address = models.TextField(_('Adresse'), blank=True, null=True)
    profile_picture = models.ImageField(_('Photo de profil'), upload_to='profile_pictures/', blank=True, null=True)
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    
    # Champs spécifiques pour les étudiants
    matricule_etudiant = models.CharField(_('Matricule étudiant'), max_length=50, blank=True, null=True)
    classe = models.CharField(_('Classe'), max_length=100, blank=True, null=True)
    
    # Champs spécifiques pour les enseignants
    matricule_enseignant = models.CharField(_('Matricule enseignant'), max_length=50, blank=True, null=True)
    departement = models.CharField(_('Département'), max_length=100, blank=True, null=True)
    grade = models.CharField(_('Grade'), max_length=100, blank=True, null=True)
    section = models.CharField(_('Section'), max_length=100, blank=True, null=True)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateurs')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def is_admin(self):
        return self.roles.filter(name=Role.ADMIN).exists()
    
    @property
    def is_administrative_role(self):
        """Vérifie si l'utilisateur a un rôle administratif (DG, SGAC, SGR, SGAD, AB)"""
        return self.roles.filter(name__in=Role.ADMIN_ROLES).exists()
        
    @property
    def is_section_role(self):
        """Vérifie si l'utilisateur est chef de section (CS, CSAE, CSR, SAAS)"""
        return self.roles.filter(name__in=Role.SECTION_ROLES).exists()
    
    @property
    def is_department_role(self):
        """Vérifie si l'utilisateur est chef de département ou secrétaire (CD, SD)"""
        return self.roles.filter(name__in=Role.DEPT_ROLES).exists()
    
    @property
    def is_enseignant(self):
        """Vérifie si l'utilisateur est un enseignant ordinaire"""
        return False
    
    @property
    def is_etudiant(self):
        """Vérifie si l'utilisateur est un étudiant"""
        return False
    
    @property
    def is_personnel_admin(self):
        """Vérifie si l'utilisateur est un personnel administratif"""
        return False
        
    def has_role_based_on_function(self, fonction):
        """Détermine le rôle approprié en fonction de la fonction de l'enseignant"""
        fonction = fonction.upper() if fonction else ''
        
        # Rôles administratifs (peuvent tout voir et tout faire, comme les administrateurs)
        if fonction in []:
            return 'administrative'
            
        # Rôles de chef de section (accès limité à leur section et départements d'attache)
        elif fonction in []:
            return 'section'
            
        # Rôles de chef de département (accès limité à leur département)
        elif fonction in []:
            return 'department'
            
        # Rôle enseignant (accès très limité)
        elif fonction in []:
            return 'enseignant'
            
        # Par défaut
        return None
        
    def can_access_section(self, section_code):
        """Vérifie si l'utilisateur peut accéder à une section spécifique"""
        if not section_code:
            return False
            
        # Les admins et rôles administratifs peuvent accéder à toutes les sections
        if self.is_admin or self.is_administrative_role:
            return True
            
        # Les chefs de section ne peuvent accéder qu'à leur propre section
        if self.is_section_role:
            return self.section and self.section.lower() == section_code.lower()
            
        # Par défaut, pas d'accès
        return False
        
    def can_access_department(self, department_code):
        """Vérifie si l'utilisateur peut accéder à un département spécifique"""
        if not department_code:
            return False
            
        # Les admins et rôles administratifs peuvent accéder à tous les départements
        if self.is_admin or self.is_administrative_role:
            return True
            
        # Les chefs de section peuvent accéder aux départements de leur section
        if self.is_section_role:
            # Note: Cette logique est simplifiée. En production, il faudrait vérifier
            # si le département appartient à la section de l'utilisateur
            return True
            
        # Les chefs de département ne peuvent accéder qu'à leur propre département
        if self.is_department_role:
            return self.departement and self.departement.lower() == department_code.lower()
            
        # Les enseignants ne peuvent voir que leur propre département
        if self.is_enseignant:
            return self.departement and self.departement.lower() == department_code.lower()
            
        # Par défaut, pas d'accès
        return False

# Signal pour créer automatiquement un profil utilisateur lorsqu'un utilisateur est créé
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Signal pour sauvegarder le profil utilisateur lorsque l'utilisateur est sauvegardé
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
