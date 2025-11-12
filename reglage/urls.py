from django.urls import path
from . import views

app_name = 'reglage'

urlpatterns = [
    path('gestion/', views.gestion_entites, name='gestion_entites'),
    
    # URLs pour Section
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<path:pk>/update/', views.SectionUpdateView.as_view(), name='section_update'),
    path('sections/<path:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # URLs pour Departement
    path('departements/', views.DepartementListView.as_view(), name='departement_list'),
    path('departements/create/', views.DepartementCreateView.as_view(), name='departement_create'),
    path('departements/<path:pk>/update/', views.DepartementUpdateView.as_view(), name='departement_update'),
    path('departements/<path:pk>/delete/', views.DepartementDeleteView.as_view(), name='departement_delete'),
    
    # URLs pour Mention
    path('mentions/', views.MentionListView.as_view(), name='mention_list'),
    path('mentions/create/', views.MentionCreateView.as_view(), name='mention_create'),
    path('mentions/<path:pk>/update/', views.MentionUpdateView.as_view(), name='mention_update'),
    path('mentions/<path:pk>/delete/', views.MentionDeleteView.as_view(), name='mention_delete'),
    
    # URLs pour Niveau
    path('niveaux/', views.NiveauListView.as_view(), name='niveau_list'),
    path('niveaux/create/', views.NiveauCreateView.as_view(), name='niveau_create'),
    path('niveaux/<path:pk>/update/', views.NiveauUpdateView.as_view(), name='niveau_update'),
    path('niveaux/<path:pk>/delete/', views.NiveauDeleteView.as_view(), name='niveau_delete'),
    
    # URLs pour Classe
    path('classes/', views.ClasseListView.as_view(), name='classe_list'),
    path('classes/create/', views.ClasseCreateView.as_view(), name='classe_create'),
    path('classes/<int:pk>/update/', views.ClasseUpdateView.as_view(), name='classe_update'),
    path('classes/<int:pk>/delete/', views.ClasseDeleteView.as_view(), name='classe_delete'),
    path('classes/import-excel/', views.classe_import_excel, name='classe_import_excel'),
    
    # URLs pour Grade
    path('grades/', views.GradeListView.as_view(), name='grade_list'),
    path('grades/create/', views.GradeCreateView.as_view(), name='grade_create'),
    path('grades/<path:pk>/update/', views.GradeUpdateView.as_view(), name='grade_update'),
    path('grades/<path:pk>/delete/', views.GradeDeleteView.as_view(), name='grade_delete'),
    
    # URLs pour CategorieEnseignant
    path('categories/', views.CategorieListView.as_view(), name='categorie_list'),
    path('categories/create/', views.CategorieCreateView.as_view(), name='categorie_create'),
    path('categories/<path:pk>/update/', views.CategorieUpdateView.as_view(), name='categorie_update'),
    path('categories/<path:pk>/delete/', views.CategorieDeleteView.as_view(), name='categorie_delete'),
    
    # URLs pour Semestre
    path('semestres/', views.SemestreListView.as_view(), name='semestre_list'),
    path('semestres/create/', views.SemestreCreateView.as_view(), name='semestre_create'),
    path('semestres/<path:pk>/update/', views.SemestreUpdateView.as_view(), name='semestre_update'),
    path('semestres/<path:pk>/delete/', views.SemestreDeleteView.as_view(), name='semestre_delete'),
    
    # URLs pour Fonction
    path('fonctions/', views.FonctionListView.as_view(), name='fonction_list'),
    path('fonctions/create/', views.FonctionCreateView.as_view(), name='fonction_create'),
    path('fonctions/<path:pk>/update/', views.FonctionUpdateView.as_view(), name='fonction_update'),
    path('fonctions/<path:pk>/delete/', views.FonctionDeleteView.as_view(), name='fonction_delete'),
    
    # URLs pour AnneeAcademique
    path('annees/', views.AnneeAcademiqueListView.as_view(), name='annee_list'),
    path('annees/create/', views.AnneeAcademiqueCreateView.as_view(), name='annee_create'),
    path('annees/<int:pk>/update/', views.AnneeAcademiqueUpdateView.as_view(), name='annee_update'),
    path('annees/<int:pk>/delete/', views.AnneeAcademiqueDeleteView.as_view(), name='annee_delete'),
    
    # URLs pour Salle
    path('salles/', views.SalleListView.as_view(), name='salle_list'),
    path('salles/create/', views.SalleCreateView.as_view(), name='salle_create'),
    path('salles/<int:pk>/update/', views.SalleUpdateView.as_view(), name='salle_update'),
    path('salles/<int:pk>/delete/', views.SalleDeleteView.as_view(), name='salle_delete'),
    
    # URLs pour Creneau
    path('creneaux/', views.CreneauListView.as_view(), name='creneau_list'),
    path('creneaux/create/', views.CreneauCreateView.as_view(), name='creneau_create'),
    path('creneaux/<int:pk>/update/', views.CreneauUpdateView.as_view(), name='creneau_update'),
    path('creneaux/<int:pk>/delete/', views.CreneauDeleteView.as_view(), name='creneau_delete'),
    
    # URLs pour SemaineCours
    path('semaines/', views.SemaineCoursListView.as_view(), name='semaine_list'),
    path('semaines/create/', views.SemaineCoursCreateView.as_view(), name='semaine_create'),
    path('semaines/<int:pk>/update/', views.SemaineCoursUpdateView.as_view(), name='semaine_update'),
    path('semaines/<int:pk>/delete/', views.SemaineCoursDeleteView.as_view(), name='semaine_delete'),
]
