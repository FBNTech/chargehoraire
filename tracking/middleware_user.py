from threading import local
from django.utils.deprecation import MiddlewareMixin

# Thread local storage pour l'utilisateur courant
_thread_locals = local()

def get_current_user():
    """Récupérer l'utilisateur courant depuis le thread local"""
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    """Définir l'utilisateur courant dans le thread local"""
    _thread_locals.user = user

class CurrentUserMiddleware(MiddlewareMixin):
    """
    Middleware pour stocker l'utilisateur courant dans le thread local
    afin qu'il soit accessible dans les signaux
    """
    
    def process_request(self, request):
        """Stocker l'utilisateur courant au début de la requête"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
    
    def process_response(self, request, response):
        """Nettoyer l'utilisateur courant à la fin de la requête"""
        set_current_user(None)
        return response
