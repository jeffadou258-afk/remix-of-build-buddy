# Socle de sécurité Admin v1 (sans dashboard, sans /admin)

## Constat (analyse)
- Il n'existe aucun rôle, aucune table d'audit et aucune permission. La seule protection est la règle « chacun ses projets », appliquée par la base de données.
- Les données client passent par deux chemins côté serveur : le relais `/api/ca/*` (vers ConstructionAgent) et `/api/chat` (ancien assistant). Ils lisent tous les deux le projet en tant qu'utilisateur connecté.
- Le relais refuse déjà `gates/*/decision` (liste blanche). Il n'existe donc encore aucune décision de Gate possible depuis l'application.
- Les secrets (`CA_API_KEY`, `LOVABLE_API_KEY`…) ne sont lus que côté serveur, mais rien n'empêche aujourd'hui une réponse du backend de les renvoyer telle quelle.

## Ce qui sera construit

### 1. Base de données (une migration)
- Liste des rôles `app_role` avec les codes de la spécification : `user` (client), `support` (assistance), `ops` (exploitation), `finance`, `admin`, `auditor` (auditeur).
- Table `user_roles` (utilisateur, rôle). Lecture : uniquement ses propres rôles. Aucune écriture depuis l'application : attribution seulement par une fonction serveur réservée à `admin`, jamais à soi-même.
- Table `role_permissions` : la matrice §1.2 de la spécification, saisie telle quelle dans la migration. Ce sont des règles de configuration, pas des données fictives.
- Table `account_status` (actif / suspendu), lue par le serveur avant toute action sensible.
- Fonctions SQL sécurisées `has_role()`, `has_permission()` et `is_suspended()`.
- Table `admin_audit_log`, en ajout seulement, avec les champs du §13. Une protection refuse toute modification et toute suppression, même par le service privilégié. Seuls `admin` et `auditor` peuvent la lire (`audit.read`). Aucune écriture directe depuis le navigateur : elle passe par une fonction SQL `log_admin_action()`, appelée par le serveur.
- Table `project_access_grants` : un accès temporaire (60 min) au contenu d'un projet, avec un motif obligatoire. Il est visible par le client propriétaire.
- Les règles actuelles « chacun ses projets » ne changent pas. Aucun rôle, même `admin`, ne reçoit d'accès direct au contenu des clients.

### 2. Vérifications côté serveur (code de l'application)
- `src/lib/security/permissions.ts` : la liste des permissions et des interdits absolus (§1.3), sans logique métier ConstructionAgent.
- `src/lib/security/guard.server.ts` : `requirePermission(perm)`, qui vérifie dans l'ordre §1.4 : session (401), compte non suspendu (403), permission (403 + audit « denied »), puis audit « allowed ». Le rôle est toujours lu depuis la base, jamais depuis le navigateur.
- `src/lib/security/redact.server.ts` : retire de toute réponse les clés, jetons et secrets, par nom de champ et par forme de valeur (`sb_secret_`, `Bearer …`, la valeur des variables secrètes). Ce filtre est appliqué au relais `/api/ca/*` et aux futures fonctions Admin.
- `src/lib/security/admin.functions.ts` : les seules fonctions sensibles de cette étape, sans interface :
  - `requestProjectContentAccess(projectId, motif)` : `projects.read_content`, ouvre un accès de 60 min et l'inscrit au journal ;
  - `readProjectContentAudited(projectId)` : vérifie l'accès, l'inscrit au journal, puis lit le projet ;
  - `grantRole` / `revokeRole` : `roles.manage`, refusé sur soi-même, avec l'avant / après inscrit au journal ;
  - `listAuditLog` : `audit.read`.

### 3. Changements strictement nécessaires dans le parcours client
- Relais `src/routes/api/ca.$.ts` :
  - filtrage des secrets sur les réponses ;
  - refus d'un compte suspendu ;
  - toute future décision de Gate refusée (403 + audit) si l'appelant n'est pas le propriétaire du projet, ou s'il agit avec un rôle autre que client. Aujourd'hui, la décision reste de toute façon bloquée par la liste blanche.
- `src/routes/api/chat.ts` : refus d'un compte suspendu. Le reste ne change pas.
- Aucun changement visible pour le client.

### 4. Tests (`src/test/`)
- `security-permissions.test.ts` : la matrice §1.2 (par exemple `finance` sans `projects.read_content`, `auditor` sans aucune écriture), et les interdits §1.3 pour tous, y compris `admin`.
- `security-redact.test.ts` : aucune clé ni aucun jeton dans une réponse filtrée.
- `security-gate-authority.test.ts` : un admin, ou un autre utilisateur, ne peut pas décider d'un Gate. Seul le propriétaire le peut.
- Tests réels sur la base, via des requêtes SQL : la modification et la suppression d'une ligne d'audit sont refusées, un utilisateur ne voit pas les rôles d'un autre, et un utilisateur ne lit pas le projet d'un autre.

## Hors périmètre
Pas de page `/admin`, pas de double authentification (ce sera l'étape dashboard), pas de modification de ConstructionAgent ni des 13 moteurs, pas de données fictives. Aucun admin n'est attribué tant que vous n'avez pas désigné le premier.

## Point à confirmer
Codes des rôles : je garde ceux de la spécification (`user`, `support`, `ops`, `finance`, `admin`, `auditor`), avec les libellés français affichés plus tard (client, assistance, exploitation, finance, admin, auditeur).

## Fichiers
Créés : 1 migration, `src/lib/security/permissions.ts`, `guard.server.ts`, `redact.server.ts`, `admin.functions.ts`, 3 tests.
Modifiés : `src/routes/api/ca.$.ts`, `src/routes/api/chat.ts`, `AGENTS.md`, `roadmap.md`.
