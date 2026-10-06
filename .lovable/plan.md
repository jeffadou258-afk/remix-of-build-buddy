# Connexion de l'application à l'API ConstructionAgent v1 : premier parcours

## Ce qui a été vérifié

- L'API v1 démarre dans l'environnement de travail (127.0.0.1:8766). `GET /v1/health` répond bien : 13 moteurs, gates `design` et `structural_concept`.
- Elle n'écoute que sur 127.0.0.1 et exige `Authorization: Bearer <CA_API_KEY>` et `X-Owner-Id` sur chaque requête.
- **Ce qui peut la joindre :**
  - le serveur de développement de l'application (localhost:8080), qui tourne sur la même machine. C'est là que le parcours sera testé de bout en bout.
  - pas l'aperçu Lovable ni le site publié, qui tournent ailleurs. Ils ne pourront la joindre que quand vous l'aurez mise en ligne (tunnel ou serveur), ce qui est hors périmètre ici. Tant que l'API n'est pas joignable, l'application affiche clairement « Backend ConstructionAgent injoignable ». Elle ne bascule jamais en silence sur l'ancien assistant local.

## Architecture

```text
Navigateur ── jeton de session ──> Relais serveur de l'app (/api/ca/*)
                                    1. vérifie la session
                                    2. vérifie que le projet appartient à l'utilisateur (RLS)
                                    3. ajoute Bearer CA_API_KEY + X-Owner-Id = id utilisateur
                                    4. ne laisse passer que les adresses /v1 de la liste
                                  ──> API ConstructionAgent v1 ──> moteurs réels
```

- **Relais** : une seule route serveur `src/routes/api/ca.$.ts`. Elle n'accepte que les adresses de la liste ci-dessous et refuse toutes les autres (404), sans aucune logique métier. La clé n'est jamais envoyée au navigateur.
- **Secrets** : `CA_API_URL` et `CA_API_KEY`. Pour le test, la clé est générée et l'API locale est démarrée avec cette même valeur. Pour la mise en ligne, vous la remplacerez par votre propre clé.
- **Correspondance des projets** : une nouvelle colonne `projects.ca_project_id` relie le projet Lovable au projet ConstructionAgent (`P_…`). Aucune donnée existante n'est supprimée.
- **Source de vérité** : pour les projets reliés, la conversation, les informations et les gates sont lus depuis l'API. Les anciens projets non reliés gardent leur comportement actuel, qui reste visible et non supprimé.

## Parcours vertical (seul connecté maintenant)

| Étape | Endpoint /v1 réellement existant |
|---|---|
| Créer le projet | `POST /v1/projects` (puis enregistre `ca_project_id`) |
| Récupérer le projet | `GET /v1/projects/{id}` (projet, état, gates) |
| Envoyer un message, extraction | `POST /v1/projects/{id}/messages`, `GET .../messages` |
| Onglet Informations | `GET .../inputs`, `PATCH .../inputs` (corrections faites par le moteur) |
| Lancer un run | `POST .../runs` (409 = blocage renvoyé tel quel) |
| Recevoir la gate | `GET .../gates`, état via `GET .../state` |

Pour obtenir une gate, il faut des pièces (le moteur Programme bloque sans elles). Le test utilise donc aussi `POST .../rooms`, une adresse existante, depuis l'onglet Informations.

## Interface

- Page projet : un bandeau « Connecté à ConstructionAgent » avec l'état d'exécution et les gates.
- Conversation : le message part vers l'API, et on affiche ce qu'elle renvoie (ce qui a été extrait, ce qui reste UNKNOWN). Aucune réponse IA n'est produite pour les projets reliés.
- Onglet Informations : il lit et écrit via l'API. Le formulaire actuel reste le même, mais `applyEdit` n'est plus utilisé pour ces projets. Les modifications passent par `PATCH .../inputs`.
- Bouton « Lancer l'exécution », puis affichage du résultat du run et de la gate ouverte.
- Pas encore connectés : décisions sur les gates, Memory, programme, plans, BIM, maquette 3D, historique. Ils seront branchés après validation de ce parcours.

## Tests

- **Avant** : tests vitest de l'application, et tests de l'API (13/13) avec la non-régression V3.4.
- **Ajoutés** : tests du relais : refus sans session, refus d'une adresse hors liste, refus d'un projet d'un autre utilisateur, clé jamais renvoyée.
- **Parcours réel** : Playwright sur localhost:8080, avec l'API locale et un compte (créé via `lovable auth-session` s'il en existe un, sinon je vous le demande).
- **Après** : relance de toutes les séries.

## Détails techniques

- Migration : `ALTER TABLE projects ADD COLUMN ca_project_id text UNIQUE`. Les règles d'accès actuelles s'appliquent déjà à cette colonne.
- Fichiers : `src/routes/api/ca.$.ts`, `src/lib/ca/client.ts` (appels côté navigateur vers le relais), `src/lib/ca/allowlist.ts` (+ test), modifications de `_authenticated.projets.index.tsx`, `_authenticated.projets.$id.tsx` et `InputsPanel.tsx`.
- Aucune modification du dépôt ConstructionAgent, aucun espace Admin, aucune mise en ligne publique de l'API.
