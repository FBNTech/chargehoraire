from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.TeacherListView.as_view(), name='list'),
    path('create/', views.TeacherCreateView.as_view(), name='create'),
    path('update/<int:pk>/', views.TeacherUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.TeacherDeleteView.as_view(), name='delete'),
    path('delete-all/', views.delete_all_teachers, name='delete_all'),
    path('import-excel/', views.import_excel, name='import_excel_file'),
    path('import/', views.import_teachers, name='import_teachers'),
    path('get-section/', views.get_section_by_departement, name='get_section_by_departement'),
]
