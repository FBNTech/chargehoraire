# Guide de test des restrictions d'accès par section

Ce document décrit les étapes à suivre pour tester les restrictions d'accès basées sur les sections.

## Préparation des données de test

1. Créer plusieurs utilisateurs avec différents rôles:
   - Un utilisateur avec le rôle "CS" (Chef de Section) pour la section "INFO"
   - Un utilisateur avec le rôle "CSAE" (Chef de Section aux Affaires Estudiantines) pour la section "GESTION"
   - Un utilisateur avec des rôles administratifs (DG, SGAC, etc.)
   - Un utilisateur standard avec le rôle "Enseignant"

2. Vérifier que les utilisateurs avec des rôles de section ont bien leur champ "section" renseigné.

## Tests à effectuer

### Test du middleware

1. Connectez-vous en tant qu'utilisateur "CS" de la section "INFO"
2. Essayez d'accéder à une URL qui contient un identifiant de section différent, par exemple `/sections/GESTION/details/`
3. Vérifiez que l'accès est refusé et que vous êtes redirigé vers le tableau de bord avec un message d'erreur

### Test des permissions dans les templates

1. Connectez-vous en tant qu'utilisateur "CS" de la section "INFO"
2. Accédez à la page exemple `/examples/section_based_permission_example/`
3. Vérifiez que seules les données de la section "INFO" sont affichées, et que les autres sections ne sont pas visibles

### Test des vues filtrées

1. Créez quelques enseignants associés à différentes sections
2. Connectez-vous en tant qu'utilisateur "CS" de la section "INFO"
3. Accédez à la liste des enseignants
4. Vérifiez que seuls les enseignants de la section "INFO" sont affichés

### Test des utilisateurs administratifs

1. Connectez-vous en tant qu'utilisateur avec un rôle administratif (DG, SGAC, SGR, SGAD, AB)
2. Accédez à toutes les pages ci-dessus
3. Vérifiez que vous pouvez voir toutes les sections et leurs données

## Résolution des problèmes courants

### Si les restrictions ne fonctionnent pas:

1. Vérifiez que la colonne 'section' existe bien dans la base de données
2. Vérifiez que les utilisateurs avec des rôles de section ont bien leur champ "section" renseigné
3. Vérifiez que le middleware `RoleBasedAccessMiddleware` est correctement enregistré dans `MIDDLEWARE`
4. Examinez les logs pour voir si des erreurs sont générées lors des vérifications de permission

### Si les restrictions sont trop restrictives:

1. Vérifiez que les administrateurs et les rôles administratifs sont bien exemptés des restrictions
2. Vérifiez que la condition `not check_admin_permission(request.user)` est bien présente dans le middleware pour les vérifications de section
