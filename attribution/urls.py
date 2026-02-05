from django.urls import path
from . import views

app_name = 'attribution'

urlpatterns = [
    path('', views.attribution_list, name='attribution_list'),
    path('teacher-info/', views.get_teacher_info, name='get_teacher_info'),
    path('add/', views.add_course_attribution, name='add_course_attribution'),
    path('delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('migrate/', views.migrate_courses, name='migrate_courses'),
    path('vider/', views.vider_cours, name='vider_cours'),
    path('filter/', views.get_filtered_courses, name='get_filtered_courses'),
    path('create-attribution/', views.create_attribution, name='create_attribution'),
    path('liste-attributions/', views.liste_attributions_view, name='list_attribution'),
    path('delete-attribution/<int:attribution_id>/', views.delete_attribution, name='delete_attribution'),
    path('create-new-attribution/', views.create_new_attribution, name='create_new_attribution'),
    path('search-attributions/', views.search_attributions, name='search_attributions'),
    path('rapport/pdf/', views.generate_pdf, name='generate_pdf'),
    path('liste-charges/', views.liste_charges, name='liste_charges'),
    path('detail-attribution/<int:attribution_id>/', views.detail_attribution, name='detail_attribution'),
    path('edit-attribution/<int:attribution_id>/', views.edit_attribution, name='edit_attribution'),
    path('schedule/', views.schedule_builder, name='schedule_builder'),
    path('schedule/pdf/', views.schedule_pdf, name='schedule_pdf'),
    path('schedule/save/', views.save_schedule_entries, name='save_schedule_entries'),
    
    # CRUD pour ScheduleEntry
    path('schedule/entry/list/', views.ScheduleEntryListView.as_view(), name='schedule_entry_list'),
    path('schedule/entry/create/', views.ScheduleEntryCreateView.as_view(), name='schedule_entry_create'),
    path('schedule/entry/<int:pk>/edit/', views.ScheduleEntryUpdateView.as_view(), name='schedule_entry_edit'),
    path('schedule/entry/<int:pk>/delete/', views.schedule_entry_delete, name='schedule_entry_delete'),
    path('schedule/entry/bulk-delete/', views.schedule_entry_bulk_delete, name='schedule_entry_bulk_delete'),
    
    # Autocomplétion et filtrage des UEs
    path('api/autocomplete/ues/', views.autocomplete_ues, name='autocomplete_ues'),
    path('api/ues/by-classe/', views.get_ues_by_classe, name='get_ues_by_classe'),
    
    # Rapport de conflits
    path('schedule/conflicts/', views.schedule_conflicts_report, name='schedule_conflicts_report'),
    
    # Heures supplémentaires par grade
    path('heures-supplementaires-grade/', views.heures_supplementaires_par_grade, name='heures_supplementaires_grade'),
    
    # Impression des charges par section
    path('imprimer-charges-section/', views.imprimer_charges_section, name='imprimer_charges_section'),
    
    # Import Excel des attributions
    path('import-excel-attributions/', views.import_excel_attributions, name='import_excel_attributions'),
    
    # Supprimer toutes les attributions (superuser uniquement)
    path('delete-all-attributions/', views.delete_all_attributions, name='delete_all_attributions'),
]
