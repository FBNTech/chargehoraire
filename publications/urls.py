from django.urls import path
from . import views

app_name = 'publications'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('liste/', views.publication_list, name='publication_list'),
    path('detail/<int:publication_id>/', views.publication_detail, name='publication_detail'),
    path('ajouter/', views.publication_add, name='publication_add'),
    path('modifier/<int:publication_id>/', views.publication_edit, name='publication_edit'),
    path('supprimer/<int:publication_id>/', views.publication_delete, name='publication_delete'),
    path('enseignant/<int:teacher_id>/', views.teacher_publications, name='teacher_publications'),
    path('departement/<str:departement_id>/', views.departement_publications, name='departement_publications'),
    path('statistiques/', views.statistics, name='statistics'),
]
