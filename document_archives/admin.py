from django.contrib import admin
from .models import DocumentEntrant, DocumentSortant

@admin.register(DocumentEntrant)
class DocumentEntrantAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_entree', 'expediteur', 'destinataire', 'departement', 'statut', 'priorite')
    list_filter = ('date_entree', 'statut', 'priorite', 'departement')
    search_fields = ('titre', 'expediteur', 'destinataire', 'reference', 'description', 'mots_cles')
    date_hierarchy = 'date_entree'
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'reference', 'description', 'fichier')
        }),
        ('Détails de réception', {
            'fields': ('date_entree', 'date_reception', 'expediteur', 'destinataire', 'departement')
        }),
        ('Classification', {
            'fields': ('statut', 'priorite', 'categorie', 'mots_cles')
        }),
        ('Notes', {
            'fields': ('note',)
        })
    )

@admin.register(DocumentSortant)
class DocumentSortantAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_sortie', 'expediteur', 'destinataire', 'departement', 'mode_envoi', 'accusé_reception')
    list_filter = ('date_sortie', 'mode_envoi', 'accusé_reception', 'departement')
    search_fields = ('titre', 'expediteur', 'destinataire', 'reference', 'description', 'mots_cles')
    date_hierarchy = 'date_sortie'
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'reference', 'description', 'fichier')
        }),
        ('Détails d\'envoi', {
            'fields': ('date_sortie', 'expediteur', 'destinataire', 'departement', 'redacteur', 'mode_envoi')
        }),
        ('Suivi', {
            'fields': ('accusé_reception', 'date_accuse_reception')
        }),
        ('Classification', {
            'fields': ('categorie', 'mots_cles')
        }),
        ('Notes', {
            'fields': ('note',)
        })
    )
