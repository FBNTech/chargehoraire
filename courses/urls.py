from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='list'),
    # Ajout d'un alias pour l'ancien nom d'URL
    path('', views.CourseListView.as_view(), name='course_list'),
    path('create/', views.CourseCreateView.as_view(), name='create'),
    # Ajout d'un alias pour l'ancien nom d'URL
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('update/<int:pk>/', views.CourseUpdateView.as_view(), name='update'),
    # Ajout d'un alias pour l'ancien nom d'URL
    path('update/<int:pk>/', views.CourseUpdateView.as_view(), name='course_update'),
    path('delete/<str:code_ue>/', views.CourseDeleteView.as_view(), name='delete'),
    # Ajout d'un alias pour l'ancien nom d'URL
    path('delete/<str:code_ue>/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('import-excel/', views.import_excel, name='import_excel_file'),
    path('import/', views.import_courses, name='import_courses'),
    path('import-progress/', views.import_progress, name='import_progress'),
    path('get-section/', views.get_section_by_departement, name='get_section_by_departement'),
    path('delete-selected/', views.delete_selected_courses, name='delete_selected'),
    path('delete-all/', views.delete_all_courses, name='delete_all'),
]

