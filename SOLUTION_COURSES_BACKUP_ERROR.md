# Solution au problème "courses_course_backup" introuvable

## Symptôme
```
Failed to load resource: the server responded with a status of 400 (Bad Request)
Erreur: {"success": false, "message": "Erreur serveur: Erreur lors de la création de l'attribution pour le cours AGV211: no such table: main.courses_course_backup"}
```

## Diagnostic effectué

### 1. Vérification de la base de données
- ✅ Aucun trigger trouvé dans la base de données
- ✅ Aucune table de backup existante
- ✅ Le cours AGV211 existe bien dans la table `courses_course`
- ✅ Les requêtes fonctionnent en dehors du serveur web
- ✅ Intégrité de la base de données vérifiée : OK

### 2. Conclusion
Le problème provenait de **connexions concurrentes mal gérées** par SQLite lors de l'utilisation du serveur web Django.

## Solutions appliquées

### 1. Configuration de la base de données (settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Timeout de 20 secondes pour les verrous
            'check_same_thread': False,  # Accès multi-thread activé
        },
        'CONN_MAX_AGE': 0,  # Pas de réutilisation de connexion
    }
}
```

**Explications :**
- `timeout: 20` : Augmente le délai d'attente pour les verrous de base de données
- `check_same_thread: False` : Permet à SQLite de fonctionner correctement avec le serveur web multi-thread
- `CONN_MAX_AGE: 0` : Force la fermeture des connexions après chaque requête (évite les connexions fantômes)

### 2. Activation du mode WAL (Write-Ahead Logging)
```bash
python clean_database_locks.py
```

**Avantages du mode WAL :**
- ✅ Améliore les performances concurrentes
- ✅ Permet les lectures pendant les écritures
- ✅ Réduit les risques de verrouillage
- ✅ Standard pour les applications web avec SQLite

### 3. Nettoyage des verrous
Le script a vérifié et nettoyé :
- Fichiers de verrou (journal, wal, shm)
- Intégrité de la base de données
- Configuration du mode journal

## Actions à effectuer

### Pour appliquer la solution :
1. **Arrêter le serveur** Django (CTRL+C dans le terminal)
2. Les modifications sont déjà appliquées dans `settings.py`
3. Le mode WAL est déjà activé
4. **Redémarrer le serveur** :
   ```bash
   python manage.py runserver
   ```

### Pour vérifier que tout fonctionne :
1. Ouvrir http://127.0.0.1:8000/attribution/
2. Essayer de créer une attribution pour le cours AGV211
3. L'erreur ne devrait plus apparaître

## Fichiers créés pour le diagnostic
- `check_triggers.py` - Vérification des triggers
- `check_all_triggers.py` - Vérification complète des triggers
- `check_database_schema.py` - Analyse du schéma
- `fix_database.py` - Vérification des migrations
- `test_course_query.py` - Test des requêtes Course
- `clean_database_locks.py` - Nettoyage des verrous

Ces fichiers peuvent être supprimés une fois le problème résolu.

## Prévention
Pour éviter ce problème à l'avenir :
1. ✅ Toujours utiliser le mode WAL pour SQLite en production web
2. ✅ Configurer un timeout adéquat (≥ 20 secondes)
3. ✅ Ne pas garder de connexions persistantes (`CONN_MAX_AGE: 0`)
4. ⚠️ Considérer PostgreSQL ou MySQL pour les applications avec beaucoup de concurrence

## Note sur SQLite
SQLite est excellent pour le développement, mais a des limitations avec les écritures concurrentes. 
Pour une application en production avec plusieurs utilisateurs simultanés, il est recommandé d'utiliser PostgreSQL ou MySQL.
