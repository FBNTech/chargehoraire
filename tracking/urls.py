from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    # Tableau de bord
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Suivi des enseignements
    path('progress/', views.TeachingProgressListView.as_view(), name='progress_list'),
    path('progress/add/', views.TeachingProgressCreateView.as_view(), name='progress_add'),
    path('progress/<int:pk>/', views.TeachingProgressDetailView.as_view(), name='progress_detail'),
    path('progress/<int:pk>/edit/', views.TeachingProgressUpdateView.as_view(), name='progress_edit'),
    path('progress/<int:pk>/delete/', views.TeachingProgressDeleteView.as_view(), name='progress_delete'),
    path('progress/print/', views.TeachingProgressPrintView.as_view(), name='progress_print'),
    
    # Semaines académiques
    path('weeks/', views.AcademicWeekListView.as_view(), name='week_list'),
    path('weeks/add/', views.AcademicWeekCreateView.as_view(), name='week_add'),
    path('weeks/<int:pk>/edit/', views.AcademicWeekUpdateView.as_view(), name='week_edit'),
    path('weeks/<int:pk>/delete/', views.AcademicWeekDeleteView.as_view(), name='week_delete'),
    
    # Progression par enseignant et par cours
    path('teacher/<int:pk>/progress/', views.TeacherProgressView.as_view(), name='teacher_progress'),
    path('course/<int:pk>/progress/', views.CourseProgressView.as_view(), name='course_progress'),
    
    # API pour les graphiques
    path('api/chart-data/', views.progress_chart_data, name='chart_data'),
    
    # API pour récupérer les cours d'un enseignant
    path('api/teacher/<int:teacher_id>/courses/', views.get_teacher_courses, name='teacher_courses'),
    
    # PDF du rapport de suivi
    path('dashboard/pdf/', views.dashboard_pdf_view, name='dashboard_pdf'),
    
    # Historique des actions (admin seulement)
    path('action-history/', views.action_history_view, name='action_history'),
]
