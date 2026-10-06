# Shell de l'espace /admin v1 (interface + contrôle d'accès serveur)

## Principe
- Espace séparé de l'espace client : layout propre, aucun lien depuis l'espace client sauf pour un compte ayant au moins une permission admin (lien affiché selon la réponse du serveur, jamais selon le navigateur).
- Accès décidé uniquement côté serveur : une fonction serveur `getAdminAccess` (session + `has_permission` en base + suspension) renvoie les permissions effectives de l'appelant. Si aucune permission admin ou compte suspendu : écran « Accès refusé » et refus journalisé via `log_security_event`.
- Chaque section exige sa propre permission (vérifiée serveur à l'entrée de la section) :

```text
Dashboard        -> au moins une permission admin
Utilisateurs     -> users.read
Projets          -> projects.read_meta   (métadonnées seulement, aucun contenu)
Gates            -> gates.read           (lecture, aucune décision possible)
Moteurs          -> engines.read
Usage & coûts    -> usage.read ou costs.read
Audit            -> audit.read
Santé système    -> health.read
Sécurité         -> security.read
```
- Le menu latéral n'affiche que les sections autorisées ; l'accès direct par URL à une section non autorisée est aussi refusé par le serveur.

## Contenu des pages (aucune fausse donnée)
- Chaque section affiche titre, permission requise, et un état « Données non encore branchées — NON MESURÉ ». Aucun chiffre, aucune ligne fictive.
- Seule exception déjà prête : Audit peut lister le vrai journal via `listAuditLog` existant (lecture seule). À confirmer : je peux le laisser non branché si vous préférez.
- Aucun bouton d'action (suspendre, rôles, Gates, moteurs) dans cette étape.
- Projets : aucun accès au contenu client ; l'accès motivé (`request_project_access`) n'est pas exposé ici.

## Fichiers
Créés :
- `src/lib/security/admin-access.functions.ts` — `getAdminAccess` et `requireAdminSection(section)` (serveur, réutilisent `guard.server.ts`).
- `src/lib/security/admin-sections.ts` — liste des sections et permission requise (affichage uniquement, ne décide pas).
- `src/routes/_authenticated.admin.tsx` — layout /admin : appel serveur, menu filtré, écran refusé, `<Outlet />`.
- `src/routes/_authenticated.admin.index.tsx` (Dashboard), `.utilisateurs.tsx`, `.projets.tsx`, `.gates.tsx`, `.moteurs.tsx`, `.usage.tsx`, `.audit.tsx`, `.sante.tsx`, `.securite.tsx`.
- `src/components/admin/AdminSection.tsx` — gabarit de page (vérification serveur + état non branché).
- `src/test/admin-access.test.ts` — client sans rôle refusé partout ; auditeur limité à Dashboard/Gates/Audit/Sécurité ; finance sans Audit ; admin voit les 9 sections ; aucune section n'expose une permission interdite.

Modifiés :
- `src/components/SiteHeader.tsx` — lien « Admin » seulement si le serveur confirme l'accès.
- `AGENTS.md` — règle sur l'espace /admin.
- `roadmap.md`.

Non modifiés : base de données (aucune migration), ConstructionAgent et ses 13 moteurs, relais `/api/ca`, parcours client.

## Vérification
- Tests Vitest complets + nouveaux tests.
- Navigateur avec votre compte admin : 9 sections visibles. Simulation d'un compte sans rôle (session annulée côté base) : refus.
