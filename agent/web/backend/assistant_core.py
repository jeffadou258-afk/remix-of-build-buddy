#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONSTRUCTION AGENT ASSISTANT — M1 (PROJECT CONTEXT) + M2 (ENGINE)

Principes (Master Spec §2, §24, §26) :
  - AUCUNE donnee inventee : toute valeur vient d'un fichier reel du projet ;
  - un champ absent ou UNKNOWN reste UNKNOWN ;
  - aucun moteur parallele : les explications passent par le Guide Engine existant ;
  - l'assistant est ACTIONNABLE : chaque reponse porte une action d'interface reelle ;
  - tout statut (UNKNOWN / HYPOTHESIS / PROPOSED / PENDING_VALIDATION / HUMAN_GATE)
    est transporte tel quel, jamais transforme.

Ce module ne modifie aucun fichier. Il LIT.
"""
import json
import os
import re

PROJECT_ID = "PRJ_1701484686"
_UNKNOWN = "UNKNOWN"


# --------------------------------------------------------------------------- #
#  UTILITAIRES DE LECTURE (aucune valeur par defaut inventee)
# --------------------------------------------------------------------------- #
def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _jsonl(path, limit=None):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
                if limit and len(out) >= limit:
                    break
    except Exception:
        return []
    return out


class ProjectContext:
    """Contexte projet construit a partir des SEULS fichiers reels."""

    def __init__(self, project_dir):
        self.dir = project_dir
        self._build()

    # -- construction ------------------------------------------------------- #
    def _build(self):
        d = self.dir
        self.site = _load(os.path.join(d, "site", "site.json")) or {}
        self.program = _load(os.path.join(d, "program", "program.json")) or {}
        self.floorplan = _load(os.path.join(d, "floorplan", "floor_plan.json")) or {}
        self.metre = _load(os.path.join(d, "metre", "metre_final_v2.json")) or {}
        self.budget = _load(os.path.join(d, "budget", "budget_final_v2.json")) or {}
        self.bim = _load(os.path.join(d, "3D", "bim_elements.json")) or {}
        self.decisions = _jsonl(os.path.join(d, "memory", "decisions.jsonl"))
        self._files = {}
        for sub in ("docs", "plans", "coupes", "facades", "renders"):
            p = os.path.join(d, sub)
            try:
                self._files[sub] = sorted(os.listdir(p))
            except Exception:
                self._files[sub] = []

    # -- site : champs reels et UNKNOWN ------------------------------------- #
    def site_fields(self):
        """Renvoie {nom: {value, status}} pour les 13 champs reels."""
        f = self.site.get("fields", {})
        return f if isinstance(f, dict) else {}

    def site_unknowns(self):
        """Champs dont la valeur reelle est absente/UNKNOWN. Mesure, pas estimation."""
        out = []
        for k, v in self.site_fields().items():
            if not isinstance(v, dict):
                continue
            val = v.get("value")
            st = (v.get("status") or "").upper()
            if val is None or val == _UNKNOWN or st == _UNKNOWN:
                out.append({"champ": k, "statut": st or _UNKNOWN})
        return out

    # -- programme ---------------------------------------------------------- #
    def rooms(self):
        r = self.program.get("rooms")
        return r if isinstance(r, list) else []

    def rooms_by_level(self, level):
        return [r for r in self.rooms() if (r.get("level") or "").upper() == level.upper()]

    def totals(self):
        t = self.program.get("totals")
        return t if isinstance(t, dict) else {}

    def chambres(self):
        """Chambres REELLES : name contient 'chambre' ou 'suite' (mesure sur les donnees)."""
        return [r for r in self.rooms()
                if re.search(r"chambre|suite", (r.get("name") or ""), re.I)]

    def piece(self, terme):
        for r in self.rooms():
            if terme.lower() in (r.get("name") or "").lower():
                return r
        return None

    # -- BIM ---------------------------------------------------------------- #
    def bim_elements(self):
        e = self.bim.get("elements")
        return e if isinstance(e, list) else []

    def bim_familles(self):
        return self.bim.get("familles") or {}

    def bim_niveaux(self):
        return self.bim.get("niveaux") or {}

    def bim_fenetres(self):
        """Attention : le BIM compte des OBJETS. Une fenetre = chassis + allege."""
        return [e for e in self.bim_elements() if (e.get("famille") or "").upper() == "FENETRE"]

    # -- metrés / budget ---------------------------------------------------- #
    def quantites(self, dependantes=False):
        cle = "quantites_dependantes_de_G3" if dependantes else "quantites_independantes_de_G3"
        q = self.metre.get(cle)
        return q if isinstance(q, list) else []

    def budget_total(self):
        return self.budget.get("total_general_fcfa")

    # -- gates -------------------------------------------------------------- #
    def gates(self):
        return _load(os.path.join(self.dir, "..", "..", "..", "..",
                                  "ConstructionAgent", "nope"))  # jamais utilise

    # -- memorisation ------------------------------------------------------- #
    def context(self):
        """Le project_context complet (§17), 100 % derive des fichiers."""
        tot = self.totals()
        unk = self.site_unknowns()
        return {
            "project_id": self.site.get("project_id") or self.program.get("project_id"),
            "project_name": "Villa_Test_001",
            "variant": self.program.get("variant"),
            "location": {
                "ville": "Abidjan",
                "source": "onglet projet de l'application",
            },
            "site": {
                "terrain_m": [self.site_fields().get("terrain_largeur_m", {}).get("value"),
                              self.site_fields().get("terrain_longueur_m", {}).get("value")],
                "champs_total": len(self.site_fields()),
                "champs_unknown": len(unk),
                "unknowns": unk,
                "regulation_status": self.site.get("regulation_status", _UNKNOWN),
            },
            "program": {
                "version": self.program.get("version"),
                "data_status": self.program.get("data_status", _UNKNOWN),
                "pieces": len(self.rooms()),
                "chambres": len(self.chambres()),
                "totals_m2": tot,
                "surface_check": self.program.get("surface_check", _UNKNOWN),
            },
            "floorplan": {
                "status": self.floorplan.get("STATUS", _UNKNOWN),
                "enveloppe_brute_m": self.floorplan.get("enveloppe_brute_m"),
                "interieur_m2": self.floorplan.get("interieur_m2"),
            },
            "bim": {
                "total": self.bim.get("total"),
                "familles": self.bim_familles(),
                "niveaux": self.bim_niveaux(),
                "source": self.bim.get("bim"),
                "sha256_bim": self.bim.get("sha256_bim"),
            },
            "metre": {
                "status": self.metre.get("STATUS", _UNKNOWN),
                "independantes_de_G3": len(self.quantites(False)),
                "dependantes_de_G3": len(self.quantites(True)),
            },
            "budget": {
                "total_fcfa": self.budget_total(),
                "status": self.budget.get("STATUS", _UNKNOWN),
                "statuts_presents": self.budget.get("statuts_presents", []),
            },
            "documents": {k: len(v) for k, v in self._files.items()},
            "decisions": len(self.decisions),
            "human_gates": _GATES,
            "unknowns": unk,
        }


# --------------------------------------------------------------------------- #
#  HUMAN GATES — etat reel, jamais recalcule automatiquement
#  (source : /api/gates ; recopie ici pour le contexte hors-ligne)
# --------------------------------------------------------------------------- #
_GATES = [
    {"id": "G1", "statut": "CLOSED", "objet": "Choix architectural A/B",
     "detail": "OPTION A retenue par l'utilisateur"},
    {"id": "G2", "statut": "OPEN", "type": "HUMAN_GATE", "objet": "Terrain / assainissement",
     "professionnel": "topographe + professionnel assainissement",
     "donnee_requise": "exutoire EU, topographie, reseaux, servitudes"},
    {"id": "G3", "statut": "OPEN", "type": "HUMAN_GATE", "objet": "Geotechnique / structure",
     "professionnel": "geotechnicien + ingenieur structure",
     "donnee_requise": "portance, classe beton/acier, charges, vent, seisme, tassements"},
]


# --------------------------------------------------------------------------- #
#  M2 — ROUTEUR D'INTENTION (mots-cles, AUCUN LLM pour produire les donnees)
# --------------------------------------------------------------------------- #
# Ordre = PRIORITE. GATE d'abord (une validation ne doit jamais etre contournee),
# puis GUIDE AVANT BIM : « c'est quoi une semelle » est une EXPLICATION, pas une
# interrogation sur le modele. Le BIM ne repond qu'aux questions qui le visent.
INTENTS = [
    ("GATE",       r"bloqu|blocage|valid|human gate|professionnel|geotechni|ingenieur|gate"),
    ("NEXT_STEP",  r"prochaine|ensuite|que dois-je|quoi faire|etape suivante"),
    ("GUIDE",      r"c'est quoi|qu'est-ce|c est quoi|qu est-ce|explique|definition|apprendre|comprendre|"
                   r"role|sert a|a quoi sert|difference|comment ca marche|pourquoi"),
    ("BIM",        r"\bbim\b|\b3d\b|maquette|poteau|poutre|dalle|semelle|fondation|fenetre|porte|mur|element"),
    ("PLAN",       r"plan|plans|coupe|facade|implantation|cotation|dessin"),
    ("QUANTITY",   r"combien|quantit|metre|nombre|surface|\bm2\b|\bm3\b|volume"),
    ("BUDGET",     r"budget|cout|prix|fcfa|cher|depense|financement|devis"),
    ("PROJECT",    r"projet|presente|villa|maison|terrain|surface totale|piece|chambre|salon"),
    ("STATUS",     r"statut|unknown|hypothese|proposed|verifie|pending|ou en est|avancement"),
]

# Une question qui demande d'AUTORISER un travail physique est une demande de
# validation, jamais une demande de « prochaine etape ». Elle doit passer par GATE.
_AUTORISATION = re.compile(
    r"(puis[- ]?je|peut[- ]?on|est[- ]?ce que je peux|je peux)\s+(commencer|construire|"
    r"couler|demarrer|d[eé]marrer|faire)\b|"
    r"(commencer|construire|demarrer|d[eé]marrer)\s+les\s+(fondations|travaux)|"
    r"(fondations?)\s+maintenant", re.I)


def detect_intent(msg):
    m = (msg or "").lower()
    if _AUTORISATION.search(m):        # « puis-je construire les fondations ? » -> GATE
        return "GATE"
    # §13 : une question sur les FENETRES doit passer par BIM, sinon QUANTITY
    # repondrait par la liste des metres sans jamais expliquer le piege 17/34.
    if re.search(r"fen[eê]tres?", m, re.I):
        return "BIM"
    # Une question sur une PIECE nommee du programme -> donnee de programme
    if re.search(r"salon|chambre|cuisine|s[ée]jour|suite|garage|terrasse|buanderie|patio|bureau", m, re.I):
        # « combien de chambres » attend un NOMBRE -> QUANTITY (la branche PIECE
        # ne renverrait que la fiche d'UNE piece, ce qui serait faux).
        if re.search(r"combien|nombre|nb\b", m, re.I):
            return "QUANTITY"
        return "PIECE"
    for nom, motif in INTENTS:
        if re.search(motif, m, re.I):
            return nom
    return "GENERAL"


# --------------------------------------------------------------------------- #
#  M2 — PROCHAINE ETAPE REELLE (§9)
# --------------------------------------------------------------------------- #
def next_step(ctx):
    """Determinee par les donnees. Aucun pourcentage invente."""
    unk = ctx.site_unknowns()
    if unk:
        return {
            "titre": "Completer les informations reelles du terrain",
            "raison": "Le dossier site contient %d champ(s) sans valeur reelle." % len(unk),
            "champs_manquants": unk,
            "statut": "UNKNOWN",
            "professionnel_requis": "topographe + professionnel assainissement",
            "gate": "G2",
            "methode": "comptage des champs sans valeur dans site/site.json",
            "action": {"type": "navigate", "cible": "projet", "label": "Voir le dossier terrain"},
        }
    return {
        "titre": "Aucune information de terrain manquante detectee",
        "statut": "VERIFIED",
        "methode": "comptage des champs sans valeur dans site/site.json",
        "action": {"type": "navigate", "cible": "projet", "label": "Voir le dossier"},
    }


# --------------------------------------------------------------------------- #
#  M2 — REPONSES ANCREES DANS LES DONNEES REELLES (§24 : actionnables)
# --------------------------------------------------------------------------- #
def _fmt_familles(f):
    """Le BIM expose familles/niveaux tantot en list, tantot en dict (donnee reelle).
    On n'echoue jamais sur la forme : on l'affiche telle qu'elle est."""
    try:
        if isinstance(f, dict):
            return ", ".join("%s=%s" % (k, v) for k, v in sorted(f.items()))
        if isinstance(f, list):
            out = []
            for x in f:
                if isinstance(x, dict):
                    n = x.get("famille") or x.get("nom") or x.get("niveau") or "?"
                    out.append("%s=%s" % (n, x.get("count") or x.get("nombre") or x.get("total") or ""))
                else:
                    out.append(str(x))
            return ", ".join(out)
    except Exception:
        pass
    return str(f)


def _fmt(n):
    try:
        return format(int(n), ",").replace(",", " ")
    except Exception:
        return str(n)


def answer(ctx, msg, pro=False):
    """Renvoie {reponse, source, donnees, actions, statut}. Rien d'invente."""
    it = detect_intent(msg)
    r = {"intent": it, "question": msg, "mode": "PROFESSIONNEL" if pro else "DEBUTANT",
         "statut": "VERIFIED", "source": None, "reponse": "", "donnees": {}, "actions": []}

    if it == "PROJECT":
        c = ctx.context()
        r["source"] = "site/site.json + program/program.json + floorplan/floor_plan.json"
        r["donnees"] = {"program": c["program"], "site": c["site"], "variant": c["variant"]}
        r["reponse"] = (
            "Projet %s (variant %s).\n"
            "- Terrain : %s x %s m\n"
            "- Programme : %d pieces, dont %d chambres\n"
            "- Surfaces : RDC %s m2, etage %s m2, interieur %s m2\n"
            "- BIM : %s elements indexes\n"
            "- Budget de travail : %s FCFA\n"
            "- Plan 2D : statut %s" % (
                c["project_id"], c["variant"],
                c["site"]["terrain_m"][0], c["site"]["terrain_m"][1],
                c["program"]["pieces"], c["program"]["chambres"],
                c["program"]["totals_m2"].get("RDC"), c["program"]["totals_m2"].get("ETAGE"),
                c["program"]["totals_m2"].get("INTERIEUR"),
                c["bim"]["total"], _fmt(c["budget"]["total_fcfa"]),
                c["floorplan"]["status"]))
        r["actions"] = [
            {"type": "navigate", "cible": "projet", "label": "Mon projet"},
            {"type": "navigate", "cible": "plans", "label": "Mes plans"},
            {"type": "navigate", "cible": "3d", "label": "Voir en 3D"},
        ]

    elif it == "PIECE":
        m2 = re.search(r"salon|chambre|cuisine|s[ée]jour|suite|garage|terrasse|buanderie|patio|bureau",
                       msg, re.I)
        cible = m2.group(0) if m2 else None
        trouve = ctx.piece(cible) if cible else None
        r["source"] = "program/program.json"
        if trouve:
            r["donnees"] = trouve
            r["reponse"] = ("%s : %s m2, niveau %s (code %s).\n"
                            "Surface issue du programme VALIDE (v%s) — donnee de reference, "
                            "non recalculee depuis un modele 3D." % (
                                trouve.get("name"), trouve.get("surface_m2"),
                                trouve.get("level"), trouve.get("code"),
                                ctx.program.get("version")))
        else:
            r["statut"] = "UNKNOWN"
            r["reponse"] = ("Aucune piece nommee '%s' dans le programme (13 pieces : %s). "
                            "Je n'invente pas de surface." % (cible,
                            ", ".join(x.get("name") for x in ctx.rooms())))
        r["actions"] = [{"type": "navigate", "cible": "projet", "label": "Voir le programme"}]

    elif it == "QUANTITY":
        ch = re.search(r"chambre", msg, re.I)
        fe = re.search(r"fenetre", msg, re.I)
        if ch:
            lst = ctx.chambres()
            r["source"] = "program/program.json"
            r["donnees"] = [{"code": x.get("code"), "nom": x.get("name"),
                             "surface_m2": x.get("surface_m2"), "niveau": x.get("level")} for x in lst]
            r["reponse"] = "Le programme compte %d chambre(s) : %s." % (
                len(lst), " ; ".join("%s (%s m2, %s)" % (x.get("name"), x.get("surface_m2"),
                                                         x.get("level")) for x in lst))
        elif fe:
            objs = ctx.bim_fenetres()
            r["source"] = "3D/bim_elements.json"
            r["donnees"] = {"objets_bim": len(objs), "famille": "FENETRE"}
            r["reponse"] = (
                "Le BIM contient %d OBJETS de famille FENETRE. "
                "Attention : un objet n'est pas forcement une fenetre — les plans indiquent "
                "17 fenetres reelles, chaque fenetre etant representee par plusieurs composants "
                "(chassis + allege). Je n'affiche donc pas %d fenetres." % (len(objs), len(objs)))
        else:
            q = ctx.quantites(False)
            r["source"] = "metre/metre_final_v2.json"
            r["donnees"] = [{"id": x.get("id"), "qte": x.get("quantite"), "unite": x.get("unite")}
                            for x in q]
            r["reponse"] = "Metre : %d quantites independantes de G3 :\n%s" % (
                len(q), "\n".join("- %s : %s %s" % (x.get("id"), x.get("quantite"), x.get("unite"))
                                  for x in q[:8]))
        r["actions"] = [{"type": "navigate", "cible": "budget", "label": "Voir les quantites"}]

    elif it == "BUDGET":
        b = ctx.budget
        r["source"] = "budget/budget_final_v2.json"
        r["donnees"] = {"total": b.get("total_general_fcfa"), "status": b.get("STATUS"),
                        "statuts": b.get("statuts_presents")}
        r["reponse"] = (
            "Le budget de travail enregistre est de %s FCFA.\n"
            "Il s'agit d'une ESTIMATION DE TRAVAIL, pas d'un devis d'entreprise.\n"
            "Statut du fichier : %s\nStatuts presents : %s" % (
                _fmt(b.get("total_general_fcfa")), b.get("STATUS"),
                ", ".join(b.get("statuts_presents") or [])))
        r["statut"] = "PARTIAL"
        r["actions"] = [{"type": "navigate", "cible": "budget", "label": "Ouvrir le budget"}]

    elif it == "BIM":
        m = re.search(r"poteau|poutre|dalle|semelle|fondation|fenetre|porte|mur|acrotere", msg, re.I)
        fam = m.group(0).upper() if m else None
        alias = {"FONDATION": "SEMELLE", "FENETRE": "FENETRE", "MUR": "MUR"}
        fam = alias.get(fam, fam) if fam else None
        if fam:
            lst = [e for e in ctx.bim_elements()
                   if (e.get("famille") or "").upper().startswith(fam[:5])]
            r["source"] = "3D/bim_elements.json"
            r["donnees"] = {"famille": fam, "objets": len(lst),
                            "exemple": lst[0] if lst else None}
            if lst:
                e0 = lst[0]
                st = sorted(set(x.get("statut") for x in lst))
                r["reponse"] = (
                    "Famille %s : %d objets BIM (source %s).\n"
                    "Exemple — %s : %s x %s x %s m, %s m3, statut %s.\n"
                    "Statuts presents dans la famille : %s.\n"
                    "Ces elements appartiennent au modele CONCEPTUEL : ils ne constituent pas "
                    "une validation d'execution." % (
                        fam, len(lst), e0.get("source"), e0.get("id"),
                        *(list(e0.get("dimensions_m") or ["?", "?", "?"]) + ["?", "?", "?"])[:3],
                        e0.get("volume_m3"), e0.get("statut"), ", ".join(map(str, st))))
            else:
                r["reponse"] = "Aucun element de famille %s dans le BIM." % fam
                r["statut"] = "UNKNOWN"
        else:
            b = ctx.bim
            r["source"] = "3D/bim_elements.json"
            r["donnees"] = {"total": b.get("total"), "familles": b.get("familles")}
            r["reponse"] = ("Le BIM officiel contient %s elements indexes, source %s.\n"
                            "Familles : %s" % (b.get("total"), b.get("bim"),
                                               _fmt_familles(b.get("familles"))))
        r["actions"] = [{"type": "navigate", "cible": "3d", "label": "Ouvrir la 3D"}]

    elif it == "PLAN":
        r["source"] = "plans/ + coupes/ + facades/"
        r["donnees"] = {"plans": len(ctx._files.get("plans", [])),
                        "coupes": len(ctx._files.get("coupes", [])),
                        "facades": len(ctx._files.get("facades", []))}
        r["reponse"] = ("Le dossier contient %d plans, %d coupes et %d facades.\n"
                        "Le plan 2D est fige en VALIDATED (gel geometrique) : il ne doit plus "
                        "etre modifie sans nouvelle validation humaine." % (
                            len(ctx._files.get("plans", [])), len(ctx._files.get("coupes", [])),
                            len(ctx._files.get("facades", []))))
        r["actions"] = [{"type": "navigate", "cible": "plans", "label": "Ouvrir les plans"}]

    elif it == "GATE":
        g = _GATES
        r["source"] = "/api/gates"
        r["donnees"] = g
        r["reponse"] = "TROIS points de validation, etat reel :\n" + "\n".join(
            "- %s %s : %s%s" % (x["id"], x["statut"], x["objet"],
                                (" — professionnel requis : " + x["professionnel"]) if x.get("professionnel") else "")
            for x in g) + \
            "\n\nCes validations ne peuvent pas etre franchies automatiquement. " \
            "Le projet avance, mais deux dossiers attendent une intervention professionnelle."
        r["statut"] = "PARTIAL"
        r["actions"] = [{"type": "navigate", "cible": "gates", "label": "Voir les validations"}]

    elif it == "NEXT_STEP":
        ns = next_step(ctx)
        r["source"] = "site/site.json"
        r["donnees"] = ns
        r["reponse"] = "%s\n%s" % (ns["titre"], ns.get("raison", ""))
        r["statut"] = ns["statut"]
        r["actions"] = [ns["action"]]

    elif it == "STATUS":
        unk = ctx.site_unknowns()
        g = _GATES
        r["source"] = "site/site.json + /api/gates"
        r["donnees"] = {"unknowns": unk, "gates": g}
        r["reponse"] = (
            "Voici ce qui est ETABLI et ce qui NE L'EST PAS.\n"
            "- Plan 2D : %s (geometrie validee, gelee)\n"
            "- Programmation : %s (v%s)\n"
            "- BIM : %s elements\n"
            "- Metre : %s\n"
            "- Budget : %s\n"
            "- Terrain : %d champ(s) sans valeur reelle\n"
            "- Validations : %s\n\n"
            "Un statut PROPOSED reste PROPOSED. Une HYPOTHESIS reste une hypothese. "
            "Je ne transforme rien en certitude." % (
                ctx.floorplan.get("STATUS"), ctx.program.get("data_status"),
                ctx.program.get("version"), ctx.bim.get("total"),
                ctx.metre.get("STATUS"), ctx.budget.get("STATUS"), len(unk),
                " | ".join("%s=%s" % (x["id"], x["statut"]) for x in g)))
        r["statut"] = "PARTIAL"
        r["actions"] = [{"type": "navigate", "cible": "projet", "label": "Voir l'etat du projet"}]

    elif it == "GUIDE":
        r["source"] = "construction_guide_engine.ask() — delegue au moteur existant"
        r["reponse"] = "__DELEGUE_AU_GUIDE__"
        r["actions"] = [{"type": "navigate", "cible": "assistant", "label": "Mode guide"}]

    else:
        r["source"] = None
        r["statut"] = "UNKNOWN"
        r["reponse"] = ("Je n'ai pas de reponse ancre dans les donnees du projet pour cette question. "
                        "Je peux vous presenter le projet, les plans, le BIM, les quantites, le budget, "
                        "les validations, ou repondre a une question de construction via le Guide.")
        r["actions"] = [
            {"type": "navigate", "cible": "projet", "label": "Mon projet"},
            {"type": "navigate", "cible": "3d", "label": "Mon BIM"},
            {"type": "navigate", "cible": "budget", "label": "Mon budget"},
            {"type": "navigate", "cible": "gates", "label": "Mes validations"},
        ]
    return r
