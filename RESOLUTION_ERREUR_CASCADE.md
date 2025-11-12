# Résolution de l'erreur "no such table: main.attribution_attribution_old"

## 🐛 Problème identifié

L'erreur `OperationalError: no such table: main.attribution_attribution_old` se produisait lors de la suppression de cours (Course) car :

1. **Relations CASCADE à 3 niveaux** :
   ```
   Course → Attribution → ScheduleEntry
   Teacher → Attribution → ScheduleEntry
   ```

2. **Comportement de SQLite** :
   - SQLite crée des tables temporaires `_old` lors des opérations CASCADE complexes
   - Ces tables temporaires causent des erreurs si les contraintes FK ne sont pas parfaitement gérées

3. **Solution initiale insuffisante** :
   - Activer `PRAGMA foreign_keys = ON` était nécessaire mais pas suffisant
   - Le simple `transaction.atomic()` ne résolvait pas les CASCADE à plusieurs niveaux

## ✅ Solution implémentée

### Approche : Suppression manuelle dans l'ordre inverse

Au lieu de compter sur CASCADE automatique, **supprimer manuellement les objets liés** dans l'ordre inverse de dépendance :

```python
def delete(self, request, *args, **kwargs):
    obj = self.get_object()
    
    try:
        with transaction.atomic():
            obj = Model.objects.select_for_update().get(pk=obj.pk)
            
            # 1. Niveau 3 (petit-enfant) : ScheduleEntry
            for child in ChildModel.objects.filter(parent=obj):
                GrandChildModel.objects.filter(parent=child).delete()
            
            # 2. Niveau 2 (enfant) : Attribution  
            ChildModel.objects.filter(parent=obj).delete()
            
            # 3. Niveau 1 (parent) : Course/Teacher
            obj.delete()
        
        messages.success(request, "Suppression réussie")
        return redirect(self.success_url)
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect(self.success_url)
```

## 🔧 Fichiers corrigés

### 1. `courses/views.py` - CourseDeleteView

**Avant** (❌ Désactivation des FK) :
```python
with connection.cursor() as cursor:
    cursor.execute('PRAGMA foreign_keys = OFF;')
try:
    result = super().delete(request, *args, **kwargs)
finally:
    cursor.execute('PRAGMA foreign_keys = ON;')
```

**Après** (✅ Suppression manuelle) :
```python
with transaction.atomic():
    course = Course.objects.select_for_update().get(pk=course.pk)
    
    # 1. Supprimer les horaires liés aux attributions
    attributions = Attribution.objects.filter(code_ue=course)
    for attribution in attributions:
        ScheduleEntry.objects.filter(attribution=attribution).delete()
    
    # 2. Supprimer les attributions
    attributions.delete()
    
    # 3. Supprimer le cours
    course.delete()
```

### 2. `teachers/views.py` - TeacherDeleteView

**Même approche** pour la suppression d'enseignants :
```python
with transaction.atomic():
    teacher = Teacher.objects.select_for_update().get(pk=teacher.pk)
    
    # 1. Supprimer les horaires liés aux attributions
    attributions = Attribution.objects.filter(matricule=teacher.matricule)
    for attribution in attributions:
        ScheduleEntry.objects.filter(attribution=attribution).delete()
    
    # 2. Supprimer les attributions
    attributions.delete()
    
    # 3. Supprimer l'enseignant
    teacher.delete()
```

## 📋 Ordre de suppression

Pour **Course** (ID: 1166) :
```
1. ScheduleEntry (horaires liés aux attributions du cours)
2. Attribution (attributions du cours)
3. Course (le cours lui-même)
```

Pour **Teacher** :
```
1. ScheduleEntry (horaires liés aux attributions de l'enseignant)
2. Attribution (attributions de l'enseignant)
3. Teacher (l'enseignant lui-même)
```

## ✅ Avantages de cette approche

1. **Contrôle total** sur l'ordre de suppression
2. **Pas de tables temporaires `_old`** créées par SQLite
3. **Messages informatifs** : "X attribution(s) supprimée(s)"
4. **Transaction atomique** : tout réussit ou tout échoue
5. **Compatible** avec toutes les bases de données

## 🧪 Test

Pour tester la correction :

1. **Supprimer un cours** :
   ```
   http://127.0.0.1:8000/courses/delete/1166/
   ```

2. **Vérifier le message de succès** :
   ```
   "Le cours [CODE] - [INTITULÉ] a été supprimé avec succès. (X attribution(s) supprimée(s))"
   ```

3. **Vérifier les suppressions en cascade** :
   ```python
   # Dans Django shell
   Course.objects.filter(id=1166).exists()  # False
   Attribution.objects.filter(code_ue_id=1166).exists()  # False
   ```

## 📝 Règle générale

**Pour toute suppression avec relations CASCADE à plusieurs niveaux** :

1. Identifier la chaîne de dépendances (A → B → C)
2. Supprimer dans l'ordre inverse (C, B, A)
3. Utiliser `transaction.atomic()`
4. Utiliser `select_for_update()` sur l'objet principal
5. Gérer les exceptions explicitement

## ⚠️ À éviter absolument

❌ **Ne JAMAIS faire** :
```python
# MAUVAIS : Désactive les contraintes FK
cursor.execute('PRAGMA foreign_keys = OFF;')
obj.delete()
cursor.execute('PRAGMA foreign_keys = ON;')
```

✅ **TOUJOURS faire** :
```python
# BON : Suppression manuelle contrôlée
with transaction.atomic():
    obj = Model.objects.select_for_update().get(pk=pk)
    # Supprimer manuellement les objets liés
    for child in obj.children.all():
        child.grandchildren.all().delete()
    obj.children.all().delete()
    obj.delete()
```

## 📚 Documentation

- **Guide complet** : `PATTERN_SUPPRESSION_ROBUSTE.md`
- **Tests** : `test_all_deletions.py`
- **Scripts de diagnostic** : `fix_deletion_issue.py`, `verify_fk_active.py`

---

**Date de résolution** : 5 novembre 2025 - 20:11  
**Erreur corrigée** : `OperationalError: no such table: main.attribution_attribution_old`  
**Méthode** : Suppression manuelle des objets liés dans l'ordre inverse de dépendance  
**Status** : ✅ Résolu
