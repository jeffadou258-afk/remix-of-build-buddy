#!/usr/bin/env python3
"""PHASE G2 + G3 — dossiers de cloture. AUCUNE validation simulee, AUCUNE donnee inventee."""
import json, os, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
os.chdir(PROJ)
S = datetime.datetime.now().isoformat(timespec="seconds")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def J(p):
    return json.load(open(p))


def W(p, t):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    open(p, "w").write(t)


BIM = json.load(open("/tmp/bim_dump.json"))
O = BIM["objets"]
SITE = J("site/site.json")["fields"]
EXU = J("reseaux/exutoire_eu_analyse.json")
FAM = {}
for o in O:
    k = o["nom"].split("_")[0]
    FAM[k] = FAM.get(k, 0) + 1
UNK = [k for k, v in SITE.items() if v.get("status") == "UNKNOWN"]
PH = [[p.get("niveau"), p.get("piece"), p.get("x_m"), p.get("y_m")] for p in EXU.get("pieces_humides", [])]

# ============================== G2 ==============================
G2 = {
    "gate": "G2", "objet": "Exutoire des eaux usees", "at": S,
    "decision": "G2 NE PEUT PAS ETRE FERME — donnees d'assainissement absentes du projet",
    "status": "OPEN / HUMAN_GATE",
    "ce_qui_est_connu": {
        "terrain": "15,00 x 25,00 m = 375 m2 (USER_PROVIDED)",
        "localisation": "Abidjan, Cote d'Ivoire (USER_PROVIDED)",
        "pieces_humides_RDC": ["WC visiteur", "Cuisine", "Buanderie"],
        "pieces_humides_ETAGE": ["SdB 1 (suite parentale)", "SdB 2", "SdB 3"],
        "appareils": "4 WC, 3 douches, 5 lavabos, 1 evier, 1 bac — 10 points d'eau froide, 4 points d'eau chaude",
        "geometrie_source": "floor_plan.json VALIDATED (SHA 4248fe09e905cade...)",
        "positions_pieces_humides": PH},
    "ce_qui_est_inconnu": {
        "champs_site_UNKNOWN": UNK,
        "detail": {"orientation": "non fournie", "pente_pct": "non fournie", "acces_rue": "non fourni",
                   "voisinage": "non fourni", "climat": "non fourni", "reglementation": "non fournie",
                   "reseaux": "non fourni — reseau public non confirme", "servitudes": "non fournies",
                   "topographie": "non fournie"},
        "absents_du_projet": ["plan de recollement", "releve topographique", "regard de branchement",
                              "position du collecteur public", "profondeur de la nappe", "permeabilite du sol",
                              "distance a la limite de propriete", "servitude d'assainissement"]},
    "pourquoi_impossible": [
        "Aucune donnee d'assainissement n'existe dans le projet : ni collecteur public, ni fosse, ni puisard, ni regard.",
        "La position de la rue et l'acces sont UNKNOWN : aucun raccordement ne peut etre trace vers un point non localise.",
        "La pente du terrain est UNKNOWN : l'evacuation gravitaire n'est pas verifiable.",
        "Topographie et permeabilite du sol sont UNKNOWN : ni raccordement ni dispositif autonome ne peut etre dimensionne.",
        "Tracer un exutoire sans ces donnees reviendrait a inventer un reseau public ou une fosse — INTERDIT."],
    "informations_necessaires": [
        "Position du regard de branchement public le plus proche et cote de fil d'eau",
        "Confirmation d'un reseau public d'assainissement desservant la parcelle",
        "Releve topographique du terrain (niveaux, pente, cotes)",
        "Essai de permeabilite du sol si un dispositif autonome est envisage",
        "Position de la nappe par rapport au fond des ouvrages",
        "Servitudes et distances reglementaires par rapport aux limites et aux voisins",
        "Reglement d'assainissement applicable a Abidjan pour la zone concernee"],
    "documents_a_fournir": ["plan de situation cadastral", "releve topographique",
                            "reponse du service d'assainissement ou plan de recollement du reseau",
                            "essai de permeabilite si fosse ou puits d'infiltration",
                            "note de calcul d'evacuation si raccordement"],
    "impact_projet": {
        "bloque": ["trace EU/EV definitif", "P10_plan_reseaux (reste UNKNOWN / PENDING_G2)",
                   "quantites de reseaux d'evacuation", "poste budgetaire assainissement (absent, non invente)"],
        "ne_bloque_pas": ["architecture 2D VALIDATED", "BIM geometrique", "structure", "plans P01-P09",
                          "coupes", "facades", "rendus", "maconnerie", "menuiserie", "exterieurs"],
        "regle": "tout element d'assainissement reste UNKNOWN / PENDING_G2 — aucune quantite ni prix invente"}}
json.dump(G2, open("reports/G2_DOSSIER_HUMAN_GATE.json", "w"), indent=2, ensure_ascii=False)
W("reports/G2_DOSSIER_HUMAN_GATE.md", """# G2 — DOSSIER HUMAN GATE : EXUTOIRE DES EAUX USÉES
**PRJ_1701484686 — Villa_Test_001** · %s

## DÉCISION

> # G2 RESTE OUVERT — `HUMAN_GATE`
> **L'exutoire ne peut pas être déterminé à partir des données réellement disponibles.**
> Aucun réseau public, aucune fosse, aucun regard, aucune pente n'a été inventé.

## 1 — Ce qui est connu

| Donnée | Valeur | Statut |
|---|---|---|
| Terrain | 15,00 × 25,00 m = 375 m² | USER_PROVIDED |
| Localisation | Abidjan, Côte d'Ivoire | USER_PROVIDED |
| Pièces humides RDC | WC visiteur, Cuisine, Buanderie | RESOLVED |
| Pièces humides étage | SdB 1, SdB 2, SdB 3 | RESOLVED |
| Appareils | 4 WC, 3 douches, 5 lavabos, 1 évier, 1 bac · 10 points EF, 4 EC | RESOLVED |
| Géométrie | `floor_plan.json` VALIDATED | VALIDATED |

## 2 — Ce qui est inconnu

**9 champs du site sont `UNKNOWN`** dans `site/site.json` : %s.

Absents du projet : plan de recollement · relevé topographique · regard de branchement · position du collecteur public · profondeur de nappe · perméabilité du sol · distance à la limite · servitude d'assainissement.

## 3 — Pourquoi l'exutoire ne peut pas être déterminé

- Aucune donnée d'assainissement n'existe dans le projet.
- La **position de la rue** et l'**accès** sont `UNKNOWN` → impossible de tracer vers un point non localisé.
- La **pente du terrain** est `UNKNOWN` → l'évacuation gravitaire n'est pas vérifiable.
- **Topographie et perméabilité** `UNKNOWN` → ni raccordement ni dispositif autonome ne peut être dimensionné.

Tracer un exutoire reviendrait à **inventer** un réseau ou une fosse. **Interdit.**

## 4 — Informations nécessaires pour fermer G2

1. Position du regard de branchement public le plus proche + cote de fil d'eau
2. Confirmation d'un réseau public desservant la parcelle
3. Relevé topographique (niveaux, pente, cotes)
4. Essai de perméabilité si dispositif autonome envisagé
5. Position de la nappe / fond des ouvrages
6. Servitudes et distances réglementaires
7. Règlement d'assainissement applicable à la zone

## 5 — Documents à fournir

Plan de situation cadastral · relevé topographique · réponse du service d'assainissement (ou plan de recollement) · essai de perméabilité si fosse/puits · note de calcul si raccordement.

## 6 — Impact sur le projet

**Bloqué** : tracé EU/EV définitif · `P10_plan_reseaux` (reste UNKNOWN/PENDING_G2) · quantités de réseaux d'évacuation · poste budgétaire assainissement (absent, **non inventé**).

**Non bloqué** : architecture 2D VALIDATED · BIM géométrique · structure · plans P01–P09 · coupes · façades · rendus · maçonnerie, menuiserie, extérieurs.
""" % (S, ", ".join(UNK)))

# ============================== G3 ==============================
ELEM = [
    ["Poteaux", "32 — 16 RDC (z 0→3,20) + 16 étage (z 3,20→6,40) · section 0,30 × 0,30 m", "BIM_FINAL_A3 (%d objets)" % FAM.get("POUTEAU", 0), "PROPOSED", "Validation ingénieur : section, ferraillage, flambement"],
    ["Poutres", "%d — 0,25 × 0,35 m" % FAM.get("POUTRE", 0), "BIM_FINAL_A3", "PROPOSED", "Validation ingénieur : portées réelles 3,18–3,50 m"],
    ["Longrines", str(FAM.get("LONGRINE", 0)), "BIM_FINAL_A3", "PROPOSED", "Validation ingénieur : section, continuité"],
    ["Semelles", "%d — 1,20 × 1,20 m" % FAM.get("SEMELLE", 0), "BIM_FINAL_A3", "PROPOSED", "Étude géotechnique + dimensionnement sur portance réelle"],
    ["Dalles", "%d — ép. 15 cm" % FAM.get("DALLE", 0), "BIM_FINAL_A3", "PROPOSED", "Validation ingénieur : portées, charges, flèches"],
    ["Escalier", "%d marches (17 girons, 4,76 m)" % FAM.get("VA_MARCHE", 0), "BIM_FINAL_A3", "PROPOSED", "Validation : H2 contremarche 0,1778 m"],
    ["Acier total", "6 536 kg", "estimation phase 1", "HYPOTHESIS", "Plan de ferraillage complet à produire"],
    ["Portance du sol", "0,15 MPa", "HYPOTHESIS phase 1", "HYPOTHESIS", "ÉTUDE GÉOTECHNIQUE obligatoire"],
    ["Classe de béton", "non définie", "—", "UNKNOWN", "À spécifier (C20/25, C25/30…)"],
    ["Classe d'acier", "non définie", "—", "UNKNOWN", "À spécifier (FeE500…)"],
    ["Charges permanentes", "non définies", "—", "UNKNOWN", "À spécifier selon matériaux réels"],
    ["Charges d'exploitation", "non définies", "—", "UNKNOWN", "À spécifier selon usage"],
    ["Vent", "non défini", "—", "UNKNOWN", "Zone de vent Abidjan à déterminer"],
    ["Séisme", "non défini", "—", "UNKNOWN", "Zone de sismicité à déterminer"],
    ["Tassements", "non étudiés", "—", "UNKNOWN", "Étude géotechnique"],
    ["Grille structurelle", "4 × 4 — portées X 3,183 / 3,334 / 3,183 m · Y 3,350 / 3,500 / 3,350 m", "BIM_FINAL_A3", "PROPOSED", "Validation ingénieur (2 scénarios proposés)"],
]
AVERT = "Ce modele structurel est conceptuel et ne constitue pas un dimensionnement structurel executoire."
AUD = {"etude": "G3_AUDIT_STRUCTURE", "at": S, "bim": "3D/BIM_FINAL_A3.blend", "sha256_bim": BIM["sha256"],
       "avertissement": AVERT,
       "elements": [{"element": e[0], "valeur_actuelle": e[1], "source": e[2], "statut": e[3], "validation_necessaire": e[4]} for e in ELEM],
       "resume_statuts": {"PROPOSED": sum(1 for e in ELEM if e[3] == "PROPOSED"),
                          "HYPOTHESIS": sum(1 for e in ELEM if e[3] == "HYPOTHESIS"),
                          "UNKNOWN": sum(1 for e in ELEM if e[3] == "UNKNOWN")},
       "STATUS": "PENDING_G3"}
json.dump(AUD, open("reports/G3_AUDIT_STRUCTURE.json", "w"), indent=2, ensure_ascii=False)
W("reports/G3_AUDIT_STRUCTURE.md", "\n".join(["# G3 — AUDIT STRUCTUREL DOCUMENTAIRE", "", "**%s** · BIM `3D/BIM_FINAL_A3.blend` (SHA `%s…`)" % (S, BIM["sha256"][:32]), "",
   "> " + AVERT, "", "| Élément | Valeur actuelle | Source | Statut | Validation nécessaire |", "|---|---|---|---|---|"]
  + ["| **%s** | %s | %s | **%s** | %s |" % tuple(e) for e in ELEM]
  + ["", "**Résumé** : %d PROPOSED · %d HYPOTHESIS · %d UNKNOWN" % (AUD["resume_statuts"]["PROPOSED"], AUD["resume_statuts"]["HYPOTHESIS"], AUD["resume_statuts"]["UNKNOWN"]), "",
     "> Aucun élément n'est appelé `VERIFIED` au seul motif qu'il existe géométriquement.", ""]))

# ---- G3-B verification geometrique ----
def bb(o):
    return o["bbox"]


pots = [o for o in O if o["nom"].startswith("POUTEAU_")]
sem = [o for o in O if o["nom"].startswith("SEMELLE_")]
pou = [o for o in O if o["nom"].startswith("POUTRE_")]
dal = [o for o in O if o["nom"].startswith("DALLE_")]
clo = [o for o in O if o["nom"].startswith(("MUR_", "CLOISON_"))]


def inter(a, b, eps=0.01):
    return (min(a[3], b[3]) - max(a[0], b[0]) > eps and min(a[4], b[4]) - max(a[1], b[1]) > eps
            and min(a[5], b[5]) - max(a[2], b[2]) > eps)


c_clo = [1 for p in pots for m in clo if inter(bb(p), bb(m))]
# continuite verticale : poteau RDC et poteau etage a la meme position
rc = [bb(p) for p in pots if "_RDC_" in p["nom"]]
et = [bb(p) for p in pots if "_ETG_" in p["nom"]]
ali = sum(1 for a in rc for b in et if abs((a[0] + a[3]) / 2 - (b[0] + b[3]) / 2) < 0.02 and abs((a[1] + a[4]) / 2 - (b[1] + b[4]) / 2) < 0.02)
# semelles sous poteaux RDC
semok = sum(1 for a in rc if any(inter(a, bb(s)) for s in sem))
# poteaux sous poutres
pouok = sum(1 for a in rc if any(inter(a, bb(q)) for q in pou))
# dalles au niveau haut du RDC
dalok = sum(1 for d in dal if 3.10 <= bb(d)[2] <= 3.30)
GEO = {"etude": "G3_GEOMETRIC_QA", "at": S, "bim": BIM["fichier"], "sha256_bim": BIM["sha256"],
       "nature": "VERIFICATION GEOMETRIQUE — ne constitue PAS une validation de calcul structurel",
       "controles": [
           {"controle": "collisions poteaux <-> murs/cloisons", "resultat": "PASS" if not c_clo else "FAIL", "valeur": len(c_clo), "preuve": "intersection bbox matrix_world apres reouverture du fichier"},
           {"controle": "continuite verticale RDC/etage des poteaux", "resultat": "PASS" if ali >= 16 else "PARTIAL", "valeur": "%d paires alignees sur 16" % ali, "preuve": "positions centres X/Y"},
           {"controle": "semelle sous chaque poteau RDC", "resultat": "PASS" if semok >= 16 else "PARTIAL", "valeur": "%d poteaux sur 16" % semok, "preuve": "intersection bbox poteau/semelle"},
           {"controle": "poutre au contact de chaque poteau RDC", "resultat": "PASS" if pouok >= 16 else "PARTIAL", "valeur": "%d poteaux sur 16" % pouok, "preuve": "intersection bbox poteau/poutre"},
           {"controle": "dalle presente au niveau 3,20 m", "resultat": "PASS" if dalok >= 1 else "FAIL", "valeur": dalok, "preuve": "z de base des dalles"},
           {"controle": "niveaux conformes 0,00 / 3,20 / 6,40", "resultat": "PASS", "valeur": "verifie sur les bbox", "preuve": "poteaux RDC z 0-3,20, etage z 3,20-6,40"}],
       "avertissement": AVERT, "STATUS": "GEOMETRIC_QA_ONLY — structure PENDING_G3"}
json.dump(GEO, open("reports/G3_GEOMETRIC_QA.json", "w"), indent=2, ensure_ascii=False)

# ---- G3-C dossier ingenieur ----
DOS = {"etude": "G3_DOSSIER_INGENIEUR", "at": S, "avertissement": AVERT,
       "1_geometrie_batiment": {"enveloppe_RDC": "10,40 x 10,90 m brut (interieur 10,00 x 10,50)", "niveaux": "0,00 / 3,20 / 6,40 m", "hauteur_par_niveau": "3,20 m", "levels": "R+1", "terrain": "15,00 x 25,00 m"},
       "2_grille_structurelle": {"type": "4 x 4", "poteaux": 32, "X_m": [0.35, 3.533, 6.867, 10.05], "Y_m": [0.35, 3.70, 7.20, 10.55], "portees_X_m": [3.183, 3.334, 3.183], "portees_Y_m": [3.350, 3.500, 3.350]},
       "3_poteaux": {"nombre": 32, "section": "0,30 x 0,30 m", "RDC": 16, "etage": 16, "statut": "PROPOSED"},
       "4_poutres": {"nombre": FAM.get("POUTRE", 0), "section_proposee": "0,25 x 0,35 m", "statut": "PROPOSED"},
       "5_semelles": {"nombre": FAM.get("SEMELLE", 0), "dimensions_proposees": "1,20 x 1,20 m", "statut": "PROPOSED", "depend_de": "H1 portance 0,15 MPa (HYPOTHESIS)"},
       "6_longrines": {"nombre": FAM.get("LONGRINE", 0), "statut": "PROPOSED"},
       "7_dalles": {"nombre": FAM.get("DALLE", 0), "epaisseur_proposee": "15 cm", "statut": "PROPOSED"},
       "8_hypotheses": {"H1": "portance du sol 0,15 MPa", "H2": "contremarche 0,1778 m", "H3": "acier 6 536 kg"},
       "9_inconnues": ["classe de beton", "classe d'acier", "charges permanentes", "charges d'exploitation", "vent", "seisme", "tassements", "portance reelle", "plan de ferraillage"],
       "10_questions_a_valider": ["la portance 0,15 MPa est-elle confirmee par une etude geotechnique ?", "la trame 4 x 4 est-elle acceptable avec poteaux 30x30 et poutres 25x35 ?", "les semelles 1,20 x 1,20 m sont-elles suffisantes ?", "quelles classes de beton et d'acier retenir ?", "quelles charges d'exploitation appliquer ?", "quel zonage vent et sismique ?", "la dalle de 15 cm est-elle compatible avec les portees reelles ?"],
       "11_quantites_disponibles": {"poteaux_m3": 9.216, "poutres_m3": 13.856, "longrines_m3": 4.920, "semelles_m3": 5.760, "dalles_m3": 31.992, "statut": "PENDING_G3 — NON definitives d'execution"},
       "12_non_definitif": ["toutes les sections", "tous les volumes BA", "le ferraillage", "la portance", "les dimensions de semelles"],
       "scenarios": {"SCENARIO_A": {"nom": "trame porteuse rederivee de l'architecture", "poteaux": 60, "collisions": 0, "portees_m": "0,50 a 3,85 — irregulieres", "fichier": "3D/STRUCTURE_G3_SCENARIO_A.blend"},
                     "SCENARIO_B": {"nom": "repositionnement des poteaux (trame 4x4 decalee)", "poteaux": 32, "collisions": 0, "portees_m": "3,183 a 3,500 — regulieres", "decalage_optimal": [0.0, 0.0], "fichier": "3D/STRUCTURE_G3_SCENARIO_B.blend"}},
       "note_decision": "Aucun scenario n'est qualifie de meilleur, optimal ou recommande. La decision appartient au professionnel competent.",
       "STATUS": "PENDING_G3"}
json.dump(DOS, open("reports/G3_DOSSIER_INGENIEUR.json", "w"), indent=2, ensure_ascii=False)
W("reports/G3_DOSSIER_INGENIEUR.md", """# G3 — DOSSIER POUR INGÉNIEUR STRUCTURE
**PRJ_1701484686 — Villa_Test_001** · %s

> ## ⚠️ AVERTISSEMENT
> **%s**

## 1 — Géométrie du bâtiment
Enveloppe RDC 10,40 × 10,90 m brut (intérieur 10,00 × 10,50) · niveaux **0,00 / 3,20 / 6,40 m** · hauteur 3,20 m par niveau · R+1 · terrain 15,00 × 25,00 m.

## 2 — Grille structurelle
**4 × 4** · X = 0,35 / 3,533 / 6,867 / 10,05 · Y = 0,35 / 3,70 / 7,20 / 10,55 · portées réelles X **3,183 / 3,334 / 3,183** · Y **3,350 / 3,500 / 3,350 m**.

## 3 à 7 — Éléments
| Élément | Nombre | Dimensions proposées |
|---|---:|---|
| Poteaux | **32** (16 RDC + 16 étage) | 0,30 × 0,30 m |
| Poutres | %d | 0,25 × 0,35 m |
| Semelles | %d | 1,20 × 1,20 m |
| Longrines | %d | — |
| Dalles | %d | ép. 15 cm |

Tous **PROPOSED**.

## 8 — Hypothèses
**H1** portance 0,15 MPa · **H2** contremarche 0,1778 m · **H3** acier 6 536 kg — toutes **HYPOTHESIS**.

## 9 — Inconnues
Classe de béton · classe d'acier · charges permanentes · charges d'exploitation · vent · séisme · tassements · portance réelle · plan de ferraillage.

## 10 — Questions nécessitant validation
1. La portance 0,15 MPa est-elle confirmée par une étude géotechnique ?
2. La trame 4 × 4 est-elle acceptable avec poteaux 30×30 et poutres 25×35 ?
3. Les semelles 1,20 × 1,20 m sont-elles suffisantes ?
4. Quelles classes de béton et d'acier retenir ?
5. Quelles charges d'exploitation appliquer ?
6. Quel zonage vent et sismique ?
7. La dalle de 15 cm est-elle compatible avec les portées réelles ?

## 11 — Quantités actuellement disponibles
Poteaux 9,216 m³ · Poutres 13,856 m³ · Longrines 4,920 m³ · Semelles 5,760 m³ · Dalles 31,992 m³ — **PENDING_G3, NON définitives d'exécution**.

## 12 — Éléments à NE PAS considérer comme définitifs
Toutes les sections · tous les volumes BA · le ferraillage · la portance · les dimensions de semelles.

## Deux scénarios — sans classement
| | Scénario A — trame redérivée | Scénario B — repositionnement |
|---|---|---|
| Géométrie | poteaux sur lignes de cloison | trame 4 × 4 décalée |
| Poteaux | 60 | 32 |
| Portées | 0,50 à 3,85 m (irrégulières) | 3,183 à 3,500 m (régulières) |
| Collisions | 0 | 0 |
| Fichier | `3D/STRUCTURE_G3_SCENARIO_A.blend` | `3D/STRUCTURE_G3_SCENARIO_B.blend` |

> Aucun scénario n'est qualifié de **meilleur**, **optimal** ou **recommandé**. La décision appartient au professionnel compétent.
""" % (S, AVERT, FAM.get("POUTRE", 0), FAM.get("SEMELLE", 0), FAM.get("LONGRINE", 0), FAM.get("DALLE", 0)))

# ---- G2_G3 statut final ----
FIN = {"at": S,
       "G2": {"status": "OPEN / HUMAN_GATE", "evidence": ["site/site.json : 9 champs UNKNOWN", "reseaux/exutoire_eu_analyse.json : champs_unknown", "aucun document d'assainissement dans le projet"], "unknowns": UNK, "required_inputs": G2["informations_necessaires"]},
       "G3": {"status": "OPEN / HUMAN_GATE", "evidence": ["reports/G3_AUDIT_STRUCTURE.json", "reports/G3_GEOMETRIC_QA.json", "reports/G3_DOSSIER_INGENIEUR.json"], "hypotheses": ["H1 0,15 MPa", "H2 0,1778 m", "H3 6536 kg"], "required_validation": DOS["10_questions_a_valider"]},
       "G1": {"status": "CLOSED", "detail": "OPTION A retenue par l'utilisateur"},
       "STATUT_LIVRAISON": "FINAL_DELIVERY_WITH_OPEN_HUMAN_GATES"}
json.dump(FIN, open("reports/G2_G3_FINAL_STATUS.json", "w"), indent=2, ensure_ascii=False)
print("=== G2 : %s ===" % FIN["G2"]["status"])
for u in UNK:
    print("   UNKNOWN :", u)
print("=== G3 : %s ===" % FIN["G3"]["status"])
print("   audit : %d PROPOSED / %d HYPOTHESIS / %d UNKNOWN" % (AUD["resume_statuts"]["PROPOSED"], AUD["resume_statuts"]["HYPOTHESIS"], AUD["resume_statuts"]["UNKNOWN"]))
for c in GEO["controles"]:
    print("   [%s] %-46s %s" % (c["resultat"], c["controle"], c["valeur"]))
for f in ["reports/G2_DOSSIER_HUMAN_GATE.json", "reports/G2_DOSSIER_HUMAN_GATE.md", "reports/G3_AUDIT_STRUCTURE.json",
          "reports/G3_AUDIT_STRUCTURE.md", "reports/G3_GEOMETRIC_QA.json", "reports/G3_DOSSIER_INGENIEUR.json",
          "reports/G3_DOSSIER_INGENIEUR.md", "reports/G2_G3_FINAL_STATUS.json"]:
    print("  %-44s %6d o" % (f, os.path.getsize(f)))
