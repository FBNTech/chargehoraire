# Transformation des Tableaux en Cards Responsives

## Vue d'ensemble
Tous les tableaux de l'application se transforment automatiquement en cards sur mobile (≤ 768px) pour une meilleure expérience utilisateur.

## Implémentation

### 1. CSS Global (base.html)
- **Media query @768px** : Transformation automatique des tableaux en cards
- **Media query @576px** : Optimisations pour très petits écrans
- Les tableaux `<table class="table-responsive">` sont ciblés automatiquement

### 2. CSS Personnalisé (static/css/custom.css)
- Styles pour `.table-responsive-cards`
- Animations et effets hover pour les cards
- Optimisations des filtres et statistiques

### 3. Attributs data-label
Chaque `<td>` doit avoir un attribut `data-label` :
```html
<td data-label="Code UE"><strong>INF101</strong></td>
<td data-label="Intitulé UE">Algorithmique</td>
<td data-label="Actions">
    <div class="btn-group">...</div>
</td>
```

## Pages Implémentées

### ✅ Page Horaires (schedule_unified.html)
- Transformation en cards avec tous les champs
- Badges colorés (semaine, jour, créneau, classe)
- Boutons d'actions (Modifier, Supprimer)
- **11 colonnes** : Semaine, Date, Jour, Créneau, Code UE, Intitulé UE, Classe, Grade, Enseignant, Salle, Actions

### ✅ Page Attributions (liste_attributions.html)
- Cards avec informations UE complètes
- Badges pour Classe et Type de Charge
- **9 colonnes** : Code UE, Intitulé UE, Intitulé EC, Crédit, CMI, TD/TP, Classe, Semestre, Type Charge

### ✅ Page Suivi (tracking/dashboard.html)
- **Suivi des cours** : Vue cards avec badges et barres de progression
- **Suivi des enseignants** : Vue cards avec heures et progression
- **Suivi des classes** : Tableau automatiquement transformé
- Filtres par semestre et type de charge

## Fonctionnalités

### Affichage Desktop (> 768px)
- Tableau classique avec toutes les colonnes
- Tri et filtrage complets
- Vue d'ensemble complète

### Affichage Mobile (≤ 768px)
- **Cards individuelles** pour chaque ligne
- **Labels en gras** à gauche, valeurs à droite
- **Badges et boutons** préservés et optimisés
- **Ombres et bordures arrondies** pour distinction visuelle
- **Espacement optimisé** entre les cards

### Affichage Très Petit (≤ 576px)
- **Padding réduit** pour économiser l'espace
- **Texte plus petit** mais lisible
- **Boutons compacts** mais utilisables
- **Statistiques empilées** verticalement

## Structure des Cards Mobile

```
┌─────────────────────────────────┐
│ ┌───────────────────────────┐   │
│ │ Label:          Valeur    │   │
│ │ Code UE:        INF101    │   │
│ │ Intitulé UE:    Algo...   │   │
│ │ Classe:         [Badge]   │   │
│ │ Actions:        [🖊️] [🗑️] │   │
│ └───────────────────────────┘   │
└─────────────────────────────────┘
```

## Avantages

1. **Meilleure lisibilité** sur mobile
2. **Navigation facilitée** avec scroll vertical
3. **Interactions tactiles** optimisées
4. **Aucune perte d'information**
5. **Transformation automatique** - pas de code JS requis
6. **Performance** - CSS pur, pas de re-rendering

## Maintenance

Pour ajouter un nouveau tableau responsive :

1. **Wrapper le tableau** : `<div class="table-responsive">`
2. **Ajouter data-label** à chaque `<td>`
3. **Tester sur mobile** : Redimensionner le navigateur à < 768px
4. **Vérifier les badges et boutons** : S'assurer qu'ils s'affichent correctement

## Tests

- ✅ Chrome DevTools (mode responsive)
- ✅ Firefox Responsive Design Mode
- ✅ Test sur téléphone réel
- ✅ Différentes tailles d'écran (320px - 768px)

## Notes Techniques

### Linter Warnings
Les warnings CSS/JS dans les templates Django sont **normaux** et **sans impact** :
- Proviennent du code template `{% if %}` dans les attributs
- Le code fonctionne correctement côté serveur
- Peuvent être ignorés en toute sécurité

### Compatibilité
- ✅ Bootstrap 5.3
- ✅ Tous les navigateurs modernes
- ✅ Support IE11 (avec fallback)
