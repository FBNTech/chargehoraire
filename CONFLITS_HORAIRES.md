# 🚫 Système de Validation des Conflits d'Horaires

## Vue d'ensemble

Un système complet de détection et prévention des conflits d'horaires a été implémenté pour garantir la cohérence des plannings.

---

## ✅ Conflits détectés automatiquement

### 1. **Conflit Enseignant** ⭐ PRIORITÉ HAUTE - BLOQUANT
Un enseignant ne peut pas être à deux endroits en même temps.

**Vérification** : Même jour + même créneau + même enseignant

**Exemple de conflit** :
```
⚠️ CONFLIT ENSEIGNANT : Prof. BONKILE est déjà programmé(e) pour le cours MAT101 
(Mathématiques) avec la classe L1MI le Lundi à 08h00-12h00
```

### 2. **Conflit Salle** ⭐ PRIORITÉ HAUTE - BLOQUANT
Une salle ne peut accueillir qu'un seul cours à la fois.

**Vérification** : Même jour + même créneau + même salle

**Exemple de conflit** :
```
⚠️ CONFLIT SALLE : La salle B1 est déjà occupée par Prof. KABILA 
pour le cours PHY201 (L2PHY) le Lundi à 08h00-12h00
```

### 3. **Conflit Classe** ⭐ PRIORITÉ HAUTE - BLOQUANT
Une classe ne peut pas suivre deux cours simultanément.

**Vérification** : Même jour + même créneau + même classe

**Exemple de conflit** :
```
⚠️ CONFLIT CLASSE : La classe L1MI a déjà le cours PHY101 (Physique) 
avec Prof. MARTIN le Lundi à 08h00-12h00
```

---

## 📁 Fichiers créés/modifiés

### **Nouveau fichier : `attribution/validators.py`**
Contient toute la logique de validation des conflits :
- `ScheduleConflictValidator` : Classe principale de validation
- `check_teacher_conflict()` : Vérifie les conflits enseignants
- `check_room_conflict()` : Vérifie les conflits de salles
- `check_class_conflict()` : Vérifie les conflits de classes
- `validate_schedule_entry()` : Validation complète d'un horaire
- `get_conflicts_for_week()` : Rapport de conflits pour une semaine

### **Modifié : `attribution/views.py`**
- `ScheduleEntryCreateView.form_valid()` : Validation avant création
- `ScheduleEntryUpdateView.form_valid()` : Validation avant modification
- `save_schedule_entries()` : Validation pour ajout rapide (modal)
- `schedule_conflicts_report()` : Vue pour le rapport de conflits

### **Modifié : `attribution/urls.py`**
Ajout de la route :
```python
path('schedule/conflicts/', views.schedule_conflicts_report, name='schedule_conflicts_report')
```

### **Nouveau template : `attribution/templates/attribution/conflicts_report.html`**
Interface de rapport de conflits avec :
- Sélecteur de semaine
- Résumé des conflits (nombre total, par type)
- Tableaux détaillés des conflits (enseignants, salles, classes)
- Affichage visuel avec badges colorés

### **Modifié : `attribution/templates/attribution/schedule_unified.html`**
Ajout du bouton :
```html
<a href="{% url 'attribution:schedule_conflicts_report' %}" class="btn btn-warning">
    <i class="fas fa-exclamation-triangle"></i> Voir les conflits
</a>
```

---

## 🎯 Fonctionnement

### **Lors de la création d'un horaire**

1. L'utilisateur remplit le formulaire
2. Avant la sauvegarde, le système vérifie :
   - ✓ Conflit enseignant
   - ✓ Conflit salle
   - ✓ Conflit classe
3. **Si conflit détecté** :
   - ❌ L'horaire N'EST PAS créé
   - 🔴 Message d'erreur rouge affiché avec détails
   - 📝 L'utilisateur reste sur le formulaire pour corriger
4. **Si aucun conflit** :
   - ✅ L'horaire est créé
   - 🟢 Message de succès : "✅ Horaire créé avec succès. Aucun conflit détecté."

### **Lors de la modification d'un horaire**

Même processus, mais l'horaire actuel est **exclu** de la vérification (pour éviter de détecter un faux conflit avec lui-même).

### **Lors de l'ajout rapide (modal)**

Si des conflits sont détectés :
- Les horaires valides sont créés
- Les horaires en conflit sont rejetés
- Message détaillé : `X horaire(s) créé(s). Y conflit(s) détecté(s).`
- Liste des erreurs affichée

---

## 📊 Rapport de Conflits

### **Accès**
`/attribution/schedule/conflicts/`

OU

Bouton **"Voir les conflits"** dans la page de gestion des horaires

### **Fonctionnalités**

1. **Sélection de semaine**
   - Dropdown avec toutes les semaines configurées
   - Semaine en cours pré-sélectionnée (★)

2. **Résumé visuel**
   - Carte avec nombre total de conflits
   - Carte conflits enseignants (jaune)
   - Carte conflits salles (bleu)

3. **Tableaux détaillés**
   - Un tableau par type de conflit
   - Liste de tous les cours en conflit
   - Informations complètes (enseignant, UE, classe, salle)

4. **Indicateur de santé**
   - ✅ Vert si aucun conflit
   - ⚠️ Rouge si des conflits existent

---

## 🔧 Utilisation pratique

### **Scénario 1 : Création sans conflit**
```
1. Ajouter un horaire : L1MI - MAT101 - Prof. BONKILE - Lundi 08h-12h - Salle B1
2. ✅ "Horaire créé avec succès. Aucun conflit détecté."
```

### **Scénario 2 : Conflit enseignant détecté**
```
1. Essayer d'ajouter : L2BC - PHY201 - Prof. BONKILE - Lundi 08h-12h - Salle A1
2. ❌ "CONFLIT ENSEIGNANT : Prof. BONKILE est déjà programmé(e) pour MAT101 (L1MI)"
3. Modifier l'enseignant OU changer l'horaire
```

### **Scénario 3 : Conflit salle détecté**
```
1. Essayer d'ajouter : L3MI - INFO301 - Prof. KABILA - Lundi 08h-12h - Salle B1
2. ❌ "CONFLIT SALLE : La salle B1 est déjà occupée par Prof. BONKILE (MAT101 - L1MI)"
3. Choisir une autre salle OU changer l'horaire
```

### **Scénario 4 : Vérification hebdomadaire**
```
1. Cliquer sur "Voir les conflits"
2. Sélectionner "Semaine 1 : 27/10 - 01/11 ★"
3. Consulter le rapport :
   - Total conflits : 0
   - ✅ "Aucun conflit détecté ! Tous les horaires sont valides."
```

---

## 🎨 Messages utilisateur

### **Messages de succès (vert)**
- ✅ Horaire créé avec succès. Aucun conflit détecté.
- ✅ Horaire modifié avec succès. Aucun conflit détecté.
- ✅ X horaire(s) créé(s) avec succès

### **Messages d'erreur (rouge)**
- ⚠️ CONFLIT ENSEIGNANT : [détails]
- ⚠️ CONFLIT SALLE : [détails]
- ⚠️ CONFLIT CLASSE : [détails]

### **Messages mixtes (jaune + vert)**
- 3 horaire(s) créé(s). 2 conflit(s) détecté(s).
- [Liste des erreurs affichée]

---

## 🚀 Avantages

1. **Prévention proactive** : Les conflits sont bloqués AVANT la création
2. **Messages clairs** : L'utilisateur sait exactement quel est le problème
3. **Gain de temps** : Pas besoin de vérifier manuellement les horaires
4. **Rapport global** : Vue d'ensemble des conflits d'une semaine
5. **Intégrité des données** : Garantit que les horaires sont toujours cohérents

---

## 📌 Notes techniques

- Les validations sont effectuées au niveau du backend (Python/Django)
- Impossible de contourner les validations via l'API
- Les conflits sont vérifiés pour chaque combinaison jour + créneau + semaine
- Un horaire peut être modifié sans conflit avec lui-même (exclude_id)
- Le rapport de conflits est généré dynamiquement à chaque consultation

---

## 🎓 Prochaines améliorations possibles

1. **Avertissements non bloquants** :
   - Surcharge horaire enseignant (> 6h/jour)
   - Capacité salle dépassée
   - Préférences pédagogiques

2. **Suggestions automatiques** :
   - Salles libres au même moment
   - Créneaux alternatifs sans conflit
   - Enseignants disponibles

3. **Export du rapport** :
   - PDF du rapport de conflits
   - Export Excel pour analyse

4. **Notifications** :
   - Email si conflit créé
   - Alerte hebdomadaire des conflits

---

**Date de création** : 26 octobre 2025  
**Version** : 1.0  
**Auteur** : Système de gestion d'horaires académiques
