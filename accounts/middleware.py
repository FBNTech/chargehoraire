from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Middleware pour restreindre l'accès aux pages qui nécessitent une authentification.
    Redirige vers la page de connexion si l'utilisateur n'est pas authentifié.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs qui ne nécessitent pas d'authentification
        self.public_urls = [
            reverse('accounts:login'), 
            reverse('accounts:logout'),
            reverse('accounts:register'),
            reverse('accounts:password_reset'),
            reverse('accounts:password_reset_done'),
            # Motif pour les URLs de réinitialisation de mot de passe avec des paramètres
            'password/reset/confirm',
            reverse('accounts:password_reset_complete'),
            # Page d'accueil publique
            reverse('home'),
            # URLs de l'administration Django
            '/admin/',
        ]
    
    def __call__(self, request):
        # Si l'utilisateur n'est pas authentifié et n'est pas sur une URL publique
        if not request.user.is_authenticated:
            current_url = request.path_info
            
            # Vérifier si l'URL actuelle est publique
            is_public = False
            for url in self.public_urls:
                if current_url.startswith(url) or url in current_url:
                    is_public = True
                    break
            
            # Si l'URL n'est pas publique, rediriger vers la page de connexion
            if not is_public and not current_url.startswith(settings.STATIC_URL) and not current_url.startswith(settings.MEDIA_URL):
                messages.warning(request, "Vous devez vous connecter pour accéder à cette page.")
                return redirect(settings.LOGIN_URL)
        
        response = self.get_response(request)
        return response
