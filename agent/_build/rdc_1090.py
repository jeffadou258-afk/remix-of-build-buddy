#!/usr/bin/env python3
"""RDC 10,00x10,50 + ETAGE grille 0,25 m avec couloir EXPLICITE."""
import os, sys, json

AGENT = "/Users/mac/ConstructionAgent"

# ---------------- RDC : interieur 10,00 x 10,50 (20 x 21 cellules de 0,5 m)
NW, NH, CELL = 20, 21, 0.5
RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle à manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]


def cells(x, y, w, h, c=CELL):
    return {(int(round((x + i * c) / c)), int(round((y + j * c) / c)))
            for i in range(int(round(w / c))) for j in range(int(round(h / c)))}


def corridor_analysis(rects, NW, NH, CELL, blocked=set()):
    occ = set()
    for r in rects:
        occ |= cells(r[0], r[1], r[2], r[3], CELL)
    free = {(x, y) for y in range(NH) for x in range(NW)
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
    main = comps[0]
    er = {p for p in main if all((p[0] + dx, p[1] + dy) in main
                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    adj = [any((q[0] + dx, q[1] + dy) in main for q in cells(r[0], r[1], r[2], r[3], CELL)
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for r in rects]
    return {"libres": len(free), "composantes": len(comps), "principale": len(main),
            "erodee": len(er), "largeur_min_m": (len(er) and CELL * 3) or None,
            "acces_direct_toutes": all(adj), "detail_acces": adj}


def solve_waste(areas_m2, mins_m, NW, NH, blocked, max_nodes=3000000, max_sols=200):
    areas = [int(round(a / (CELL * CELL))) for a in areas_m2]
    mins = [int(round(m / CELL)) for m in mins_m]
    free = NW * NH - len(blocked)
    budget = free - sum(areas)
    if budget < 0:
        return None, {"err": "surface insuffisante"}
    grid = [[1 if (x, y) in blocked else 0 for x in range(NW)] for y in range(NH)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    can = [None]
    sols, nodes = [0], [0]

    def ff():
        for y in range(NH):
            r = grid[y]
            for x in range(NW):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k, wasted):
        nodes[0] += 1
        if nodes[0] > max_nodes or can[0] or sols[0] >= max_sols:
            return
        if k == len(areas):
            if wasted == budget:
                sols[0] += 1
                rects = [(c[0] * CELL, c[1] * CELL, c[2] * CELL, c[3] * CELL) for c in cur]
                info = corridor_analysis(rects, NW, NH, CELL, blocked)
                if info["acces_direct_toutes"] and info["erodee"] > 0:
                    v = sum(max(r[2], r[3]) / min(r[2], r[3]) for r in rects)
                    if v < bs[0]:
                        bs[0] = v
                        best[0] = list(cur)
                        can[0] = info
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
        return None, {"sols": sols[0], "nodes": nodes[0]}
    rects = [(c[0] * CELL, c[1] * CELL, c[2] * CELL, c[3] * CELL) for c in best[0]]
    # critere L
    A, B = rects[0], rects[1]
    adj = ((abs((A[1] + A[3]) - B[1]) < 1e-9 or abs((B[1] + B[3]) - A[1]) < 1e-9) and
           (min(A[0] + A[2], B[0] + B[2]) - max(A[0], B[0]) > 1e-9)) or \
          ((abs((A[0] + A[2]) - B[0]) < 1e-9 or abs((B[0] + B[2]) - A[0]) < 1e-9) and
           (min(A[1] + A[3], B[1] + B[3]) - max(A[1], B[1]) > 1e-9))
    rect_union = (abs(A[0] - B[0]) < 1e-9 and abs(A[2] - B[2]) < 1e-9) or \
                 (abs(A[1] - B[1]) < 1e-9 and abs(A[3] - B[3]) < 1e-9)
    return rects, {"sols": sols[0], "nodes": nodes[0], "corridor": can[0],
                   "L_adjacent": adj, "L_union_rect": rect_union}


print("=" * 70)
print("RDC — 10,40 x 10,90 brut (interieur 10,00 x 10,50 = 105,00 m2)")
print("=" * 70)
rdc, info = solve_waste([d[2] for d in RDC_DEF], [d[3] for d in RDC_DEF], NW, NH, set())
print(json.dumps(info, indent=1))
if rdc:
    for i, r in enumerate(rdc):
        print("  %-16s %5.2f m2   %.2f x %.2f m @ (%.2f, %.2f)"
              % (RDC_DEF[i][1], r[2] * r[3], r[2], r[3], r[0], r[1]))
    json.dump({"rects": [[r[0], r[1], r[2], r[3]] for r in rdc],
               "names": [d[1] for d in RDC_DEF], "areas": [d[2] for d in RDC_DEF],
               "corridor": info["corridor"], "L_adjacent": info["L_adjacent"],
               "L_union_rect": info["L_union_rect"]},
              open(AGENT + "/_build/_rdc_v2.json", "w"), indent=1)
    print("-> _build/_rdc_v2.json")
