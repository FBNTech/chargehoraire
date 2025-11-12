from django.contrib import admin
from .models import Income, Expense, Loan, FinancialReport

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('montant', 'categorie', 'date', 'source', 'departement')
    list_filter = ('categorie', 'date', 'departement')
    search_fields = ('description', 'source', 'reference')
    date_hierarchy = 'date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('montant', 'categorie', 'date', 'beneficiaire', 'departement')
    list_filter = ('categorie', 'date', 'departement')
    search_fields = ('description', 'beneficiaire', 'reference')
    date_hierarchy = 'date'

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('montant', 'emprunteur', 'date_emprunt', 'date_echeance', 'statut', 'solde_restant')
    list_filter = ('statut', 'date_emprunt', 'departement')
    search_fields = ('emprunteur', 'motif')
    date_hierarchy = 'date_emprunt'
    readonly_fields = ('solde_restant',)

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('titre', 'periode_debut', 'periode_fin', 'departement', 'statut', 'date_signature')
    list_filter = ('statut', 'departement')
    search_fields = ('titre', 'description')
    date_hierarchy = 'periode_fin'
    readonly_fields = ('created_at', 'updated_at')
