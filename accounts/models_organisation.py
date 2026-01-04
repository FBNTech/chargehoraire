from django.db import models
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
