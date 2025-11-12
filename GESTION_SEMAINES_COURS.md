# 📅 Gestion des Semaines de Cours

## ✅ **Nouvelle Fonctionnalité Ajoutée**

Un nouveau module de gestion des **Semaines de Cours** a été ajouté dans la page Réglage avec :
- Dates de début et fin pour chaque semaine
- Numérotation des semaines (1, 2, 3...)
- Statut "En cours" (une seule semaine peut être en cours à la fois)
- Lien avec l'année académique
- Filtrage par année académique

---

## 🎯 **Modèle SemaineCours**

### Champs

| Champ | Type | Description |
|-------|------|-------------|
| `numero_semaine` | Integer | Numéro de la semaine (1, 2, 3...) |
| `date_debut` | Date | Date de début de la semaine |
| `date_fin` | Date | Date de fin de la semaine |
| `designation` | CharField | Description (ex: "Semaine 1 du 1er semestre") |
| `est_en_cours` | Boolean | Marquer comme semaine en cours |
| `annee_academique` | CharField | Année académique (ex: "2024-2025") |
| `remarques` | TextField | Remarques optionnelles |

### Contraintes
- **unique_together** : `(numero_semaine, annee_academique)` - Pas de doublon
- **Automatisme** : Quand une semaine est marquée "en cours", les autres sont désactivées

### Méthodes
```python
def __str__(self):
    # Retourne: "Semaine 1 : 14/10 - 20/10 (En cours)"
    
def get_periode(self):
    # Retourne: "14/10/2024 - 20/10/2024"
```

---

## 🎨 **Interface Utilisateur**

### Page Principale Réglage

**Nouvelle carte ajoutée** :
```
┌────────────────────────────────────┐
│   🗓️ Semaines de Cours              │
│                                    │
│   Gérer les semaines de cours      │
│   avec dates de début et fin       │
│                                    │
│        [⚙️ Gérer]                   │
└────────────────────────────────────┘
```

**Couleur** : Rouge (border-danger)
**Icône** : `fa-calendar-week`

---

### Page Liste des Semaines

**URL** : `/reglage/semaines/`

**Fonctionnalités** :
- ✅ Tableau avec toutes les semaines
- ✅ Filtre par année académique
- ✅ Badge "En cours" rouge pour la semaine active
- ✅ Affichage de la période complète
- ✅ Actions : Modifier, Supprimer

**Colonnes du tableau** :
1. N° (numéro de semaine)
2. Désignation
3. Date Début
4. Date Fin
5. Période (format complet)
6. Année Académique
7. Statut (En cours / Inactive)
8. Actions

**Exemple de ligne** :
```
┌──┬──────────────────────┬───────────┬──────────┬────────────────────┬────────┬──────────┬─────────┐
│1 │Semaine 1 du 1er sem. │14/10/2024 │20/10/2024│14/10/2024-20/10/24 │2024-25 │★ En cours│✏️ 🗑️   │
└──┴──────────────────────┴───────────┴──────────┴────────────────────┴────────┴──────────┴─────────┘
```

---

### Formulaire Création/Modification

**URL Création** : `/reglage/semaines/create/`
**URL Modification** : `/reglage/semaines/<id>/update/`

**Champs** :
```
┌─ Numéro de Semaine ────────┐
│ [  1  ]                    │
│ Ex: 1, 2, 3...             │
└────────────────────────────┘

┌─ Année Académique ─────────┐
│ [2024-2025]                │
│ Ex: 2024-2025              │
└────────────────────────────┘

┌─ Désignation ──────────────┐
│ [Semaine 1 du 1er semestre]│
│ Ex: Semaine 1 du 1er sem.  │
└────────────────────────────┘

┌─ Date Début ───┬─ Date Fin ─┐
│ [14/10/2024]   │ [20/10/2024]│
└────────────────┴─────────────┘

┌─ Remarques ────────────────┐
│ [                          ]│
│ [                          ]│
└────────────────────────────┘

☑️ Marquer comme semaine en cours
   Si cochée, les autres seront
   automatiquement désactivées.

[⬅️ Annuler]    [💾 Enregistrer]
```

---

## 🔄 **Workflow d'Utilisation**

### Étape 1 : Créer les semaines du semestre

1. Aller sur `/reglage/semaines/`
2. Cliquer "➕ Nouvelle Semaine"
3. Remplir :
   - Numéro : `1`
   - Désignation : `Semaine 1 du 1er semestre`
   - Date début : `14/10/2024`
   - Date fin : `20/10/2024`
   - Année : `2024-2025`
   - ☑️ Cocher "En cours" si c'est la semaine actuelle
4. Enregistrer

**Répéter pour toutes les semaines du semestre**

---

### Étape 2 : Marquer la semaine en cours

**Deux méthodes** :

#### Méthode A : À la création
- Cocher "En cours" lors de la création de la semaine actuelle

#### Méthode B : Par modification
1. Aller sur `/reglage/semaines/`
2. Cliquer ✏️ sur la semaine à activer
3. Cocher "En cours"
4. Enregistrer

**Résultat** : Les autres semaines sont automatiquement désactivées

---

### Étape 3 : Filtrer par année

1. Sur la page liste, utiliser le filtre "Année académique"
2. Sélectionner l'année (ex: 2024-2025)
3. Cliquer "🔍 Filtrer"

---

## 📊 **Exemples d'Utilisation**

### Exemple 1 : Semestre complet (16 semaines)

```
Semaine  | Période               | Statut
---------|----------------------|----------
1        | 14/10/24 - 20/10/24  | En cours ★
2        | 21/10/24 - 27/10/24  | Inactive
3        | 28/10/24 - 03/11/24  | Inactive
4        | 04/11/24 - 10/11/24  | Inactive
...      | ...                  | ...
16       | 27/01/25 - 02/02/25  | Inactive
```

---

### Exemple 2 : Plusieurs années académiques

```
Année      | Semaines
-----------|----------
2024-2025  | 16 semaines
2023-2024  | 16 semaines
2022-2023  | 16 semaines
```

**Filtrage** : Voir uniquement les semaines d'une année

---

## 🎯 **Fonctionnalités Avancées**

### 1. **Une Seule Semaine "En Cours"**

**Logique métier** :
```python
def save(self, *args, **kwargs):
    if self.est_en_cours:
        SemaineCours.objects.filter(est_en_cours=True).update(est_en_cours=False)
    super().save(*args, **kwargs)
```

**Avantage** : Garantit la cohérence des données

---

### 2. **Contrainte d'Unicité**

```python
unique_together = [('numero_semaine', 'annee_academique')]
```

**Empêche** :
- Deux "Semaine 1" pour la même année
- Permet : "Semaine 1" pour 2024-2025 ET "Semaine 1" pour 2025-2026

---

### 3. **Affichage de la Période**

**Méthode** : `get_periode()`
```python
"14/10/2024 - 20/10/2024"
```

**Utilisation** : Affichage rapide de la période dans les tableaux

---

## 📂 **Fichiers Créés/Modifiés**

### Backend

#### `reglage/models.py`
- ✅ Nouveau modèle `SemaineCours`
- ✅ Champs : numero_semaine, date_debut, date_fin, designation, etc.
- ✅ Méthode `save()` pour gestion "en cours"
- ✅ Méthode `get_periode()`

#### `reglage/views.py`
- ✅ `SemaineCoursListView` : Liste avec filtrage
- ✅ `SemaineCoursCreateView` : Création
- ✅ `SemaineCoursUpdateView` : Modification
- ✅ `SemaineCoursDeleteView` : Suppression

#### `reglage/urls.py`
- ✅ 4 nouvelles URLs (list, create, update, delete)

---

### Frontend

#### `reglage/templates/reglage/gestion_entites.html`
- ✅ Nouvelle carte "Semaines de Cours" (rouge)

#### `reglage/templates/reglage/semaine_list.html`
- ✅ Tableau des semaines
- ✅ Filtre par année académique
- ✅ Badge "En cours"

#### `reglage/templates/reglage/semaine_form.html`
- ✅ Formulaire complet
- ✅ Aide contextuelle
- ✅ Validation Bootstrap

#### `reglage/templates/reglage/semaine_confirm_delete.html`
- ✅ Page de confirmation de suppression

---

### Migration

#### `reglage/migrations/0004_semainecours.py`
- ✅ Création de la table SemaineCours

---

## 🧪 **Tests**

### Script de test : `test_semaines_cours.py`

**Tests effectués** :
1. ✅ Création de 3 semaines
2. ✅ Vérification semaine en cours
3. ✅ Changement de semaine en cours (automatisme)
4. ✅ Listage de toutes les semaines
5. ✅ Filtrage par année académique
6. ✅ Méthode get_periode()
7. ✅ Vérification des URLs

**Résultats** :
```
✓ 3 semaines créées
✓ Semaine en cours : Semaine 2
✓ Une seule semaine en cours (validation OK)
✓ Toutes les URLs fonctionnelles
```

---

## 🔗 **URLs**

| Action | URL | Méthode |
|--------|-----|---------|
| Liste | `/reglage/semaines/` | GET |
| Créer | `/reglage/semaines/create/` | GET/POST |
| Modifier | `/reglage/semaines/<id>/update/` | GET/POST |
| Supprimer | `/reglage/semaines/<id>/delete/` | GET/POST |

---

## 💡 **Cas d'Usage**

### Cas 1 : Planification Semestrielle

**Besoin** : Planifier 16 semaines de cours

**Solution** :
1. Créer 16 entrées dans Semaines de Cours
2. Numéroter de 1 à 16
3. Définir les dates de début/fin de chaque semaine
4. Marquer la semaine actuelle comme "en cours"

---

### Cas 2 : Suivi de Progression

**Besoin** : Savoir quelle est la semaine en cours

**Solution** :
- Filtrer les semaines avec `est_en_cours=True`
- Afficher dans un dashboard
- Mettre à jour chaque semaine

---

### Cas 3 : Historique Multi-Années

**Besoin** : Conserver l'historique des années précédentes

**Solution** :
- Créer des semaines pour chaque année académique
- Utiliser le filtre année pour naviguer
- Contrainte d'unicité évite les doublons

---

## 🎯 **Intégration Future**

### Possibilités d'intégration

1. **Page Horaires** : Filtrer les horaires par semaine
2. **Dashboard** : Afficher la semaine en cours
3. **Statistiques** : Nombre de cours par semaine
4. **Rapports** : Génération de rapports hebdomadaires

---

## 📝 **Exemples de Données**

### Premier Semestre 2024-2025

```sql
INSERT INTO reglage_semainecours (numero_semaine, date_debut, date_fin, designation, annee_academique, est_en_cours)
VALUES
  (1, '2024-10-14', '2024-10-20', 'Semaine 1 du 1er semestre', '2024-2025', true),
  (2, '2024-10-21', '2024-10-27', 'Semaine 2 du 1er semestre', '2024-2025', false),
  (3, '2024-10-28', '2024-11-03', 'Semaine 3 du 1er semestre', '2024-2025', false),
  (4, '2024-11-04', '2024-11-10', 'Semaine 4 du 1er semestre', '2024-2025', false),
  (5, '2024-11-11', '2024-11-17', 'Semaine 5 du 1er semestre', '2024-2025', false),
  ...
```

---

## ⚠️ **Points d'Attention**

### 1. Contrainte d'Unicité
❌ **Impossible** : Deux "Semaine 1" pour "2024-2025"
✅ **Possible** : "Semaine 1" pour "2024-2025" ET "Semaine 1" pour "2025-2026"

### 2. Semaine En Cours
- Une seule semaine peut être "en cours" à la fois
- Automatisme : Les autres sont désactivées automatiquement

### 3. Dates Cohérentes
- Vérifier que date_fin > date_debut
- Éviter les chevauchements de dates (non vérifié par le système)

---

## 🎓 **Formation Utilisateur**

### Message pour les utilisateurs
```
📢 NOUVELLE FONCTIONNALITÉ : SEMAINES DE COURS

Vous pouvez maintenant gérer les semaines de cours avec :

✨ FONCTIONNALITÉS :
• Numérotation des semaines (1, 2, 3...)
• Dates de début et fin pour chaque semaine
• Marquage de la semaine "en cours"
• Filtrage par année académique

🚀 COMMENT L'UTILISER ?

1. Allez dans Réglage → Semaines de Cours
2. Créez les semaines de votre semestre
3. Marquez la semaine actuelle comme "en cours"
4. Mettez à jour chaque semaine

🔗 Accès : /reglage/semaines/
```

---

## 📊 **Statistiques d'Implémentation**

- ✅ 1 nouveau modèle
- ✅ 4 nouvelles vues CRUD
- ✅ 4 nouvelles URLs
- ✅ 3 nouveaux templates
- ✅ 1 nouvelle carte dans page Réglage
- ✅ 1 migration
- ✅ Tests passés avec succès

---

**Date d'implémentation** : 23 octobre 2025
**Version** : 1.0
**Statut** : ✅ Complété et Fonctionnel

🎉 **La gestion des semaines de cours est opérationnelle !**
