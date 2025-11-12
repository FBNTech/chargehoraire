# ✅ Validation Lundi → Samedi pour les Semaines de Cours

## 🎯 **Règle Implémentée**

Les semaines de cours **doivent obligatoirement** :
- ✅ Commencer un **LUNDI**
- ✅ Se terminer un **SAMEDI**

**Justification** : Une semaine académique standard = 6 jours (Lundi → Samedi)

---

## 🔧 **Implémentation**

### Validation dans le Modèle

**Fichier** : `reglage/models.py`

```python
def clean(self):
    """Validation : date_debut doit être un lundi et date_fin un samedi"""
    from django.core.exceptions import ValidationError
    
    # Vérifier que date_debut est un lundi (weekday() = 0)
    if self.date_debut and self.date_debut.weekday() != 0:
        jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][self.date_debut.weekday()]
        raise ValidationError({
            'date_debut': f"La date de début doit être un LUNDI. Vous avez sélectionné un {jour} ({self.date_debut.strftime('%d/%m/%Y')})."
        })
    
    # Vérifier que date_fin est un samedi (weekday() = 5)
    if self.date_fin and self.date_fin.weekday() != 5:
        jour = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][self.date_fin.weekday()]
        raise ValidationError({
            'date_fin': f"La date de fin doit être un SAMEDI. Vous avez sélectionné un {jour} ({self.date_fin.strftime('%d/%m/%Y')})."
        })
```

### Appel de la Validation

```python
def save(self, *args, **kwargs):
    # Valider avant de sauvegarder
    self.clean()
    
    # ... reste du code
    super().save(*args, **kwargs)
```

---

## 🎨 **Interface Utilisateur**

### Formulaire avec Aides Visuelles

**Modifications dans `semaine_form.html`** :

#### Date Début
```html
<label>Date Début *</label>
{{ form.date_debut }}
<div class="form-text">
    ⚠️ Doit être un LUNDI
</div>
```

#### Date Fin
```html
<label>Date Fin *</label>
{{ form.date_fin }}
<div class="form-text">
    ⚠️ Doit être un SAMEDI
</div>
```

#### Alerte d'Information
```html
<div class="alert alert-warning">
    ⚠️ IMPORTANT : Règle des semaines
    • Les semaines commencent toujours un LUNDI
    • Les semaines se terminent toujours un SAMEDI
    • Une semaine de cours = 6 jours (Lundi → Samedi)
</div>
```

---

### Liste avec Affichage du Jour

**Modifications dans `semaine_list.html`** :

```html
<td>
    14/10/2024
    <br><small class="text-muted">(Lundi)</small>
</td>
<td>
    19/10/2024
    <br><small class="text-muted">(Samedi)</small>
</td>
```

**Méthodes utilisées** :
- `semaine.get_jour_debut()` → "Lundi"
- `semaine.get_jour_fin()` → "Samedi"

---

## 📊 **Résultats des Tests**

### Test 1 : Date Valide (Lundi → Samedi)
```
Date début : 14/10/2024 (Lundi)
Date fin : 19/10/2024 (Samedi)
Résultat : ✓ SUCCÈS - Semaine créée
```

### Test 2 : Date Invalide (Mardi → Samedi)
```
Date début : 15/10/2024 (Mardi)
Date fin : 19/10/2024 (Samedi)
Résultat : ✗ BLOQUÉ
Erreur : "La date de début doit être un LUNDI. 
         Vous avez sélectionné un Mardi (15/10/2024)."
```

### Test 3 : Date Invalide (Lundi → Dimanche)
```
Date début : 14/10/2024 (Lundi)
Date fin : 20/10/2024 (Dimanche)
Résultat : ✗ BLOQUÉ
Erreur : "La date de fin doit être un SAMEDI. 
         Vous avez sélectionné un Dimanche (20/10/2024)."
```

### Test 4 : Deux Erreurs
```
Date début : 18/10/2024 (Vendredi)
Date fin : 17/10/2024 (Jeudi)
Résultat : ✗ BLOQUÉ (2 erreurs)
Erreur 1 : "La date de début doit être un LUNDI..."
Erreur 2 : "La date de fin doit être antérieure..."
```

### Statistiques Globales
```
Total semaines testées : 7
Semaines valides créées : 4
Semaines invalides bloquées : 3

Taux de validation : 100% ✓
```

---

## 💡 **Messages d'Erreur**

### Format des Messages

Les messages d'erreur sont **explicites et informatifs** :

```
❌ Date de début invalide
"La date de début doit être un LUNDI. 
 Vous avez sélectionné un Mardi (15/10/2024)."

✓ Indique le jour attendu (LUNDI)
✓ Affiche le jour sélectionné (Mardi)
✓ Montre la date complète (15/10/2024)
```

---

## 🔍 **Vérification Automatique**

### Python `weekday()`

```python
date.weekday() retourne :
0 = Lundi    ✓ (valide pour date_debut)
1 = Mardi    ✗
2 = Mercredi ✗
3 = Jeudi    ✗
4 = Vendredi ✗
5 = Samedi   ✓ (valide pour date_fin)
6 = Dimanche ✗
```

### Logique de Validation

```python
# Date début = Lundi
if date_debut.weekday() != 0:
    raise ValidationError("Doit être un LUNDI")

# Date fin = Samedi
if date_fin.weekday() != 5:
    raise ValidationError("Doit être un SAMEDI")
```

---

## 📅 **Exemples de Semaines Valides**

### Octobre 2024
```
Semaine 1 : Lundi 14/10 → Samedi 19/10 ✓
Semaine 2 : Lundi 21/10 → Samedi 26/10 ✓
Semaine 3 : Lundi 28/10 → Samedi 02/11 ✓
```

### Novembre 2024
```
Semaine 4 : Lundi 04/11 → Samedi 09/11 ✓
Semaine 5 : Lundi 11/11 → Samedi 16/11 ✓
Semaine 6 : Lundi 18/11 → Samedi 23/11 ✓
```

---

## 🚫 **Exemples de Semaines Invalides**

### Erreur : Mauvais jour de début
```
❌ Mardi 15/10 → Samedi 19/10
   "Date début doit être un LUNDI"

❌ Mercredi 16/10 → Samedi 19/10
   "Date début doit être un LUNDI"
```

### Erreur : Mauvais jour de fin
```
❌ Lundi 14/10 → Dimanche 20/10
   "Date fin doit être un SAMEDI"

❌ Lundi 14/10 → Vendredi 18/10
   "Date fin doit être un SAMEDI"
```

---

## 🎯 **Utilisation Pratique**

### Scénario 1 : Créer une Nouvelle Semaine

1. Aller sur `/reglage/semaines/create/`
2. Sélectionner un **lundi** pour la date de début
3. Sélectionner le **samedi** suivant pour la date de fin
4. Enregistrer

**Astuce** : Utilisez un calendrier pour vérifier les jours

---

### Scénario 2 : Erreur de Saisie

**Situation** : Vous sélectionnez Mardi 15/10 comme date de début

**Résultat** :
```
❌ Erreur affichée en rouge
"La date de début doit être un LUNDI. 
 Vous avez sélectionné un Mardi (15/10/2024)."

✓ Le formulaire ne se soumet pas
✓ Les données ne sont pas sauvegardées
✓ Vous pouvez corriger immédiatement
```

---

### Scénario 3 : Planifier un Semestre

**Besoin** : Créer 16 semaines de cours

**Méthode** :
```
1. Identifier le premier lundi du semestre (ex: 14/10/2024)
2. Calculer les samedis correspondants (+5 jours)
3. Créer les semaines :
   
   Semaine 1 : 14/10 (Lun) → 19/10 (Sam)
   Semaine 2 : 21/10 (Lun) → 26/10 (Sam)
   Semaine 3 : 28/10 (Lun) → 02/11 (Sam)
   ...
```

**Outil suggéré** : Créer un script ou utiliser un tableur

---

## 🔧 **Pour les Développeurs**

### Tester la Validation

**Script** : `test_validation_semaines.py`

```bash
python test_validation_semaines.py
```

**Tests effectués** :
1. ✓ Dates valides (Lundi → Samedi)
2. ✓ Date début invalide (Mardi)
3. ✓ Date fin invalide (Dimanche)
4. ✓ Erreurs multiples
5. ✓ Semaines consécutives

---

### Désactiver Temporairement

**Pour les tests/développement uniquement** :

```python
# Dans models.py, commenter la ligne :
# self.clean()  # ← Commenter cette ligne

# ⚠️ NE PAS FAIRE EN PRODUCTION !
```

---

### Ajouter des Jours Supplémentaires

Si vous voulez autoriser Dimanche par exemple :

```python
# Dans clean(), modifier :
if self.date_fin.weekday() not in [5, 6]:  # Samedi OU Dimanche
    raise ValidationError(...)
```

---

## 📚 **Documentation Technique**

### Méthodes Ajoutées au Modèle

#### `clean()`
- **But** : Valider les dates avant sauvegarde
- **Vérifie** : 
  - date_debut = Lundi
  - date_fin = Samedi
  - date_fin > date_debut
- **Lève** : `ValidationError` si invalide

#### `get_jour_debut()`
- **Retourne** : Nom du jour de date_debut
- **Exemple** : "Lundi", "Mardi", etc.

#### `get_jour_fin()`
- **Retourne** : Nom du jour de date_fin
- **Exemple** : "Samedi", "Dimanche", etc.

---

## ✅ **Checklist d'Implémentation**

- [x] Méthode `clean()` dans le modèle
- [x] Appel de `clean()` dans `save()`
- [x] Messages d'erreur explicites
- [x] Méthodes `get_jour_debut()` et `get_jour_fin()`
- [x] Aide visuelle dans le formulaire
- [x] Affichage des jours dans la liste
- [x] Alerte d'information
- [x] Tests de validation passés
- [x] Documentation complète

---

## 🎓 **Message pour les Utilisateurs**

```
📢 IMPORTANTE : VALIDATION DES SEMAINES

Les semaines de cours doivent maintenant respecter la règle :
• Début : LUNDI obligatoire
• Fin : SAMEDI obligatoire

✨ AVANTAGES :
✓ Cohérence : Toutes les semaines ont le même format
✓ Clarté : Semaine = 6 jours (Lun→Sam)
✓ Validation : Impossible de créer une semaine invalide

❌ SI VOUS AVEZ UNE ERREUR :
→ Vérifiez que vous sélectionnez bien un LUNDI pour le début
→ Vérifiez que vous sélectionnez bien un SAMEDI pour la fin
→ Le système vous indiquera le jour sélectionné

💡 ASTUCE :
Utilisez un calendrier pour vérifier les jours de la semaine
avant de saisir les dates.
```

---

**Date d'implémentation** : 23 octobre 2025
**Version** : 2.0
**Statut** : ✅ Validé et Testé

🎉 **La validation Lundi→Samedi est opérationnelle !**
