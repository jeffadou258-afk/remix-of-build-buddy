#!/usr/bin/env python3
"""PHASE G2 + G3 — dossiers de cloture. AUCUNE validation simulee."""
import json, os, hashlib, datetime, shutil

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
os.chdir(PROJ)
S = datetime.datetime.now().isoformat(timespec="seconds")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def J(p): return json.load(open(p))
BIM = json.load(open("/tmp/bim_dump.json")); O = BIM["objets"]
SITE = J("site/site.json")["fields"]
FAM = {}
for o in O:
    k = o["nom"].split("_")[0]; FAM[k] = FAM.get(k, 0) + 1
PH_REF = []
if os.path.exists("reseaux/exutoire_eu_analyse.json"):
    for p in J("reseaux/exutoire_eu_analyse.json").get("pieces_humides", []):
        PH_REF.append([p.get("niveau"), p.get("piece"), p.get("x_m"), p.get("y_m")])
UNK = [k for k, v in SITE.items() if v.get("status") == "UNKNOWN"]
KNOWN = [k for k, v in SITE.items() if v.get("status") in ("USER_PROVIDED", "DERIVED")]

# ================= G2 =================
G2 = {
 "gate": "G2", "objet": "Exutoire des eaux usees", "at": S,
 "decision": "G2 NE PEUT PAS ETRE FERME — donnees d'assainissement absentes",
 "status": "OPEN / HUMAN_GATE",
 "1_ce_qui_est_connu": {
   "terrain": "15,00 x 25,00 m = 375 m2", "terrain_statut": "USER_PROVIDED",
   "localisation": "Abidjan, Cote d'Ivoire", "localisation_statut": "USER_PROVIDED",
   "pieces_humides_RDC": "WC visiteur, Cuisine, Buanderie",
   "pieces_humides_ETAGE": "SdB 1 (suite), SdB 2, SdB 3",
   "appareils": "4 WC, 3 douches, 5 lavabos, 1 evier, 1 bac — 10 points d'eau froide, 4 points d'eau chaude",
   "geometrie": "floor_plan.json VALIDATED (SHA 4248fe09e905cade...)",
   "source_reseaux": "reseaux/exutoire_eu_analyse.json + reseaux/networks_concept.json"},
 "2_ce_qui_est_inconnu": {
   "champs_site_UNKNOWN": UNK,
   "detail": {
     "orientation": "non fournie",
     "pente_pct": "non fournie — aucune pente de terrain connue",
     "acces_rue": "non fourni — position de la rue inconnue",
     "voisinage": "non fourni",
     "climat": "non fourni",
     "reglementation": "non fournie — aucune conformite affirmee",
     "reseaux": "non fourni — reseau public d'assainissement non confirme",
     "servitudes": "non fournies",
     "topographie": "non fournie"},
   "absents_du_projet": ["plan de recollement", "releve topographique", "regard de branchement",
     "position du collecteur public", "profondeur de la nappe", "perméabilité du sol",
     "distance a la limite de propriete", "servitude d'assainissement"]},
 "3_pourquoi_impossible": [
   "Aucune donnee d'assainissement n'existe dans le projet : ni collecteur public, ni fosse, ni puisard, ni regard.",
   "La position de la rue et l'acces sont UNKNOWN : un raccordement ne peut pas etre trace vers un point non localise.",
   "La pente du terrain est UNKNOWN : le mode d'evacuation gravitaire ne peut pas etre verifie.",
   "La topographie et la permeabilite du sol sont UNKNOWN : ni raccordement ni dispositif autonome ne peut etre dimensionne.",
   "Tracer un exutoire sans ces donnees serait inventer un reseau public ou une fosse — INTERDIT."),
 "4_informations_necessaires": [
   "Position du regard de branchement public le plus proche et cote de fil d'eau",
   "Confirmation de l'existence d'un reseau public d'assainissement desservant la parcelle",
   "Releve topographique du terrain (niveaux, pente, cotes)",
   "Permeabilite du sol (essai de percolation) si un dispositif autonome est envisage",
   "Position de la nappe par rapport au fond des ouvrages",
   "Servitudes et distances reglementaires par rapport aux limites et aux voisins",
   "Reglement d'assainissement applicable a Abidjan pour la zone concernee"),
 "5_documents_a_fournir": ["plan de situation cadastral", "releve topographique", "reponse du service d'assainissement "
   "(ou plan de recollement du reseau)", "essai de permeabilite si fosse/puits d'infiltration",
   "note de calcul d'evacuation si raccordement"),
 "6_impact_projet": {
   "bloque": ["trace EU/EV definitif", "P10_plan_reseaux (reste UNKNOWN/PENDING_G2)",
     "quantites de reseaux d'evacuation", "poste budgetaire assainissement (absent, non invente)"),
   "ne_bloque_pas": ["architecture 2D VALIDATED", "BIM geometrique", "structure", "plans P01-P09",
     "coupes, facades, rendus", "maconnerie, menuiserie, exterieurs"),
   "regle": "tout element d'assainissement reste UNKNOWN / PENDING_G2 — aucune quantite ni prix invente"},
 "pieces_humides_reference": PH_REF}

json.dump(G2, open("reports/G2_DOSSIER_HUMAN_GATE.json", "w"), indent=2, ensure_ascii=False)
open("reports/G2_DOSSIER_HUMAN_GATE.md", "w").write(f"""# G2 — DOSSIER HUMAN GATE : EXUTOIRE DES EAUX USÉES
**PRJ_1701484686 — Villa_Test_001** · {S}

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
| Pièces humides étage | SdB 1 (suite), SdB 2, SdB 3 | RESOLVED |
| Appareils | 4 WC, 3 douches, 5 lavabos, 1 évier, 1 bac — 10 points EF, 4 points EC | RESOLVED |
| Géométrie | `floor_plan.json` VALIDATED | VALIDATED |

## 2 — Ce qui est inconnu
**9 champs du site sont `UNKNOWN` dans `site/site.json`** : {", ".join(UNK)}.
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
""")

# ================= G3 =================
ELEM = [
 ("Poteaux", "32 (16 RDC z0→3,20 + 16 étage z3,20→6,40) — section 0,30 × 0,30 m", f"BIM_FINAL_A3 ({FAM.get('POUTEAU',0)} objets)", "PROPOSED", "Validation ingenieur : section, ferraillage, flambement"),
 ("Poutres", f"{FAM.get('POUTRE',0)} — 0,25 × 0,35 m", "BIM_FINAL_A3", "PROPOSED", "Validation ingenieur : portees reelles 3,18-3,50 m"),
 ("Longrines", f"{FAM.get('LONGRINE',0)}", "BIM_FINAL_A3", "PROPOSED", "Validation ingenieur : section, continuite"),
 ("Semelles", f"{FAM.get('SEMELLE',0)} — 1,20 × 1,20 m", "BIM_FINAL_A3", "PROPOSED", "Etude geotechnique + validation : dimensionnement sur portance reelle"),
 ("Dalles", f"{FAM.get('DALLE',0)} — ep. 15 cm", "BIM_FINAL_A3", "PROPOSED", "Validation ingenieur : portees, charges, fleches"),
 ("Escalier", f"{FAM.get('VA_MARCHE',0)} marches (17 girons, 4,76 m)", "BIM_FINAL_A3", "PROPOSED", "Validation : H2 contremarche 0,1778 m"),
 ("Acier", "6 536 kg", "estimation phase 1", "HYPOTHESIS", "Plan de ferraillage complet a produire"),
 ("Portance sol", "0,15 MPa", "HYPOTHESIS phase 1", "HYPOTHESIS", "ETUDE GEOTECHNIQUE obligatoire"),
 ("Classe beton", "non definie", "-", "UNKNOWN", "A specifier (C20/25, C25/30...)"),
 ("Classe acier", "non definie", "-", "UNKNOWN", "A specifier (FeE500...)"),
 ("Charges permanentes", "non definies", "-", "UNKNOWN", "A specifier selon materiaux reels"),
 ("Charges exploitation", "non definies", "-", "UNKNOWN", "A specifier selon usage (NF EN 1991)"),
 ("Vent", "non defini", "-", "UNKNOWN", "Zone de vent Abidjan a determiner"),
 ("Seisme", "non defini", "-", "UNKNOWN", "Zona sismicite a determiner"),
 ("Tassements", "non etudies", "-", "UNKNOWN", "Etude geotechnique"),
 ("Grille structurelle", "4 x 4 — portees 3,183 / 3,334 / 3,183 m (X) et 3,350 / 3,500 / 3,350 (Y)", "BIM_FINAL_A3", "PROPOSED", "Validation ingenieur (2 scenarios proposes)"),
]
AUD = {"etude": "G3_AUDIT_STRUCTURE", "at": S, "bim": "3D/BIM_FINAL_A3.blend", "sha256_bim": BIM["sha256"),
 "avertissement": "Ce modele structurel est conceptuel et ne constitue pas un dimensionnement structurel executoire.",
 "elements": [{"element": e[0], "valeur_actuelle": e[1], "source": e[2], "statut": e[3], "validation_necessaire": e[4]} for e in ELEM],
 "resume_statuts": {"PROPOSED": sum(1 for e in ELEM if e[3] == "PROPOSED"), "HYPOTHESIS": sum(1 for e in ELEM if e[3] == "HYPOTHESIS"),
   "UNKNOWN": sum(1 for e in ELEM if e[3] == "UNKNOWN")},
 "STATUS": "PENDING_G3"}
json.dump(AUD, open("reports/G3_AUDIT_STRUCTURE.json", "w"), indent=2, ensure_ascii=False)
open("reports/G3_AUDIT_STRUCTURE.md", "w").write("# G3 — AUDIT STRUCTUREL DOCUMENTAIRE\n\n"
 + f"**{S}** · BIM `3D/BIM_FINAL_A3.blend` (SHA `{BIM['sha256'][:32]}…`)\n\n"
 + "> " + AUD["avertissement"] + "\n\n"
 + "| Élément | Valeur actuelle | Source | Statut | Validation nécessaire |\n|---|---|---|---|---|\n"
 + "\n".join("| **%s** | %s | %s | **%s** | %s |" % e for e in ELEM)
 + f"\n\n**Résumé** : {AUD['resume_statuts']['PROPOSED']} PROPOSED · {AUD['resume_statuts']['HYPOTHESIS']} HYPOTHESIS · {AUD['resume_statuts']['UNKNOWN']} UNKNOWN\n\n"
 + "> Aucun élément n'est appelé `VERIFIED` au seul motif qu'il existe géométriquement.\n")
print("G2 + audits G3 ecrits")
