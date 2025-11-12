from django.contrib import admin
from .models import Publication, ArticleScientifique, Livre, These, Communication

class PublicationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'date_publication', 'get_auteurs', 'departement')
    list_filter = ('type', 'date_publication', 'departement')
    search_fields = ('titre', 'description', 'mots_cles')
    date_hierarchy = 'date_publication'
    filter_horizontal = ('auteurs',)
    
    def get_auteurs(self, obj):
        return ", ".join([auteur.nom_complet for auteur in obj.auteurs.all()])
    
    get_auteurs.short_description = 'Auteurs'

@admin.register(ArticleScientifique)
class ArticleScientifiqueAdmin(admin.ModelAdmin):
    list_display = ('titre', 'journal', 'date_publication', 'get_auteurs', 'impact_factor', 'peer_reviewed')
    list_filter = ('peer_reviewed', 'date_publication')
    search_fields = ('titre', 'journal', 'doi', 'description', 'mots_cles')
    date_hierarchy = 'date_publication'
    filter_horizontal = ('auteurs',)
    
    def get_auteurs(self, obj):
        return ", ".join([auteur.nom_complet for auteur in obj.auteurs.all()])
    
    get_auteurs.short_description = 'Auteurs'

@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'editeur', 'date_publication', 'get_auteurs', 'isbn')
    list_filter = ('date_publication',)
    search_fields = ('titre', 'editeur', 'isbn', 'description', 'mots_cles')
    date_hierarchy = 'date_publication'
    filter_horizontal = ('auteurs',)
    
    def get_auteurs(self, obj):
        return ", ".join([auteur.nom_complet for auteur in obj.auteurs.all()])
    
    get_auteurs.short_description = 'Auteurs'

@admin.register(These)
class TheseAdmin(admin.ModelAdmin):
    list_display = ('titre', 'niveau', 'universite', 'date_publication', 'get_auteurs')
    list_filter = ('niveau', 'date_publication', 'universite')
    search_fields = ('titre', 'universite', 'directeur', 'description', 'mots_cles')
    date_hierarchy = 'date_publication'
    filter_horizontal = ('auteurs',)
    
    def get_auteurs(self, obj):
        return ", ".join([auteur.nom_complet for auteur in obj.auteurs.all()])
    
    get_auteurs.short_description = 'Auteurs'

@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'nom_conference', 'lieu', 'date_debut', 'get_auteurs', 'publie_dans_actes')
    list_filter = ('publie_dans_actes', 'date_debut')
    search_fields = ('titre', 'nom_conference', 'lieu', 'description', 'mots_cles')
    date_hierarchy = 'date_debut'
    filter_horizontal = ('auteurs',)
    
    def get_auteurs(self, obj):
        return ", ".join([auteur.nom_complet for auteur in obj.auteurs.all()])
    
    get_auteurs.short_description = 'Auteurs'

# Register the base Publication model
admin.site.register(Publication, PublicationAdmin)
