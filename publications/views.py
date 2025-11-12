from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO

from .models import Publication, ArticleScientifique, Livre, These, Communication
from teachers.models import Teacher
from reglage.models import Departement

def dashboard(request):
    """Vue du tableau de bord des publications"""
    # Récupérer les statistiques générales
    total_publications = Publication.objects.count()
    total_articles = ArticleScientifique.objects.count()
    total_livres = Livre.objects.count()
    total_theses = These.objects.count()
    total_communications = Communication.objects.count()
    
    # Publications récentes
    recent_publications = Publication.objects.all().order_by('-date_publication')[:10]
    
    # Statistiques par département
    dept_stats = Departement.objects.annotate(pub_count=Count('publications')).order_by('-pub_count')[:5]
    
    # Statistiques par enseignant
    teacher_stats = Teacher.objects.annotate(pub_count=Count('publications')).order_by('-pub_count')[:5]
    
    context = {
        'total_publications': total_publications,
        'total_articles': total_articles,
        'total_livres': total_livres,
        'total_theses': total_theses,
        'total_communications': total_communications,
        'recent_publications': recent_publications,
        'dept_stats': dept_stats,
        'teacher_stats': teacher_stats,
    }
    
    return render(request, 'publications/dashboard.html', context)

def publication_list(request):
    """Liste des publications avec filtrage"""
    publications = Publication.objects.all()
    
    # Filtrage par type
    publication_type = request.GET.get('type', '')
    if publication_type:
        publications = publications.filter(type=publication_type)
    
    # Filtrage par année
    year = request.GET.get('year', '')
    if year:
        publications = publications.filter(date_publication__year=year)
    
    # Filtrage par département
    departement_id = request.GET.get('departement', '')
    if departement_id:
        publications = publications.filter(departement_id=departement_id)
    
    # Filtrage par auteur (enseignant)
    teacher_id = request.GET.get('teacher', '')
    if teacher_id:
        publications = publications.filter(auteurs__id=teacher_id)
    
    # Recherche textuelle
    query = request.GET.get('query', '')
    if query:
        publications = publications.filter(
            models.Q(titre__icontains=query) | 
            models.Q(description__icontains=query) | 
            models.Q(mots_cles__icontains=query)
        )
    
    # Trier les résultats
    order_by = request.GET.get('order_by', '-date_publication')
    publications = publications.order_by(order_by)
    
    # Listes pour les filtres
    departments = Departement.objects.all()
    teachers = Teacher.objects.all()
    
    # Liste des années de publication
    years = Publication.objects.dates('date_publication', 'year', order='DESC')
    years = [date.year for date in years]
    
    context = {
        'publications': publications,
        'departments': departments,
        'teachers': teachers,
        'years': years,
        'filters': request.GET,
    }
    
    return render(request, 'publications/publication_list.html', context)

def publication_detail(request, publication_id):
    """Détail d'une publication"""
    publication = get_object_or_404(Publication, id=publication_id)
    
    # Déterminer le type spécifique de publication pour afficher des détails supplémentaires
    specific_publication = None
    pub_type = publication.type
    
    if pub_type == 'article':
        specific_publication = ArticleScientifique.objects.filter(id=publication_id).first()
    elif pub_type == 'livre':
        specific_publication = Livre.objects.filter(id=publication_id).first()
    elif pub_type in ['these', 'memoire']:
        specific_publication = These.objects.filter(id=publication_id).first()
    elif pub_type == 'communication':
        specific_publication = Communication.objects.filter(id=publication_id).first()
    
    context = {
        'publication': publication,
        'specific_publication': specific_publication,
    }
    
    return render(request, 'publications/publication_detail.html', context)

def publication_add(request):
    """Ajout d'une nouvelle publication"""
    if request.method == 'POST':
        # Traitement du formulaire d'ajout
        # Code pour créer une nouvelle publication
        pass
    
    # Formulaire vide pour l'ajout
    departments = Departement.objects.all()
    teachers = Teacher.objects.all()
    
    context = {
        'departments': departments,
        'teachers': teachers,
    }
    
    return render(request, 'publications/publication_add.html', context)

def publication_edit(request, publication_id):
    """Modification d'une publication existante"""
    publication = get_object_or_404(Publication, id=publication_id)
    
    if request.method == 'POST':
        # Traitement du formulaire de modification
        # Code pour mettre à jour la publication
        pass
    
    # Formulaire pré-rempli avec les données de la publication
    departments = Departement.objects.all()
    teachers = Teacher.objects.all()
    
    context = {
        'publication': publication,
        'departments': departments,
        'teachers': teachers,
    }
    
    return render(request, 'publications/publication_edit.html', context)

def publication_delete(request, publication_id):
    """Suppression d'une publication"""
    publication = get_object_or_404(Publication, id=publication_id)
    
    if request.method == 'POST':
        publication.delete()
        messages.success(request, "La publication a été supprimée avec succès.")
        return redirect('publications:publication_list')
    
    context = {
        'publication': publication,
    }
    
    return render(request, 'publications/publication_delete.html', context)

def teacher_publications(request, teacher_id):
    """Liste des publications d'un enseignant spécifique"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    publications = teacher.publications.all().order_by('-date_publication')
    
    context = {
        'teacher': teacher,
        'publications': publications,
    }
    
    return render(request, 'publications/teacher_publications.html', context)

def departement_publications(request, departement_id):
    """Liste des publications d'un département spécifique"""
    departement = get_object_or_404(Departement, CodeDept=departement_id)
    publications = Publication.objects.filter(departement=departement).order_by('-date_publication')
    
    context = {
        'departement': departement,
        'publications': publications,
    }
    
    return render(request, 'publications/departement_publications.html', context)

def statistics(request):
    """Statistiques sur les publications"""
    # Calculer le total des publications
    total_publications = Publication.objects.count()
    
    # Statistiques par type de publication
    type_stats = Publication.objects.values('type').annotate(count=Count('id')).order_by('-count')
    
    # Calculer le nombre pour chaque type spécifique
    total_articles = Publication.objects.filter(type='article').count()
    total_livres = Publication.objects.filter(type='livre').count()
    total_theses = Publication.objects.filter(type='these').count()
    total_memoires = Publication.objects.filter(type='memoire').count()
    total_communications = Publication.objects.filter(type='communication').count()
    
    # Statistiques par année
    year_stats = Publication.objects.dates('date_publication', 'year', order='DESC')
    year_counts = []
    for year in year_stats:
        count = Publication.objects.filter(date_publication__year=year.year).count()
        year_counts.append({'year': year.year, 'count': count})
    
    # Statistiques par département avec pourcentages
    dept_stats = Departement.objects.annotate(pub_count=Count('publications')).order_by('-pub_count')
    
    # Précalculer les pourcentages pour les barres de progression
    if dept_stats:
        max_dept_count = dept_stats[0].pub_count if dept_stats else 0
        for dept in dept_stats:
            if max_dept_count > 0:
                dept.percentage = int((dept.pub_count / max_dept_count) * 100)
            else:
                dept.percentage = 0
    
    # Statistiques par enseignant (top 10) avec pourcentages
    teacher_stats = Teacher.objects.annotate(pub_count=Count('publications')).order_by('-pub_count')[:10]
    
    # Précalculer les pourcentages pour les barres de progression
    if teacher_stats:
        max_teacher_count = teacher_stats[0].pub_count if teacher_stats else 0
        for teacher in teacher_stats:
            if max_teacher_count > 0:
                teacher.percentage = int((teacher.pub_count / max_teacher_count) * 100)
            else:
                teacher.percentage = 0
    
    context = {
        'total_publications': total_publications,
        'total_articles': total_articles,
        'total_livres': total_livres,
        'total_theses': total_theses,
        'total_memoires': total_memoires,
        'total_communications': total_communications,
        'type_stats': type_stats,
        'year_counts': year_counts,
        'dept_stats': dept_stats,
        'teacher_stats': teacher_stats,
    }
    
    return render(request, 'publications/statistics.html', context)
