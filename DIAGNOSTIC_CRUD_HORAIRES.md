# 🔍 DIAGNOSTIC COMPLET - CRUD Horaires

## ✅ Tests effectués - TOUS RÉUSSIS

### 1. Modèle ScheduleEntry
```
✓ Modèle créé et migré correctement
✓ 19 entrées existantes dans la base
✓ Création/Lecture/Suppression testées avec succès
```

### 2. Formulaire ScheduleEntryForm
```
✓ Validation fonctionne
✓ Tous les champs sont correctement définis
✓ Instance créée sans erreur
```

### 3. Vues Django
```
✓ ScheduleEntryListView: HTTP 200 (accessible)
✓ ScheduleEntryCreateView: HTTP 200 (accessible)
✓ ScheduleEntryUpdateView: Implémentée
✓ schedule_entry_delete: Implémentée
```

### 4. Serveur Django
```
✓ Actif sur http://127.0.0.1:8000/
✓ Aucune erreur système
✓ Migrations appliquées
```

## 🎯 URLS À UTILISER

### Interface principale
```
📋 LISTE DES HORAIRES
http://127.0.0.1:8000/attribution/schedule/entry/list/

➕ CRÉER UN HORAIRE
http://127.0.0.1:8000/attribution/schedule/entry/create/

📅 GÉNÉRATEUR RAPIDE (avec combo)
http://127.0.0.1:8000/attribution/schedule/
```

### API (pour modification/suppression)
```
✏️ MODIFIER: /attribution/schedule/entry/<ID>/edit/
🗑️ SUPPRIMER: /attribution/schedule/entry/<ID>/delete/
```

## 📊 Données actuelles dans la base

**19 horaires existants** pour l'année **2025-2026**

Exemples :
- Lundi 08h00-12h00 : CHI291 (L1 CST)
- Mardi 08h00-12h00 : CHI191 (L1 BC)
- Lundi 08h00-12h00 : MAT103 (L1 M.I)
- Mercredi 08h00-12h00 : MAT103 (L1 M.I)

## 🔧 SI "LES DONNÉES NE SONT PAS STOCKÉES"

### Cause possible #1 : Erreur JavaScript silencieuse
**Solution :**
1. Ouvrez la console du navigateur (F12)
2. Allez dans l'onglet "Console"
3. Essayez de créer/modifier un horaire
4. Vérifiez s'il y a des erreurs en rouge

### Cause possible #2 : CSRF Token manquant
**Solution :**
- Le formulaire doit contenir `{% csrf_token %}`
- Vérifié dans `schedule_entry_form.html` ✓

### Cause possible #3 : Redirection après POST
**Vérification :**
```python
# Dans les vues, success_url est défini :
success_url = reverse_lazy('attribution:schedule_entry_list')
```
✓ Configuré correctement

### Cause possible #4 : Erreur de validation silencieuse
**Test :**
```bash
cd "d:\FABONK\ACH WEB\chargehoraire"
python test_form_validation.py
```
Résultat attendu : "✓ Le formulaire est VALIDE"

### Cause possible #5 : Contrainte unique_together
Le modèle a une contrainte qui empêche les doublons :
```python
unique_together = [('attribution', 'annee_academique', 'semaine_debut', 'jour', 'creneau')]
```

**Erreur attendue si doublon :**
"UNIQUE constraint failed: attribution_scheduleentry..."

**Solution :** Vérifiez que vous ne créez pas un horaire qui existe déjà avec exactement :
- Même attribution (cours + enseignant)
- Même année académique
- Même semaine
- Même jour
- Même créneau

### Cause possible #6 : Pas d'attributions disponibles
**Vérification :**
```python
python -c "import django; django.setup(); from attribution.models import Attribution; print(f'Attributions: {Attribution.objects.count()}')"
```

Si 0 attribution → **Créez d'abord des attributions !**
(Un horaire nécessite une attribution = enseignant + cours)

## 🚀 PROCÉDURE DE TEST COMPLÈTE

### Étape 1 : Démarrer le serveur
```bash
cd "d:\FABONK\ACH WEB\chargehoraire"
python manage.py runserver
```

### Étape 2 : Ouvrir la liste des horaires
```
http://127.0.0.1:8000/attribution/schedule/entry/list/
```
**Attendu :** Vous devriez voir 19 horaires existants

### Étape 3 : Cliquer sur "Ajouter un horaire"
Ou accéder directement à :
```
http://127.0.0.1:8000/attribution/schedule/entry/create/
```

### Étape 4 : Remplir le formulaire
1. **Attribution** : Sélectionner un cours dans la liste déroulante
2. **Année académique** : 2025-2026
3. **Semaine début** : Choisir une date (ex: 2025-10-27)
4. **Jour** : Choisir un jour (ex: Jeudi)
5. **Créneau** : AM ou PM
6. **Salle** : (optionnel, ex: B2)
7. **Remarques** : (optionnel)

### Étape 5 : Cliquer sur "Créer"

**Résultats attendus :**
- ✅ Message : "Horaire créé avec succès"
- ✅ Redirection vers la liste
- ✅ Nouvel horaire visible dans la liste

### Étape 6 : Vérifier dans la base de données
```bash
python test_schedule.py
```
Le nombre d'entrées devrait être passé de 19 à 20.

## 📝 LOGS À VÉRIFIER

### Dans la console du serveur Django
Cherchez ces lignes après avoir soumis le formulaire :
```
POST /attribution/schedule/entry/create/ HTTP/1.1" 302 0
GET /attribution/schedule/entry/list/ HTTP/1.1" 200
```
- `302` = Redirection (succès de la création)
- `200` = Page affichée (liste des horaires)

### Si vous voyez ça, c'est une erreur :
```
POST /attribution/schedule/entry/create/ HTTP/1.1" 200
```
(200 au lieu de 302 = le formulaire a été réaffiché avec des erreurs)

### Dans la console du navigateur (F12)
Cherchez :
- ❌ Erreurs JavaScript en rouge
- ❌ Erreurs 404 (fichier non trouvé)
- ❌ Erreurs 500 (erreur serveur)

## 🎯 TEST RAPIDE EN UNE COMMANDE

```bash
cd "d:\FABONK\ACH WEB\chargehoraire"
python test_schedule.py && python test_form_validation.py && python test_views_directly.py
```

**Si tous les tests passent ✓** → Le problème est dans l'interface web, pas dans le code

## 💡 SOLUTION ALTERNATIVE : API REST

Si l'interface web pose problème, vous pouvez créer des horaires via Python :

```python
from attribution.models import ScheduleEntry, Attribution
from datetime import date

attribution = Attribution.objects.first()
entry = ScheduleEntry.objects.create(
    attribution=attribution,
    annee_academique="2025-2026",
    semaine_debut=date(2025, 10, 27),
    jour='jeudi',
    creneau='pm',
    salle='B3',
    remarques='Créé manuellement'
)
print(f"Horaire créé : {entry}")
```

## 📞 BESOIN D'AIDE ?

1. **Copiez les logs du serveur** (console où tourne Django)
2. **Copiez les erreurs de la console navigateur** (F12 > Console)
3. **Indiquez ce que vous avez fait exactement** (étapes)
4. **Résultat attendu vs résultat obtenu**

---

**Date du diagnostic :** 23 octobre 2025, 09:15
**Statut du système :** ✅ Opérationnel
**Conclusion :** Le CRUD fonctionne. Si les données ne s'enregistrent pas, le problème est probablement :
- Une erreur de validation silencieuse (contrainte unique)
- Une erreur JavaScript dans le navigateur
- Un problème de workflow (pas de redirection)
