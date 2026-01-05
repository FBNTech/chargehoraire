#!/bin/bash

# Script de mise à jour automatique sur PythonAnywhere
# Usage: ./update_pythonanywhere.sh

echo "=========================================="
echo "Mise à jour de l'application sur PythonAnywhere"
echo "=========================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Aller dans le répertoire du projet
echo -e "${YELLOW}[1/7] Navigation vers le répertoire du projet...${NC}"
cd ~/chargehoraire || { echo -e "${RED}Erreur: Impossible d'accéder au répertoire ~/chargehoraire${NC}"; exit 1; }
echo -e "${GREEN}✓ Répertoire trouvé${NC}"
echo ""

# Récupérer les dernières modifications depuis GitHub
echo -e "${YELLOW}[2/7] Récupération des modifications depuis GitHub...${NC}"
git pull origin main || { echo -e "${RED}Erreur lors du git pull${NC}"; exit 1; }
echo -e "${GREEN}✓ Code mis à jour${NC}"
echo ""

# Activer l'environnement virtuel
echo -e "${YELLOW}[3/7] Activation de l'environnement virtuel...${NC}"
source ~/.virtualenvs/chargehoraire/bin/activate || { echo -e "${RED}Erreur: Impossible d'activer l'environnement virtuel${NC}"; exit 1; }
echo -e "${GREEN}✓ Environnement virtuel activé${NC}"
echo ""

# Installer/mettre à jour les dépendances
echo -e "${YELLOW}[4/7] Installation des dépendances...${NC}"
pip install -r requirements.txt --quiet || { echo -e "${RED}Erreur lors de l'installation des dépendances${NC}"; exit 1; }
echo -e "${GREEN}✓ Dépendances installées${NC}"
echo ""

# Appliquer les migrations
echo -e "${YELLOW}[5/7] Application des migrations de base de données...${NC}"
python manage.py migrate || { echo -e "${RED}Erreur lors des migrations${NC}"; exit 1; }
echo -e "${GREEN}✓ Migrations appliquées${NC}"
echo ""

# Collecter les fichiers statiques
echo -e "${YELLOW}[6/7] Collection des fichiers statiques...${NC}"
python manage.py collectstatic --noinput || { echo -e "${RED}Erreur lors de la collecte des fichiers statiques${NC}"; exit 1; }
echo -e "${GREEN}✓ Fichiers statiques collectés${NC}"
echo ""

# Recharger l'application web
echo -e "${YELLOW}[7/7] Rechargement de l'application web...${NC}"
touch /var/www/phukuta_pythonanywhere_com_wsgi.py || { echo -e "${RED}Erreur lors du rechargement${NC}"; exit 1; }
echo -e "${GREEN}✓ Application rechargée${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Mise à jour terminée avec succès!${NC}"
echo "=========================================="
echo ""
echo "Votre application est maintenant à jour sur:"
echo "https://phukuta.pythonanywhere.com"
echo ""
