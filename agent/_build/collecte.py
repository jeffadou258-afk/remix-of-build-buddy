#!/usr/bin/env python3
"""DOSSIER DE COLLECTE G2 + G3 — preparation des donnees externes. Aucune donnee inventee."""
import json, os, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
os.chdir(PROJ)
S = datetime.datetime.now().isoformat(timespec="seconds")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def W(p, t): open(p, "w").write(t)
STATUTS = ["UNKNOWN", "RECEIVED", "TO_VERIFY", "VERIFIED", "HUMAN_GATE", "HYPOTHESIS", "REJECTED"]

def champ(cid, question, unite="", type_="Oui / Non / Inconnu", source_pre_remplie=""):
    return {"id": cid, "question": question, "valeur": None, "unite": unite, "type_reponse": type_,
            "source": source_pre_remplie or None, "auteur_organisme": None, "document_justificatif": None,
            "date": None, "professionnel": None, "statut": "UNKNOWN"}

# ============================== G2 ==============================
G2C = [
 ("G2.01", "Réseau public d'assainissement disponible ?", "", "Oui / Non / Inconnu"),
 ("G2.02", "Position du regard de branchement", "m", "X / Y + référence topographique"),
 ("G2.03", "Cote du fil d'eau du regard", "m", "cote + référence"),
 ("G2.04", "Relevé topographique", "", "document + date + système de référence + fichier"),
 ("G2.05", "Pente du terrain", "%", "valeur + source"),
 ("G2.06", "Essai de perméabilité", "mm/h", "résultat + méthode + date + rapport"),
 ("G2.07", "Niveau de nappe", "m", "niveau + date + source"),
 ("G2.08", "Servitudes", "", "présentes + description + document"),
 ("G2.09", "Réglementation locale d'assainissement", "", "référence + organisme + document"),
 ("G2.10", "Accès / position de la rue", "", "description + plan + source"),
]
F2 = {"fiche": "G2_FICHE_COLLECTE", "gate": "G2", "objet": "Assainissement / exutoire des eaux usees",
      "at": S, "projet": "PRJ_1701484686 — Villa_Test_001",
      "statut_gate": "OPEN / HUMAN_GATE",
      "regle": "STATUS = UNKNOWN tant qu'aucune donnee reelle n'est fournie. Aucune valeur inventee.",
      "statuts_autorises": STATUTS,
      "champs": [champ(*c) for c in G2C],
      "note": "Ces 10 champs correspondent exactement aux informations identifiees dans reports/G2_DOSSIER_HUMAN_GATE.json."}
json.dump(F2, open("reports/G2_FICHE_COLLECTE.json", "w"), indent=2, ensure_ascii=False)
W("reports/G2_FICHE_COLLECTE.md", "\n".join([
    "# G2 — FICHE DE COLLECTE : ASSAINISSEMENT",
    "**PRJ_1701484686 — Villa_Test_001** · %s" % S,
    "",
    "> Statut du gate : **OPEN / HUMAN_GATE** — `UNKNOWN` tant qu'aucune donnée réelle n'est fournie.",
    "> **Aucune valeur n'a été pré-remplie.** À remplir par le professionnel compétent.",
    "",
    "| # | Information | Valeur | Unité | Source | Document justificatif | Statut |",
    "|---|---|---|---|---|---|---|"]
    + ["| %s | %s | *(vide)* | %s | | | `UNKNOWN` |" % (c[0], c[1], c[2] or "—") for c in G2C]
    + ["", "## Détail des champs", ""]
    + ["### %s — %s" % (c[0], c[1]) + ("\n- **Valeur** :\n- **Unité** : %s\n- **Source** :\n- **Auteur / organisme** :\n- **Document justificatif** :\n- **Date** :\n- **Statut** : `UNKNOWN`" % c[2] if c[2] else "\n- **Valeur** :\n- **Source** :\n- **Auteur / organisme** :\n- **Document justificatif** :\n- **Date** :\n- **Statut** : `UNKNOWN`") + "\n" for c in G2C]
    + ["## Règle de traçabilité", "",
       "Toute donnée reçue devra être enregistrée avec : **SOURCE · DATE · AUTEUR/ORGANISME · DOCUMENT · VALEUR · UNITÉ · STATUT**.",
       "",
       "> Aucune valeur ne sera acceptée sans source lorsqu'elle conditionne une décision technique critique.",
       "",
       "## Statuts autorisés", "", " · ".join("`%s`" % s for s in STATUTS), ""]))

# ============================== G3 ==============================
G3C = [
 ("A", "G3.01", "Portance admissible du sol", "MPa", "etude geotechnique"),
 ("A", "G3.02", "Type de sol", "", "etude geotechnique"),
 ("A", "G3.03", "Profondeur d'ancrage recommandee", "m", "etude geotechnique"),
 ("A", "G3.04", "Niveau de nappe", "m", "etude geotechnique"),
 ("A", "G3.05", "Risque de tassement", "", "etude geotechnique"),
 ("A", "G3.06", "Rapport geotechnique", "", "document"),
 ("A", "G3.07", "Date de l'etude", "", "document"),
 ("A", "G3.08", "Laboratoire / bureau d'etude", "", "document"),
 ("B", "G3.09", "Classe de beton", "", "ingenieur structure"),
 ("B", "G3.10", "Resistance caracteristique du beton (fck)", "MPa", "ingenieur structure"),
 ("B", "G3.11", "Classe d'acier", "", "ingenieur structure"),
 ("B", "G3.12", "Limite d'elasticite de l'acier (fy)", "MPa", "ingenieur structure"),
 ("B", "G3.13", "Enrobage", "mm", "ingenieur structure"),
 ("C", "G3.14", "Charges permanentes", "kN/m2", "ingenieur structure"),
 ("C", "G3.15", "Charges d'exploitation RDC", "kN/m2", "ingenieur structure"),
 ("C", "G3.16", "Charges d'exploitation etage", "kN/m2", "ingenieur structure"),
 ("C", "G3.17", "Charges toiture", "kN/m2", "ingenieur structure"),
 ("C", "G3.18", "Charges terrasse", "kN/m2", "ingenieur structure"),
 ("C", "G3.19", "Charges escalier", "kN/m2", "ingenieur structure"),
 ("D", "G3.20", "Vent — action", "", "ingenieur structure"),
 ("D", "G3.21", "Zone / valeur de calcul du vent", "m/s ou kN/m2", "ingenieur structure"),
 ("D", "G3.22", "Seisme — action", "", "ingenieur structure"),
 ("D", "G3.23", "Classe / zone sismique applicable", "", "ingenieur structure"),
 ("E", "G3.24", "Trame des poteaux retenue", "m", "ingenieur structure — scenario A (60 poteaux) ou B (32 poteaux)"),
 ("E", "G3.25", "Position definitive des semelles", "m", "ingenieur structure — voir GEO_01"),
 ("E", "G3.26", "Verification de l'alignement poteaux/semelles", "m", "ingenieur structure — voir GEO_01"),
 ("E", "G3.27", "Debordement des semelles en limite", "m", "ingenieur structure — voir GEO_02"),
 ("E", "G3.28", "Section definitive des poteaux", "cm", "ingenieur structure — actuellement 0,30 x 0,30 PROPOSED"),
 ("E", "G3.29", "Section definitive des poutres", "cm", "ingenieur structure — actuellement 0,25 x 0,35 PROPOSED"),
 ("E", "G3.30", "Epaisseur definitive des dalles", "cm", "ingenieur structure — actuellement 15 cm PROPOSED"),
 ("E", "G3.31", "Longrines", "", "ingenieur structure"),
 ("E", "G3.32", "Fondations", "", "ingenieur structure"),
]
F3 = {"fiche": "G3_FICHE_COLLECTE", "gate": "G3", "objet": "Validation geotechnique et dimensionnement structure",
      "at": S, "projet": "PRJ_1701484686 — Villa_Test_001", "statut_gate": "OPEN / HUMAN_GATE",
      "regle": "STATUS = UNKNOWN tant qu'aucune donnee reelle n'est fournie. Aucune validation simulee.",
      "statuts_autorises": STATUTS,
      "sections": {"A": "GEOTECHNIQUE", "B": "MATERIAUX", "C": "CHARGES", "D": "ACTIONS CLIMATIQUES", "E": "VALIDATION DE LA GEOMETRIE STRUCTURELLE"},
      "champs": [dict(champ(c[1], c[2], c[3], "valeur + unite + source + document + professionnel + date"), section=c[0], source_attendue=c[4]) for c in G3C],
      "questions_a_arbitrer": [
        {"id": "GEO_01", "objet": "Ecart entre la grille des semelles et la grille des poteaux",
         "mesure": "ecarts mesures : 0 m / 0,15 m / 0,30 m", "cause_identifiee": "les 16 semelles sont calees sur l'ANCIENNE grille, les 32 poteaux sur la trame 4x4 retablie",
         "qualification": "NON QUALIFIE D'ERREUR — situation soumise a l'ingenieur", "statut": "HUMAN_GATE / A VALIDER PAR INGENIEUR",
         "action_automatique": "AUCUNE — ni deplacement de poteaux, ni deplacement de semelles"},
        {"id": "GEO_02", "objet": "Debordement des semelles hors de l'emprise",
         "mesure": "12 semelles depassent x[0..10,40] et y[0..10,90]", "cause_identifiee": "non determinee",
         "qualification": "NON QUALIFIE D'ERREUR — une semelle excentree peut etre normale (fondation en limite)",
         "statut": "HUMAN_GATE / A VALIDER PAR INGENIEUR", "action_automatique": "AUCUNE"}],
      "avertissement": "Ce modele structurel est conceptuel et ne constitue pas un dimensionnement structurel executoire."}
json.dump(F3, open("reports/G3_FICHE_COLLECTE.json", "w"), indent=2, ensure_ascii=False)
L = ["# G3 — FICHE DE COLLECTE : STRUCTURE", "**PRJ_1701484686 — Villa_Test_001** · %s" % S, "",
     "> Statut du gate : **OPEN / HUMAN_GATE** — `UNKNOWN` tant qu'aucune donnée réelle n'est fournie.",
     "> " + F3["avertissement"], ""]
for sec, nom in F3["sections"].items():
    L += ["## %s — %s" % (sec, nom), "", "| # | Information | Unité | Source attendue | Valeur | Statut |", "|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | *(vide)* | `UNKNOWN` |" % (c[1], c[2], c[3] or "—", c[4]) for c in G3C if c[0] == sec]
    L += [""]
L += ["## QUESTIONS G3 À ARBITRER", "",
      "> Statut : **HUMAN_GATE / À VALIDER PAR INGÉNIEUR**. Ces situations **ne sont pas qualifiées d'erreurs** et **n'ont pas été corrigées automatiquement**.", "",
      "### GEO_01 — Écart entre grille des semelles et grille des poteaux", "",
      "- **Mesure** : écarts constatés **0 m / 0,15 m / 0,30 m**",
      "- **Cause identifiée** : les 16 semelles sont calées sur l'**ancienne** grille ; les 32 poteaux sur la trame 4 × 4 rétablie.",
      "- **Qualification** : non qualifié d'erreur — décalage entre deux états du modèle.",
      "- **Action automatique** : *aucune*. Aucun poteau ni semelle n'a été déplacé.", "",
      "### GEO_02 — Débordement des semelles hors emprise", "",
      "- **Mesure** : **12 semelles** dépassent l'emprise x[0..10,40] et y[0..10,90].",
      "- **Qualification** : non qualifié d'erreur — une semelle excentrée peut être normale (fondation en limite de propriété).",
      "- **Action automatique** : *aucune*.", "",
      "## Règle de traçabilité", "",
      "Toute donnée reçue devra être enregistrée avec : **SOURCE · DATE · AUTEUR/ORGANISME · DOCUMENT · VALEUR · UNITÉ · STATUT**.",
      "Aucune valeur ne sera acceptée sans source lorsqu'elle conditionne une décision technique critique.", "",
      "## Statuts autorisés", "", " · ".join("`%s`" % s for s in STATUTS), ""]
W("reports/G3_FICHE_COLLECTE.md", "\n".join(L))
print("fiches G2/G3 ecrites")
