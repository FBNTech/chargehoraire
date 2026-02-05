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


class PaiementHeuresSupplementaires(models.Model):
    """Modèle pour suivre les paiements des heures supplémentaires"""
    organisation = models.ForeignKey('accounts.Organisation', on_delete=models.CASCADE, related_name='paiements_heures_sup', verbose_name='Organisation', null=True, blank=True)
    
    STATUT_PAIEMENT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('PAYE', 'Payé'),
        ('ANNULE', 'Annulé'),
    ]
    
    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE, related_name='paiements', verbose_name="Attribution")
    enseignant = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='paiements_heures_sup', verbose_name="Enseignant")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant à payer")
    taux_horaire = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Taux horaire")
    nombre_heures = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Nombre d'heures")
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='EN_ATTENTE', verbose_name="Statut du paiement")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    reference_paiement = models.CharField(max_length=100, null=True, blank=True, verbose_name="Référence de paiement")
    notes = models.TextField(null=True, blank=True, verbose_name="Notes")
    cree_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='paiements_crees', verbose_name="Créé par")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Paiement heures supplémentaires"
        verbose_name_plural = "Paiements heures supplémentaires"
        ordering = ['-date_creation']
        unique_together = [['attribution', 'enseignant', 'date_creation']]
    
    def __str__(self):
        return f"Paiement {self.enseignant.nom_complet} - {self.attribution.code_ue.code_ue} ({self.montant} FCFA)"
    
    def calculer_montant(self):
        """Calcule le montant automatiquement basé sur le taux horaire et le nombre d'heures"""
        if self.taux_horaire and self.nombre_heures:
            self.montant = self.taux_horaire * self.nombre_heures
            self.save()
        return self.montant
