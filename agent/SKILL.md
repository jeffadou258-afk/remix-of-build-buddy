---
name: construction-agent
description: "Pilote un projet de construction, de l'idée à la réception."
category: productivity
tags:
  - construction
  - architecture
  - bim
  - blender
  - rendu
  - plans
  - permis
  - chantier
  - preuve
  - qa
author: Jeff Adou
version: 2.0.0
---

# Construction Agent — v2.0.0

Agent de production architecturale **orienté preuves**. Transforme un besoin en
projet documenté et vérifiable : programme → contraintes → conception → plans →
maquette 3D → rendus → documentation → QA → livraison.

L'agent est **installé et exécutable** dans `/Users/mac/ConstructionAgent/`.
Ce skill est sa porte d'entrée : lis-le, puis pilote l'agent via `terminal`.

## Règle absolue — NO FAKE EXECUTION

**Aucun `SUCCESS` / `COMPLETED` / `READY` / `PASSED` sans preuve observable.**

INTERDIT : inventer un fichier, un chemin, une surface, un rendu, une résolution,
un checksum, un résultat Blender, un test réussi, un export, une livraison,
l'usage d'un outil, le lancement d'un moteur.

Preuve = fichier réellement présent + taille réelle + SHA-256 réel + sortie réelle
d'une commande (code retour) + inspection réelle de l'image.

**Piège majeur déjà rencontré** : un agent précédent a déclaré 8 rendus PNG
« réussis » alors qu'aucun fichier n'existait, puis a accusé un « environnement
Hermes isolé ». Le backend terminal est `local` (`HOME=/Users/mac`) : l'agent
écrit DIRECTEMENT sur le Mac. Avant toute explication d'échec, vérifier
`echo $HOME; pwd` et l'existence réelle du fichier.

Si un `cp` renvoie `zsh: no matches found` ou `No such file or directory`,
**la source n'existe pas** — le dire, ne pas le contourner par un ZIP ou un serveur HTTP.

## Quand l'utiliser

- Concevoir une maison : programme, surfaces, zoning, variantes
- Produire des plans, une maquette 3D ou des rendus architecturaux
- Documenter un projet (rapport, hypothèses, décisions)
- Contrôler la cohérence (surfaces, dimensions, QA)
- Livrer un paquet de livrables vérifié

Ne pas utiliser pour : calcul structurel réglementaire, diagnostic, permis signé,
conformité réglementaire opposable (→ human gate, professionnel habilité).

## Prérequis réels (vérifiés le 2026-10-02)

| Outil | Statut |
|---|---|
| Blender **5.2.2 LTS** | `/Applications/Blender.app/Contents/MacOS/Blender` |
| `python3` 3.9.6 | `/usr/bin/python3` (`requests` seul) |
| `sips` | `/usr/bin/sips` — largeur/hauteur d'image |
| `zip`, `git`, `ffmpeg` 9.0.1 | disponibles |
| FreeCAD / OpenSCAD / Inkscape / LibreOffice / ImageMagick / ffprobe | **ABSENTS** |

> `which blender` renvoie vide : Blender n'est pas dans le `PATH`.
> **Toujours** utiliser le chemin absolu du bundle `.app`.

## Comment lancer

```bash
cd /Users/mac/ConstructionAgent

# test minimal obligatoire (cree txt + blend + png, verifie chaque fichier)
terminal(command="cd /Users/mac/ConstructionAgent && python3 tests/minimal_install_test.py", timeout=600)

# projet complet (s'arrete aux human gates)
terminal(command="cd /Users/mac/ConstructionAgent && python3 run_agent.py projects/PRJ_xxx --yes", timeout=2400)

# un seul moteur
terminal(command="cd /Users/mac/ConstructionAgent && python3 engines/bim_3d/engine.py projects/PRJ_xxx", timeout=900)
```

## Reference rapide

| Besoin | Commande |
|---|---|
| Détecter l'environnement | `python3 engines/discovery/engine.py <PRJ>` |
| Programme + surfaces | `python3 engines/programming/engine.py <PRJ>` |
| Site / contraintes | `python3 engines/site_analysis/engine.py <PRJ>` |
| Variantes A/B/C | `python3 engines/design/engine.py <PRJ>` |
| Dimensions | `python3 engines/dimension/engine.py <PRJ>` |
| Plans SVG | `python3 engines/floor_plan/engine.py <PRJ>` |
| Structure conceptuelle | `python3 engines/structural_concept/engine.py <PRJ>` |
| Maquette `.blend` | `python3 engines/bim_3d/engine.py <PRJ>` |
| Intentions de vue | `python3 engines/visualization/engine.py <PRJ>` |
| Rendus PNG | `python3 engines/rendering/engine.py <PRJ>` |
| Rapport | `python3 engines/documentation/engine.py <PRJ>` |
| QA/QC | `python3 engines/qa/engine.py <PRJ>` |
| Paquet ZIP | `python3 engines/delivery/engine.py <PRJ>` |
| Chaîne complète | `python3 run_agent.py <PRJ> [--yes] [--force] [--until moteur]` |

## Procédure

1. **Discovery** — lancer `engines/discovery/engine.py`. Critère :
   `project_context.json` existe et `tools.blender.available` reflète un test réel.
2. **Programmation + site** — `programming` puis `site_analysis`.
   Critère : `program.json.coherent == true` ; chaque champ site porte un statut.
3. **Conception** — `design` produit VARIANT_A/B/C avec `selected: null`.
   **HUMAN GATE** : ne jamais choisir une variante à la place de l'utilisateur.
4. **Dimensionnement + plans** — `dimension` (surface_check == PASS) puis `floor_plan`.
   Critère : chaque `plan_*.svg` existe et pèse plus de 500 octets.
5. **3D + rendus** — `bim_3d` puis `visualization` puis `rendering`.
   Critère : `scene_villa.blend` existe (hash réel) et chaque PNG est vérifié
   en résolution via `sips`.
6. **Documentation + QA** — `documentation` puis `qa`.
   Critère : `qa_report.json.overall == PASS`, aucun `NOT_EXECUTED` compté comme réussi.
7. **Livraison** — `delivery` écrit `delivery.json` + un ZIP, et vérifie que
   **tous** les items sont bien dans l'archive.

Chaque étape écrit `evidence/<operation>/evidence.json`. Pas d'`evidence.json` →
opération non prouvée.

## Pièges

1. **Inventer un rendu.** Toujours re-vérifier par `sips` + taille + SHA-256, et
   inspecter visuellement l'image. Un PNG noir/blanc/unicolore = échec.
2. **Croire `which blender`.** Blender est hors `PATH` — utiliser le chemin du bundle.
3. **Confondre fichier créé et fichier livré.** Un fichier dans `workspace/` n'est
   pas un livrable ; le `delivery` engine doit confirmer l'archive.
4. **Présenter une hypothèse comme un fait.** Profondeur 6 m, surfaces indicatives,
   orientation : tout est `HYPOTHESIS`. Un `HYPOTHESIS` ne devient jamais `FACT`.
5. **Affirmer une conformité réglementaire.** Sans source : `UNKNOWN`.
6. **Passer un human gate en silence.** `design` et `structural_concept` exigent
   une validation explicite (`--yes` seulement si l'utilisateur l'a demandé).
7. **Lancer Blender en 4K par défaut.** 5 vues en 1920×1080 prennent ~4 min ;
   monter la résolution multiplie le temps. Vérifier le budget temps.

## Vérification

Le succès se prouve, il ne se déclare pas :

```bash
cd /Users/mac/ConstructionAgent
python3 tests/minimal_install_test.py     # exit 0 <=> STATUS=VERIFIED
python3 engines/qa/engine.py <PRJ>        # overall == PASS
```

Contrôler ensuite le rapport : `workspace/construction_agent_installation_report.json`
et `projects/<PRJ>/reports/qa_report.json`.
