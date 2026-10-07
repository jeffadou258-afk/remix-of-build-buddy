#!/usr/bin/env python3
"""Soldeur v2 : perte par TRONCONS + filtre couloir (connexe, >=1,2 m, touche toutes les pieces)."""
import os, sys, json

AGENT = "/Users/mac/ConstructionAgent"
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


def corridor_ok(rects, blocked):
    occ = set()
    for r in rects:
        occ |= cellsof(*r[:4])
    free = {(x, y) for y in range(N) for x in range(N)
            if (x, y) not in occ and (x, y) not in blocked}
    if not free:
        return False, {}
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
    main = comps[0]
    er = {p for p in main if all((p[0] + dx, p[1] + dy) in main
                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    adj = [any((q[0] + dx, q[1] + dy) in main for q in cellsof(*r[:4])
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for r in rects]
    return (all(adj) and len(er) > 0 and len(main) >= 32), {
        "libres": len(free), "composantes": len(comps), "principale": len(main),
        "erodee": len(er), "largeur_min_m": 1.5 if er else None,
        "touche_toutes": all(adj), "detail": adj}


def solve(areas_m2, mins_m, blocked, max_nodes, max_sols):
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * 2)) for m in mins_m]
    free = N * N - len(blocked)
    if sum(areas) > free:
        return None, {"err": "surface"}
    budget = free - sum(areas)
    grid = [[1 if (x, y) in blocked else 0 for x in range(N)] for y in range(N)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]
    found_ok = [None]

    def ff():
        for y in range(N):
            r = grid[y]
            for x in range(N):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k, wasted):
        if found_ok[0] is not None:
            return
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            if wasted == budget:
                sols[0] += 1
                rects = [(c[0] / 2.0, c[1] / 2.0, c[2] / 2.0, c[3] / 2.0) for c in cur]
                okc, info = corridor_ok(rects, blocked)
                if okc:
                    v = sum(max(w, h) / float(min(w, h)) for (_, _, w, h) in cur)
                    if v < bs[0]:
                        bs[0] = v
                        best[0] = list(cur)
                        found_ok[0] = info
                        return
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
        # perte par TRONCON horizontal (1 a L cellules)
        if wasted < budget:
            maxL = min(budget - wasted, N - x0)
            for L in range(1, maxL + 1):
                for j in range(L):
                    grid[y0][x0 + j] = 9
                rec(k, wasted + L)
                for j in range(L):
                    grid[y0][x0 + j] = 0
                if found_ok[0] is not None:
                    return

    rec(0, 0)
    if best[0] is None:
        return None, {"sols": sols[0], "nodes": nodes[0]}
    rects = [(c[0] / 2.0, c[1] / 2.0, c[2] / 2.0, c[3] / 2.0) for c in best[0]]
    return rects, {"sols": sols[0], "nodes": nodes[0], "corridor": found_ok[0]}


out = {}
for label, defn, blocked_m in [("RDC", RDC_DEF, []), ("ETAGE", ETG_DEF, [RECESS])]:
    bl = set()
    for (bx, by, bw, bh) in blocked_m:
        bl |= cellsof(bx, by, bw, bh)
    print(">>> %s (budget recherche : 8M noeuds / 400 solutions)" % label)
    lay, info = solve([a for _, _, a, _ in defn], [m for _, _, _, m in defn], bl,
                      8000000, 400)
    print("    %s" % json.dumps(info))
    if lay:
        out[label] = {"rects": [[lay[i][0], lay[i][1], lay[i][2], lay[i][3], defn[i][2], defn[i][1]]
                                for i in range(len(defn))], "info": info}
        for i, r in enumerate(lay):
            print("      %-16s %5.2f m2  %.1f x %.1f m @ (%.1f, %.1f)"
                  % (defn[i][1], defn[i][2], r[2], r[3], r[0], r[1]))
    else:
        out[label] = {"erreur": "echec", "info": info}

json.dump(out, open(AGENT + "/_build/_sol2.json", "w"), indent=1)
print("\nOK les deux :", all("rects" in out.get(l, {}) for l in ("RDC", "ETAGE")))
print("-> _build/_sol2.json")
