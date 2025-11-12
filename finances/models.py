from django.db import models
from django.utils import timezone
from teachers.models import Teacher
from reglage.models import Departement

CATEGORY_CHOICES = [
    ('salaire', 'Salaire'),
    ('subvention', 'Subvention'),
    ('frais_scolarite', 'Frais de scolarité'),
    ('don', 'Don/Contribution'),
    ('autre', 'Autre'),
]

EXPENSE_CATEGORY_CHOICES = [
    ('fourniture', 'Fournitures scolaires'),
    ('materiel', 'Matériel informatique/Électronique'),
    ('maintenance', 'Maintenance et réparations'),
    ('salaire', 'Salaire et primes'),
    ('deplacement', 'Frais de déplacement'),
    ('service', 'Services externes'),
    ('autre', 'Autre'),
]

LOAN_STATUS_CHOICES = [
    ('en_cours', 'En cours'),
    ('rembourse', 'Remboursé'),
    ('retard', 'En retard'),
    ('annule', 'Annulé'),
]

REPORT_STATUS_CHOICES = [
    ('brouillon', 'Brouillon'),
    ('en_attente', 'En attente de signature'),
    ('signe', 'Signé'),
    ('publie', 'Publié'),
    ('archive', 'Archivé'),
]

class Income(models.Model):
    """Modèle pour les entrées d'argent"""
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    date = models.DateField(default=timezone.now, verbose_name="Date")
    categorie = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    source = models.CharField(max_length=100, verbose_name="Source")
    reference = models.CharField(max_length=50, blank=True, verbose_name="N° de référence") 
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Département")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    enregistre_par = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='incomes_created', verbose_name="Enregistré par")
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Revenu"
        verbose_name_plural = "Revenus"
    
    def __str__(self):
        return f"{self.montant} - {self.categorie} - {self.date}"

class Expense(models.Model):
    """Modèle pour les sorties d'argent"""
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    date = models.DateField(default=timezone.now, verbose_name="Date")
    categorie = models.CharField(max_length=50, choices=EXPENSE_CATEGORY_CHOICES, verbose_name="Catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    beneficiaire = models.CharField(max_length=100, verbose_name="Bénéficiaire")
    reference = models.CharField(max_length=50, blank=True, verbose_name="N° de référence/facture")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Département")
    justificatif = models.FileField(upload_to='finances/justificatifs/', null=True, blank=True, verbose_name="Justificatif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    enregistre_par = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='expenses_created', verbose_name="Enregistré par")
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
    
    def __str__(self):
        return f"{self.montant} - {self.categorie} - {self.date}"

class Loan(models.Model):
    """Modèle pour les prêts"""
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    date_emprunt = models.DateField(default=timezone.now, verbose_name="Date d'emprunt")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    emprunteur = models.CharField(max_length=100, verbose_name="Emprunteur")
    motif = models.TextField(verbose_name="Motif du prêt")
    statut = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='en_cours', verbose_name="Statut")
    date_remboursement = models.DateField(null=True, blank=True, verbose_name="Date de remboursement")
    montant_rembourse = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant remboursé")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Département")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    enregistre_par = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='loans_created', verbose_name="Enregistré par")
    
    class Meta:
        ordering = ['-date_emprunt']
        verbose_name = "Prêt"
        verbose_name_plural = "Prêts"
    
    def __str__(self):
        return f"{self.montant} - {self.emprunteur} - {self.statut}"
    
    @property
    def solde_restant(self):
        return self.montant - self.montant_rembourse

class FinancialReport(models.Model):
    """Modèle pour les rapports financiers"""
    titre = models.CharField(max_length=200, verbose_name="Titre du rapport")
    periode_debut = models.DateField(verbose_name="Période début")
    periode_fin = models.DateField(verbose_name="Période fin")
    description = models.TextField(blank=True, verbose_name="Description")
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, verbose_name="Département")
    chef_departement = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='financial_reports_signed', verbose_name="Chef de département")
    signature = models.ImageField(upload_to='finances/signatures/', null=True, blank=True, verbose_name="Signature")
    date_signature = models.DateTimeField(null=True, blank=True, verbose_name="Date de signature")
    rapport_pdf = models.FileField(upload_to='finances/rapports/', null=True, blank=True, verbose_name="Rapport PDF")
    statut = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='brouillon', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='financial_reports_created', verbose_name="Créé par")
    
    class Meta:
        ordering = ['-periode_fin']
        verbose_name = "Rapport financier"
        verbose_name_plural = "Rapports financiers"
    
    def __str__(self):
        return f"{self.titre} - {self.periode_debut} à {self.periode_fin}"

    def sign_report(self, chef_departement, signature_image=None):
        """Méthode pour signer le rapport"""
        self.chef_departement = chef_departement
        self.date_signature = timezone.now()
        if signature_image:
            self.signature = signature_image
        self.statut = 'signe'
        self.save()
