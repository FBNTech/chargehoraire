from django.db import models
from django.utils import timezone
from teachers.models import Teacher
from reglage.models import Departement

class BaseDocument(models.Model):
    """Modèle de base pour les documents"""
    titre = models.CharField(max_length=255, verbose_name="Libellé du document")
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    fichier = models.FileField(upload_to='documents/', blank=True, null=True, verbose_name="Fichier")
    categorie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Catégorie")
    mots_cles = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mots clés")
    note = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    class Meta:
        abstract = True

class DocumentEntrant(BaseDocument):
    """Modèle pour les documents entrants"""
    date_entree = models.DateField(default=timezone.now, verbose_name="Date d'entrée")
    expediteur = models.CharField(max_length=255, verbose_name="Expéditeur")
    destinataire = models.CharField(max_length=255, verbose_name="Destinataire")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_entrants', verbose_name="Département")
    date_reception = models.DateField(default=timezone.now, verbose_name="Date de réception")
    statut = models.CharField(max_length=50, default="Reçu", verbose_name="Statut")
    priorite = models.CharField(max_length=20, default="Normal", choices=[
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
        ('basse', 'Basse'),
    ], verbose_name="Priorité")
    
    class Meta:
        verbose_name = "Document entrant"
        verbose_name_plural = "Documents entrants"
        ordering = ["-date_entree"]
    
    def __str__(self):
        return f"{self.titre} - {self.expediteur} - {self.date_entree}"

class DocumentSortant(BaseDocument):
    """Modèle pour les documents sortants"""
    date_sortie = models.DateField(default=timezone.now, verbose_name="Date de sortie")
    expediteur = models.CharField(max_length=255, verbose_name="Expéditeur")
    destinataire = models.CharField(max_length=255, verbose_name="Destinataire")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_sortants', verbose_name="Département d'origine")
    redacteur = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_rediges', verbose_name="Rédacteur")
    mode_envoi = models.CharField(max_length=50, default="Courrier", choices=[
        ('courrier', 'Courrier'),
        ('email', 'Email'),
        ('fax', 'Fax'),
        ('en_personne', 'En personne'),
    ], verbose_name="Mode d'envoi")
    accusé_reception = models.BooleanField(default=False, verbose_name="Accusé de réception reçu")
    date_accuse_reception = models.DateField(null=True, blank=True, verbose_name="Date d'accusé de réception")
    
    class Meta:
        verbose_name = "Document sortant"
        verbose_name_plural = "Documents sortants"
        ordering = ["-date_sortie"]
    
    def __str__(self):
        return f"{self.titre} - {self.destinataire} - {self.date_sortie}"
