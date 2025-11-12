from django.db import models
from django.utils import timezone
from teachers.models import Teacher
from reglage.models import Departement

class Publication(models.Model):
    """Modèle de base pour les publications des enseignants"""
    TYPE_CHOICES = [
        ('article', 'Article scientifique'),
        ('livre', 'Livre'),
        ('chapitre', 'Chapitre de livre'),
        ('these', 'Thèse'),
        ('memoire', 'Mémoire'),
        ('communication', 'Communication de conférence'),
        ('rapport', 'Rapport de recherche'),
        ('autre', 'Autre'),
    ]
    
    titre = models.CharField(max_length=255, verbose_name="Titre de la publication")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='article', verbose_name="Type de publication")
    date_publication = models.DateField(default=timezone.now, verbose_name="Date de publication")
    auteurs = models.ManyToManyField(Teacher, related_name='publications', verbose_name="Auteurs")
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, related_name='publications', verbose_name="Département")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Métadonnées communes
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    mots_cles = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mots clés")
    url = models.URLField(blank=True, null=True, verbose_name="URL")
    fichier = models.FileField(upload_to='publications/', blank=True, null=True, verbose_name="Fichier")
    
    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "Publications"
        ordering = ["-date_publication"]
        
    def __str__(self):
        return self.titre

class ArticleScientifique(Publication):
    """Modèle spécifique pour les articles scientifiques"""
    journal = models.CharField(max_length=255, verbose_name="Nom du journal/revue")
    volume = models.CharField(max_length=50, blank=True, null=True, verbose_name="Volume")
    numero = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro")
    pages = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pages")
    impact_factor = models.FloatField(blank=True, null=True, verbose_name="Facteur d'impact")
    peer_reviewed = models.BooleanField(default=True, verbose_name="À comité de lecture")
    doi = models.CharField(max_length=100, blank=True, null=True, verbose_name="DOI")
    
    class Meta:
        verbose_name = "Article scientifique"
        verbose_name_plural = "Articles scientifiques"

class Livre(Publication):
    """Modèle spécifique pour les livres"""
    editeur = models.CharField(max_length=255, verbose_name="Éditeur")
    lieu_publication = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu de publication")
    isbn = models.CharField(max_length=20, blank=True, null=True, verbose_name="ISBN")
    nombre_pages = models.PositiveIntegerField(blank=True, null=True, verbose_name="Nombre de pages")
    edition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Édition")

    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"

class These(Publication):
    """Modèle spécifique pour les thèses"""
    NIVEAU_CHOICES = [
        ('doctorat', 'Doctorat'),
        ('master', 'Master'),
        ('licence', 'Licence'),
        ('autre', 'Autre'),
    ]
    niveau = models.CharField(max_length=50, choices=NIVEAU_CHOICES, default='doctorat', verbose_name="Niveau")
    universite = models.CharField(max_length=255, verbose_name="Université")
    directeur = models.CharField(max_length=255, blank=True, null=True, verbose_name="Directeur de thèse")
    nombre_pages = models.PositiveIntegerField(blank=True, null=True, verbose_name="Nombre de pages")
    mention = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mention")

    class Meta:
        verbose_name = "Thèse/Mémoire"
        verbose_name_plural = "Thèses/Mémoires"

class Communication(Publication):
    """Modèle spécifique pour les communications de conférence"""
    nom_conference = models.CharField(max_length=255, verbose_name="Nom de la conférence")
    lieu = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lieu")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date de fin")
    publie_dans_actes = models.BooleanField(default=False, verbose_name="Publié dans les actes")
    presentation_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type de présentation")

    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communications"
