#!/usr/bin/env python3
"""RDC : collecter les pavages et retenir celui dont le couloir touche TOUTES les pieces."""
import os, sys, json

AGENT = "/Users/mac/ConstructionAgent"
N, CELL = 20, 0.5
RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle a manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]


def cellsof(x, y, w, h):
    return {(int(round((x + i * CELL) * 2)), int(round((y + j * CELL) * 2)))
            for i in range(int(round(w / CELL))) for j in range(int(round(h / CELL)))}


def corridor(rects):
    occ = set()
    for r in rects:
        occ |= cellsof(*r[:4])
    free = {(x, y) for y in range(N) for x in range(N) if (x, y) not in occ}
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
    return all(adj) and len(er) > 0 and len(main) >= 32, {
        "libres": len(free), "composantes": len(comps), "principale": len(main),
        "erodee": len(er), "largeur_min_m": 1.5 if er else None, "touche_toutes": all(adj),
        "detail": adj}


areas = [int(round(a * 4)) for a, in [(d[2],) for d in RDC_DEF]]
mins = [int(round(m * 2)) for m in [d[3] for d in RDC_DEF]]
budget = N * N - sum(areas)
grid = [[0] * N for _ in range(N)]
idx = sorted(range(len(areas)), key=lambda i: -areas[i])
cur = [None] * len(areas)
cands = []
nodes = [0]


def ff():
    for y in range(N):
        r = grid[y]
        for x in range(N):
            if r[x] == 0:
                return x, y
    return None


def rec(k, wasted):
    nodes[0] += 1
    if nodes[0] > 4000000 or len(cands) >= 40:
        return
    if k == len(areas):
        if wasted == budget:
            rects = [(c[0] / 2.0, c[1] / 2.0, c[2] / 2.0, c[3] / 2.0) for c in cur]
            ok, info = corridor(rects)
            if ok:
                cands.append({"rects": rects, "corridor": info})
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
print("noeuds explores :", nodes[0], "| candidats valides (couloir OK) :", len(cands))
if cands:
    best = min(cands, key=lambda c: sum(max(r[2], r[3]) / min(r[2], r[3]) for r in c["rects"]))
    print("couloir :", json.dumps(best["corridor"]))
    for i, r in enumerate(best["rects"]):
        print("  %-16s %5.2f m2  %.1f x %.1f m @ (%.1f, %.1f)"
              % (RDC_DEF[i][1], RDC_DEF[i][2], r[2], r[3], r[0], r[1]))
    json.dump({"rects": [[r[0], r[1], r[2], r[3]] for r in best["rects"]],
               "corridor": best["corridor"],
               "names": [d[1] for d in RDC_DEF],
               "areas": [d[2] for d in RDC_DEF]},
              open(AGENT + "/_build/_rdc_ok.json", "w"), indent=1)
    print("-> _build/_rdc_ok.json")
else:
    print("AUCUN candidat avec couloir valide")
