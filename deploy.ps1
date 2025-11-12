# Script de déploiement rapide sur Heroku (PowerShell)
# Usage: .\deploy.ps1 "message de commit"

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

Write-Host "🚀 Déploiement sur Heroku" -ForegroundColor Blue

# Ajouter tous les fichiers
Write-Host "📦 Ajout des fichiers..." -ForegroundColor Blue
git add .

# Commit
Write-Host "💾 Commit des modifications..." -ForegroundColor Blue
git commit -m $CommitMessage

# Push vers Heroku
Write-Host "☁️  Push vers Heroku..." -ForegroundColor Blue
try {
    git push heroku main
} catch {
    git push heroku master
}

# Exécuter les migrations
Write-Host "🔄 Exécution des migrations..." -ForegroundColor Blue
heroku run python manage.py migrate

# Collecter les fichiers statiques
Write-Host "📁 Collecte des fichiers statiques..." -ForegroundColor Blue
heroku run python manage.py collectstatic --noinput

# Redémarrer l'application
Write-Host "🔄 Redémarrage de l'application..." -ForegroundColor Blue
heroku restart

Write-Host "✅ Déploiement terminé avec succès!" -ForegroundColor Green
Write-Host "🌐 Ouvrir l'application..." -ForegroundColor Blue
heroku open
