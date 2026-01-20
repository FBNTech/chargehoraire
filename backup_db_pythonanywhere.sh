#!/bin/bash
# Script de sauvegarde automatique de la base de données sur PythonAnywhere
# À placer dans /home/chargehoraire/chargehoraire/backup_db.sh
# À configurer dans les Scheduled Tasks de PythonAnywhere

# Configuration
PROJECT_DIR="/home/chargehoraire/chargehoraire"
BACKUP_DIR="/home/chargehoraire/db_backups"
DB_FILE="$PROJECT_DIR/db.sqlite3"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sqlite3"

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p $BACKUP_DIR

# Copier la base de données
cp $DB_FILE $BACKUP_FILE

# Compresser la sauvegarde pour économiser l'espace
gzip $BACKUP_FILE

# Garder uniquement les 30 dernières sauvegardes (1 mois)
cd $BACKUP_DIR
ls -t db_backup_*.sqlite3.gz | tail -n +31 | xargs -r rm

echo "$(date): Sauvegarde créée: $BACKUP_FILE.gz" >> $BACKUP_DIR/backup.log
