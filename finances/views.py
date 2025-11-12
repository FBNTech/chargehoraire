from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
from io import BytesIO
from datetime import datetime

from .models import Income, Expense, Loan, FinancialReport
from teachers.models import Teacher
from reglage.models import Departement

def dashboard(request):
    """Vue principale pour la gestion financière"""
    # Statistiques des revenus et dépenses récentes
    recent_incomes = Income.objects.order_by('-date')[:5]
    recent_expenses = Expense.objects.order_by('-date')[:5]
    active_loans = Loan.objects.filter(statut='en_cours').order_by('-date_emprunt')
    recent_reports = FinancialReport.objects.order_by('-created_at')[:5]
    
    # Totaux
    total_income = Income.objects.all().values('montant')
    total_income_sum = sum(item['montant'] for item in total_income) if total_income else 0
    
    total_expense = Expense.objects.all().values('montant')
    total_expense_sum = sum(item['montant'] for item in total_expense) if total_expense else 0
    
    balance = total_income_sum - total_expense_sum
    
    # Solde des prêts en cours
    loans_balance = sum(loan.solde_restant for loan in active_loans)
    
    context = {
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        'active_loans': active_loans,
        'recent_reports': recent_reports,
        'total_income': total_income_sum,
        'total_expense': total_expense_sum,
        'balance': balance,
        'loans_balance': loans_balance,
    }
    
    return render(request, 'finances/dashboard.html', context)

def income_list(request):
    """Liste des entrées d'argent"""
    incomes = Income.objects.all().order_by('-date')
    return render(request, 'finances/income_list.html', {'incomes': incomes})

def expense_list(request):
    """Liste des dépenses"""
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'finances/expense_list.html', {'expenses': expenses})

def loan_list(request):
    """Liste des prêts"""
    loans = Loan.objects.all().order_by('-date_emprunt')
    return render(request, 'finances/loan_list.html', {'loans': loans})

def report_list(request):
    """Liste des rapports financiers"""
    reports = FinancialReport.objects.all().order_by('-periode_fin')
    return render(request, 'finances/report_list.html', {'reports': reports})

def generate_financial_report(request, report_id=None):
    """Générer un rapport financier PDF"""
    if report_id:
        report = get_object_or_404(FinancialReport, id=report_id)
    else:
        # Valeurs par défaut pour un nouveau rapport
        periode_debut = request.GET.get('periode_debut', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        periode_fin = request.GET.get('periode_fin', datetime.now().strftime('%Y-%m-%d'))
        departement_id = request.GET.get('departement')
        
        try:
            departement = Departement.objects.get(pk=departement_id) if departement_id else None
        except Departement.DoesNotExist:
            messages.error(request, "Le département spécifié n'existe pas.")
            return redirect('finances:report_list')
            
        # Créer un rapport temporaire (ne sera pas enregistré)
        report = FinancialReport(
            titre=f"Rapport financier du {periode_debut} au {periode_fin}",
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            departement=departement,
            statut='brouillon'
        )
    
    # Récupérer les données financières pour la période
    incomes = Income.objects.filter(
        date__gte=report.periode_debut,
        date__lte=report.periode_fin
    )
    if report.departement:
        incomes = incomes.filter(departement=report.departement)
        
    expenses = Expense.objects.filter(
        date__gte=report.periode_debut,
        date__lte=report.periode_fin
    )
    if report.departement:
        expenses = expenses.filter(departement=report.departement)
        
    loans = Loan.objects.filter(
        date_emprunt__gte=report.periode_debut,
        date_emprunt__lte=report.periode_fin
    )
    if report.departement:
        loans = loans.filter(departement=report.departement)
    
    # Calculs des totaux
    total_income = sum(income.montant for income in incomes)
    total_expense = sum(expense.montant for expense in expenses)
    balance = total_income - total_expense
    
    # Informations du chef de département
    chef = None
    if report.departement:
        try:
            # Essayer de trouver le chef de département
            chefs = Teacher.objects.filter(departement=report.departement.CodeDept, est_chef=True)
            if chefs.exists():
                chef = chefs.first()
        except Exception:
            pass
    
    # Contexte pour le PDF
    context = {
        'report': report,
        'incomes': incomes,
        'expenses': expenses,
        'loans': loans,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'chef_departement': chef,
        'date_generation': timezone.now(),
    }
    
    # Générer le PDF
    template_path = 'finances/financial_report_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    
    # Créer la réponse PDF
    response = HttpResponse(content_type='application/pdf')
    fichier = f"rapport_financier_{report.periode_debut.strftime('%Y%m%d')}_{report.periode_fin.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{fichier}"'
    
    # Génération du PDF avec xhtml2pdf
    pdf_status = pisa.CreatePDF(html, dest=response)
    
    if pdf_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=400)
    
    return response
