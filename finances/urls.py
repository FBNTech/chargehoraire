from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('revenus/', views.income_list, name='income_list'),
    path('depenses/', views.expense_list, name='expense_list'),
    path('prets/', views.loan_list, name='loan_list'),
    path('rapports/', views.report_list, name='report_list'),
    path('generer-rapport/', views.generate_financial_report, name='generate_report'),
    path('generer-rapport/<int:report_id>/', views.generate_financial_report, name='generate_report_by_id'),
]
