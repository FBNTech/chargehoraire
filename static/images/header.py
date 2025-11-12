"""
Module pour générer l'en-tête institutionnelle pour les PDF
"""
import os
from reportlab.lib.units import inch
from reportlab.platypus import Image, Spacer
from django.conf import settings

def create_header_table():
    """
    Crée une image d'en-tête à partir du fichier local entete.PNG
    """
    # Construire le chemin absolu vers l'image dans le dossier static
    image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    
    # Vérifier si le fichier image existe avant de l'utiliser
    if os.path.exists(image_path):
        # Utiliser directement le fichier image local
        header_image = Image(image_path, width=10*inch, height=1*inch)
        return header_image
    else:
        # Retourner un spacer vide si l'image n'est pas trouvée
        return Spacer(1, 1) # Retourne un élément vide pour éviter une erreur
