# Bootstrap du premier administrateur

## Constat (lecture seule, déjà vérifié)
- Compte unique dans l'application : jeffadou258@gmail.com (id ca2da636-0bf9-4094-914a-936571988664).
- Aucun rôle attribué à personne (0 admin). Journal d'audit vide.
- Le rôle admin prévoit 23 permissions, dont roles.manage et audit.read.

## Pourquoi pas `grant_role`
`grant_role` exige déjà roles.manage et interdit de s'attribuer un rôle à soi-même. Sans aucun admin, il ne peut donc pas servir au premier. C'est voulu : aucune voie applicative ne permet de devenir admin seul.

## Opération (une seule migration, à usage unique)
1. Vérifie dans la base qu'aucun admin n'existe ; sinon l'opération s'annule entièrement.
2. Vérifie que l'id cible correspond bien à jeffadou258@gmail.com ; sinon annulation.
3. Ajoute le rôle admin à ce seul compte.
4. Écrit une entrée dans le journal d'audit : action `roles.bootstrap_first_admin`, résultat `allowed`, avant `[]`, après `["admin"]`, motif « Bootstrap du premier administrateur (approuvé par le propriétaire) ».
5. Aucune fonction, règle d'accès ou code n'est modifié. Pas de /admin, ConstructionAgent intact.

## Vérifications après
- Le compte a le rôle admin et une seule entrée d'audit existe.
- En simulant une session à votre nom : has_permission vrai pour roles.manage, audit.read et les 23 permissions admin ; lecture du journal autorisée.
- En simulant un client sans rôle (session annulée) : `grant_role` vers admin refusé, écriture directe dans user_roles refusée, `log_admin_action` non appelable.
- Vous ne pouvez pas vous retirer/ré-attribuer vous-même (self_grant_forbidden).
- Relance des tests de sécurité de l'application.
