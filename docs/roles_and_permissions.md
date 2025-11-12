# Système de Rôles et Permissions

Ce document décrit le système de rôles et de permissions dans l'application de gestion de la charge horaire.

## Rôles disponibles

### Rôles administratifs (Accès complet)
Ces rôles peuvent voir et modifier toutes les données dans l'application, y compris les sections de finance, de réglage, et la gestion des utilisateurs.

- **Administrateur (admin)** : Accès complet à toutes les fonctionnalités de l'application.
- **Directeur Général (dg)** : Accès complet à toutes les fonctionnalités de l'application.
- **Secrétaire Général Académique (sgac)** : Accès complet à toutes les fonctionnalités de l'application.
- **Secrétaire Général à la Recherche (sgr)** : Accès complet à toutes les fonctionnalités de l'application.
- **Secrétaire Général Administratif (sgad)** : Accès complet à toutes les fonctionnalités de l'application.
- **Agent Budgétaire (ab)** : Accès complet à toutes les fonctionnalités de l'application.

### Rôles de section
Ces rôles ont un accès limité à leur section et aux départements qui y sont rattachés.

- **Chef de Section (cs)** : Accès aux données de sa section et de ses départements.
- **Chef de Section aux Affaires Estudiantines (csae)** : Accès aux données de sa section et de ses départements, spécialisé dans les affaires estudiantines.
- **Chef de Section à la Recherche (csr)** : Accès aux données de sa section et de ses départements, spécialisé dans la recherche.
- **Service d'Appui aux Activités Scientifiques (saas)** : Accès aux données de sa section et de ses départements, spécialisé dans les activités scientifiques.

### Rôles de département
Ces rôles ont un accès limité à leur département.

- **Chef de Département (cd)** : Accès aux données de son département uniquement.
- **Secrétaire de Département (sd)** : Accès aux données de son département uniquement.

### Rôles de base
Ces rôles ont un accès très limité.

- **Enseignant (enseignant)** : Accès à son profil, liste des enseignants (lecture seule), et liste des UE (lecture seule).
- **Étudiant (etudiant)** : Accès uniquement à la liste des UE de son département.
- **Personnel administratif (personnel_admin)** : Accès limité selon les besoins spécifiques.

## Attribution automatique des rôles

Les rôles sont automatiquement attribués en fonction de la fonction de l'enseignant lors de la création d'un compte utilisateur pour un enseignant existant. Par exemple:

- Un enseignant avec fonction "DG" recevra le rôle "Directeur Général"
- Un enseignant avec fonction "CD" recevra le rôle "Chef de Département"
- Un enseignant avec fonction "ENS" ou "ENSEIGNANT" recevra le rôle "Enseignant"

## Restrictions par section

Les utilisateurs avec des rôles de chef de section (CS, CSAE, CSR, SAAS) sont limités aux données de leur propre section. Pour que cette restriction fonctionne correctement:

1. Chaque utilisateur avec un rôle de section doit avoir son champ "section" rempli dans son profil
2. Les administrateurs peuvent définir la section d'un utilisateur dans le formulaire de gestion des rôles
3. Le middleware vérifie automatiquement l'accès aux données de section

Exemple: Un utilisateur avec le rôle "CS" et la section "INFO" ne pourra voir que les données de la section Informatique, pas celles des autres sections.

## Permissions fonctionnelles

- **Accès aux réglages** : Administrateurs et rôles administratifs
- **Accès aux finances** : Administrateurs et rôles administratifs
- **Création d'utilisateurs** : Administrateurs et rôles administratifs
- **Modification des cours et enseignants** : Administrateurs, rôles administratifs, chefs de section et chefs de département

## Remarques importantes

1. Les permissions sont vérifiées à chaque requête via un middleware spécifique.
2. Les templates utilisent les variables de contexte pour afficher/masquer des éléments selon les permissions.
3. Chaque vue est protégée par des décorateurs ou mixins de permissions.
