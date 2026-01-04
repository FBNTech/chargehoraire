from django.db import models
from teachers.models import Teacher
from courses.models import Course
from django.utils import timezone

# Create your models here.

class Attribution(models.Model):
    organisation = models.ForeignKey('accounts.Organisation', on_delete=models.CASCADE, related_name='attributions', verbose_name='Organisation', null=True, blank=True)
    TYPE_CHARGE_CHOICES = [
        ('Reguliere', 'Régulière'),
        ('Supplementaire', 'Supplémentaire'),
    ]
    
    matricule = models.ForeignKey(Teacher, on_delete=models.CASCADE, to_field='matricule', verbose_name="Matricule enseignant", null=True)
    code_ue = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Code UE", null=True, related_name='attributions')
    annee_academique = models.CharField(max_length=9, verbose_name="Année académique", default="2024-2025", null=True)
    type_charge = models.CharField(max_length=15, choices=TYPE_CHARGE_CHOICES, verbose_name="Type de charge", null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Attribution"
        verbose_name_plural = "Attributions"
        unique_together = [['matricule', 'code_ue', 'annee_academique']]

    def __str__(self):
        return f"{self.code_ue.classe} | {self.code_ue.code_ue} - {self.code_ue.intitule_ue} ({self.matricule.grade} {self.matricule.nom_complet}) - {self.annee_academique}"

class Cours_Attribution(models.Model):
    organisation = models.ForeignKey('accounts.Organisation', on_delete=models.CASCADE, related_name='cours_attributions', verbose_name='Organisation', null=True, blank=True)
    CLASSE_CHOICES = [
        ('L1', 'L1'),
        ('L2', 'L2'),
        ('L3', 'L3'),
        ('M1', 'M1'),
        ('M2', 'M2'),
    ]
    
    SEMESTRE_CHOICES = [
        ('S1', 'S1'),
        ('S2', 'S2'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('Informatique', 'Informatique'),
        ('Physique', 'Physique'),
        ('Chimie', 'Chimie'),
        ('Biologie', 'Biologie'),
        ('SCAD', 'SCAD'),
        ('Histoire', 'Histoire'),
        ('Anglais', 'Anglais'),
    ]
    
    code_ue = models.CharField(max_length=20)
    intitule_ue = models.CharField(max_length=255)
    intitule_ec = models.CharField(max_length=255)
    credit = models.IntegerField()
    cmi = models.FloatField()
    td_tp = models.FloatField()
    classe = models.CharField(max_length=50)
    semestre = models.CharField(max_length=20)
    departement = models.CharField(max_length=50)
    section = models.CharField(max_length=100, blank=True, null=True, verbose_name="Section")

    def __str__(self):
        return f"{self.code_ue} - {self.intitule_ue}"

    class Meta:
        verbose_name = 'Cours Attribution'
        verbose_name_plural = 'Cours Attributions'

 

class ScheduleEntry(models.Model):
    organisation = models.ForeignKey('accounts.Organisation', on_delete=models.CASCADE, related_name='schedule_entries', verbose_name='Organisation', null=True, blank=True)
    
    TYPE_HORAIRE_CHOICES = [
        ('cours', 'Cours'),
        ('examen', 'Examen'),
    ]
    
    DAYS = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
    ]

    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE, related_name='schedule_entries')
    type_horaire = models.CharField(max_length=10, choices=TYPE_HORAIRE_CHOICES, default='cours', 
                                   help_text="Type d'horaire : cours ou examen")
    annee_academique = models.CharField(max_length=9)
    semaine_debut = models.DateField(null=True, blank=True, help_text="Date de début de la plage de dates")
    date_fin = models.DateField(null=True, blank=True, help_text="Date de fin de la plage de dates (inclusive)")
    numero_semaine = models.IntegerField(null=True, blank=True, help_text="Numéro de la semaine de cours")
    date_cours = models.DateField(null=True, blank=True, help_text="Date exacte du cours (pour compatibilité)")
    jour = models.CharField(max_length=10, choices=DAYS)
    creneau = models.ForeignKey('reglage.Creneau', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créneau horaire")
    salle = models.CharField(max_length=50, null=True, blank=True, verbose_name="Salle (ancien)")
    salle_link = models.ForeignKey('reglage.Salle', on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='schedule_entries', verbose_name="Salle")
    remarques = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = [('attribution', 'annee_academique', 'semaine_debut', 'jour', 'creneau')]

    def __str__(self):
        return f"{self.attribution} {self.jour}-{self.creneau}"
    
    def get_creneau_display_complet(self):
        """Retourne l'affichage des heures du créneau"""
        if self.creneau:
            return self.creneau.get_format_court()
        return "Non défini"
