from django.db import models
from django.db.models import Value, F, OuterRef, Subquery, Q
from django.db.models.functions import Replace, Concat
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from courses.models import Course
from .models import Attribution

@require_GET
def get_ues_by_classe(request):
    """Vue pour récupérer les UE d'une classe spécifique"""
    try:
        # Journalisation de la requête entrante
        print(f"Requête reçue: {request.GET}")
        
        # Récupération des paramètres
        classe = request.GET.get('classe')
        semestre = request.GET.get('semestre')  # Nouveau paramètre pour le filtre par semestre
        
        if not classe:
            print("Erreur: Paramètre 'classe' manquant")
            return JsonResponse({'error': 'Paramètre classe manquant', 'details': 'Le paramètre classe est requis'}, status=400)
        
        # Nettoyer le code de la classe en supprimant les espaces
        classe_nettoyee = classe.replace(' ', '')
        print(f"Classe nettoyée: '{classe}' -> '{classe_nettoyee}'")
        print(f"Semestre sélectionné: {semestre or 'Non spécifié'}")
        
        # Vérifier s'il y a des cours pour cette classe
        cours_count = Course.objects.annotate(
            classe_sans_espace=Replace('classe', Value(' '), Value(''))
        ).filter(classe_sans_espace=classe_nettoyee).count()
        
        print(f"Nombre de cours trouvés pour la classe '{classe_nettoyee}': {cours_count}")
        
        # Sous-requête pour récupérer les noms des enseignants pour chaque cours
        try:
            enseignants_subquery = Attribution.objects.filter(
                code_ue=OuterRef('pk')
            ).annotate(
                nom_enseignant=F('matricule__nom_complet')
            ).values('nom_enseignant')[:1]
            print("Sous-requête enseignants créée avec succès")
        except Exception as e:
            print(f"Erreur lors de la création de la sous-requête enseignants: {str(e)}")
            return JsonResponse({
                'error': 'Erreur lors de la préparation des données',
                'details': str(e)
            }, status=500)
    
        # Préparer le filtre de base pour la classe
        base_filter = Q(classe_sans_espace=classe_nettoyee)
        
        # Ajouter le filtre par semestre si spécifié
        if semestre:
            base_filter &= Q(semestre=semestre)
        
        # Récupérer les UE pour la classe spécifiée, en ignorant les espaces dans le champ classe
        try:
            ues = Course.objects.annotate(
                classe_sans_espace=Replace('classe', Value(' '), Value(''))
            ).filter(
                base_filter
            ).annotate(
                enseignant=Subquery(enseignants_subquery)
            ).order_by('code_ue', 'semestre')
            print(f"Requête UE exécutée avec succès, {len(ues)} résultats")
        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête UE: {str(e)}")
            return JsonResponse({
                'error': 'Erreur lors de la récupération des UE',
                'details': str(e)
            }, status=500)
    
        # Préparer les données de réponse
        data = []
        try:
            for ue in ues:
                try:
                    # Récupérer toutes les attributions pour ce cours
                    attributions = Attribution.objects.filter(code_ue=ue)
                    print(f"  - UE: {ue.code_ue}, {attributions.count()} attribution(s) trouvée(s)")
                    
                    if attributions.exists():
                        # Si des attributions existent, créer une entrée pour chaque enseignant
                        for attr in attributions:
                            try:
                                enseignant_nom = attr.matricule.nom_complet if (attr.matricule and hasattr(attr.matricule, 'nom_complet')) else 'Non attribué'
                                display_text = f"{ue.code_ue} - {ue.intitule_ue} | {ue.intitule_ec or 'Sans EC'} | {enseignant_nom}"
                                
                                data.append({
                                    'id': attr.id,  # Utiliser l'ID de l'attribution pour le formulaire
                                    'code': ue.code_ue,
                                    'intitule': ue.intitule_ue,
                                    'intitule_ec': ue.intitule_ec or '',
                                    'classe': ue.classe,
                                    'semestre': ue.semestre,
                                    'departement': ue.departement or '',
                                    'enseignant': enseignant_nom,
                                    'display_text': display_text
                                })
                            except Exception as e:
                                print(f"    Erreur avec l'attribution {attr.id}: {str(e)}")
                                continue
                    else:
                        # Si aucune attribution, afficher juste l'UE
                        display_text = f"{ue.code_ue} - {ue.intitule_ue} | {ue.intitule_ec or 'Sans EC'} | Non attribué"
                        data.append({
                            'id': ue.id,
                            'code': ue.code_ue,
                            'intitule': ue.intitule_ue,
                            'intitule_ec': ue.intitule_ec or '',
                            'classe': ue.classe,
                            'semestre': ue.semestre,
                            'departement': ue.departement or '',
                            'enseignant': 'Non attribué',
                            'display_text': display_text
                        })
                except Exception as e:
                    print(f"Erreur lors du traitement de l'UE {getattr(ue, 'id', 'inconnu')}: {str(e)}")
                    continue
            
            print(f"Préparation des données terminée: {len(data)} entrées créées")
            return JsonResponse({'ues': data})
            
        except Exception as e:
            print(f"Erreur lors de la préparation des données: {str(e)}")
            return JsonResponse({
                'error': 'Erreur lors de la préparation des données',
                'details': str(e)
            }, status=500)
            
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
        return JsonResponse({
            'error': 'Une erreur inattendue est survenue',
            'details': str(e)
        }, status=500)
