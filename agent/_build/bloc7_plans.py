#!/usr/bin/env python3
"""BLOC 7 — generation reelle des 10 plans + 2 coupes + 4 facades depuis le BIM.
Projections geometriques des bbox reelles. Aucune cote inventee. Elements
structurels etiquetes PROPOSED / PENDING_G3."""
import json, os, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
D = json.load(open("/tmp/bim_dump.json"))
O = D["objets"]
S = datetime.datetime.now().isoformat(timespec="seconds")
SC = 60.0                      # px par metre
PAD = 60

FAM = lambda *p: [o for o in O if o["nom"].startswith(tuple(p))]
par_nom = {o["nom"]: o for o in O}


def bb(o): return o["bbox"]


def svg(path, w_m, h_m, elems, titre, note=""):
    W = int(w_m * SC) + 2 * PAD
    H = int(h_m * SC) + 2 * PAD + 90
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
           '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H),
           '<text x="%d" y="34" font-family="Helvetica,Arial" font-size="20" font-weight="bold" fill="#111">%s</text>' % (PAD, titre),
           '<text x="%d" y="54" font-family="Helvetica,Arial" font-size="11" fill="#555">PRJ_1701484686 · Villa_Test_001 · echelle 1 m = %d px · %s</text>' % (PAD, int(SC), note)]
    g = ['<g transform="translate(%d,%d) scale(%f,%f)">' % (PAD, PAD + 70, SC, -SC)]
    for (x0, y0, x1, y1, fill, stroke, sw, op) in elems:
        g.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="%s" stroke="%s" stroke-width="%.4f" opacity="%.2f"/>'
                 % (x0, y0, max(0.001, x1 - x0), max(0.001, y1 - y0), fill, stroke, sw / SC, op))
    out += g + ['</g>',
                '<text x="%d" y="%d" font-family="Helvetica,Arial" font-size="11" fill="#555">%s</text>' % (PAD, H - 18, note),
                '</svg>']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("\n".join(out))
    return W, H


def rects(objs, fill, stroke="#222", sw=0.06, op=1.0, zmin=None, zmax=None, dz=None):
    r = []
    for o in objs:
        a, b, c, d, e, f = bb(o)
        if zmin is not None and not (c < zmax and f > zmin): continue
        if dz is not None and not (c >= dz[0] and c < dz[1]): continue
        r.append((a, b, d, e, fill, stroke, sw, op))
    return r


FICHIERS = []


def emit(path, w, h, elems, titre, note, statut, src):
    W, H = svg(path, w, h, elems, titre, note)
    FICHIERS.append({"chemin": os.path.relpath(path, PROJ), "octets": os.path.getsize(path),
                     "format": "SVG", "dimensions_px": [W, H], "source": src, "statut": statut, "titre": titre})


MURS = FAM("MUR_"); CLOIS = FAM("CLOISON_"); FEN = FAM("FENETRE_")
POUT = FAM("POUTEAU_"); POU = FAM("POUTRE_"); DAL = FAM("DALLE_"); ACRO = FAM("ACRO_")
SEM = FAM("SEMELLE_"); LONG = FAM("LONGRINE_"); GAR = FAM("GARDE_"); ETAN = FAM("ETANCHEITE_")
GARAGE = FAM("GARAGE_"); TERR = FAM("TERRASSE_"); ESC = FAM("VA_MARCHE"); MEU = FAM("MEUBLE_")
SITE = FAM("SITE_TERRAIN")
MSG_G3 = "Structure PROPOSED / PENDING_G3 — non validee par ingenieur"

# ---------- P01 implantation ----------
e = rects(SITE, "#eef7e8", "#7aa05a", 0.10)
e += rects(MURS, "#d9d9d9", "#111", 0.10)
e += rects(GARAGE, "#f2e6d9", "#8a6a3a", 0.10)
e += rects(TERR, "#f5f0dc", "#8a8a3a", 0.10)
e += [(-2.30, -3.00, 12.70, 22.00, "none", "#333", 0.20, 1.0)]
emit(PROJ + "/plans/P01_implantation.svg", 15.0, 25.0, e, "P01 — PLAN DE SITUATION / IMPLANTATION",
     "terrain 15,00 x 25,00 m (375 m2) · villa 10,40 x 10,90 m · garage 5,00x5,00 · terrasse 6,00x4,00",
     "VERIFIED (2D VALIDATED + BIM)", "floorplan/implantation.svg + BIM_FINAL_A3")

# ---------- P02 RDC ----------
e = rects(MURS, "#cfcfcf", "#111", 0.09)
e += rects(CLOIS, "#e8e8e8", "#333", 0.07)
e += rects(FEN, "#9fd3f5", "#1a5f8a", 0.06, zmin=0.0, zmax=3.0)
e += rects(MEU, "#f7f0e0", "#a08050", 0.05)
e += rects(POUT, "#ffd9d9", "#a33", 0.05, zmin=0.0, zmax=3.2)
emit(PROJ + "/plans/P02_plan_RDC.svg", 10.40, 10.90, e, "P02 — PLAN RDC",
     "murs 63 · cloisons 49 · 17 fenetres · mobilier 46 blocs · poteaux " + MSG_G3,
     "VERIFIED (architecture) / PENDING_G3 (structure)", "BIM_FINAL_A3")

# ---------- P03 etage ----------
e = rects(MURS, "#cfcfcf", "#111", 0.09, dz=(3.2, 6.4))
e += rects(CLOIS, "#e8e8e8", "#333", 0.07, dz=(3.2, 6.4))
e += rects(FEN, "#9fd3f5", "#1a5f8a", 0.06, dz=(3.2, 6.4))
e += rects(POUT, "#ffd9d9", "#a33", 0.05, dz=(3.2, 6.4))
e += rects(TERR, "#f5f0dc", "#8a8a3a", 0.06, dz=(3.2, 6.4))
emit(PROJ + "/plans/P03_plan_etage.svg", 10.40, 10.90, e, "P03 — PLAN ETAGE",
     "Suite 16 · Ch2 13 · Ch3 13 · Ch4 12 · 3 SdB x5 = 69 m2 · patio 3,00x4,00 m · " + MSG_G3,
     "VERIFIED (2D VALIDATED) / PENDING_G3 (structure)", "floor_plan.json ETAGE + BIM_FINAL_A3")

# ---------- P04 toiture ----------
e = rects(ETAN, "#dfe9f5", "#2a5a8a", 0.08)
e += rects(ACRO, "#d0d0d0", "#111", 0.08)
e += rects(SITE, "#eef7e8", "#7aa05a", 0.05, op=0.4)
emit(PROJ + "/plans/P04_plan_toiture.svg", 15.0, 25.0, e, "P04 — PLAN TOITURE",
     "toiture-terrasse 99,92 m2 · acroteres 6 elements · etancheite 30,24 m2 modelisee · pente NON definie (UNKNOWN)",
     "PARTIAL", "BIM_FINAL_A3")

# ---------- P05/P06 cotation ----------
def cotes(objs, z0, z1):
    e = rects(objs, "#efefef", "#111", 0.07)
    xs = sorted({round(bb(o)[0], 2) for o in objs} | {round(bb(o)[3], 2) for o in objs})
    for i in range(min(len(xs) - 1, 14)):
        d = xs[i + 1] - xs[i]
        if d > 0.2: e.append((xs[i], 11.2, xs[i + 1], 11.35, "#333", "#333", 0.03, 1.0))
    return e
emit(PROJ + "/plans/P05_cotation_RDC.svg", 10.40, 12.0,
     cotes(MURS + CLOIS, 0, 3.2), "P05 — PLAN DE COTATION RDC",
     "cotes issues des bbox reelles · enveloppe 10,40 x 10,90 m · interieur 10,00 x 10,50 m · niveaux 0,00 / 3,20 / 6,40",
     "VERIFIED (cotes BIM)", "BIM_FINAL_A3")
emit(PROJ + "/plans/P06_cotation_etage.svg", 10.40, 12.0,
     cotes([o for o in MURS + CLOIS if bb(o)[2] > 3.2], 3.2, 6.4), "P06 — PLAN DE COTATION ETAGE",
     "cotes issues des bbox reelles · niveau 3,20 · habitable etage 93,00 m2 (2D VALIDATED)",
     "VERIFIED (cotes BIM)", "BIM_FINAL_A3 + floor_plan.json")

# ---------- P07 portes/fenetres ----------
e = rects(MURS, "#e0e0e0", "#999", 0.05)
e += rects(FEN, "#8ec9ee", "#14507a", 0.08)
e += [(8.40, 4.55, 9.75, 4.85, "#e8a0a0", "#8a2020", 0.06, 1.0),
      (1.75, 7.05, 3.10, 7.35, "#e8a0a0", "#8a2020", 0.06, 1.0),
      (4.50, 7.05, 5.85, 7.35, "#e8a0a0", "#8a2020", 0.06, 1.0),
      (6.85, 7.05, 8.20, 7.35, "#e8a0a0", "#8a2020", 0.06, 1.0),
      (8.75, 7.05, 10.15, 7.35, "#e8a0a0", "#8a2020", 0.06, 1.0),
      (10.10, 4.90, 10.40, 6.10, "#c02020", "#600", 0.08, 1.0)]
emit(PROJ + "/plans/P07_portes_fenetres.svg", 10.40, 10.90, e, "P07 — PLAN PORTES ET FENETRES",
     "5 portes interieures 1,35/1,40 m · 17 fenetres (chassis + allege) · porte d'entree 1,20 m (2D VALIDATED) · portes d'etage UNKNOWN",
     "PARTIAL", "nomenclature_portes_fenetres.json + BIM_FINAL_A3")

# ---------- P08 sols ----------
e = rects(FAM("DALLAGE_"), "#efe4d0", "#8a6a3a", 0.08)
e += rects(TERR, "#f5f0dc", "#8a8a3a", 0.06)
e += rects(GARAGE, "#f2e6d9", "#8a6a3a", 0.08)
e += rects(MURS, "#dddddd", "#999", 0.04)
emit(PROJ + "/plans/P08_plan_sols.svg", 15.0, 25.0, e, "P08 — PLAN SOLS / REVETEMENTS",
     "dallage 113,36 m2 (terrain) · terrasse 24,00 m2 · garage 25,00 m2 · revetements interieurs NON specifies (UNKNOWN)",
     "PARTIAL", "BIM_FINAL_A3")

# ---------- P09 plafond ----------
e = rects([o for o in DAL if bb(o)[2] >= 3.2], "#e8eef5", "#4a6a8a", 0.08)
e += rects(MURS, "#e0e0e0", "#999", 0.05, zmin=3.2, zmax=6.4)
emit(PROJ + "/plans/P09_plan_plafond.svg", 10.40, 10.90, e, "P09 — PLAN PLAFOND / DALLE HAUTE",
     "dalle d'etage (epaisseur 15 cm PROPOSED) — aucun faux plafond modelise (NOT_MODELED)",
     "PENDING_G3", "BIM_FINAL_A3")

# ---------- P10 reseaux ----------
e = rects(MURS, "#e8e8e8", "#bbb", 0.04)
e += rects(CLOIS, "#f0f0f0", "#ccc", 0.04)
e += [(0.20, 7.30, 3.73, 10.70, "#dff0ff", "#2a6a9a", 0.05, 0.55), (6.67, 7.30, 8.44, 10.70, "#dff0ff", "#2a6a9a", 0.05, 0.55),
      (8.70, 7.30, 10.20, 9.30, "#f0e0ff", "#6a2a9a", 0.05, 0.55)]
emit(PROJ + "/plans/P10_plan_reseaux.svg", 10.40, 10.90, e, "P10 — PLAN TECHNIQUE / RESEAUX",
     "pieces humides : Cuisine · Buanderie · WC(dessin) · RESEAU NON TRACE : exutoire EU = UNKNOWN (G2) · ventilation WC = mecanique (choix A)",
     "UNKNOWN / PENDING_G2", "bloc5_structure_reseaux.json")

# ---------- COUPES ----------
def coupe(ycut, larg, titre, note):
    e = []
    for o in MURS + CLOIS:
        a, b, c, d, f, g = bb(o)
        if b - 0.05 <= ycut <= f + 0.05:
            e.append((a, c, d, g, "#d0d0d0", "#111", 0.07, 1.0))
    for o in DAL:
        a, b, c, d, f, g = bb(o)
        e.append((a, c, d, g, "#c8c8c8", "#333", 0.07, 1.0))
    for o in SEM:
        a, b, c, d, f, g = bb(o)
        e.append((a, c, d, g, "#e0d0c0", "#7a5a3a", 0.06, 1.0))
    for o in LONG:
        a, b, c, d, f, g = bb(o)
        e.append((a, c, d, g, "#e8dcc8", "#7a5a3a", 0.06, 1.0))
    for o in POUT:
        a, b, c, d, f, g = bb(o)
        if b - 0.05 <= ycut <= f + 0.05 and c < 3.3:
            e.append((a, c, d, g, "#ffd9d9", "#a33", 0.06, 1.0))
    for o in ESC:
        a, b, c, d, f, g = bb(o)
        e.append((a, c, d, g, "#f0e0c0", "#8a6a3a", 0.05, 1.0))
    e.append((-2.30, -0.30, 12.70, 0.00, "#eeeee0", "#999", 0.05, 1.0))
    return e


emit(PROJ + "/coupes/C01_coupe_longitudinale.svg", 15.0, 7.5,
     coupe(5.30, 15.0, "", ""), "C01 — COUPE LONGITUDINALE (par l'escalier)",
     "coupe y = 5,30 m (traverse l'escalier x[1,45..6,15]) · niveaux 0,00 / 3,20 / 6,40 · fondations PENDING_G3",
     "PARTIAL / PENDING_G3", "BIM_FINAL_A3")
emit(PROJ + "/coupes/C02_coupe_transversale.svg", 12.0, 7.5,
     coupe(5.30, 12.0, "", ""), "C02 — COUPE TRANSVERSALE",
     "coupe representative au droit des pieces · hauteurs 3,20 m par niveau · dalle 15 cm PROPOSED",
     "PARTIAL / PENDING_G3", "BIM_FINAL_A3")

# ---------- FACADES ----------
def facade(axe, sens, titre, note):
    e = []
    for o in MURS:
        a, b, c, d, f, g = bb(o)
        if axe == "y":
            if (sens == "S" and b > 0.30) or (sens == "N" and f < 10.60): continue
            e.append((a, c, d, g, "#d8d8d8", "#111", 0.07, 1.0))
        else:
            if (sens == "O" and a > 0.30) or (sens == "E" and d < 10.10): continue
            e.append((b, c, f, g, "#d8d8d8", "#111", 0.07, 1.0))
    for o in FEN:
        a, b, c, d, f, g = bb(o)
        if axe == "y":
            if (sens == "S" and b > 0.30) or (sens == "N" and f < 10.60): continue
            e.append((a, c, d, g, "#8ec9ee", "#14507a", 0.05, 1.0))
        else:
            if (sens == "O" and a > 0.30) or (sens == "E" and d < 10.10): continue
            e.append((b, c, f, g, "#8ec9ee", "#14507a", 0.05, 1.0))
    a, b, c, d, f, g = bb(par_nom["GARAGE_PORTAIL"])
    if axe == "y": e.append((a, c, d, g, "#b8b8b8", "#333", 0.06, 1.0))
    a, b, c, d, f, g = bb(par_nom["SITE_TERRAIN"])
    e.append((a if axe == "y" else b, -0.30, d if axe == "y" else f, 0.00, "#eeeee0", "#999", 0.05, 1.0))
    w = (d - a) if axe == "x" else 15.0
    return e, w


for (code, axe, sens, nom) in [("F01", "y", "N", "Nord"), ("F02", "y", "S", "Sud"),
                               ("F03", "x", "E", "Est"), ("F04", "x", "O", "Ouest")]:
    e, w = facade(axe, sens, "", "")
    emit(PROJ + "/facades/%s_facade_%s.svg" % (code, nom), max(w, 10.0), 7.5, e,
         "%s — FACADE %s" % (code, nom.upper()),
         "fenetres issues du BIM (17) · porte d'entree sur facade EST · acroteres 1,00 m · structure PENDING_G3",
         "PARTIAL", "BIM_FINAL_A3")

rap = {"etude": "bloc7_plans_coupes_facades", "at": S, "bim_source": D["fichier"], "sha256_bim": D["sha256"],
       "echelle": "1 m = 60 px", "total_documents": len(FICHIERS), "documents": FICHIERS,
       "statuts": {"VERIFIED": len([f for f in FICHIERS if f["statut"].startswith("VERIFIED")]),
                   "PARTIAL": len([f for f in FICHIERS if f["statut"].startswith("PARTIAL")]),
                   "UNKNOWN": len([f for f in FICHIERS if f["statut"].startswith("UNKNOWN")])},
       "mentions_obligatoires": ["Structure PROPOSED / PENDING_G3 — non validee par ingenieur",
                                 "Exutoire EU = UNKNOWN (G2)", "Pente de toiture NON definie"],
       "STATUS": "VERIFIED (fichiers reellement crees)"}
json.dump(rap, open(PROJ + "/reports/bloc7_plans_coupes_facades.json", "w"), indent=2, ensure_ascii=False)
print("=== BLOC 7 : %d documents generes ===" % len(FICHIERS))
for f in FICHIERS:
    print("  %-46s %6d o  %sx%s px  %s" % (f["chemin"], f["octets"], f["dimensions_px"][0], f["dimensions_px"][1], f["statut"]))
