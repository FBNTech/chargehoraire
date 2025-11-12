# 📅 Guide Utilisateur - Gestion des Horaires

## 🎯 Une seule page pour tout gérer !

Désormais, **tout se passe sur une seule page** :
```
http://127.0.0.1:8000/attribution/schedule/entry/list/
```

## 🚀 Démarrage rapide

### 1️⃣ Accéder à la page des horaires

**Option A** : Tapez directement l'URL
```
http://127.0.0.1:8000/attribution/schedule/entry/list/
```

**Option B** : Depuis le menu (si configuré)
- Cliquez sur "Horaires" dans le menu principal

**Option C** : L'ancienne URL fonctionne toujours !
```
http://127.0.0.1:8000/attribution/schedule/
→ Redirige automatiquement vers la nouvelle page
```

## 📊 Interface de la page

```
┌─────────────────────────────────────────────────────────────────┐
│ 📅 Gestion des Horaires                                         │
│                    [➕ Ajouter] [⚡ Ajout rapide] [📄 Générer PDF]│
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Filtres                                                       │
│ [Année ▼] [Jour ▼] [Créneau ▼] [Classe____] [🔍 Filtrer]       │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Statistiques                                                  │
│ [Total: 19] [Année: 2025-26] [Cours: 19] [Salles: 5]            │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Liste des horaires enregistrés                               │
│ [Tableau avec 19 horaires]                                      │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Fonctionnalités principales

### 🔍 **Filtrer les horaires**

Pour trouver rapidement un horaire spécifique :

1. **Sélectionnez vos critères** :
   - Année académique (ex: 2025-2026)
   - Jour (Lundi, Mardi, etc.)
   - Créneau (08h00-12h00 ou 13h00-17h00)
   - Classe (ex: L1BC)

2. **Cliquez sur "Filtrer"**

3. Le tableau se met à jour instantanément

**Astuce** : Laissez un champ vide pour ne pas filtrer sur ce critère

---

### ➕ **Ajouter un horaire (méthode complète)**

Pour ajouter un horaire avec tous les détails :

1. **Cliquez sur le bouton "➕ Ajouter un horaire"** (en haut à droite)

2. **Remplissez le formulaire** :
   - 📚 **Cours (UE + Enseignant)** : Sélectionnez dans la liste
   - 📆 **Année académique** : ex: 2025-2026
   - 📅 **Semaine (date de début)** : ex: 21/10/2025
   - 📆 **Jour** : Lundi, Mardi, etc.
   - ⏰ **Créneau** : AM (08h00-12h00) ou PM (13h00-17h00)
   - 🏢 **Salle** : ex: B1 (optionnel)
   - 📝 **Remarques** : Notes optionnelles

3. **Cliquez sur "Créer"**

4. ✅ Message de confirmation + retour à la liste

**Quand utiliser ?**
- Première saisie d'un horaire
- Besoin d'ajouter des remarques détaillées
- Vérification visuelle avant enregistrement

---

### ⚡ **Ajout rapide** (RECOMMANDÉ)

Pour ajouter rapidement un horaire sans quitter la page :

1. **Cliquez sur "⚡ Ajout rapide"** (en haut à droite)

2. Une **fenêtre pop-up** s'ouvre

3. **Remplissez les champs** :
   - Cours (la liste se charge automatiquement)
   - Date (le jour se calcule automatiquement)
   - Créneau
   - Salle (optionnel)
   - Remarques (optionnel)

4. **Cliquez sur "Enregistrer"**

5. ✅ Horaire ajouté instantanément + la fenêtre se ferme

**Avantages** :
- ✨ Ultra rapide (5 secondes)
- 📌 Pas de changement de page
- 🎯 Focus sur l'essentiel
- 🔄 Ajoutez plusieurs horaires d'affilée

**Quand utiliser ?**
- Ajout de plusieurs horaires consécutifs
- Modifications rapides en cours de semaine
- Workflow quotidien

---

### ✏️ **Modifier un horaire**

1. **Trouvez la ligne** de l'horaire à modifier (utilisez les filtres si besoin)

2. **Cliquez sur l'icône ✏️** dans la colonne "Actions"

3. Le formulaire de modification s'ouvre avec les données actuelles

4. **Modifiez les champs** nécessaires

5. **Cliquez sur "Modifier"**

6. ✅ Horaire mis à jour + retour à la liste

**Info** : Vous voyez un récapitulatif des informations du cours en bas du formulaire

---

### 🗑️ **Supprimer un horaire**

1. **Trouvez la ligne** de l'horaire à supprimer

2. **Cliquez sur l'icône 🗑️** dans la colonne "Actions"

3. **Confirmez** la suppression dans la boîte de dialogue

4. ✅ Horaire supprimé + la page se rafraîchit

**⚠️ Attention** : Cette action est irréversible !

---

### 📄 **Générer un PDF d'horaires**

Pour créer un emploi du temps imprimable :

1. **Appliquez les filtres** souhaités (optionnel)
   - Ex: Année 2025-2026, Classe L1BC

2. **Cliquez sur "📄 Générer PDF"**

3. Le **PDF s'ouvre dans un nouvel onglet** avec :
   - Horaires regroupés par niveau académique (L1, L2, L3, M1, M2)
   - Jours en lignes (Lundi à Samedi)
   - Options de classe en colonnes (L1BC, L1CST, etc.)
   - 2 créneaux par jour (AM et PM)
   - Code UE, Intitulé, Grade et Nom de l'enseignant

4. **Imprimez ou téléchargez** le PDF

**Format du PDF** :
```
SECTION DES SCIENCES & TECHNOLOGIES
Horaires des Cours - Niveau L1 : semaine du 21/10/2025

┌─────────┬───────────┬──────┬──────┬──────┐
│ Jour    │ Heures    │ L1BC │ L1MI │ L1CST│
├─────────┼───────────┼──────┼──────┼──────┤
│ Lundi   │08h00-12h00│CHI191│MAT103│CHI291│
│         │           │(...)  │(...)  │(...) │
│         │           │Dr XX │Pr YY │Dr ZZ │
│         ├───────────┼──────┼──────┼──────┤
│         │13h00-17h00│      │      │      │
├─────────┼───────────┼──────┼──────┼──────┤
│ Mardi   │...        │...   │...   │...   │
└─────────┴───────────┴──────┴──────┴──────┘
```

---

## 💡 Astuces et bonnes pratiques

### ⚡ Workflow recommandé pour la saisie hebdomadaire

1. **Lundi matin** : Planifiez la semaine
   - Utilisez "⚡ Ajout rapide" pour tous les cours de la semaine
   - Remplissez cours par cours, jour par jour

2. **En cours de semaine** : Ajustez si nécessaire
   - Modifiez (✏️) si changement de salle
   - Supprimez (🗑️) si cours annulé

3. **Vendredi** : Générez le PDF
   - Appliquez les filtres pour la semaine en cours
   - Générez et distribuez l'emploi du temps

### 🔍 Recherche efficace

**Pour trouver un cours spécifique** :
```
Filtres : Classe = "L1BC" + Jour = "Lundi" + Créneau = "AM"
→ Affiche uniquement les cours L1BC du lundi matin
```

**Pour voir tous les horaires d'un enseignant** :
- Malheureusement, pas de filtre enseignant pour l'instant
- Solution : Générez le PDF et utilisez Ctrl+F

**Pour voir une semaine complète** :
- Filtrez par année académique
- Ne mettez pas de filtre jour/créneau
- Regardez le tableau complet

### 📊 Utilisation des statistiques

Les 4 cartes en haut donnent un aperçu rapide :

- **Total horaires** : Nombre d'horaires enregistrés (avec filtres appliqués)
- **Année active** : L'année académique la plus récente
- **Cours planifiés** : Même chose que "Total horaires"
- **Salles utilisées** : Nombre de salles différentes

### ⚠️ Éviter les erreurs courantes

**Erreur 1** : "UNIQUE constraint failed"
- **Cause** : Vous essayez de créer un horaire qui existe déjà
- **Solution** : Vérifiez qu'il n'y a pas déjà un horaire avec :
  - Même cours + Même année + Même semaine + Même jour + Même créneau
- **Astuce** : Utilisez les filtres pour vérifier avant d'ajouter

**Erreur 2** : Horaire invisible après ajout
- **Cause** : Les filtres sont activés et masquent le nouvel horaire
- **Solution** : Cliquez sur "Filtrer" sans aucun filtre pour voir tout

**Erreur 3** : Le jour ne correspond pas à la date
- **Cause** : Erreur dans le calcul automatique du jour
- **Solution** : L'ajout rapide calcule automatiquement le jour depuis la date

## 🆘 Problèmes fréquents

### Problème : La page est vide / Aucun horaire affiché

**Solutions** :
1. Vérifiez que vous êtes bien sur `/attribution/schedule/entry/list/`
2. Enlevez tous les filtres (cliquez sur "Filtrer" sans sélection)
3. Vérifiez qu'il y a des horaires : regardez "Total: X" en haut

### Problème : Impossible d'ajouter un horaire

**Solutions** :
1. Vérifiez qu'il existe des **attributions** (cours + enseignants)
2. Vérifiez que l'année académique est correcte
3. Utilisez "Ajout rapide" au lieu du formulaire complet

### Problème : Le PDF ne se génère pas

**Solutions** :
1. Vérifiez qu'il y a des horaires enregistrés
2. Désactivez les bloqueurs de pop-up
3. Essayez dans un autre navigateur

### Problème : "Aucun cours ajouté" dans le tableau

**Cause** : Vous êtes sur l'ancienne page qui n'existe plus
**Solution** : Utilisez la nouvelle URL `/attribution/schedule/entry/list/`

## 📚 Pour aller plus loin

### Intégration avec d'autres modules

- **Attributions** : Les horaires utilisent les attributions existantes
- **Enseignants** : Les grades et noms viennent de la table enseignants
- **Cours** : Codes UE et intitulés viennent de la table cours

### Données stockées

Chaque horaire enregistré contient :
- Attribution (= cours + enseignant + année)
- Semaine de début
- Jour (lundi à samedi)
- Créneau (AM ou PM)
- Salle (optionnel)
- Remarques (optionnel)

### Limites actuelles

- **Pas de gestion multi-semaines** : Il faut créer un horaire par semaine
- **Pas de récurrence** : Impossible de dire "tous les lundis"
- **Pas de filtre par enseignant** : Seulement par classe, jour, créneau

## 🎓 Formation

Pour former un nouvel utilisateur :

1. **Montrez la page unifiée** (5 min)
   - Expliquez les 4 boutons en haut
   - Montrez le tableau avec les horaires existants

2. **Démonstration "Ajout rapide"** (5 min)
   - Ajoutez 2-3 horaires en direct
   - Montrez la rapidité du workflow

3. **Exercice pratique** (10 min)
   - Laissez-le ajouter des horaires pour une semaine
   - Supervisez et corrigez

4. **Génération PDF** (5 min)
   - Générez le PDF de ce qui vient d'être créé
   - Expliquez l'utilité

**Durée totale** : 25 minutes

---

## 📞 Support

Pour toute question ou problème :
1. Consultez ce guide
2. Vérifiez la documentation technique (`HARMONISATION_HORAIRES.md`)
3. Contactez le support technique

---

**Version** : 1.0
**Date** : 23 octobre 2025
**Auteur** : Équipe développement
