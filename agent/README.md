# Construction Agent v2.0.0

Agent autonome de conception architecturale et de construction.
Il transforme un besoin en projet **documenté, cohérent, vérifiable et reproductible**.

> **Règle absolue : PREUVE > AFFIRMATION.**
> Aucun `SUCCESS`, `READY` ou `PASSED` n'est écrit sans preuve observable
> (fichier réel, taille réelle, hash réel, sortie réelle de commande).

---

## Installation

Ce dossier **est** l'agent. Aucune dépendance à installer.

```bash
cd /Users/mac/ConstructionAgent
```

Prérequis vérifiés sur cette machine : Blender 5.2.2 LTS
(`/Applications/Blender.app`), `python3` 3.9.6, `sips`, `zip`, `ffmpeg`.

---

## Démarrage rapide

```bash
# 1. Test minimal obligatoire (crée txt + blend + png et VÉRIFIE chaque fichier)
python3 tests/minimal_install_test.py

# 2. Lancer un projet complet (s'arrête aux human gates)
python3 run_agent.py workspace/mon_projet

# 3. Idem en passant les human gates
python3 run_agent.py workspace/mon_projet --yes
```

## Lancer un seul moteur

```bash
python3 engines/discovery/engine.py          workspace/mon_projet
python3 engines/programming/engine.py        workspace/mon_projet
python3 engines/bim_3d/engine.py             workspace/mon_projet
python3 engines/rendering/engine.py          workspace/mon_projet
```

Chaque moteur écrit son `evidence/<operation>/evidence.json`.

---

## Arborescence

```
ConstructionAgent/
├── SOUL.md                     identité, interdits, doctrine de la preuve
├── AGENT_SPEC.md               spécification complète
├── README.md                   ce fichier
├── SKILL.md                    mode opératoire (skill Hermes)
├── agent.json                  manifeste (version, moteurs, statuts)
├── run_agent.py                orchestrateur (13 moteurs enchaînés)
│
├── engines/                    13 moteurs exécutables
│   ├── _core.py                noyau : Evidence, sha256, sips, Blender
│   ├── discovery/ programming/ site_analysis/ design/ dimension/
│   ├── floor_plan/ structural_concept/ bim_3d/ visualization/
│   └── rendering/ documentation/ qa/ delivery/
│
├── scripts/
│   ├── build_scene.py          Blender : construit le .blend paramétrique
│   └── render_views.py         Blender : ouvre le .blend et rend les vues
│
├── schemas/                    8 JSON Schemas (draft-07)
├── memory/                     6 journaux JSONL append-only
├── skills/                     8 skills internes
├── tests/
│   └── minimal_install_test.py test obligatoire de la section 27
│
├── projects/                   projets réels, un dossier par PRJ_xxxxx
├── workspace/                  zone de travail / tests
├── evidence/                   preuves par moteur
└── logs/agent.log              journal
```

---

## Test minimal obligatoire

L'agent ne se déclare installé qu'après ce test, qui produit et **vérifie
physiquement** trois artefacts :

| Artefact | Contenu attendu | Vérifications |
|---|---|---|
| `workspace/construction_agent_test.txt` | `CONSTRUCTION_AGENT_REAL_EXECUTION_TEST` | `test -f`, `ls -lh`, `stat`, contenu exact, SHA-256 |
| `workspace/construction_agent_test.blend` | scène Blender réelle | existence, taille > 1 Ko, SHA-256 |
| `workspace/construction_agent_test.png` | un rendu réel | existence, taille > 5 Ko, **1280×720** via `sips`, SHA-256 |

Résultat écrit dans `workspace/construction_agent_installation_report.json`.
Exit code `0` **si et seulement si** `STATUS = VERIFIED`.

---

## Modèle de statut

`DRAFT · ANALYZING · PROPOSED · HYPOTHESIS · USER_VALIDATION_REQUIRED ·
VALIDATED · IN_PROGRESS · EXECUTED · VERIFIED · READY · BLOCKED · FAILED · CANCELLED`

## Statut des données

`VERIFIED · USER_PROVIDED · DERIVED · HYPOTHESIS · UNKNOWN`

---

## Limites assumées

- Documents **conceptuels** : aucune valeur contractuelle.
- Aucun calcul structurel réglementaire — `HUMAN_GATE = REQUIRED`.
- Aucune conformité réglementaire affirmée sans source vérifiée
  (`REGULATION_STATUS = UNKNOWN` par défaut).
- FreeCAD, OpenSCAD, Inkscape, LibreOffice et ImageMagick sont absents :
  les plans sont produits en SVG natif et les images inspectées via `sips`.
