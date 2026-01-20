#!/bin/bash
# Script de sauvegarde journalière depuis PythonAnywhere vers votre machine locale
# À exécuter sur votre machine Windows via WSL ou Git Bash

# Configuration
PYTHONANYWHERE_USER="chargehoraire"
PYTHONANYWHERE_HOST="ssh.pythonanywhere.com"
REMOTE_DB="/home/chargehoraire/chargehoraire/db.sqlite3"
LOCAL_BACKUP_DIR="d:/chargehoraire/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$LOCAL_BACKUP_DIR/db_backup_$DATE.sqlite3"

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p "$LOCAL_BACKUP_DIR"

# Télécharger la base de données depuis PythonAnywhere
scp $PYTHONANYWHERE_USER@$PYTHONANYWHERE_HOST:$REMOTE_DB "$BACKUP_FILE"

# Compresser la sauvegarde
gzip "$BACKUP_FILE"

# Garder uniquement les 30 dernières sauvegardes (1 mois)
cd "$LOCAL_BACKUP_DIR"
ls -t db_backup_*.sqlite3.gz | tail -n +31 | xargs -r rm

echo "Sauvegarde créée: $BACKUP_FILE.gz"
