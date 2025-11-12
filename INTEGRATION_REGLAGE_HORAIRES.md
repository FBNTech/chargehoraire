# 🔗 Intégration Réglage → Horaires

## ✅ Modifications Apportées

Les données des modèles de réglage (Années Académiques, Salles, Créneaux) sont maintenant **automatiquement utilisées** dans la page horaire.

---

## 🎯 **Ce qui a changé**

### 1️⃣ **Formulaire de création d'horaire** (`schedule_entry_form.html`)

#### Avant ❌
- Champs texte pour année, créneau, salle
- Pas de suggestions
- Risque d'erreurs de saisie

#### Après ✅
- **Année Académique** : Combo avec années enregistrées + pré-remplissage avec l'année en cours
- **Créneau** : Combo avec créneaux actifs (affiche désignation + format court)
- **Salle** : Combo avec salles disponibles (affiche code, désignation et capacité)
- Possibilité de saisie manuelle en fallback

---

### 2️⃣ **Modal Ajout Rapide** (`schedule_unified.html`)

#### Avant ❌
- Créneaux codés en dur : AM, PM
- Salle en texte libre

#### Après ✅
- **Créneaux dynamiques** : Charge tous les créneaux actifs depuis `Creneau` table
- **Salles dynamiques** : Combo avec toutes les salles disponibles
- Affichage enrichi : "Matinée (08h00-12h00)", "B1 - Salle Sciences (50 places)"

---

## 📂 **Fichiers Modifiés**

### Backend
1. **`attribution/forms.py`**
   - Import des modèles : `from reglage.models import AnneeAcademique, Salle, Creneau`
   - Ajout de 3 nouveaux champs : `annee_academique_select`, `salle_select`, `creneau_select`
   - Méthode `clean()` pour convertir les objets en codes
   - Pré-remplissage automatique avec l'année en cours

2. **`attribution/views.py`**
   - `ScheduleEntryListView.get_context_data()` enrichi
   - Ajout de : `annees_reglage`, `annee_courante`, `salles_disponibles`, `creneaux_actifs`

### Frontend
3. **`attribution/templates/attribution/schedule_entry_form.html`**
   - Remplacement des champs texte par des combos
   - Affichage des données de réglage

4. **`attribution/templates/attribution/schedule_unified.html`**
   - Modal avec créneaux/salles dynamiques
   - Fallback si pas de données dans réglage

---

## 🔄 **Flux de Données**

```
┌─────────────────────┐
│  RÉGLAGE            │
│  /reglage/gestion/  │
└──────┬──────────────┘
       │
       │ Enregistrement dans :
       ├─ AnneeAcademique
       ├─ Salle
       └─ Creneau
       │
       ↓
┌──────────────────────┐
│  VUES HORAIRES       │
│  get_context_data()  │
└──────┬───────────────┘
       │
       │ Récupération :
       ├─ annees_reglage
       ├─ salles_disponibles
       └─ creneaux_actifs
       │
       ↓
┌──────────────────────┐
│  TEMPLATES           │
│  Combos remplis      │
└──────────────────────┘
       │
       ↓
┌──────────────────────┐
│  UTILISATEUR         │
│  Sélectionne         │
└──────────────────────┘
```

---

## 🎨 **Interface Utilisateur**

### Formulaire Complet

```html
┌─ Année Académique ─────────────────┐
│ [2024-2025 (En cours) ▼]          │
│ ℹ️ Ou saisir manuellement : [___] │
└────────────────────────────────────┘

┌─ Créneau ──────────────────────────┐
│ [Matinée (08h00-12h00) ▼]         │
│ ℹ️ Ou code : [__]                  │
└────────────────────────────────────┘

┌─ Salle ────────────────────────────┐
│ [B1 - Salle Sciences (50 pl.) ▼]  │
│ ℹ️ Ou code : [__]                  │
└────────────────────────────────────┘
```

### Modal Ajout Rapide

```html
┌─ Créneau ──────────────────────────┐
│ • Matinée (08h00-12h00)           │
│ • Après-midi (13h00-17h00)        │
│ • Soirée (18h00-20h00)            │
└────────────────────────────────────┘

┌─ Salle ────────────────────────────┐
│ -- Sélectionner une salle --      │
│ • B1 - Salle B1 Sciences (50 pl.) │
│ • A205 - Salle info (30 pl.)      │
│ • AMPHI-A - Amphithéâtre (200 pl.)│
└────────────────────────────────────┘
```

---

## 🚀 **Utilisation**

### Scénario complet

#### 1. **Configurer les données de base** (une seule fois)

**A. Créer des années académiques**
```
/reglage/annees/
→ Ajouter : 2024-2025 ✅ En cours
→ Ajouter : 2025-2026
```

**B. Créer des salles**
```
/reglage/salles/
→ B1 - Salle B1 Bâtiment Sciences (TD, 50 places) ✅ Disponible
→ A205 - Salle informatique (TP, 30 places) ✅ Disponible
→ AMPHI-A - Amphithéâtre A (AMPHI, 200 places) ✅ Disponible
```

**C. Créer des créneaux**
```
/reglage/creneaux/
→ AM - Matinée (08:00-12:00) - Ordre: 1 ✅ Actif
→ PM - Après-midi (13:00-17:00) - Ordre: 2 ✅ Actif
→ SOIR - Soirée (18:00-20:00) - Ordre: 3 ✅ Actif
```

---

#### 2. **Créer un horaire** (utilise les données de réglage)

**Option A : Formulaire complet**
```
/attribution/schedule/entry/create/

1. Cours : [L1BC | CHI191 - Chimie générale ▼]
2. Année : [2024-2025 (En cours) ▼]  ← Pré-rempli automatiquement !
3. Date : [2025-10-27]
4. Jour : [Lundi ▼]
5. Créneau : [Matinée (08h00-12h00) ▼]  ← Depuis Réglage !
6. Salle : [B1 - Salle Sciences (50 places) ▼]  ← Depuis Réglage !
7. Remarques : [Prévoir projecteur]

→ Cliquer "Créer"
```

**Option B : Ajout rapide**
```
/attribution/schedule/entry/list/
→ Cliquer "⚡ Ajout rapide"

Dans le modal :
1. Cours : [L1BC | CHI191 ▼]
2. Date : [2025-10-27]
3. Créneau : [Matinée (08h00-12h00) ▼]  ← Depuis Réglage !
4. Salle : [B1 - Salle Sciences ▼]  ← Depuis Réglage !

→ Cliquer "Enregistrer"
```

---

## 🔍 **Avantages**

### Pour l'utilisateur
✅ **Pas d'erreurs de saisie** : Sélection depuis des listes
✅ **Plus rapide** : Pas besoin de taper les codes
✅ **Plus clair** : Affichage complet (désignation, horaires, capacité)
✅ **Cohérence** : Utilise les mêmes données partout
✅ **Année en cours automatique** : Pré-remplie par défaut

### Pour l'admin
✅ **Centralisation** : Une seule source de vérité (table Réglage)
✅ **Flexibilité** : Ajout/Modification centralisée
✅ **Filtrage intelligent** : Seules les salles disponibles et créneaux actifs sont proposés
✅ **Historique** : Conservation des anciennes années

---

## 🛠️ **Fonctionnalités Techniques**

### Filtrage Automatique

```python
# Seules les salles DISPONIBLES sont proposées
Salle.objects.filter(est_disponible=True)

# Seuls les créneaux ACTIFS sont proposés
Creneau.objects.filter(est_actif=True)

# Année EN COURS pré-remplie
AnneeAcademique.objects.filter(est_en_cours=True).first()
```

### Conversion Automatique

```python
# Le formulaire convertit automatiquement :
annee_select (objet) → annee_academique (code)
salle_select (objet) → salle (code)
creneau_select (objet) → creneau (code)

# Via la méthode clean() du formulaire
```

### Affichage Enrichi

```python
# Créneaux
f"{designation} ({heure_debut}-{heure_fin})"
# Ex: "Matinée (08h00-12h00)"

# Salles
f"{code} - {designation} ({capacite} places)"
# Ex: "B1 - Salle Sciences (50 places)"
```

---

## 🧪 **Tests Recommandés**

### Test 1 : Année en cours automatique
1. Aller dans `/reglage/annees/`
2. Marquer "2024-2025" comme "En cours"
3. Aller dans `/attribution/schedule/entry/create/`
4. **Vérifier** : Le champ année est pré-rempli avec "2024-2025"

### Test 2 : Créneaux personnalisés
1. Aller dans `/reglage/creneaux/`
2. Créer : "MATIN" - "Matin" (07:30-11:30)
3. Aller dans modal ajout rapide
4. **Vérifier** : Le créneau "Matin (07h30-11h30)" apparaît

### Test 3 : Salles avec capacité
1. Aller dans `/reglage/salles/`
2. Créer : "LAB-PHYS" - "Laboratoire Physique" (25 places)
3. Aller dans formulaire horaire
4. **Vérifier** : "LAB-PHYS - Laboratoire Physique (25 places)" apparaît

### Test 4 : Salle indisponible
1. Dans `/reglage/salles/`, modifier B1
2. Décocher "Disponible"
3. Aller dans formulaire horaire
4. **Vérifier** : B1 n'apparaît plus dans le combo

### Test 5 : Créneau inactif
1. Dans `/reglage/creneaux/`, modifier AM
2. Décocher "Actif"
3. Aller dans modal ajout rapide
4. **Vérifier** : "Matinée" n'apparaît plus

---

## 📝 **Fallback (Sécurité)**

Si aucune donnée n'est enregistrée dans Réglage, le système fonctionne quand même :

### Créneaux
```html
{% if creneaux_actifs %}
    <!-- Charge depuis la base -->
{% else %}
    <!-- Valeurs par défaut -->
    <option value="am">08h00-12h00</option>
    <option value="pm">13h00-17h00</option>
{% endif %}
```

### Salles
- Champ texte disponible pour saisie manuelle
- Utilisable si aucune salle n'est enregistrée

### Années
- Champ texte pour saisie manuelle
- Format : "2024-2025"

---

## 🔄 **Compatibilité**

### Données existantes
✅ **Conservées** : Les horaires existants fonctionnent toujours
✅ **Pas de migration** : Aucun changement dans les champs de ScheduleEntry
✅ **Rétrocompatible** : Les codes saisis manuellement continuent de fonctionner

### Anciennes interfaces
✅ L'ancien générateur PDF (`/attribution/schedule/`) redirige vers la nouvelle interface
✅ Les URLs restent les mêmes

---

## 🎓 **Message pour les utilisateurs**

```
📢 AMÉLIORATION : INTÉGRATION RÉGLAGE ↔ HORAIRES

Les données que vous enregistrez dans "Réglage" sont maintenant
automatiquement utilisées dans la page "Horaires" !

✨ NOUVEAUTÉS :

1️⃣ ANNÉE EN COURS AUTOMATIQUE
   → Marquez une année comme "en cours" dans Réglage
   → Elle sera pré-sélectionnée dans les horaires

2️⃣ SALLES EN COMBO
   → Créez vos salles dans Réglage (code, nom, capacité)
   → Sélectionnez-les facilement dans les horaires

3️⃣ CRÉNEAUX PERSONNALISÉS
   → Définissez vos créneaux dans Réglage (horaires exacts)
   → Ils apparaissent automatiquement dans les horaires

🎯 WORKFLOW RECOMMANDÉ :
1. Configurez vos données dans "Réglage" (une fois)
2. Utilisez les combos dans "Horaires" (tous les jours)

📚 Plus d'infos : INTEGRATION_REGLAGE_HORAIRES.md
```

---

## ✅ **Checklist d'Implémentation**

- [x] Import des modèles de réglage dans forms.py
- [x] Ajout de 3 champs dans ScheduleEntryForm
- [x] Méthode clean() pour conversion
- [x] Pré-remplissage année en cours
- [x] Enrichissement get_context_data() dans la vue
- [x] Modification template schedule_entry_form.html
- [x] Modification template schedule_unified.html
- [x] Combos créneaux dynamiques
- [x] Combos salles dynamiques
- [x] Fallback si pas de données
- [x] JavaScript mis à jour pour select
- [x] Documentation complète

---

**Date d'intégration** : 23 octobre 2025
**Version** : 2.0
**Statut** : ✅ Complété et Fonctionnel
