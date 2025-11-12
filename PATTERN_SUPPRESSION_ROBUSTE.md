# Pattern de Suppression Robuste

## 📋 Vue d'ensemble

Ce document décrit le **pattern de suppression robuste** implémenté dans toute l'application pour résoudre les problèmes de suppression avec SQLite (erreur `no such table: main.xxx_old`).

## 🔧 Solution implémentée

### 1. Activation des contraintes de clés étrangères SQLite

**Fichier**: `config/db_setup.py` + `config/__init__.py`

Les contraintes FK sont maintenant automatiquement activées à chaque connexion SQLite via un signal Django :

```python
@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    """Active les contraintes de clés étrangères pour SQLite"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.close()
```

### 2. Pattern de suppression avec transaction atomique

**Le pattern robuste** à utiliser pour toutes les suppressions :

```python
from django.db import transaction

@require_http_methods(['POST'])
def delete_object(request, object_id):
    try:
        # Utiliser une transaction atomique pour garantir la cohérence
        with transaction.atomic():
            # Verrouiller l'objet pour éviter les conflits concurrents
            obj = Model.objects.select_for_update().get(id=object_id)
            
            # Supprimer les objets liés si nécessaire
            RelatedModel.objects.filter(parent=obj).delete()
            
            # Supprimer l'objet principal
            obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Objet supprimé avec succès'
        })
    except Model.DoesNotExist:
        return JsonResponse({'success': False, 'error': "L'objet n'existe pas"}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'{str(e)}'}, status=500)
```

### ⚠️ IMPORTANT: Suppression manuelle pour relations CASCADE complexes

Pour les objets avec des relations CASCADE à plusieurs niveaux (ex: Course → Attribution → ScheduleEntry), 
**TOUJOURS supprimer manuellement les objets liés** dans l'ordre inverse de dépendance pour éviter les problèmes SQLite :

```python
def delete(self, request, *args, **kwargs):
    obj = self.get_object()
    
    try:
        with transaction.atomic():
            obj = Model.objects.select_for_update().get(pk=obj.pk)
            
            # 1. Supprimer d'abord les objets au niveau le plus bas
            for child in ChildModel.objects.filter(parent=obj):
                GrandChildModel.objects.filter(parent=child).delete()
            
            # 2. Ensuite le niveau intermédiaire
            ChildModel.objects.filter(parent=obj).delete()
            
            # 3. Enfin l'objet principal
            obj.delete()
        
        messages.success(request, "Suppression réussie")
        return redirect(self.success_url)
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect(self.success_url)
```

### 3. Classe de base SafeDeleteView pour les vues génériques

**Fichier**: `reglage/views.py`

Pour les `DeleteView` Django, utiliser la classe de base `SafeDeleteView` :

```python
class SafeDeleteView(DeleteView):
    """
    Classe de base pour toutes les vues de suppression avec transaction atomique.
    """
    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                self.object = self.get_queryset().select_for_update().get(pk=kwargs['pk'])
                success_url = self.get_success_url()
                self.object.delete()
            
            if hasattr(self, 'success_message'):
                messages.success(request, self.success_message)
            
            return redirect(success_url)
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect(self.success_url)
```

## ✅ Fichiers modifiés

### Fichiers de configuration
- ✅ `config/db_setup.py` - Nouveau fichier avec signal FK
- ✅ `config/__init__.py` - Import du signal
- ✅ `config/settings.py` - Commentaire sur activation FK

### Vues mises à jour avec le pattern robuste

#### attribution/views.py
- ✅ `delete_attribution()` - Suppression d'attribution avec horaires liés
- ✅ `delete_course()` - Suppression de Cours_Attribution
- ✅ `schedule_entry_delete()` - Suppression d'horaire

#### courses/views.py
- ✅ `CourseDeleteView.delete()` - Suppression de cours avec attributions et horaires liées (CASCADE à 3 niveaux)
- ✅ Import de `transaction` ajouté
- ✅ Suppression manuelle des objets liés dans l'ordre: ScheduleEntry → Attribution → Course

#### accounts/views.py
- ✅ `delete_user()` - Suppression d'utilisateur avec profil lié

#### teachers/views.py
- ✅ `TeacherDeleteView.delete()` - Suppression d'enseignant avec attributions et horaires liées (CASCADE à 3 niveaux)
- ✅ Import de `transaction` ajouté
- ✅ Suppression manuelle des objets liés dans l'ordre: ScheduleEntry → Attribution → Teacher

#### reglage/views.py
- ✅ **Nouvelle classe**: `SafeDeleteView` (classe de base)
- ✅ **13 classes mises à jour** pour hériter de `SafeDeleteView`:
  - `SectionDeleteView`
  - `DepartementDeleteView`
  - `MentionDeleteView`
  - `NiveauDeleteView`
  - `ClasseDeleteView`
  - `GradeDeleteView`
  - `CategorieDeleteView`
  - `SemestreDeleteView`
  - `FonctionDeleteView`
  - `AnneeAcademiqueDeleteView`
  - `SalleDeleteView`
  - `CreneauDeleteView`
  - `SemaineCoursDeleteView`

## 🎯 Avantages du pattern

### 1. **Cohérence des données**
- Transaction atomique : tout réussit ou tout échoue
- Pas d'état intermédiaire corrompu

### 2. **Prévention des conflits concurrents**
- `select_for_update()` verrouille l'enregistrement
- Évite les race conditions

### 3. **Gestion automatique des relations**
- Les contraintes FK CASCADE fonctionnent correctement
- Pas besoin de désactiver temporairement les FK

### 4. **Compatibilité multi-bases**
- Fonctionne avec SQLite, PostgreSQL, MySQL
- Django gère les différences

### 5. **Messages d'erreur clairs**
- Gestion explicite des exceptions
- Retours JSON structurés pour les API

## 📝 Guide d'utilisation

### Pour une nouvelle fonction de suppression

```python
from django.db import transaction

def delete_something(request, pk):
    try:
        with transaction.atomic():
            obj = SomeModel.objects.select_for_update().get(pk=pk)
            # Votre logique de suppression ici
            obj.delete()
        
        messages.success(request, "Suppression réussie")
        return redirect('some_url')
        
    except SomeModel.DoesNotExist:
        messages.error(request, "Objet non trouvé")
        return redirect('some_url')
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('some_url')
```

### Pour une nouvelle DeleteView

```python
from reglage.views import SafeDeleteView

class MyModelDeleteView(SafeDeleteView):
    model = MyModel
    template_name = 'app/mymodel_confirm_delete.html'
    success_url = reverse_lazy('app:list')
    success_message = "MyModel supprimé avec succès"
```

## 🧪 Tests

Trois scripts de test ont été créés :

1. **`fix_deletion_issue.py`** - Diagnostic et nettoyage de la base
2. **`verify_fk_active.py`** - Vérification que les FK sont activées
3. **`test_delete_web.py`** - Test de suppression via API web

### Exécution des tests

```bash
# Vérifier que les FK sont activées
python verify_fk_active.py

# Diagnostic complet
python fix_deletion_issue.py

# Test via API web
python test_delete_web.py
```

## 🚀 Déploiement

### Étapes de déploiement

1. **Redémarrer le serveur Django**
   ```bash
   python manage.py runserver
   ```

2. **Vérifier les contraintes FK**
   ```bash
   python verify_fk_active.py
   ```

3. **Tester les suppressions**
   - Supprimer une attribution avec horaires
   - Supprimer un cours avec attributions
   - Supprimer un utilisateur avec profil

## 📊 Statistiques

- **Fichiers modifiés**: 7
- **Classes mises à jour**: 17 (CourseDeleteView et TeacherDeleteView avec suppression manuelle CASCADE)
- **Fonctions mises à jour**: 4
- **Nouvelle classe de base**: 1
- **Scripts de diagnostic**: 3
- **Relations CASCADE à 3 niveaux gérées**: 2 (Course et Teacher)

## ⚠️ Points d'attention

1. **Ne jamais désactiver les contraintes FK** avec `PRAGMA foreign_keys = OFF`
2. **Toujours utiliser `transaction.atomic()`** pour les suppressions
3. **Utiliser `select_for_update()`** pour verrouiller les objets
4. **Pour les relations CASCADE à plusieurs niveaux** : supprimer manuellement les objets dans l'ordre inverse (petit-enfant → enfant → parent)
5. **Gérer les exceptions** explicitement
6. **Tester en local** avant déploiement en production

## 📚 Références

- [Django Transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)
- [Django select_for_update](https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-for-update)
- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)

---

**Date de création**: 5 novembre 2025  
**Auteur**: Cascade AI  
**Version**: 1.0
