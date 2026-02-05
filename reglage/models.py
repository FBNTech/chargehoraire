from django.db import models

class Section(models.Model):
    CodeSection = models.CharField(max_length=20, primary_key=True)
    DesignationSection = models.CharField(max_length=100)

    def __str__(self):
        return self.DesignationSection

class Departement(models.Model):
    CodeDept = models.CharField(max_length=20, primary_key=True)
    DesignationDept = models.CharField(max_length=100)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='departements')

    def __str__(self):
        return self.DesignationDept

class Mention(models.Model):
    CodeMention = models.CharField(max_length=20, primary_key=True)
    DesignationMention = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='mentions', null=True, blank=True)

    def __str__(self):
        return self.DesignationMention

class Niveau(models.Model):
    CodeNiveau = models.CharField(max_length=20, primary_key=True)
    DesignationNiveau = models.CharField(max_length=100)

    def __str__(self):
        return self.DesignationNiveau

class Classe(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE)
    mention = models.ForeignKey(Mention, on_delete=models.CASCADE)
    CodeClasse = models.CharField(max_length=40, unique=True, blank=True)
    DesignationClasse = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('niveau', 'mention')

    def save(self, *args, **kwargs):
        self.CodeClasse = f"{self.niveau.CodeNiveau}{self.mention.CodeMention}"
        self.DesignationClasse = f"{self.niveau.DesignationNiveau} {self.mention.DesignationMention}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.DesignationClasse

class Grade(models.Model):
    CodeGrade = models.CharField(max_length=10, primary_key=True)
    DesignationGrade = models.CharField(max_length=100)
    
    def __str__(self):
        return self.DesignationGrade

class CategorieEnseignant(models.Model):
    CodeCategorie = models.CharField(max_length=10, primary_key=True)
    DesignationCategorie = models.CharField(max_length=100)
    
    def __str__(self):
        return self.DesignationCategorie

class Semestre(models.Model):
    CodeSemestre = models.CharField(max_length=10, primary_key=True)
    DesignationSemestre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.DesignationSemestre

class Fonction(models.Model):
    CodeFonction = models.CharField(max_length=10, primary_key=True)
    DesignationFonction = models.CharField(max_length=100)
    
    def __str__(self):
        return self.DesignationFonction


class AnneeAcademique(models.Model):
    """Gestion des années académiques avec année en cours"""
    code = models.CharField(max_length=9, unique=True, help_text="Format: 2024-2025")
    designation = models.CharField(max_length=100, help_text="Ex: Année académique 2024-2025")
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    est_en_cours = models.BooleanField(default=False, help_text="Marquer comme année en cours")
    
    class Meta:
        verbose_name = "Année Académique"
        verbose_name_plural = "Années Académiques"
        ordering = ['-code']
    
    def save(self, *args, **kwargs):
        # Si cette année est marquée comme "en cours", désactiver les autres
        if self.est_en_cours:
            AnneeAcademique.objects.filter(est_en_cours=True).update(est_en_cours=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        statut = " (En cours)" if self.est_en_cours else ""
        return f"{self.code}{statut}"


class Salle(models.Model):
    """Gestion des salles de classe"""
    code = models.CharField(max_length=20, unique=True, help_text="Ex: B1, A205, AMPHI-A")
    designation = models.CharField(max_length=200, help_text="Ex: Salle B1 - Bâtiment Sciences")
    capacite = models.IntegerField(null=True, blank=True, help_text="Nombre de places")
    type_salle = models.CharField(
        max_length=20,
        choices=[
            ('TD', 'Salle de TD'),
            ('TP', 'Salle de TP'),
            ('AMPHI', 'Amphithéâtre'),
            ('LAB', 'Laboratoire'),
            ('AUTRE', 'Autre'),
        ],
        default='TD'
    )
    est_disponible = models.BooleanField(default=True, help_text="Salle disponible pour planification")
    remarques = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.designation}"


class Creneau(models.Model):
    """Gestion des créneaux horaires"""
    TYPE_CHOICES = [
        ('cours', 'Cours'),
        ('examen', 'Examen'),
        ('les_deux', 'Cours et Examens'),
    ]
    
    code = models.CharField(max_length=10, unique=True, help_text="Ex: AM, PM, S1, S2")
    designation = models.CharField(max_length=100, help_text="Ex: Matinée, Après-midi")
    type_creneau = models.CharField(max_length=10, choices=TYPE_CHOICES, default='les_deux', 
                                   help_text="Type d'horaire où ce créneau apparaît")
    section = models.ForeignKey('Section', on_delete=models.CASCADE, null=True, blank=True,
                               help_text="Section pour les créneaux d'examens (laisser vide pour les cours généraux)")
    heure_debut = models.TimeField(help_text="Heure de début (ex: 08:00)")
    heure_fin = models.TimeField(help_text="Heure de fin (ex: 12:00)")
    est_actif = models.BooleanField(default=True, help_text="Créneau actif pour planification")
    ordre = models.IntegerField(default=0, help_text="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Créneau"
        verbose_name_plural = "Créneaux"
        ordering = ['ordre', 'heure_debut']
    
    def __str__(self):
        return f"{self.designation} ({self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')})"
    
    def get_format_court(self):
        """Format court pour affichage dans les horaires"""
        return f"{self.heure_debut.strftime('%Hh%M')}-{self.heure_fin.strftime('%Hh%M')}"


class SemaineCours(models.Model):
    """Gestion des semaines de cours avec période et statut en cours"""
    numero_semaine = models.IntegerField(help_text="Numéro de la semaine (1, 2, 3...)")
    date_debut = models.DateField(help_text="Date de début de la semaine (doit être un LUNDI)")
    date_fin = models.DateField(help_text="Date de fin de la semaine (doit être un SAMEDI)")
    designation = models.CharField(max_length=200, help_text="Ex: Semaine 1 du 1er semestre")
    est_en_cours = models.BooleanField(default=False, help_text="Marquer comme semaine en cours")
    annee_academique = models.CharField(max_length=9, null=True, blank=True, help_text="Année académique (ex: 2024-2025)")
    remarques = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Semaine de Cours"
        verbose_name_plural = "Semaines de Cours"
        ordering = ['date_debut']
        unique_together = [('numero_semaine', 'annee_academique')]
    
    def clean(self):
        """Validation : date_debut doit être un lundi et date_fin un samedi"""
        from django.core.exceptions import ValidationError
        
        # Vérifier que date_debut est un lundi (weekday() = 0)
        if self.date_debut and self.date_debut.weekday() != 0:
            jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][self.date_debut.weekday()]
            raise ValidationError({
                'date_debut': f"La date de début doit être un LUNDI. Vous avez sélectionné un {jour} ({self.date_debut.strftime('%d/%m/%Y')})."
            })
        
        # Vérifier que date_fin est un samedi (weekday() = 5)
        if self.date_fin and self.date_fin.weekday() != 5:
            jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][self.date_fin.weekday()]
            raise ValidationError({
                'date_fin': f"La date de fin doit être un SAMEDI. Vous avez sélectionné un {jour} ({self.date_fin.strftime('%d/%m/%Y')})."
            })
        
        # Vérifier que date_fin > date_debut
        if self.date_debut and self.date_fin and self.date_fin <= self.date_debut:
            raise ValidationError({
                'date_fin': "La date de fin doit être postérieure à la date de début."
            })
    
    def save(self, *args, **kwargs):
        # Valider avant de sauvegarder
        self.clean()
        
        # Générer automatiquement la désignation si non fournie
        if not self.designation:
            self.designation = f"Semaine {self.numero_semaine}"
            if self.annee_academique:
                self.designation += f" - {self.annee_academique}"
        
        # Si cette semaine est marquée comme "en cours", désactiver les autres
        if self.est_en_cours:
            SemaineCours.objects.filter(est_en_cours=True).update(est_en_cours=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def update_statut_automatique(cls):
        """
        Met à jour automatiquement le statut 'en cours' des semaines
        en fonction de la date actuelle.
        La semaine en cours est celle où date_debut <= aujourd'hui <= date_fin
        """
        from datetime import date
        aujourd_hui = date.today()
        
        # Désactiver toutes les semaines
        cls.objects.filter(est_en_cours=True).update(est_en_cours=False)
        
        # Trouver et activer la semaine en cours
        semaine_actuelle = cls.objects.filter(
            date_debut__lte=aujourd_hui,
            date_fin__gte=aujourd_hui
        ).first()
        
        if semaine_actuelle:
            semaine_actuelle.est_en_cours = True
            # Utiliser update pour éviter de déclencher save() et la boucle infinie
            cls.objects.filter(pk=semaine_actuelle.pk).update(est_en_cours=True)
            return semaine_actuelle
        
        return None
    
    def __str__(self):
        statut = " (En cours)" if self.est_en_cours else ""
        return f"Semaine {self.numero_semaine} : {self.date_debut.strftime('%d/%m')} - {self.date_fin.strftime('%d/%m')}{statut}"
    
    def get_periode(self):
        """Retourne la période formatée"""
        return f"{self.date_debut.strftime('%d/%m/%Y')} - {self.date_fin.strftime('%d/%m/%Y')}"
    
    def get_jour_debut(self):
        """Retourne le jour de la semaine de date_debut"""
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return jours[self.date_debut.weekday()]
    
    def get_jour_fin(self):
        """Retourne le jour de la semaine de date_fin"""
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return jours[self.date_fin.weekday()]

class TypeCharge(models.Model):
    """Modèle pour gérer les types de charge"""
    code_type_charge = models.CharField(max_length=50, unique=True, verbose_name="Code du type de charge")
    designation_type_charge = models.CharField(max_length=100, verbose_name="Désignation du type de charge")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Type de charge"
        verbose_name_plural = "Types de charge"
        ordering = ['code_type_charge']
    
    def __str__(self):
        return f"{self.code_type_charge} - {self.designation_type_charge}"

class Taux(models.Model):
    """Modèle pour gérer les taux horaires par grade"""
    grade = models.CharField(max_length=100, unique=True, verbose_name="Grade")
    montant_par_heure = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant par heure ($)")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Taux horaire"
        verbose_name_plural = "Taux horaires"
        ordering = ['grade']
    
    def __str__(self):
        return f"{self.grade} - ${self.montant_par_heure}/h"
