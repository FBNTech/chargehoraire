from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import DocumentEntrant, DocumentSortant

def dashboard(request):
    """Vue principale pour l'archivage des documents"""
    # Récupérer quelques documents récents
    documents_entrants_recent = DocumentEntrant.objects.all().order_by('-date_entree')[:5]
    documents_sortants_recent = DocumentSortant.objects.all().order_by('-date_sortie')[:5]
    
    # Compter le nombre total de documents
    total_entrants = DocumentEntrant.objects.count()
    total_sortants = DocumentSortant.objects.count()
    
    context = {
        'documents_entrants_recent': documents_entrants_recent,
        'documents_sortants_recent': documents_sortants_recent,
        'total_entrants': total_entrants,
        'total_sortants': total_sortants,
    }
    
    return render(request, 'document_archives/dashboard.html', context)

def documents_entrants(request):
    """Liste des documents entrants avec filtrage"""
    documents = DocumentEntrant.objects.all()
    
    # Filtrage
    if 'recherche' in request.GET and request.GET['recherche']:
        query = request.GET['recherche']
        documents = documents.filter(
            Q(titre__icontains=query) |
            Q(expediteur__icontains=query) |
            Q(destinataire__icontains=query) |
            Q(reference__icontains=query) |
            Q(description__icontains=query) |
            Q(mots_cles__icontains=query)
        )
    
    # Filtrage par date
    if 'date_debut' in request.GET and request.GET['date_debut']:
        documents = documents.filter(date_entree__gte=request.GET['date_debut'])
    
    if 'date_fin' in request.GET and request.GET['date_fin']:
        documents = documents.filter(date_entree__lte=request.GET['date_fin'])
    
    # Filtrage par expéditeur
    if 'expediteur' in request.GET and request.GET['expediteur']:
        documents = documents.filter(expediteur__icontains=request.GET['expediteur'])
    
    # Filtrage par destinataire
    if 'destinataire' in request.GET and request.GET['destinataire']:
        documents = documents.filter(destinataire__icontains=request.GET['destinataire'])
    
    # Trier les résultats
    order_by = request.GET.get('order_by', '-date_entree')
    documents = documents.order_by(order_by)
    
    context = {
        'documents': documents,
        'filtres': request.GET,
    }
    
    return render(request, 'document_archives/documents_entrants.html', context)

def documents_sortants(request):
    """Liste des documents sortants avec filtrage"""
    documents = DocumentSortant.objects.all()
    
    # Filtrage
    if 'recherche' in request.GET and request.GET['recherche']:
        query = request.GET['recherche']
        documents = documents.filter(
            Q(titre__icontains=query) |
            Q(expediteur__icontains=query) |
            Q(destinataire__icontains=query) |
            Q(reference__icontains=query) |
            Q(description__icontains=query) |
            Q(mots_cles__icontains=query)
        )
    
    # Filtrage par date
    if 'date_debut' in request.GET and request.GET['date_debut']:
        documents = documents.filter(date_sortie__gte=request.GET['date_debut'])
    
    if 'date_fin' in request.GET and request.GET['date_fin']:
        documents = documents.filter(date_sortie__lte=request.GET['date_fin'])
    
    # Filtrage par expéditeur
    if 'expediteur' in request.GET and request.GET['expediteur']:
        documents = documents.filter(expediteur__icontains=request.GET['expediteur'])
    
    # Filtrage par destinataire
    if 'destinataire' in request.GET and request.GET['destinataire']:
        documents = documents.filter(destinataire__icontains=request.GET['destinataire'])
    
    # Trier les résultats
    order_by = request.GET.get('order_by', '-date_sortie')
    documents = documents.order_by(order_by)
    
    context = {
        'documents': documents,
        'filtres': request.GET,
    }
    
    return render(request, 'document_archives/documents_sortants.html', context)

def detail_document_entrant(request, document_id):
    """Afficher les détails d'un document entrant"""
    document = get_object_or_404(DocumentEntrant, pk=document_id)
    return render(request, 'document_archives/detail_document_entrant.html', {'document': document})

def detail_document_sortant(request, document_id):
    """Afficher les détails d'un document sortant"""
    document = get_object_or_404(DocumentSortant, pk=document_id)
    return render(request, 'document_archives/detail_document_sortant.html', {'document': document})
