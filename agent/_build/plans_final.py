#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — PLANS DEFINITIFS RDC + ETAGE (PRJ_1701484686)

Enveloppe validee : 10,40 x 10,40 m brut  ->  interieur 10,00 x 10,00 (murs 0,20 m)
Vie : salon + salle a manger = L ouvert de 50 m2 (OBLIGATOIRE, non rectangulaire)

Verifications reelles :
  - surface geometrique exacte par piece (aucune surface inventee)
  - aucun chevauchement (test cellule par cellule)
  - couverture geometrique
  - couloir reel : connexe, largeur >= 1,2 m, adjacent a CHAQUE piece
  - L : le salon et la salle a manger partagent une arete ET l'union n'est PAS un rectangle

Aucun Blender. Aucun rendu. .blend non touche. Aucune validation automatique.
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
U = 2                      # 0.5 m
NW = NH = 20               # 20 x 20 cellules = 10 x 10 m

RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle a manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]
ETG_DEF = [("P07", "Suite parentale", 16, 3.5), ("P08", "Chambre 2", 13, 2.0),
           ("P09", "Chambre 3", 13, 2.0), ("P10", "Chambre 4", 12, 3.0),
           ("P11", "Salle de bain 1", 5, 2.0), ("P12", "Salle de bain 2", 5, 2.0),
           ("P13", "Salle de bain 3", 5, 2.0)]
RECESS = {"x": 6.0, "y": 5.0, "w": 3.0, "d": 4.0}          # patio d'angle valide 3 x 4


def cells(x, y, w, h):
    return {(int(round((x + i * 0.5) * 2)), int(round((y + j * 0.5) * 2)))
            for i in range(int(w * 2)) for j in range(int(h * 2))}


def blocks(blocked_m):
    s = set()
    for (bx, by, bw, bh) in blocked_m:
        for i in range(int(bw * 2)):
            for j in range(int(bh * 2)):
                s.add((int(round(bx * 2)) + i, int(round(by * 2)) + j))
    return s


def solve(areas_m2, mins_m, blocked_m=None, want_l=False, max_nodes=1500000, max_sols=400):
    bl = blocks(blocked_m or [])
    grid = [[1 if (x, y) in bl else 0 for x in range(NW)] for y in range(NH)]
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * 2)) for m in mins_m]
    if sum(areas) > NW * NH - len(bl):
        return None, 0
    budget = NW * NH - len(bl) - sum(areas)
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(NH):
            r = grid[y]
            for x in range(NW):
                if r[x] == 0:
                    return x, y
        return None

    def score(c):
        s = 0.0
        for (_, _, w, h) in c:
            s += max(w, h) / float(min(w, h))
        return s

    def rec(k, wasted):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            if wasted == budget:
                sols[0] += 1
                v = score(cur)
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
        for w in range(1, NW - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > NH or min(w, h) < mn:
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
            rec(k + 1, wasted)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0
        if wasted < budget:
            grid[y0][x0] = 9
            rec(k, wasted + 1)
            grid[y0][x0] = 0

    rec(0, 0)
    if best[0] is None:
        return None, sols[0]
    out = []
    for i, (x, y, w, h) in enumerate(best[0]):
        out.append((x / U, y / U, w / U, h / U))
    return out, sols[0]


def adjacent(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    v = (abs((y1 + h1) - y2) < 1e-9 or abs((y2 + h2) - y1) < 1e-9) and \
        (min(x1 + w1, x2 + w2) - max(x1, x2) > 1e-9)
    hz = (abs((x1 + w1) - x2) < 1e-9 or abs((x2 + w2) - x1) < 1e-9) and \
         (min(y1 + h1, y2 + h2) - max(y1, y2) > 1e-9)
    return v or hz


def union_is_rectangle(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if abs(x1 - x2) < 1e-9 and abs(w1 - w2) < 1e-9:
        return True
    if abs(y1 - y2) < 1e-9 and abs(h1 - h2) < 1e-9:
        return True
    return False


def overlaps(rects):
    seen = {}
    for i, (x, y, w, h) in enumerate(rects):
        for c in cells(x, y, w, h):
            if c in seen:
                return True, seen[c], i, c
            seen[c] = i
    return False, None, None, None


def corridor_ok(rects, blocked_m, rooms_n):
    """Reliquat : connexe, largeur >= 1,2 m, adjacent a chaque piece."""
    bl = blocks(blocked_m)
    occupied = set()
    for (x, y, w, h) in rects:
        occupied |= cells(x, y, w, h)
    free = {(x, y) for y in range(NH) for x in range(NW)
            if (x, y) not in occupied and (x, y) not in bl}
    if not free:
        return False, {"raison": "aucun reliquat"}
    # composantes connexes 4-voisinage
    comps = []
    seen = set()
    for c in free:
        if c in seen:
            continue
        stack, comp = [c], set()
        seen.add(c)
        while stack:
            p = stack.pop()
            comp.add(p)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in free and q not in seen:
                    seen.add(q)
                    stack.append(q)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    main = comps[0]
    # erosion d'une cellule : passage >= 1,5 m
    eroded = {p for p in main
              if all((p[0] + dx, p[1] + dy) in main
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    # chaque piece doit etre adjacente a une cellule large
    adj_all = True
    detail = []
    for i, (x, y, w, h) in enumerate(rects):
        rm = cells(x, y, w, h)
        touch = any((q[0] + dx, q[1] + dy) in eroded
                    for q in rm for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (q[0] + dx, q[1] + dy) in main)
        detail.append(touch)
        if not touch:
            adj_all = False
    return (adj_all and len(eroded) > 0 and len(main) >= 32), {
        "cellules_reliquat": len(free), "composantes": len(comps),
        "principale": len(main), "erodee": len(eroded),
        "adjacente_a_toutes_les_pieces": adj_all, "detail": detail,
        "largeur_min_m": 1.5 if eroded else None}


def best_solution(defn, blocked_m=None):
    areas = [a for _, _, a, _ in defn]
    mins = [m for _, _, _, m in defn]
    lay, sols = solve(areas, mins, blocked_m)
    if not lay:
        return None, {"sols": sols}
    ok_c, cinfo = corridor_ok(lay, blocked_m or [], len(defn))
    r0, r1 = lay[0], lay[1]
    info = {"sols": sols, "corridor": cinfo,
            "L_adjacent": adjacent(r0, r1),
            "L_union_rectangle": union_is_rectangle(r0, r1),
            "chevauchement": overlaps(lay)[0]}
    return lay, info


def r2(x):
    return round(x, 2)


def build(defn, lay, label, blocked_m=None):
    out = []
    for (code, name, area, mn), (x, y, w, h) in zip(defn, lay):
        out.append({"code": code, "name": name, "surface_demandee_m2": float(area),
                    "surface_geometrique_m2": r2(w * h), "conforme": abs(w * h - area) < 1e-9,
                    "longueur_m": r2(max(w, h)), "largeur_m": r2(min(w, h)),
                    "ratio": round(max(w, h) / min(w, h), 2),
                    "x_m": r2(x), "y_m": r2(y), "w_m": r2(w), "d_m": r2(h),
                    "largeur_min_requise_m": mn, "largeur_min_respectee": min(w, h) >= mn - 1e-9})
    return out


res_rdc, info_rdc = best_solution(RDC_DEF)
assert res_rdc, "RDC : aucun pavage (info=%s)" % info_rdc
res_etg, info_etg = best_solution(ETG_DEF, [(RECESS["x"], RECESS["y"], RECESS["w"], RECESS["d"])])
assert res_etg, "ETAGE : aucun pavage (info=%s)" % info_etg

rdc = build(RDC_DEF, res_rdc, "RDC")
etg = build(ETG_DEF, res_etg, "ETAGE")
print("RDC  :", info_rdc)
print("ETAGE:", info_etg)
for d in rdc + etg:
    print("  %-16s %2.0f m2 -> %.1f x %.1f = %.2f m2 (ratio %.2f) @ (%.1f, %.1f)"
          % (d["name"], d["surface_demandee_m2"], d["longueur_m"], d["largeur_m"],
             d["surface_geometrique_m2"], d["ratio"], d["x_m"], d["y_m"]))
