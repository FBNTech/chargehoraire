from django.contrib import admin
from .models import AcademicWeek, TeachingProgress, ProgressStats

@admin.register(AcademicWeek)
class AcademicWeekAdmin(admin.ModelAdmin):
    list_display = ['codesemaine', 'semestre', 'start_date', 'end_date', 'academic_year', 'is_active']
    list_filter = ['academic_year', 'is_active', 'semestre']
    search_fields = ['codesemaine', 'academic_year']
    ordering = ['-academic_year', 'codesemaine']

@admin.register(TeachingProgress)
class TeachingProgressAdmin(admin.ModelAdmin):
    list_display = ['course', 'teacher', 'week', 'hours_done', 'status', 'created_at']
    list_filter = ['status', 'week__annee_academique', 'created_at']
    search_fields = ['course__code_ue', 'teacher__nom_complet', 'week__designation', 'week__numero_semaine']
    ordering = ['-created_at']

@admin.register(ProgressStats)
class ProgressStatsAdmin(admin.ModelAdmin):
    list_display = ['course', 'teacher', 'academic_year', 'total_hours_done', 'last_update']
    list_filter = ['academic_year', 'last_update']
    search_fields = ['course__code_ue', 'teacher__nom_complet']
    ordering = ['-last_update']
