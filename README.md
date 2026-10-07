# ConstructionAgent — application + moteur

Dépôt unique du produit **ConstructionAgent** : l'application web et le moteur
d'architecture qui la fait fonctionner.

```
.
├── src/ , public/ , package.json …   ← APPLICATION (TanStack Start + React 19 + Supabase)
├── supabase/                          ← configuration du projet Supabase
└── agent/                             ← MOTEUR (Python, API v1, Blender)
```

## Les deux composants

| Composant | Emplacement | Déploiement | Rôle |
|---|---|---|---|
| **Application web** | racine du dépôt | **Vercel** | Interface : comptes, projets, chat, maquette 3D, espace admin, Gates |
| **Base de données** | Supabase | **Supabase** | Tables, RLS, rôles, fonctions `SECURITY DEFINER` |
| **Moteur `/v1`** | `agent/` | **Render** | 13 moteurs Python + rendus Blender |

> Le moteur ne peut **pas** tourner sur Vercel : Blender pèse 335 Mo et exige
> Docker + un disque persistant. Il va sur Render (`agent/render.yaml`).

L'application ne parle jamais directement au moteur : elle passe par le relais
serveur `/api/ca/…` (`src/routes/api/ca.$.ts`), qui garde la clé API côté serveur
et n'autorise qu'une liste d'endpoints.

## Développer l'application

```sh
npm i
npm run dev
```

Build de production (sortie Vercel `.vercel/output`) :

```sh
npm run build
npx vercel deploy --prebuilt
```

## Développer le moteur

```sh
cd agent
python3 run_agent.py workspace/mon_projet          # chaîne complète
python3 tests/minimal_install_test.py              # test d'installation obligatoire
```

API `/v1` en local :

```sh
cd agent/web/api
CA_API_KEY="<32 caractères minimum>" CA_API_PORT=8766 python3 server.py
# GET http://127.0.0.1:8766/v1/health
```

Chaque requête (hors `/v1/health`) exige `Authorization: Bearer <clé>` **et**
`X-Owner-Id`. Détail du parcours et pièges : `agent/SKILL.md`.

## Base de données

Schéma : 7 tables, 2 enums, 12 fonctions SQL. Inventaire :
`scripts/schema_inventory.py`.

---

Ce projet a été initialement construit avec [Lovable](https://lovable.dev).
Éditeur : https://lovable.dev/projects/5ba654e7-96b3-4dab-abc5-648b8d8ffd44

> **Ne jamais réécrire l'historique publié** (force push, rebase, squash de
> commits déjà poussés) : cela réécrit l'historique côté Lovable et fait perdre
> l'historique du projet.
