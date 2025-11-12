# Charge Horaire - Système de Gestion des Charges Horaires

Application Django pour la gestion des charges horaires des enseignants.

## 📋 Prérequis

- Python 3.11+
- PostgreSQL (pour production)
- Git
- Compte Heroku

## 🚀 Déploiement sur Heroku

### 1. Installation de Heroku CLI

Téléchargez et installez Heroku CLI depuis : https://devcenter.heroku.com/articles/heroku-cli

### 2. Connexion à Heroku

```bash
heroku login
```

### 3. Créer une application Heroku

```bash
# Créer une nouvelle application (le nom doit être unique)
heroku create votre-nom-app-charge-horaire

# Ou laisser Heroku générer un nom automatiquement
heroku create
```

### 4. Ajouter PostgreSQL

```bash
# Ajouter l'addon PostgreSQL (plan gratuit)
heroku addons:create heroku-postgresql:essential-0
```

### 5. Configurer les variables d'environnement

```bash
# Générer une nouvelle SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configurer les variables
heroku config:set SECRET_KEY="votre-secret-key-generee"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=".herokuapp.com"
heroku config:set CSRF_TRUSTED_ORIGINS="https://votre-app.herokuapp.com"
```

### 6. Initialiser Git (si pas déjà fait)

```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### 7. Déployer sur Heroku

```bash
# Ajouter le remote Heroku
heroku git:remote -a votre-nom-app

# Pousser le code
git push heroku main

# Si votre branche s'appelle master
git push heroku master
```

### 8. Exécuter les migrations

```bash
heroku run python manage.py migrate
```

### 9. Créer un superutilisateur

```bash
heroku run python manage.py createsuperuser
```

### 10. Collecter les fichiers statiques

```bash
heroku run python manage.py collectstatic --noinput
```

### 11. Ouvrir l'application

```bash
heroku open
```

## 🔧 Commandes utiles

### Voir les logs

```bash
heroku logs --tail
```

### Redémarrer l'application

```bash
heroku restart
```

### Accéder au shell Django

```bash
heroku run python manage.py shell
```

### Accéder à la base de données PostgreSQL

```bash
heroku pg:psql
```

### Voir les variables d'environnement

```bash
heroku config
```

### Mettre à jour l'application

```bash
git add .
git commit -m "Description des modifications"
git push heroku main
```

## 📊 Monitoring

### Voir l'état de l'application

```bash
heroku ps
```

### Voir les métriques

```bash
heroku logs --tail
```

## 🔒 Sécurité

- ✅ SECRET_KEY configurée via variable d'environnement
- ✅ DEBUG=False en production
- ✅ ALLOWED_HOSTS configuré
- ✅ CSRF protection activée
- ✅ HTTPS forcé en production
- ✅ Cookies sécurisés
- ✅ Headers de sécurité configurés

## 📦 Structure du projet

```
chargehoraire/
├── config/              # Configuration Django
├── accounts/            # Gestion des utilisateurs
├── attribution/         # Gestion des attributions
├── courses/             # Gestion des cours
├── teachers/            # Gestion des enseignants
├── tracking/            # Suivi et dashboard
├── reglage/             # Paramètres et réglages
├── static/              # Fichiers statiques
├── templates/           # Templates HTML
├── Procfile             # Configuration Heroku
├── runtime.txt          # Version Python
└── requirements.txt     # Dépendances Python
```

## 🐛 Dépannage

### Erreur de migration

```bash
heroku run python manage.py migrate --run-syncdb
```

### Erreur de collecte des fichiers statiques

```bash
heroku config:set DISABLE_COLLECTSTATIC=1
git push heroku main
heroku run python manage.py collectstatic --noinput
heroku config:unset DISABLE_COLLECTSTATIC
```

### Réinitialiser la base de données

```bash
heroku pg:reset DATABASE_URL
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## 📝 Notes importantes

1. **Base de données** : SQLite en local, PostgreSQL sur Heroku
2. **Fichiers média** : Utilisez un service comme AWS S3 pour les fichiers uploadés en production
3. **Email** : Configurez un service d'email (SendGrid, Mailgun) pour la production
4. **Backup** : Configurez des backups réguliers de la base de données

## 🔗 Liens utiles

- [Documentation Heroku Django](https://devcenter.heroku.com/articles/django-app-configuration)
- [Documentation Django](https://docs.djangoproject.com/)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

## 📞 Support

Pour toute question ou problème, consultez les logs avec `heroku logs --tail`
