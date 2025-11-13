#!/usr/bin/env bash
# Script pour importer les données sur Render

echo "=== Import des données ==="
echo "Assurez-vous d'avoir uploadé data_backup.json sur Render"
echo ""

# Supprimer les anciennes données (optionnel)
# python manage.py flush --no-input

# Importer les données
python manage.py loaddata data_backup.json

echo ""
echo "=== Import terminé ! ==="
