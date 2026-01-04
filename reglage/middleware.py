"""
Middleware pour la mise à jour automatique du statut des semaines de cours
"""
from datetime import date, timedelta


class SemaineCoursMiddleware:
    """
    Middleware qui met à jour automatiquement le statut 'en cours' des semaines
    en fonction de la date actuelle.
    
    La mise à jour est effectuée une fois par jour maximum pour éviter
    des requêtes inutiles à chaque requête HTTP.
    """
    
    # Variable de classe pour stocker la dernière date de mise à jour
    _last_update_date = None
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier si une mise à jour est nécessaire
        today = date.today()
        
        # Mettre à jour seulement si c'est un nouveau jour
        if SemaineCoursMiddleware._last_update_date != today:
            try:
                from reglage.models import SemaineCours
                semaine_actuelle = SemaineCours.update_statut_automatique()
                
                # Enregistrer la date de mise à jour
                SemaineCoursMiddleware._last_update_date = today
                
                if semaine_actuelle:
                    print(f"[SemaineCoursMiddleware] Semaine en cours mise a jour: {semaine_actuelle}")
                else:
                    print(f"[SemaineCoursMiddleware] Aucune semaine en cours pour aujourd'hui ({today})")
            except Exception as e:
                # En cas d'erreur, ne pas bloquer la requête
                print(f"[SemaineCoursMiddleware] Erreur lors de la mise a jour: {e}")
        
        # Continuer avec la requête
        response = self.get_response(request)
        return response
