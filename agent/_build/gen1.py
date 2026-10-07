#!/usr/bin/env python3
"""Construction Agent v2.0.0 — Generateur 1/2 : arborescence, schemas, memoire, skills internes."""
import os, json, textwrap

ROOT = "/Users/mac/ConstructionAgent"

DIRS = [
    "", "engines", "engines/discovery", "engines/programming", "engines/site_analysis",
    "engines/design", "engines/dimension", "engines/floor_plan", "engines/structural_concept",
    "engines/bim_3d", "engines/visualization", "engines/rendering", "engines/documentation",
    "engines/qa", "engines/delivery",
    "skills", "skills/architectural_design", "skills/spatial_planning", "skills/building_geometry",
    "skills/blender", "skills/bim", "skills/architectural_rendering",
    "skills/documentation", "skills/quality_control",
    "schemas", "memory", "projects", "workspace", "logs", "evidence", "scripts", "tests",
]

def w(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p

for d in DIRS:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

# ------------------------------------------------------------------ agent.json
w("agent.json", json.dumps({
    "id": "construction-agent",
    "name": "Construction Agent",
    "version": "2.0.0",
    "language": "fr",
    "domain": ["architecture", "construction", "BIM", "conception spatiale",
               "documentation technique", "visualisation architecturale"],
    "principle": "PREUVE > AFFIRMATION",
    "no_fake_execution": True,
    "engines": ["discovery", "programming", "site_analysis", "design", "dimension",
                "floor_plan", "structural_concept", "bim_3d", "visualization",
                "rendering", "documentation", "qa", "delivery"],
    "status_model": ["DRAFT", "ANALYZING", "PROPOSED", "HYPOTHESIS",
                     "USER_VALIDATION_REQUIRED", "VALIDATED", "IN_PROGRESS", "EXECUTED",
                     "VERIFIED", "READY", "BLOCKED", "FAILED", "CANCELLED"],
    "data_status": ["VERIFIED", "USER_PROVIDED", "DERIVED", "HYPOTHESIS", "UNKNOWN"],
}, indent=2, ensure_ascii=False) + "\n")

# ------------------------------------------------------------------ schemas
SCHEMAS = {
"project.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "project_context",
  "type": "object",
  "required": ["project_id", "created_at", "tools", "status"],
  "properties": {
    "project_id": {"type": "string", "pattern": "^PRJ_[A-Za-z0-9_]+$"},
    "created_at": {"type": "string"},
    "status": {"enum": ["DRAFT", "ANALYZING", "IN_PROGRESS", "BLOCKED", "VERIFIED"]},
    "client": {"type": ["object", "null"]},
    "site": {"type": ["object", "null"]},
    "tools": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["available"],
        "properties": {"available": {"type": "boolean"},
                       "path": {"type": ["string", "null"]},
                       "version": {"type": ["string", "null"]}}
      }
    },
    "human_gate_required": {"type": "boolean"}
  }
},
"program.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "program",
  "type": "object",
  "required": ["project_id", "rooms", "total_surface_m2"],
  "properties": {
    "project_id": {"type": "string"},
    "rooms": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "name", "surface_m2", "status"],
        "properties": {
          "code": {"type": "string"},
          "name": {"type": "string"},
          "surface_m2": {"type": "number", "exclusiveMinimum": 0},
          "quantity": {"type": "integer", "minimum": 1},
          "level": {"enum": ["RDC", "ETAGE", "SOUS_SOL", "EXTERIEUR"]},
          "status": {"enum": ["USER_PROVIDED", "DERIVED", "HYPOTHESIS", "UNKNOWN"]}
        }
      }
    },
    "total_surface_m2": {"type": "number"},
    "computed_surface_m2": {"type": "number"},
    "coherent": {"type": "boolean"}
  }
},
"dimensions.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "dimensions",
  "type": "object",
  "required": ["project_id", "levels"],
  "properties": {
    "project_id": {"type": "string"},
    "levels": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["level", "width_m", "depth_m", "surface_m2"],
        "properties": {
          "level": {"enum": ["RDC", "ETAGE", "SOUS_SOL"]},
          "width_m": {"type": "number", "exclusiveMinimum": 0},
          "depth_m": {"type": "number", "exclusiveMinimum": 0},
          "surface_m2": {"type": "number", "exclusiveMinimum": 0},
          "source": {"enum": ["DERIVED", "USER_PROVIDED", "HYPOTHESIS"]}
        }
      }
    },
    "total_surface_m2": {"type": "number"},
    "surface_check": {"enum": ["PASS", "FAIL", "NOT_EXECUTED"]}
  }
},
"design.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "design_variants",
  "type": "object",
  "required": ["project_id", "variants"],
  "properties": {
    "project_id": {"type": "string"},
    "selected": {"type": ["string", "null"]},
    "variants": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "concept", "zoning", "advantages", "constraints", "status"],
        "properties": {
          "id": {"type": "string"},
          "concept": {"type": "string"},
          "zoning": {"type": "array", "items": {"type": "string"}},
          "advantages": {"type": "array", "items": {"type": "string"}},
          "constraints": {"type": "array", "items": {"type": "string"}},
          "assumptions": {"type": "array", "items": {"type": "string"}},
          "status": {"enum": ["PROPOSED", "USER_VALIDATION_REQUIRED", "VALIDATED", "CANCELLED"]}
        }
      }
    }
  }
},
"floor_plan.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "floor_plan",
  "type": "object",
  "required": ["project_id", "levels"],
  "properties": {
    "project_id": {"type": "string"},
    "unit": {"enum": ["m", "mm"]},
    "levels": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["level", "width_m", "depth_m", "wall_thickness_m", "rooms", "files"],
        "properties": {
          "level": {"type": "string"},
          "width_m": {"type": "number"},
          "depth_m": {"type": "number"},
          "wall_thickness_m": {"type": "number"},
          "rooms": {"type": "array", "items": {"type": "object"}},
          "files": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
},
"model_3d.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "model_3d",
  "type": "object",
  "required": ["project_id", "blend_file", "blender_version", "verified"],
  "properties": {
    "project_id": {"type": "string"},
    "blend_file": {"type": "string"},
    "blend_exists": {"type": "boolean"},
    "blend_size_bytes": {"type": "integer"},
    "blend_sha256": {"type": ["string", "null"]},
    "blender_path": {"type": "string"},
    "blender_version": {"type": "string"},
    "objects": {"type": "integer"},
    "verified": {"type": "boolean"}
  }
},
"render.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "render",
  "type": "object",
  "required": ["project_id", "views"],
  "properties": {
    "project_id": {"type": "string"},
    "engine": {"type": "string"},
    "views": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "file", "exists", "verified"],
        "properties": {
          "name": {"type": "string"},
          "file": {"type": "string"},
          "exists": {"type": "boolean"},
          "size_bytes": {"type": ["integer", "null"]},
          "sha256": {"type": ["string", "null"]},
          "resolution": {"type": ["string", "null"]},
          "camera": {"type": "object"},
          "intention": {"type": "string"},
          "inspected": {"type": "boolean"},
          "verified": {"type": "boolean"}
        }
      }
    },
    "all_verified": {"type": "boolean"}
  }
},
"delivery.schema.json": {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "delivery",
  "type": "object",
  "required": ["project_id", "items", "delivery_status"],
  "properties": {
    "project_id": {"type": "string"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["filename", "exists", "verified"],
        "properties": {
          "filename": {"type": "string"},
          "path": {"type": "string"},
          "exists": {"type": "boolean"},
          "size_bytes": {"type": ["integer", "null"]},
          "format": {"type": ["string", "null"]},
          "resolution": {"type": ["string", "null"]},
          "sha256": {"type": ["string", "null"]},
          "verified": {"type": "boolean"}
        }
      }
    },
    "package": {"type": ["string", "null"]},
    "package_verified": {"type": "boolean"},
    "delivery_status": {"enum": ["DELIVERED", "BLOCKED", "FAILED"]}
  }
},
}
for name, sch in SCHEMAS.items():
    w(f"schemas/{name}", json.dumps(sch, indent=2, ensure_ascii=False) + "\n")

# ------------------------------------------------------------------ memory (jsonl vides mais valides)
MEM_FILES = ["decisions.jsonl", "assumptions.jsonl", "constraints.jsonl",
             "design_history.jsonl", "known_issues.jsonl", "project_lessons.jsonl"]
for m in MEM_FILES:
    w(f"memory/{m}", "")

w("memory/README.md", "# Memoire Construction Agent\n\n"
  "Fichiers JSONL append-only. Une ligne = un enregistrement JSON.\n\n"
  "| Fichier | Contenu |\n|---|---|\n"
  "| decisions.jsonl | DECISION -> SOURCE -> JUSTIFICATION -> IMPACT |\n"
  "| assumptions.jsonl | hypotheses explicites, jamais presentees comme faits |\n"
  "| constraints.jsonl | contraintes avec statut VERIFIED/USER_PROVIDED/DERIVED/HYPOTHESIS/UNKNOWN |\n"
  "| design_history.jsonl | variantes et choix successifs |\n"
  "| known_issues.jsonl | problemes connus, non resolus |\n"
  "| project_lessons.jsonl | lecons projet |\n\n"
  "**INTERDIT** : API keys, passwords, tokens, private keys, secrets.\n")

# ------------------------------------------------------------------ skills internes
SKILLS = {
"architectural_design": ("Conception architecturale", [
  "Raisonner PROGRAM FIRST : aucune piece sans justification.",
  "Produire VARIANT_A / VARIANT_B / VARIANT_C quand plusieurs solutions existent.",
  "Aucune variante ne devient la variante de travail sans HUMAN GATE.",
  "Tracer chaque decision : DECISION -> SOURCE -> JUSTIFICATION -> IMPACT."]),
"spatial_planning": ("Planification spatiale", [
  "Construire zoning, matrice d'adjacence, circulations.",
  "Hierarchie : PUBLIC / PRIVE / SERVICE.",
  "Verifier les relations verticales et interieur/exterieur.",
  "Sortie : spatial_strategy.json avec statuts explicites."]),
"building_geometry": ("Geometrie du batiment", [
  "surface calculee == somme des surfaces des espaces, sinon FAIL.",
  "dimensions -> surface -> geometrie -> circulation doivent rester coherents.",
  "Toute incoherence BLOQUE la validation (section 5, PHASE 5).",
  "Largeurs de couloir et portes : valeurs proposees, pas normatives."]),
"blender": ("Blender headless", [
  "Toujours : which blender PUIS blender --version (valeur reelle).",
  "Si absent : STATUS = BLOCKED. Ne jamais pretendre avoir utilise Blender.",
  "Apres creation : test -f scene.blend + ls -lh + stat + sha256.",
  "Apres rendu : test -f + file + stat + resolution reelle (sips).",
  "Echec de commande Blender => BLENDER_STATUS = FAILED, jamais SUCCESS."]),
"bim": ("BIM / maquette 3D", [
  "Un .blend n'existe que s'il a ete ecrit et re-verifie sur disque.",
  "Nommage : scene_<projet>.blend.",
  "Documenter les objets crees et leur nombre.",
  "Pas de calcul structurel reglementaire : HUMAN_GATE = REQUIRED."]),
"architectural_rendering": ("Rendu architectural", [
  "Chaque rendu repond a une INTENTION architecturale declaree.",
  "Vues : 01_Facade 02_Entree 03_Terrasse 04_Garage 05_Aerienne 06_Salon 07_Cuisine 08_Suite 09_Circulation 10_Generale.",
  "Un PNG noir, blanc, vide ou unicolore = ECHEC de rendu.",
  "Chaque image : existence + taille + format + resolution + inspection visuelle."]),
"documentation": ("Documentation technique", [
  "Distinguer CONCEPTUAL vs ENGINEERED / VERIFIED.",
  "Ne jamais inventer une reglementation. Si aucune source : REGULATION_STATUS = UNKNOWN.",
  "Chaque document liste ses hypotheses et ses donnees UNKNOWN.",
  "Historiser : hypotheses, decisions, revisions."]),
"quality_control": ("QA/QC architectural", [
  "Chaine QA : PROGRAM > SURFACES > DIMENSIONS > GEOMETRY > CIRCULATION > STRUCTURE > 3D > RENDERS > DOCUMENTS > FILES > DELIVERY.",
  "Aucune etape PASS sans preuve. Non execute = NOT_EXECUTED.",
  "Un test echoue reste FAILED : jamais arrondi a PASS.",
  "Un test non execute n'est jamais compte comme reussi."]),
}
for slug, (title, rules) in SKILLS.items():
    body = [f"# {title}\n", f"Skill interne de Construction Agent (`{slug}`).\n", "## Regles\n"]
    body += [f"{i}. {r}" for i, r in enumerate(rules, 1)]
    body += ["\n## Preuve requise\n",
             "Toute sortie de ce skill doit etre accompagnee d'un `evidence.json`",
             "conforme au systeme Evidence (section 21 de la specification).\n"]
    w(f"skills/{slug}/SKILL.md", "\n".join(body) + "\n")

print("gen1: OK")
print("dirs:", len(DIRS), "| schemas:", len(SCHEMAS), "| skills:", len(SKILLS), "| memory:", len(MEM_FILES))
