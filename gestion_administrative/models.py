from django.db import models
from django.utils import timezone
from teachers.models import Teacher


class AutorisationAbsenceEnseignant(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='autorisations_absence')
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    motif = models.TextField()
    destination = models.CharField(max_length=255)
    disposition_cours = models.TextField(blank=True)
    disposition_stage = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Autorisation d'absence - {self.teacher.nom_complet} du {self.periode_debut} au {self.periode_fin}"


class AbsenceEnseignant(models.Model):
    MatriculeEnseignant = models.CharField(max_length=20)
    dateDebut = models.DateField()
    dateFin = models.DateField()
    Destination = models.CharField(max_length=255)
    Motif = models.TextField()
    Date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-Date']

    def __str__(self):
        return f"Absence {self.MatriculeEnseignant} du {self.dateDebut} au {self.dateFin}"


class Etudiant(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    matricule = models.CharField(max_length=20, unique=True, verbose_name="Matricule")
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True, null=True, verbose_name="Sexe")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    departement = models.ForeignKey('reglage.Departement', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Département")
    classe = models.CharField(max_length=40, blank=True, null=True, verbose_name="Classe")
    annee_academique = models.CharField(max_length=20, blank=True, null=True, verbose_name="Année académique")
    
    # Champs de suivi
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['nom_complet']
    
    def __str__(self):
        return f"{self.matricule} - {self.nom_complet}"


class AutorisationAbsenceEtudiant(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Étudiant")
    periode_debut = models.DateField(verbose_name="Début de période")
    periode_fin = models.DateField(verbose_name="Fin de période")
    motif = models.TextField(verbose_name="Motif de l'absence")
    destination = models.CharField(max_length=200, blank=True, null=True, verbose_name="Destination")
    disposition_cours = models.TextField(blank=True, null=True, verbose_name="Disposition prise pour les cours")
    chef_departement = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True, 
                                     related_name='autorisations_absence_etudiant', verbose_name="Chef de Département")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Autorisation d'absence étudiant"
        verbose_name_plural = "Autorisations d'absence étudiants"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Absence {self.etudiant.matricule} du {self.periode_debut} au {self.periode_fin}"


class Annonce(models.Model):
    TYPE_CHOICES = [
        ('annonce', 'Annonce'),
        ('communique', 'Communiqué'),
        ('evenement', 'Événement'),
        ('information', 'Information'),
    ]
    
    CIBLE_CHOICES = [
        ('tous', 'Tous les utilisateurs'),
        ('enseignants', 'Enseignants seulement'),
        ('etudiants', 'Étudiants seulement'),
        ('administratif', 'Personnel administratif'),
    ]
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    contenu = models.TextField(verbose_name="Contenu")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='information', verbose_name="Type")
    cible = models.CharField(max_length=20, choices=CIBLE_CHOICES, default='tous', verbose_name="Destiné à")
    date_publication = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    date_expiration = models.DateTimeField(blank=True, null=True, verbose_name="Date d'expiration")
    publie_par = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True, related_name='annonces_publiees', verbose_name="Publié par")
    publie = models.BooleanField(default=True, verbose_name="Publié")
    important = models.BooleanField(default=False, verbose_name="Important")
    piece_jointe = models.FileField(upload_to='annonces/', blank=True, null=True, verbose_name="Pièce jointe")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Annonce/Communiqué"
        verbose_name_plural = "Annonces et Communiqués"
        ordering = ['-important', '-date_publication']
    
    def __str__(self):
        return self.titre
    
    @property
    def est_expire(self):
        if self.date_expiration:
            return timezone.now() > self.date_expiration
        return False
