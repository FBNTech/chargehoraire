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
    from PIL import Image as PILImage
    
    # Construire le chemin absolu vers l'image dans le dossier static
    image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'entete.PNG')
    
    # Vérifier si le fichier image existe avant de l'utiliser
    if os.path.exists(image_path):
        # Lire les dimensions originales de l'image
        try:
            with PILImage.open(image_path) as img:
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
            
            # Définir la largeur souhaitée et calculer la hauteur proportionnelle
            desired_width = 6.5 * inch  # Largeur réduite pour l'en-tête
            calculated_height = desired_width / aspect_ratio
            
            # Créer l'image avec les bonnes proportions
            header_image = Image(image_path, width=desired_width, height=calculated_height)
            return header_image
        except Exception as e:
            # En cas d'erreur, utiliser des dimensions par défaut raisonnables
            header_image = Image(image_path, width=7*inch, height=1.0*inch)
            return header_image
    else:
        # Retourner un spacer vide si l'image n'est pas trouvée
        return Spacer(1, 1) # Retourne un élément vide pour éviter une erreur
