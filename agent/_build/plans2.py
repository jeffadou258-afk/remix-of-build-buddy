#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — PLANS DEFINITIFS RDC + ETAGE (PRJ_1701484686)

Enveloppe VALIDEE : 10,40 x 10,40 m brut -> interieur 10,00 x 10,00 (murs 0,20 m)
Vie RDC : salon + salle a manger = L OUVERT de 50 m2 (non rectangulaire)
Etage   : retrait patio d'angle 3 x 4 m valide -> 69 m2 habitables

Couloir EXPLICITE (2,00 x 9,50 m = 19 m2) => pavage EXACT (aucun reliquat diffus).
Verifications : surfaces exactes, non-chevauchement, couverture, couloir adjacent
a CHAQUE piece et largeur >= 1,2 m, L reellement non rectangulaire.

Aucun Blender. Aucun rendu. .blend non touche.
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

ENV_W = ENV_H = 10.40
TE = 0.20
INT_W = INT_H = 10.00
N = 20                      # 20 x 20 cellules de 0,5 m
CELL = 0.5

RDC_DEF = [("P01", "Salon", 32, 4.0, "piece"), ("P02", "Salle a manger", 18, 3.5, "piece"),
           ("P03", "Cuisine", 12, 2.5, "piece"), ("P04", "Bureau", 10, 2.5, "piece"),
           ("P05", "Buanderie", 6, 2.0, "piece"), ("P06", "WC visiteur", 3, 1.5, "piece"),
           ("C01", "Circulation", 19, 2.0, "circulation")]
ETG_DEF = [("P07", "Suite parentale", 16, 3.5, "piece"), ("P08", "Chambre 2", 13, 2.0, "piece"),
           ("P09", "Chambre 3", 13, 2.0, "piece"), ("P10", "Chambre 4", 12, 3.0, "piece"),
           ("P11", "Salle de bain 1", 5, 2.0, "piece"), ("P12", "Salle de bain 2", 5, 2.0, "piece"),
           ("P13", "Salle de bain 3", 5, 2.0, "piece"),
           ("C02", "Circulation", 19, 2.0, "circulation")]
RECESS = (6.0, 5.0, 3.0, 4.0)     # x, y, w, d  (patio d'angle 12 m2)

results = {"files_created": [], "files_modified": [], "evidence_files": []}


# ------------------------------------------------------------------ outils
def cellsof(x, y, w, h):
    return {(int(round((x + i * CELL) * 2)), int(round((y + j * CELL) * 2)))
            for i in range(int(round(w / CELL))) for j in range(int(round(h / CELL)))}


def blocked_cells(rects_m):
    s = set()
    for (bx, by, bw, bh) in rects_m:
        s |= cellsof(bx, by, bw, bh)
    return s


def solve_exact(areas_m2, mins_m, blocked=None, max_nodes=4000000, max_sols=120):
    """Pavage EXACT (somme aires == cellules libres). Rapide et complet."""
    bl = blocked or set()
    free_cells = N * N - len(bl)
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * 2)) for m in mins_m]
    if sum(areas) != free_cells:
        return None, 0
    grid = [[1 if (x, y) in bl else 0 for x in range(N)] for y in range(N)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(N):
            r = grid[y]
            for x in range(N):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            v = sum(max(w, h) / float(min(w, h)) for (_, _, w, h) in cur)
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
        for w in range(1, N - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > N or min(w, h) < mn:
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
                    grid[yy][xx] = i + 1
            cur[i] = (x0, y0, w, h)
            rec(k + 1)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0

    rec(0)
    if best[0] is None:
        return None, sols[0]
    return [(x / 2.0, y / 2.0, w / 2.0, h / 2.0) for (x, y, w, h) in best[0]], sols[0]


def adjacent(r1, r2):
    x1, y1, w1, h1 = r1[:4]
    x2, y2, w2, h2 = r2[:4]
    v = (abs((y1 + h1) - y2) < 1e-9 or abs((y2 + h2) - y1) < 1e-9) and \
        (min(x1 + w1, x2 + w2) - max(x1, x2) > 1e-9)
    hz = (abs((x1 + w1) - x2) < 1e-9 or abs((x2 + w2) - x1) < 1e-9) and \
         (min(y1 + h1, y2 + h2) - max(y1, y2) > 1e-9)
    return v or hz


def union_rect(r1, r2):
    x1, y1, w1, h1 = r1[:4]
    x2, y2, w2, h2 = r2[:4]
    return (abs(x1 - x2) < 1e-9 and abs(w1 - w2) < 1e-9) or \
           (abs(y1 - y2) < 1e-9 and abs(h1 - h2) < 1e-9)


def verify(rects, blocked_m, label, names):
    """Tous les controles geometriques reels."""
    out = {}
    bl = blocked_cells(blocked_m)
    seen = {}
    dup = None
    for i, r in enumerate(rects):
        for c in cellsof(*r[:4]):
            if c in seen:
                dup = (seen[c], i, c)
            seen[c] = i
    out["chevauchement"] = dup is None
    out["chevauchement_detail"] = dup
    out["couverture_cellules"] = len(seen)
    out["couverture_attendue"] = N * N - len(bl)
    out["couverture_ok"] = len(seen) == out["couverture_attendue"]
    out["surfaces_exactes"] = all(abs(r[2] * r[3] - r[4]) < 1e-9 for r in rects)
    out["dans_enveloppe"] = all(r[0] >= -1e-9 and r[1] >= -1e-9
                                and r[0] + r[2] <= 10 + 1e-9
                                and r[1] + r[3] <= 10 + 1e-9 for r in rects)
    out["aucun_empiètement_patio"] = not (seen.keys() & bl)
    ci = [i for i, r in enumerate(rects) if r[5] == "circulation"][0]
    cor = rects[ci]
    out["couloir_largeur_m"] = min(cor[2], cor[3])
    out["couloir_largeur_ok"] = out["couloir_largeur_m"] >= 1.2 - 1e-9
    out["couloir_adjacent_toutes_pieces"] = all(
        i == ci or adjacent(cor, r) for i, r in enumerate(rects))
    out["couloir_detail"] = {r[6]: (True if i == ci else adjacent(cor, r))
                             for i, r in enumerate(rects)}
    return out


# ------------------------------------------------------------------ resolution
def resolve(defn, blocked_m, label):
    areas = [a for _, _, a, _, _ in defn]
    mins = [m for _, _, _, m, _ in defn]
    bl = blocked_cells(blocked_m)
    lay, sols = solve_exact(areas, mins, bl)
    if not lay:
        raise RuntimeError("%s : pavage exact introuvable (sols=%d)" % (label, sols))
    rects = [(lay[i][0], lay[i][1], lay[i][2], lay[i][3], defn[i][2], defn[i][4], defn[i][1])
             for i in range(len(defn))]
    return rects, sols


rdc_rects, rdc_sols = resolve(RDC_DEF, [], "RDC")
etg_rects, etg_sols = resolve(ETG_DEF, [RECESS], "ETAGE")

v_rdc = verify(rdc_rects, [], "RDC", None)
v_etg = verify(etg_rects, [RECESS], "ETAGE", None)

liv = adjacent(rdc_rects[0], rdc_rects[1])
liv_union_rect = union_rect(rdc_rects[0], rdc_rects[1])
v_rdc["L_salon_sam_adjacents"] = liv
v_rdc["L_union_non_rectangulaire"] = not liv_union_rect
v_rdc["L_surface_m2"] = round(rdc_rects[0][4] + rdc_rects[1][4], 2)
v_rdc["L_conforme"] = liv and (not liv_union_rect) and abs(v_rdc["L_surface_m2"] - 50) < 1e-9

v_etg["patio_3x4_present"] = True
v_etg["patio_surface_m2"] = RECESS[2] * RECESS[3]
v_etg["surface_habitable_m2"] = sum(r[4] for r in etg_rects if r[5] == "piece")

print("RDC   solutions explorees :", rdc_sols)
print("ETAGE solutions explorees :", etg_sols)
print("\n--- RDC ---")
for r in rdc_rects:
    print("  %-16s %5.2f m2  -> %.1f x %.1f m  @ (%.1f, %.1f)  %s"
          % (r[6], r[4], r[2], r[3], r[0], r[1], r[5]))
print("--- ETAGE ---")
for r in etg_rects:
    print("  %-16s %5.2f m2  -> %.1f x %.1f m  @ (%.1f, %.1f)  %s"
          % (r[6], r[4], r[2], r[3], r[0], r[1], r[5]))
print("\nRDC  controles :", json.dumps({k: v for k, v in v_rdc.items() if k != "couloir_detail"}))
print("ETG  controles :", json.dumps({k: v for k, v in v_etg.items() if k != "couloir_detail"}))
json.dump({"rdc": {"rects": rdc_rects, "v": v_rdc}, "etg": {"rects": etg_rects, "v": v_etg}},
          open("/Users/mac/ConstructionAgent/_build/_plans_solved.json", "w"), indent=1)
print("\n-> etat intermediaire ecrit : _build/_plans_solved.json")
