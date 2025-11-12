# Restrictions d'accès pour les rôles de section

Ce document décrit les restrictions d'accès mises en place pour les utilisateurs ayant des rôles de section (CS, CSAE, CSR, SAAS) dans l'application.

## Rôles de section concernés

- **Chef de Section (CS)**
- **Chef de Section aux Affaires Estudiantines (CSAE)**
- **Chef de Section à la Recherche (CSR)**
- **Service d'Appui aux Activités Scientifiques (SAAS)**

## Principe général

Les utilisateurs avec un rôle de section ne peuvent voir et manipuler que les données relatives à leur propre section. Ils ne peuvent pas accéder aux données des autres sections.

## Fonctionnement de la restriction

1. Chaque utilisateur avec un rôle de section doit avoir un champ `section` renseigné dans son profil.
2. Lors de chaque requête, le middleware `RoleBasedAccessMiddleware` vérifie si l'utilisateur tente d'accéder à des données d'une section autre que la sienne.
3. Si c'est le cas, l'accès est refusé et l'utilisateur est redirigé vers le tableau de bord avec un message d'avertissement.

## Types de restrictions appliquées

1. **Restriction par paramètre d'URL**: Si un paramètre `section` est présent dans l'URL et ne correspond pas à la section de l'utilisateur, l'accès est refusé.
2. **Restriction par segment d'URL**: Si l'URL contient un segment de la forme `/section/{code}/`, l'accès est vérifié.
3. **Restriction par page**: Certaines pages sont spécifiquement restreintes aux données de la section de l'utilisateur.

## Utilisation dans les templates

Les templates peuvent utiliser la fonction `can_view_section_data` pour conditionner l'affichage d'éléments:

```html
{% if can_view_section_data 'CS001' %}
    <!-- Contenu spécifique à la section CS001 -->
{% endif %}
```

## Configuration pour un utilisateur

Pour configurer correctement un utilisateur avec un rôle de section:

1. Attribuer le rôle approprié (CS, CSAE, CSR ou SAAS) via l'interface de gestion des rôles.
2. Dans le profil utilisateur, renseigner le champ "Section" avec le code de la section à laquelle l'utilisateur appartient.

## Comportements spécifiques

### Chefs de section

- Peuvent voir tous les départements rattachés à leur section
- Ne peuvent pas voir les données des autres sections
- Ont accès aux fonctionnalités d'attribution et de suivi mais limitées à leur section
- Peuvent voir la liste des enseignants et des cours mais uniquement ceux rattachés à leur section

## Notes techniques

Pour le développement futur, il est recommandé:

1. D'établir une relation entre les sections et les départements dans la base de données
2. De compléter la fonction `check_department_belongs_to_section` pour vérifier correctement cette relation
3. D'ajouter des contraintes supplémentaires dans les vues pour filtrer les données par section
