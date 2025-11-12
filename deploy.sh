#!/bin/bash

# Script de déploiement rapide sur Heroku
# Usage: ./deploy.sh "message de commit"

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Déploiement sur Heroku${NC}"

# Vérifier si un message de commit est fourni
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erreur: Veuillez fournir un message de commit${NC}"
    echo "Usage: ./deploy.sh \"votre message de commit\""
    exit 1
fi

# Ajouter tous les fichiers
echo -e "${BLUE}📦 Ajout des fichiers...${NC}"
git add .

# Commit
echo -e "${BLUE}💾 Commit des modifications...${NC}"
git commit -m "$1"

# Push vers Heroku
echo -e "${BLUE}☁️  Push vers Heroku...${NC}"
git push heroku main || git push heroku master

# Exécuter les migrations
echo -e "${BLUE}🔄 Exécution des migrations...${NC}"
heroku run python manage.py migrate

# Collecter les fichiers statiques
echo -e "${BLUE}📁 Collecte des fichiers statiques...${NC}"
heroku run python manage.py collectstatic --noinput

# Redémarrer l'application
echo -e "${BLUE}🔄 Redémarrage de l'application...${NC}"
heroku restart

echo -e "${GREEN}✅ Déploiement terminé avec succès!${NC}"
echo -e "${BLUE}🌐 Ouvrir l'application...${NC}"
heroku open
