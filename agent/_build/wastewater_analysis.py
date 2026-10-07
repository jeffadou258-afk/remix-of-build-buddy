#!/usr/bin/env python3
"""EXUTOIRE DES EAUX USEES — analyse des solutions possibles a partir des donnees REELLES.
Aucune donnee inventee : tout ce qui n'est pas fourni reste UNKNOWN."""
import os, json, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


site = json.load(open(os.path.join(PROJ, "site", "site.json")))
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
lock = json.load(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json")))
net = json.load(open(os.path.join(PROJ, "reseaux", "networks_concept.json")))
S = site["fields"]

print("=" * 78)
print("ANALYSE — EXUTOIRE DES EAUX USEES (EU/EV)")
print("=" * 78)

# ---------- 1. DONNEES REELLEMENT DISPONIBLES ----------
print("\n[1] DONNEES DE SITE (site/site.json) — statut reel de chaque champ")
dispo = {}
for k, v in S.items():
    st = v.get("status")
    dispo[k] = st
    print("    %-24s %-14s %s" % (k, st, v.get("value")))
UNK = [k for k, v in dispo.items() if v == "UNKNOWN"]
print("    -> %d champs UNKNOWN : %s" % (len(UNK), ", ".join(UNK)))

# ---------- 2. PIECES HUMIDES ET LEURS POSITIONS (plan VALIDATED) ----------
print("\n[2] PIECES HUMIDES (positions lues dans floor_plan.json VALIDATED)")
humides = []
for lvl, rooms in (("RDC", fp["RDC"]["rooms"]), ("ETAGE", fp["ETAGE"]["rooms"])):
    for r in rooms:
        n = r["name"]
        if any(m in n for m in ("Cuisine", "Buanderie", "WC", "bain", "Salle de bain")):
            humides.append({"niveau": lvl, "piece": n, "x_m": r["x_m"], "y_m": r["y_m"],
                            "w_m": r["w_m"], "d_m": r["d_m"],
                            "surface_m2": r["surface_geometrique_m2"]})
            print("    %-6s %-18s x=%5.2f y=%5.2f  %.1f m2"
                  % (lvl, n, r["x_m"], r["y_m"], r["surface_geometrique_m2"]))
n_ref = {"RDC": 3, "ETAGE": 3}

# ---------- 3. EMPRISES CONSTRUITES SUR LE TERRAIN (implantation validee) ----------
EB = (10.40, 10.90)
VILLA = (2.30, 6.00, 10.40, 10.90)        # x, y, w, d  (mesure implantation.svg)
GARAGE = (5.00, 0.00, 5.00, 5.00)
TERRASSE = (2.30, 16.90, 6.00, 4.00)
TERRAIN = (15.0, 25.0)
print("\n[3] EMPRISES SUR LE TERRAIN (reprises de implantation.svg, HYPOTHESE d'implantation)")
for nom, (x, y, w, d) in (("Villa R+1", VILLA), ("Garage", GARAGE), ("Terrasse", TERRASSE)):
    print("    %-12s x[%5.2f..%5.2f] y[%5.2f..%5.2f]  %5.2f m2" % (nom, x, x + w, y, y + d, w * d))

# ---------- 4. ZONES LIBRES DISPONIBLES POUR UN EXUTOIRE (rasterisation reelle) ----------
RES = 0.25
NX = int(TERRAIN[0] / RES)
NY = int(TERRAIN[1] / RES)
occ = [[False] * NY for _ in range(NX)]
for (x, y, w, d) in (VILLA, GARAGE, TERRASSE):
    for i in range(int(round(x / RES)), int(round((x + w) / RES))):
        for j in range(int(round(y / RES)), int(round((y + d) / RES))):
            if 0 <= i < NX and 0 <= j < NY:
                occ[i][j] = True


def libre(x0, y0, w, h):
    i0, i1 = int(round(x0 / RES)), int(round((x0 + w) / RES))
    j0, j1 = int(round(y0 / RES)), int(round((y0 + h) / RES))
    if i0 < 0 or j0 < 0 or i1 > NX or j1 > NY:
        return False
    return not any(occ[i][j] for i in range(i0, i1) for j in range(j0, j1))


aire_libre = sum(1 for i in range(NX) for j in range(NY) if not occ[i][j]) * RES * RES
print("\n[4] TERRAIN LIBRE (hors villa/garage/terrasse) : %.2f m2 / %.2f m2 (%.0f%%)"
      % (aire_libre, TERRAIN[0] * TERRAIN[1], 100 * aire_libre / (TERRAIN[0] * TERRAIN[1])))

# recherche des zones libres >= 4 m2 pour un ouvrage de traitement
zones = []
for w in range(int(3.0 / RES), NX + 1):
    for h in range(int(2.0 / RES), NY + 1):
        for x0 in range(0, NX - w + 1):
            for y0 in range(0, NY - h + 1):
                if libre(x0 * RES, y0 * RES, w * RES, h * RES):
                    zones.append((w * RES * h * RES, x0 * RES, y0 * RES, w * RES, h * RES))
zones.sort(reverse=True)
print("    zones libres admissibles (>= 3,00 x 2,00 m) : %d" % len(zones))
for z in zones[:3]:
    print("      %.2f m2 a x=%5.2f y=%5.2f  (%.2f x %.2f m)" % z)

# ---------- 5. SOLUTIONS TECHNiquement POSSIBLES ----------
solutions = [
    {"code": "S1", "solution": "Raccordement au reseau public d'assainissement (collecteur de rue)",
     "principe": "EU+EV vers un regard de branchement puis le collecteur public",
     "conditions_requises": ["existence d'un collecteur public desservant la parcelle",
                             "autorisation et point de branchement delivres par le concessionnaire",
                             "cote de fil d'eau du collecteur compatible avec l'ecoulement gravitaire"],
     "statut": "UNKNOWN", "faisable_avec_donnees_actuelles": False},
    {"code": "S2", "solution": "Fosse septique (toutes eaux) + puits d'infiltration",
     "principe": "decantation + digestion dans une fosse etanche, infiltration des effluents dans le sol",
     "conditions_requises": ["etude de permeabilite du sol (coefficient de permeabilite)",
                             "profondeur de la nappe phretique >= 1,50 m sous le fond du puits",
                             "distance >= 3 m aux limites et >= 15 m a tout point d'eau",
                             "surface libre suffisante pour fosse + puits"],
     "statut": "UNKNOWN", "faisable_avec_donnees_actuelles": False,
     "verification_possible": ("surface libre mesuree ci-dessus : %s" %
                               ("suffisante" if zones and zones[0][0] >= 4 else "insuffisante"))},
    {"code": "S3", "solution": "Fosse septique + champ d'epandage souterrain",
     "principe": "effluents repartis dans des tranchees drainantes",
     "conditions_requises": ["sol permeabilite moyenne a bonne",
                             "surface d'epandage de l'ordre de 15 a 30 m2 selon le sol",
                             "pente, nappe et distances reglementaires"],
     "statut": "UNKNOWN", "faisable_avec_donnees_actuelles": False},
    {"code": "S4", "solution": "Fosse etanche + vidange periodique (bac a graisse sur cuisine)",
     "principe": "stockage integral, evacuation par camion de vidange",
     "conditions_requises": ["acces camion de vidange a moins de 10 m de la fosse",
                             "contrat de vidange (cout d'exploitation recurrent)"],
     "statut": "HYPOTHESIS", "faisable_avec_donnees_actuelles": True,
     "commentaire": "techniquement realisable sans donnee de sol ; impose un cout d'exploitation"},
]
print("\n[5] SOLUTIONS TECHNiquement POSSIBLES")
for s in solutions:
    print("    %-4s %-58s %s" % (s["code"], s["solution"][:58], s["statut"]))

# ---------- 6. DONNEES MANQUANTES POUR TRANCHER ----------
manquant = [
    {"code": "M1", "donnee": "Existence et cote d'un collecteur public d'assainissement "
                             "desservant la parcelle",
     "pourquoi": "conditionne S1 (solution la moins couteuse en exploitation)",
     "qui_peut_la_fournir": "concessionnaire d'assainissement / mairie de la commune",
     "statut": "UNKNOWN"},
    {"code": "M2", "donnee": "Position de la rue et des acces (cote rue du terrain)",
     "pourquoi": "determine l'orientation du reseau et le point de branchement possible",
     "qui_peut_la_fournir": "utilisateur (plan de situation, releve)",
     "statut": "UNKNOWN"},
    {"code": "M3", "donnee": "Nature du sol et coefficient de permeabilite (essai d'infiltration)",
     "pourquoi": "conditionne S2 et S3 (infiltration ou epandage)",
     "qui_peut_la_fournir": "etude geotechnique / essai de permeabilite",
     "statut": "UNKNOWN"},
    {"code": "M4", "donnee": "Profondeur de la nappe phretique (haute eau)",
     "pourquoi": "interdit ou autorise l'infiltration ; distance minimale sous l'ouvrage",
     "qui_peut_la_fournir": "etude geotechnique / piezometre",
     "statut": "UNKNOWN"},
    {"code": "M5", "donnee": "Pente du terrain",
     "pourquoi": "ecoulement gravitaire vers l'exutoire ; emplacement du point bas",
     "qui_peut_la_fournir": "releve topographique",
     "statut": "UNKNOWN"},
    {"code": "M6", "donnee": "Distances reglementaires et servitudes locales (limites, puits voisins)",
     "pourquoi": "implantation de la fosse et de l'epandage",
     "qui_peut_la_fournir": "reglement communal d'assainissement / urbanisme",
     "statut": "UNKNOWN"},
    {"code": "M7", "donnee": "Presence d'un puits ou forage sur la parcelle ou chez les voisins",
     "pourquoi": "distance sanitaire minimale a respecter",
     "qui_peut_la_fournir": "utilisateur (enquete de voisinage)",
     "statut": "UNKNOWN"},
]
print("\n[6] DONNEES MANQUANTES POUR TRANCHER : %d" % len(manquant))
for m in manquant:
    print("    %-4s %s" % (m["code"], m["donnee"][:70]))

# ---------- 7. CONVERGENCE DU RESEAU (ce qui est mesurable) ----------
print("\n[7] POINT DE CONVERGENCE DU RESEAU (deduit du plan VALIDATED)")
bas_rdc = max(humides, key=lambda h: h["y_m"]) if humides else None
print("    pièce humide RDC la plus au nord : %s (y=%.2f)" % (bas_rdc["piece"], bas_rdc["y_m"]))
print("    -> colonne EU/EV a raccorder vers l'extérieur en façade NORD (y=10,70 intérieur)")
print("    collecte estimee (conceptuelle) : EU Ø100 sur 34 m / EV Ø100 sur 22 m / EP Ø110 sur 28 m")
print("    STATUT : HYPOTHESIS (trace du reseau non dessinee, seuls les diametres sont proposes)")

out = {"analyse": "exutoire_eaux_usees", "at": STAMP,
       "geometrie_source": {"file": "floor_plan.json",
                            "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"],
                            "statut": "VALIDATED"},
       "donnees_site": {k: {"valeur": v.get("value"), "statut": v.get("status")}
                        for k, v in S.items()},
       "champs_unknown": UNK,
       "pieces_humides": humides, "nb_pieces_humides": len(humides),
       "terrain": {"m": list(TERRAIN), "m2": TERRAIN[0] * TERRAIN[1],
                   "emprises": {"villa": list(VILLA), "garage": list(GARAGE),
                                "terrasse": list(TERRASSE)},
                   "aire_libre_m2": round(aire_libre, 2),
                   "zones_libres_3x2m": [{"aire_m2": round(z[0], 2), "x": z[1], "y": z[2],
                                          "w": z[3], "h": z[4]} for z in zones[:5]]},
       "solutions_techniques": solutions,
       "donnees_manquantes": manquant,
       "conclusion": {
           "exutoire": "UNKNOWN",
           "motif": "aucune donnee reelle ne permet de determiner l'exutoire : ni l'existence "
                    "d'un collecteur public, ni la nature du sol, ni la nappe, ni la pente, "
                    "ni la position de la rue ne sont fournies",
           "solution_retenue": None,
           "solution_realisable_sans_donnee_supplementaire": "S4 (fosse etanche + vidange), "
                                                             "marquee HYPOTHESIS"},
       "STATUS": "UNKNOWN"}
p = os.path.join(PROJ, "reseaux", "exutoire_eu_analyse.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("CONCLUSION : exutoire EU = UNKNOWN  (%d donnees manquantes identifiees)" % len(manquant))
print("-> %s (%d o, %s)" % (p, os.path.getsize(p), sha(p)[:24] + "…"))
print("=" * 78)
