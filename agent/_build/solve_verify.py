#!/usr/bin/env python3
"""Solve + verification du couloir sur le reliquat REEL, puis generation des plans."""
import os, sys, json, datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, file_info, now, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
N, CELL = 20, 0.5
RECESS = (6.0, 5.0, 3.0, 4.0)

RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle a manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]
ETG_DEF = [("P07", "Suite parentale", 16, 3.5), ("P08", "Chambre 2", 13, 2.0),
           ("P09", "Chambre 3", 13, 2.0), ("P10", "Chambre 4", 12, 3.0),
           ("P11", "Salle de bain 1", 5, 2.0), ("P12", "Salle de bain 2", 5, 2.0),
           ("P13", "Salle de bain 3", 5, 2.0)]


def cellsof(x, y, w, h):
    return {(int(round((x + i * CELL) * 2)), int(round((y + j * CELL) * 2)))
            for i in range(int(round(w / CELL))) for j in range(int(round(h / CELL)))}


def solve_waste(areas_m2, mins_m, blocked, max_nodes=3000000, max_sols=250):
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * 2)) for m in mins_m]
    free = N * N - len(blocked)
    if sum(areas) > free:
        return None, {"err": "trop de surface"}
    budget = free - sum(areas)
    grid = [[1 if (x, y) in blocked else 0 for x in range(N)] for y in range(N)]
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

    def rec(k, wasted):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            if wasted == budget:
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
        return None, {"sols": sols[0], "nodes": nodes[0]}
    return [(x / 2.0, y / 2.0, w / 2.0, h / 2.0) for (x, y, w, h) in best[0]], \
           {"sols": sols[0], "nodes": nodes[0]}


def analyse_corridor(rects, blocked):
    occ = set()
    for (x, y, w, h) in rects:
        occ |= cellsof(x, y, w, h)
    free = {(x, y) for y in range(N) for x in range(N)
            if (x, y) not in occ and (x, y) not in blocked}
    comps, seen = [], set()
    for c in free:
        if c in seen:
            continue
        st, comp = [c], set()
        seen.add(c)
        while st:
            p = st.pop()
            comp.add(p)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in free and q not in seen:
                    seen.add(q)
                    st.append(q)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    main = comps[0] if comps else set()
    eroded = {p for p in main if all((p[0] + dx, p[1] + dy) in main
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    adj = []
    for (x, y, w, h) in rects:
        ok = any((q[0] + dx, q[1] + dy) in main
                 for q in cellsof(x, y, w, h)
                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        adj.append(ok)
    return {"cellules_libres": len(free), "composantes": len(comps),
            "principale": len(main), "erodee": len(eroded),
            "largeur_min_m": 1.5 if eroded else None,
            "adjacent_a_toutes_les_pieces": all(adj), "detail_adj": adj,
            "ok": all(adj) and len(eroded) > 0 and len(main) >= 32}


def bl_of(rects_m):
    s = set()
    for (bx, by, bw, bh) in rects_m:
        s |= cellsof(bx, by, bw, bh)
    return s


print("=" * 90)
out = {}
for label, defn, blocked_m in [("RDC", RDC_DEF, []), ("ETAGE", ETG_DEF, [RECESS])]:
    bl = bl_of(blocked_m)
    lay, info = solve_waste([a for _, _, a, _ in defn], [m for _, _, _, m in defn], bl)
    print("%-6s solve : %s" % (label, info))
    if not lay:
        out[label] = {"erreur": "aucun pavage", "info": info}
        continue
    rects = [(lay[i][0], lay[i][1], lay[i][2], lay[i][3], defn[i][2], defn[i][1])
             for i in range(len(defn))]
    cor = analyse_corridor([(r[0], r[1], r[2], r[3]) for r in rects], bl)
    print("       couloir : %s" % json.dumps(cor))
    out[label] = {"rects": [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rects],
                  "corridor": cor, "info": info}
    for r in rects:
        print("         %-16s %5.2f m2  %.1f x %.1f m @ (%.1f, %.1f)"
              % (r[5], r[4], r[2], r[3], r[0], r[1]))
print("=" * 90)
ok = all(out.get(l, {}).get("corridor", {}).get("ok") for l in ("RDC", "ETAGE"))
print("COULOIR OK pour les deux niveaux :", ok)
json.dump(out, open(AGENT + "/_build/_sol.json", "w"), indent=1)
print("-> _build/_sol.json")
