from django.urls import path
from . import views

app_name = 'gestion_administrative'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('autorisation-absence-enseignant/', views.autorisation_absence_enseignant, name='autorisation_absence_enseignant'),
    path('liste-absences/', views.liste_absences, name='liste_absences'),
    path('modifier-absence/<int:absence_id>/', views.modifier_absence, name='modifier_absence'),
    path('supprimer-absence/<int:absence_id>/', views.supprimer_absence, name='supprimer_absence'),
    
    # URLs pour la gestion des annonces et communiqués
    path('annonces/', views.liste_annonces, name='annonces'),
    path('annonces/ajouter/', views.ajouter_annonce, name='ajouter_annonce'),
    path('annonces/modifier/<int:annonce_id>/', views.modifier_annonce, name='modifier_annonce'),
    path('annonces/supprimer/<int:annonce_id>/', views.supprimer_annonce, name='supprimer_annonce'),
    
    # URLs pour la gestion des étudiants
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('etudiants/modifier/<int:etudiant_id>/', views.modifier_etudiant, name='modifier_etudiant'),
    path('etudiants/supprimer/<int:etudiant_id>/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('etudiants/importer/', views.importer_etudiants_excel, name='importer_etudiants_excel'),
    path('etudiants/autorisation-absence/', views.autorisation_absence_etudiant, name='autorisation_absence_etudiant'),
    path('etudiants/liste-absences/', views.liste_absences_etudiants, name='liste_absences_etudiants'),
    path('etudiants/supprimer-absence/<int:absence_id>/', views.supprimer_absence_etudiant, name='supprimer_absence_etudiant'),
]
