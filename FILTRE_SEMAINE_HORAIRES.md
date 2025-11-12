# 🔍 Filtre Semaine dans la Page Charge Horaire

## ✅ **Fonctionnalité Ajoutée**

Un nouveau **filtre par semaine** a été ajouté dans la page charge horaire pour filtrer les horaires selon la semaine de cours sélectionnée.

---

## 🎯 **Objectif**

Permettre aux utilisateurs de :
- ✅ Filtrer les horaires par semaine de cours
- ✅ Voir la semaine en cours avec indicateur ★
- ✅ Naviguer rapidement entre les semaines (S1, S2, S3...)

---

## 🔧 **Implémentation**

### 1️⃣ **Backend : Vue (attribution/views.py)**

#### Filtrage dans `get_queryset()`
```python
def get_queryset(self):
    queryset = ScheduleEntry.objects.select_related(
        'attribution__matricule',
        'attribution__code_ue'
    ).order_by('-semaine_debut', 'jour', 'creneau')
    
    # Récupérer le paramètre semaine
    semaine = self.request.GET.get('semaine')
    
    # Filtrer si semaine sélectionnée
    if semaine:
        queryset = queryset.filter(semaine_debut=semaine)
    
    return queryset
```

#### Enrichissement du contexte dans `get_context_data()`
```python
def get_context_data(self, **kwargs):
    from reglage.models import SemaineCours
    
    context = super().get_context_data(**kwargs)
    
    # Ajouter les semaines de cours
    context['semaines_cours'] = SemaineCours.objects.all().order_by('numero_semaine')
    
    # Ajouter la semaine en cours
    context['semaine_courante'] = SemaineCours.objects.filter(est_en_cours=True).first()
    
    return context
```

---

### 2️⃣ **Frontend : Template (schedule_unified.html)**

#### Nouveau combo dans les filtres
```html
<div class="col-md-2">
    <label class="form-label">Semaine</label>
    <select name="semaine" class="form-select">
        <option value="">Toutes</option>
        {% if semaines_cours %}
            {% for semaine in semaines_cours %}
                <option value="{{ semaine.date_debut }}" 
                        {% if request.GET.semaine == semaine.date_debut|date:"Y-m-d" %}selected{% endif %}>
                    S{{ semaine.numero_semaine }}{% if semaine.est_en_cours %} ★{% endif %}
                </option>
            {% endfor %}
        {% endif %}
    </select>
</div>
```

**Format d'affichage** :
- `S1 ★` → Semaine 1 (en cours)
- `S2` → Semaine 2
- `S3` → Semaine 3

---

## 🎨 **Interface Utilisateur**

### Barre de Filtres Complète

```
┌─ Filtres ──────────────────────────────────────────────┐
│                                                        │
│  Année        Semaine    Jour       Créneau   Classe  │
│  [2025-26 ▼] [S1 ★ ▼]  [Lundi ▼]  [AM ▼]    [L1BC ▼] │
│                                                        │
│                          [🔍 Filtrer]                  │
└────────────────────────────────────────────────────────┘
```

**Organisation** :
- Année académique : col-md-2
- **Semaine** : col-md-2 ⭐ NOUVEAU
- Jour : col-md-2
- Créneau : col-md-2
- Classe : col-md-2
- Bouton : col-md-2

**Total** : 12 colonnes (Bootstrap grid)

---

## 📊 **Résultats des Tests**

### Test 1 : Semaines Disponibles
```
✓ 1 semaine enregistrée
  • S1 : 27/10 - 01/11 ★
```

### Test 2 : Contexte de la Vue
```
✓ 'semaines_cours' présent
✓ Nombre de semaines : 1
✓ 'semaine_courante' présent : S1 ★
```

### Test 3 : Filtrage
```
Total horaires : 16
Horaires S1 : 5

✓ Filtrage fonctionnel
✓ Requête : /attribution/schedule/entry/list/?semaine=2025-10-27
✓ Résultats : 5 horaires filtrés
```

---

## 💡 **Utilisation**

### Scénario 1 : Voir les Horaires d'une Semaine

**Étapes** :
1. Aller sur `/attribution/schedule/entry/list/`
2. Dans le filtre "Semaine", sélectionner `S1 ★`
3. Cliquer "🔍 Filtrer"

**Résultat** : Seuls les horaires de la semaine 1 s'affichent

---

### Scénario 2 : Voir la Semaine en Cours

**Automatique** :
- La semaine marquée "en cours" dans Réglage
- Apparaît avec l'indicateur ★ dans le combo
- `S1 ★` = Semaine 1 en cours

**Pour la sélectionner** :
- Choisir `S1 ★` dans le combo
- Filtrer

---

### Scénario 3 : Combiner Plusieurs Filtres

**Exemple** : Voir les horaires de L1BC le lundi de la semaine 1

**Filtres** :
- Semaine : `S1 ★`
- Jour : `Lundi`
- Classe : `L1BC`

**Résultat** : Horaires très précis

---

## 🔗 **Intégration avec Réglage**

### Lien avec SemaineCours

**Le combo semaine** utilise le modèle `SemaineCours` du module Réglage :
```python
SemaineCours.objects.all().order_by('numero_semaine')
```

**Données affichées** :
- `numero_semaine` → "S1", "S2", "S3"...
- `date_debut` → Valeur du filtre (2024-10-14)
- `est_en_cours` → Indicateur ★

---

### Workflow Complet

```
1. Créer des semaines dans Réglage
   /reglage/semaines/create/
   → Semaine 1 : 14/10 - 19/10 (en cours)
   → Semaine 2 : 21/10 - 26/10
   → Semaine 3 : 28/10 - 02/11

2. Les semaines apparaissent automatiquement
   dans le filtre de la page horaire
   → S1 ★
   → S2
   → S3

3. Filtrer les horaires par semaine
   → Sélectionner S1 ★
   → Cliquer Filtrer
   → Voir uniquement les horaires de S1
```

---

## 📈 **Avantages**

### Avant ❌
- Pas de filtre par semaine
- Difficile de voir les horaires d'une semaine spécifique
- Navigation manuelle dans la liste complète

### Après ✅
- **Filtre dédié** : Sélection rapide de la semaine
- **Indicateur visuel** : Semaine en cours marquée ★
- **Format simple** : S1, S2, S3... (facile à comprendre)
- **Intégration** : Utilise les semaines de Réglage

---

## 🎯 **Cas d'Usage**

### Cas 1 : Planification Hebdomadaire

**Besoin** : Voir les horaires de la semaine prochaine

**Solution** :
```
Filtre Semaine : S2
→ Affiche tous les horaires de la semaine 2
→ Permet de vérifier les conflits
→ Facilite la planification
```

---

### Cas 2 : Suivi de la Semaine en Cours

**Besoin** : Voir rapidement les horaires actuels

**Solution** :
```
Filtre Semaine : S1 ★ (en cours)
→ Affiche les horaires de cette semaine
→ Indicateur ★ pour repérage rapide
→ Mise à jour automatique chaque semaine
```

---

### Cas 3 : Analyse Comparative

**Besoin** : Comparer les horaires de deux semaines

**Solution** :
```
1. Filtrer par S1 → Noter les horaires
2. Filtrer par S2 → Comparer
3. Identifier les différences
```

---

## 📚 **Documentation Technique**

### Format de la Valeur

**Option combo** :
```html
<option value="2024-10-14">S1 ★</option>
```

**Valeur** : Date de début de semaine (YYYY-MM-DD)
**Label** : SX (★ si en cours)

### Filtrage Base de Données

```python
# URL : ?semaine=2024-10-14
queryset.filter(semaine_debut='2024-10-14')
```

**Champ utilisé** : `ScheduleEntry.semaine_debut` (DateField)

---

## ✅ **Checklist d'Implémentation**

- [x] Ajouter filtrage dans `get_queryset()`
- [x] Ajouter `semaines_cours` dans contexte
- [x] Ajouter `semaine_courante` dans contexte
- [x] Créer combo semaine dans template
- [x] Indicateur ★ pour semaine en cours
- [x] Format compact "SX"
- [x] Tests de filtrage passés
- [x] Documentation créée

---

## 🔄 **URLs Disponibles**

### Filtrage Simple
```
/attribution/schedule/entry/list/?semaine=2024-10-14
```
→ Horaires de la semaine du 14 octobre

### Filtrage Combiné
```
/attribution/schedule/entry/list/?semaine=2024-10-14&jour=lundi&classe=L1BC
```
→ Horaires L1BC du lundi de la semaine du 14 octobre

---

## 💬 **Message pour les Utilisateurs**

```
📢 NOUVEAU : FILTRE PAR SEMAINE

Vous pouvez maintenant filtrer les horaires par semaine de cours !

✨ FONCTIONNALITÉS :
• Sélectionnez une semaine (S1, S2, S3...)
• L'indicateur ★ montre la semaine en cours
• Combinez avec d'autres filtres (jour, classe...)

🚀 COMMENT L'UTILISER ?
1. Dans la page horaire, cherchez le filtre "Semaine"
2. Sélectionnez la semaine voulue (ex: S1 ★)
3. Cliquez "Filtrer"

💡 ASTUCE :
Combinez le filtre semaine avec les autres filtres
pour des résultats très précis !
```

---

**Date d'implémentation** : 23 octobre 2025  
**Version** : 1.0  
**Statut** : ✅ Testé et Validé

🎉 **Le filtre semaine est opérationnel dans la page charge horaire !**
