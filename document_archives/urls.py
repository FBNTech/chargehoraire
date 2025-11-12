from django.urls import path
from . import views

app_name = 'document_archives'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('entrants/', views.documents_entrants, name='documents_entrants'),
    path('sortants/', views.documents_sortants, name='documents_sortants'),
    path('entrants/<int:document_id>/', views.detail_document_entrant, name='detail_document_entrant'),
    path('sortants/<int:document_id>/', views.detail_document_sortant, name='detail_document_sortant'),
]
