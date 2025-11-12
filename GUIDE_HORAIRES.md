# 📅 Guide d'utilisation - Gestion des Horaires

## ✅ URLs disponibles

### Pages principales
- **Liste des horaires**: http://127.0.0.1:8000/attribution/schedule/entry/list/
- **Créer un horaire**: http://127.0.0.1:8000/attribution/schedule/entry/create/
- **Générateur PDF**: http://127.0.0.1:8000/attribution/schedule/

### API
- **Modifier**: http://127.0.0.1:8000/attribution/schedule/entry/<ID>/edit/
- **Supprimer**: http://127.0.0.1:8000/attribution/schedule/entry/<ID>/delete/ (POST)

## 🔧 Tests effectués

### ✓ Modèle ScheduleEntry
- ✅ 19 entrées existantes dans la base de données
- ✅ Création/Suppression fonctionne correctement
- ✅ Relations avec Attribution, Course, Teacher fonctionnent

### ✓ Formulaire ScheduleEntryForm
- ✅ Validation fonctionne correctement
- ✅ Tous les champs sont validés
- ✅ Instance créée avec succès

### ✓ Serveur Django
- ✅ Démarré sur http://127.0.0.1:8000/
- ✅ Aucune erreur de système détectée

## 📋 Structure des données

### Champs du modèle ScheduleEntry
```python
- attribution (ForeignKey → Attribution)
  ↳ contient: code_ue, intitule_ue, classe, enseignant, grade
- annee_academique (CharField, ex: "2024-2025")
- semaine_debut (DateField)
- jour (Choice: lundi, mardi, mercredi, jeudi, vendredi, samedi)
- creneau (Choice: am=08h00-12h00, pm=13h00-17h00)
- salle (CharField, optionnel)
- remarques (TextField, optionnel)
```

## 🎯 Comment utiliser

### 1. Accéder à la liste des horaires
```
URL: /attribution/schedule/entry/list/
```
- Filtrez par année académique, jour, créneau ou classe
- Cliquez sur "Ajouter un horaire" pour créer une nouvelle entrée

### 2. Créer un nouvel horaire
```
URL: /attribution/schedule/entry/create/
```
1. Sélectionnez un cours (qui contient déjà l'enseignant et ses infos)
2. Entrez l'année académique (ex: 2024-2025)
3. Sélectionnez la date de début de semaine
4. Choisissez le jour
5. Choisissez le créneau (AM ou PM)
6. Ajoutez la salle (optionnel)
7. Ajoutez des remarques (optionnel)
8. Cliquez sur "Créer"

### 3. Modifier un horaire existant
- Depuis la liste, cliquez sur l'icône ✏️ (Edit)
- Modifiez les champs nécessaires
- Cliquez sur "Modifier"

### 4. Supprimer un horaire
- Depuis la liste, cliquez sur l'icône 🗑️ (Trash)
- Confirmez la suppression

### 5. Générer un PDF d'horaires
```
URL: /attribution/schedule/
```
- Utilisez l'ancien formulaire pour générer rapidement un PDF
- Sélectionnez un cours, une date, un créneau
- Ajoutez à l'horaire ou générez directement le PDF

## 🐛 Résolution des problèmes

### Si les données ne s'enregistrent pas :

1. **Vérifier que le serveur est actif**
   ```bash
   python manage.py runserver
   ```

2. **Vérifier les migrations**
   ```bash
   python manage.py migrate attribution
   ```

3. **Vérifier les logs du serveur**
   - Regardez la console où le serveur tourne
   - Cherchez les erreurs en rouge

4. **Tester manuellement**
   ```bash
   python test_schedule.py
   python test_form_validation.py
   ```

5. **Vérifier qu'il existe des attributions**
   - Il faut d'abord créer des attributions (enseignant + cours)
   - Sans attribution, impossible de créer un horaire

### Erreur commune : "IntegrityError"
- Cette erreur survient si vous essayez de créer un horaire qui existe déjà
- La contrainte `unique_together` empêche les doublons
- Vérifiez qu'il n'y a pas déjà un horaire pour cette combinaison :
  * même attribution
  * même année académique
  * même semaine
  * même jour
  * même créneau

## 📊 Données actuelles

- **Horaires existants**: 19 entrées
- **Attributions disponibles**: 19 entrées
- **Modèle**: Opérationnel ✅
- **Formulaire**: Opérationnel ✅
- **Serveur**: En cours d'exécution ✅

## 🚀 Prochaines étapes

1. Testez l'accès aux pages web
2. Créez un nouvel horaire depuis l'interface
3. Vérifiez que l'horaire apparaît dans la liste
4. Générez un PDF pour voir le résultat

---

**Note**: Si vous rencontrez toujours des problèmes, vérifiez :
- Les logs dans la console du serveur
- Les messages d'erreur dans le navigateur (F12 > Console)
- Que vous êtes connecté (si authentification requise)
