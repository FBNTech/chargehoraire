# Système de gestion des rôles utilisateurs

Ce document décrit le système de gestion des rôles utilisateurs basé sur les fonctions des enseignants.

## Rôles disponibles

Le système comprend les rôles suivants, organisés par niveau d'accès:

### Rôles administratifs
- **Administrateur**: Accès complet à toutes les fonctionnalités, y compris la finance et la création d'utilisateurs
- **Direction (DG, SGAC, SGR, SGAD, AB)**: Accès à toutes les fonctionnalités sauf la finance et la création d'utilisateurs

### Rôles de section
- **Chefs de section (CS, CSAE, CSR, SAAS)**: Accès limité aux informations de leur section et des départements d'attache

### Rôles de département
- **Chefs de département (CD, SD)**: Accès limité aux informations de leur département uniquement

### Rôles de base
- **Enseignant**: Accès limité en lecture seule à son profil, la liste des enseignants et la liste des UE (sans pouvoir ajouter, modifier ou supprimer)
- **Étudiant**: Accès uniquement à la liste des UE de leur département

## Permissions par fonctionnalité

| Fonctionnalité | Administrateurs | Direction | Chefs de section | Chefs de département | Enseignants | Étudiants |
|----------------|-----------------|-----------|------------------|----------------------|------------|-----------|
| Liste des enseignants | ✓ Accès total | ✓ Accès total | ✓ Section uniquement | ✓ Département uniquement | ✓ Lecture seule sans actions | ✗ |
| Liste des UE | ✓ Accès total | ✓ Accès total | ✓ Section uniquement | ✓ Département uniquement | ✓ Lecture seule sans actions | ✓ Département uniquement |
| Attribution | ✓ Accès total | ✓ Accès total | ✓ Section uniquement | ✓ Département uniquement | ✗ | ✗ |
| Liste des charges | ✓ Accès total | ✓ Accès total | ✓ Section uniquement | ✓ Département uniquement | ✗ | ✗ |
| Réglage | ✓ Accès total | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestion administrative | ✓ Accès total | ✓ Accès total | ✗ | ✗ | ✗ | ✗ |
| Suivi des enseignements | ✓ Accès total | ✓ Accès total | ✓ Section uniquement | ✓ Département uniquement | ✗ | ✗ |
| Finance | ✓ Accès total | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestion des utilisateurs | ✓ Accès total | ✗ | ✗ | ✗ | ✗ | ✗ |

## Attribution automatique des rôles

Le système peut attribuer automatiquement les rôles en fonction de la fonction de l'enseignant:

1. Si un utilisateur est associé à un enseignant (via le matricule)
2. Le système peut synchroniser le rôle utilisateur avec la fonction de l'enseignant
3. La synchronisation peut être lancée manuellement depuis la page de gestion des rôles

## Fonctions et rôles associés

| Fonction | Rôle attribué |
|----------|---------------|
| DG | Direction - Directeur Général |
| SGAC | Direction - Secrétaire Général Académique |
| SGR | Direction - Secrétaire Général à la Recherche |
| SGAD | Direction - Secrétaire Général Administratif |
| AB | Direction - Agent Budgétaire |
| CS | Chef de Section |
| CSAE | Chef de Section aux Affaires Estudiantines |
| CSR | Chef de Section à la Recherche |
| SAAS | Service d'Appui aux Activités Scientifiques |
| CD | Chef de Département |
| SD | Secrétaire de Département |
| ENS/ENSEIGNANT | Enseignant |

## Comment configurer les rôles

1. Utiliser la commande `python manage.py create_roles` pour créer tous les rôles dans la base de données
2. Assigner les rôles aux utilisateurs via l'interface d'administration ou la page de gestion des rôles
3. Pour synchroniser automatiquement avec la fonction d'un enseignant, cocher l'option dans la page de gestion des rôles
