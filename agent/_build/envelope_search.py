#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — RECHERCHE D'ENVELOPPE BRUTE (PRJ_1701484686)

Modele explicite :
  - murs exterieurs 0,20 m
  - couloir de circulation 1,20 m (bande pleine largeur)
  - reserve cloisons = reliquat du bloc (verifie <= 8 % du bloc)
  - les pieces sont placees en rectangles + 1 rectangle "reserve" (cloisons)
    => pavage EXACT du bloc, donc verification cellule par cellule possible

Aucun SVG definitif. Aucun Blender. Aucun rendu. Aucune validation.
Toute enveloppe reste HYPOTHESIS.
"""
import os
import sys
import json
import datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, file_info, now, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))

TE = 0.20      # mur exterieur
CW = 1.20      # couloir
U = 2          # 0.5 m par cellule


def solve(areas_m2, mins_m, Wcells, Hcells, max_nodes=900000, max_sols=250):
    areas = [int(round(a * U * U)) for a in areas_m2]
    mins = [int(round(m * U)) for m in mins_m]
    if sum(areas) != Wcells * Hcells:
        return None, 0
    grid = [[0] * Wcells for _ in range(Hcells)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(Hcells):
            r = grid[y]
            for x in range(Wcells):
                if r[x] == 0:
                    return x, y
        return None

    def sc(rects):
        s = 0.0
        for i, (x, y, w, h) in enumerate(rects):
            if i == len(rects) - 1:      # la reserve n'est pas notee
                continue
            s += max(w, h) / float(min(w, h))
        return s

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            v = sc(cur)
            if v < bs[0]:
                bs[0] = v
                best[0] = list(cur)
            return
        p = ff()
        if p is None:
            return
        x0, y0 = p
        i = idx[k]
        a, mn = areas[i], mins[i]
        for w in range(1, Wcells - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > Hcells or min(w, h) < mn:
                continue
            ok = True
            for yy in range(y0, y0 + h):
                row = grid[yy]
                for xx in range(x0, x0 + w):
                    if row[xx]:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 1
            cur[i] = (x0, y0, w, h)
            rec(k + 1)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0

    rec(0)
    if best[0] is None:
        return None, sols[0]
    out = [None] * len(areas)
    for i, (x, y, w, h) in enumerate(best[0]):
        out[i] = (x / U, y / U, w / U, h / U)
    return out, sols[0]


ROOMS = [("Salon", 32, 4.0), ("Salle a manger", 18, 3.5), ("Cuisine", 12, 2.5),
         ("Bureau", 10, 2.5), ("Buanderie", 6, 2.0), ("WC visiteur", 3, 1.5)]
SUM_ROOMS = sum(a for _, a, _ in ROOMS)
TER_W, TER_D = 15.0, 25.0
GAR_W, TERRA_D = 5.0, 4.0

CANDIDATES = [
    (9.2, 9.5), (9.5, 9.5), (9.5, 9.8), (9.8, 9.8), (10.0, 9.5), (10.0, 10.0),
    (10.0, 10.6), (10.0, 11.1), (10.4, 10.4), (10.4, 10.9), (9.5, 11.1),
    (10.5, 10.5), (10.9, 10.9), (10.0, 11.6), (9.9, 11.1),
]

rows = []
for (W, H) in CANDIDATES:
    brute = round(W * H, 2)
    int_w = round(W - 2 * TE, 2)
    int_h = round(H - 2 * TE, 2)
    # bloc de pieces : on retire le couloir (bande pleine largeur)
    blk_w = int_w
    blk_h = round(int_h - CW, 2)
    # alignement sur la grille 0,5 m (le reste = reserve de murs)
    cw_cells = int(blk_w // 0.5)
    ch_cells = int(blk_h // 0.5)
    blk_use_w = cw_cells * 0.5
    blk_use_h = ch_cells * 0.5
    blk_use = round(blk_use_w * blk_use_h, 2)
    reserve_murs = round((blk_w - blk_use_w) * blk_h + blk_use_w * (blk_h - blk_use_h), 2)
    couloir = round(CW * int_w, 2)
    res = round(blk_use - SUM_ROOMS, 2)
    row = {"enveloppe": "%.1f x %.1f" % (W, H), "W": W, "H": H,
           "surface_brute": brute, "interieur": round(int_w * int_h, 2),
           "couloir_m2": couloir, "couloir_pct": round(100 * couloir / (int_w * int_h), 1),
           "bloc_disponible": blk_use, "reserve_cloisons_m2": res,
           "reserve_cloisons_pct": round(100 * res / blk_use, 1) if blk_use else None,
           "reserve_alignement_m2": reserve_murs,
           "ratio_habitable_brut": round(SUM_ROOMS / brute, 3),
           "faisable": None, "raison": "", "layout": None, "sols": 0}
    # critere : le bloc doit contenir 81 m2 + une reserve de cloisons <= 8%
    if blk_use < SUM_ROOMS + 3.0:
        row["faisable"] = False
        row["raison"] = "bloc %.2f m2 insuffisant pour 81 m2 + cloisons" % blk_use
    elif res / blk_use > 0.08:
        row["faisable"] = False
        row["raison"] = "reserve cloisons %.1f%% > 8%%" % (100 * res / blk_use)
    else:
        areas = [a for _, a, _ in ROOMS] + [res]
        mins = [m for _, _, m in ROOMS] + [0.5]
        lay, sols = solve(areas, mins, cw_cells, ch_cells)
        row["sols"] = sols
        if lay:
            row["faisable"] = True
            row["layout"] = [{"nom": n, "surface_m2": a,
                              "w_m": r[2], "d_m": r[3],
                              "min_cote_m": min(r[2], r[3]),
                              "ratio": round(max(r[2], r[3]) / min(r[2], r[3]), 2),
                              "x_m": r[0], "y_m": r[1]}
                             for (n, a, _), r in zip(ROOMS, lay)]
            row["reserve_shape"] = {"w_m": lay[-1][2], "d_m": lay[-1][3], "m2": res}
            rr = [p["ratio"] for p in row["layout"]]
            row["ratio_moyen"] = round(sum(rr) / len(rr), 2)
            row["ratio_max"] = max(rr)
            row["min_cote_min"] = min(p["min_cote_m"] for p in row["layout"])
            # implantation terrain
            if W + GAR_W <= TER_W:
                imp = {"mode": "garage cote a cote", "largeur": round(W + GAR_W, 2),
                       "profondeur": round(max(H, GAR_W) + TERRA_D, 2)}
            else:
                imp = {"mode": "garage en profondeur", "largeur": round(max(W, GAR_W), 2),
                       "profondeur": round(GAR_W + H + TERRA_D, 2)}
            imp["terrain"] = "15 x 25 m"
            imp["compatible"] = imp["largeur"] <= TER_W and imp["profondeur"] <= TER_D
            imp["jardin_m2"] = round(375 - brute - 25 - 24, 2)
            row["implantation"] = imp
        else:
            row["faisable"] = False
            row["raison"] = ("aucun pavage trouve en %d solutions explorees" % sols)
    rows.append(row)

# ---------------------------------------------------------------- classement
def rank(r):
    """Critere technique explicite : conformite, proportions, efficacite, circulation, terrain."""
    if not r["faisable"]:
        return None
    c_conformite = 100.0
    c_proportions = max(0.0, 100.0 - 25.0 * (r["ratio_max"] - 1.0) - 12.0 * (r["ratio_moyen"] - 1.0))
    c_efficacite = 100.0 * r["ratio_habitable_brut"]
    c_circulation = max(0.0, 100.0 - 4.0 * abs(r["couloir_pct"] - 9.0))
    c_terrain = 100.0 if r.get("implantation", {}).get("compatible") else 0.0
    total = (0.30 * c_conformite + 0.28 * c_proportions + 0.20 * c_efficacite
             + 0.10 * c_circulation + 0.12 * c_terrain)
    r["score_detail"] = {"conformite": round(c_conformite, 1),
                         "proportions": round(c_proportions, 1),
                         "efficacite": round(c_efficacite, 1),
                         "circulation": round(c_circulation, 1),
                         "terrain": round(c_terrain, 1)}
    r["score"] = round(total, 1)
    return total


for r in rows:
    rank(r)
valides = sorted([r for r in rows if r["faisable"]], key=lambda r: -r["score"])

# ---------------------------------------------------------------- ecriture
ev = Evidence("envelope_search", P)
ev.tool("python3")
out = {"project_id": PID, "at": STAMP, "type": "ENVELOPE_SEARCH",
       "modele": {"murs_exterieurs_m": TE, "couloir_m": CW,
                  "methode": "pavage exact bloc = 6 pieces + 1 reserve cloisons",
                  "statut_enveloppes": "HYPOTHESIS — aucune validation"},
       "programme_inchange": {n: a for n, a, _ in ROOMS},
       "somme_pieces_m2": SUM_ROOMS,
       "terrain": "15 x 25 m", "garage_m2": 25, "terrasse_m2": 24,
       "candidats": rows, "valides": [r["enveloppe"] for r in valides],
       "solutions": valides[:3],
       "STATUS": "HYPOTHESIS_AWAITING_USER_SELECTION"}
p_out = os.path.join(P, "reports", "envelope_search.json")
save_json(p_out, out)
ev.created(p_out)
ev.test("programme_non_modifie", SUM_ROOMS == 81)
ev.test("au_moins_une_enveloppe_valide", len(valides) > 0, "%d valides" % len(valides))
for r in rows:
    ev.test("enveloppe_%s_faisable" % r["enveloppe"].replace(" ", "").replace(".", "_"),
            bool(r["faisable"]), r["raison"] or "ok")
ev.close("VERIFIED" if valides else "FAILED")
evf = ev.out()

SHA_A = sha256(BLEND)
PNG_A = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
print("=" * 96)
print("BALAYAGE DES ENVELOPPES — modele : murs 0,20 m | couloir 1,20 m | reserve cloisons <= 8 %")
print("=" * 96)
print("%-12s %7s %8s %8s %8s %7s %8s  %s" % ("ENVELOPPE", "BRUT", "INTER.", "COULOIR",
                                             "BLOC", "CLOIS.", "RATIO", "VERDICT"))
for r in rows:
    print("%-12s %7.2f %8.2f %5.2f(%4.1f%%) %8.2f %5.1f%% %8.3f  %s"
          % (r["enveloppe"], r["surface_brute"], r["interieur"], r["couloir_m2"],
             r["couloir_pct"], r["bloc_disponible"],
             r["reserve_cloisons_pct"] or 0, r["ratio_habitable_brut"],
             "VALIDE" if r["faisable"] else "REJETEE (" + r["raison"][:34] + ")"))

print()
print("=" * 96)
print("SOLUTIONS GEOMETRIQUEMENT VALIDES — classees par score technique")
print("=" * 96)
for i, r in enumerate(valides[:3], 1):
    print("\n--- SOLUTION %d : enveloppe brute %s m  (%.2f m2)  |  score %.1f" %
          (i, r["enveloppe"], r["surface_brute"], r["score"]))
    print("    couloir %.2f m2 (%.1f%%) | reserve cloisons %.2f m2 (%.1f%%) | ratio habitable/brut %.3f"
          % (r["couloir_m2"], r["couloir_pct"], r["reserve_cloisons_m2"],
             r["reserve_cloisons_pct"], r["ratio_habitable_brut"]))
    print("    plus grande piece : ratio %.2f | plus petite largeur : %.1f m"
          % (r["ratio_max"], r["min_cote_min"]))
    for p in r["layout"]:
        print("      %-16s %2d m2  ->  %.1f x %.1f m   (cote min %.1f m, ratio %.2f)"
              % (p["nom"], p["surface_m2"], p["w_m"], p["d_m"], p["min_cote_m"], p["ratio"]))
    im = r.get("implantation", {})
    print("    implantation : %s | %.2f x %.2f m  vs terrain 15 x 25 — %s | jardin ~%.0f m2"
          % (im.get("mode"), im.get("largeur", 0), im.get("profondeur", 0),
             "COMPATIBLE" if im.get("compatible") else "INCOMPATIBLE", im.get("jardin_m2", 0)))
    print("    score detail :", json.dumps(r["score_detail"]))

print("\n=== STATUS ===")
print("  enveloppes valides :", out["valides"])
print("  aucune marquee VALIDATED — en attente du choix utilisateur")
print("  fichier :", p_out)
print("  .blend inchange :", SHA_A == SHA_B, "| PNG generes :", PNG_A - PNG_B)
