#!/usr/bin/env python3
"""ETAGE grille 0,25 m — solveur EXACT COMPLET (tous les rectangles au 1er coin libre)."""
import os, json

AGENT = "/Users/mac/ConstructionAgent"
C = 0.25
NW, NH = 40, 42
ROOMS = [("Suite parentale", 16.0, [(16, 16)]),
         ("Chambre 2", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 3", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 4", 12.0, [(12, 16), (16, 12)]),
         ("Salle de bain 1", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 2", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 3", 5.0, [(8, 10), (10, 8)]), ]
RC = [int(round(r[1] / (C * C))) for r in ROOMS]


def solve(patio, cor_dims, n_filler, max_nodes=3000000):
    px, py, pw, pd = patio
    blocked = {(int(px / C) + i, int(py / C) + j)
               for i in range(int(pw / C)) for j in range(int(pd / C))}
    free_cells = NW * NH - len(blocked)
    cor_area = cor_dims[0] * cor_dims[1]
    rest = free_cells - sum(RC) - cor_area
    if rest < 0 or n_filler < 1 or rest % n_filler:
        return None, {"err": "aire", "rest": rest}
    fillers = [rest // n_filler] * n_filler
    items = []                                   # (nom, cellules, dims autorisees|None)
    for i, r in enumerate(ROOMS):
        items.append((r[0], RC[i], r[2]))
    items.append(("COULOIR", cor_area, [cor_dims]))
    for i in range(n_filler):
        items.append(("CLOISONS %d" % (i + 1), fillers[i], None))
    if sum(it[1] for it in items) != free_cells:
        return None, {"err": "somme", "sum": sum(it[1] for it in items), "free": free_cells}
    grid = [[1 if (x, y) in blocked else 0 for x in range(NW)] for y in range(NH)]
    used = [False] * len(items)
    cur = [None] * len(items)
    res, nodes = [None], [0]

    def ff():
        for y in range(NH):
            row = grid[y]
            for x in range(NW):
                if row[x] == 0:
                    return x, y
        return None

    def dims_for(idx_i, x0, y0):
        a = items[idx_i][1]
        allowed = items[idx_i][2]
        out = allowed if allowed else [(w, a // w) for w in range(1, NW - x0 + 1) if a % w == 0]
        return [(w, h) for (w, h) in out
                if w >= 1 and h >= 1 and x0 + w <= NW and y0 + h <= NH]

    def rec(placed):
        nodes[0] += 1
        if res[0] or nodes[0] > max_nodes:
            return
        p = ff()
        if p is None:
            res[0] = list(cur)
            return
        x0, y0 = p
        order = sorted([i for i in range(len(items)) if not used[i]],
                       key=lambda i: -items[i][1])
        for i in order:
            for (w, h) in dims_for(i, x0, y0):
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
                used[i] = True
                cur[i] = (x0, y0, w, h)
                rec(placed + 1)
                used[i] = False
                cur[i] = None
                for yy in range(y0, y0 + h):
                    for xx in range(x0, x0 + w):
                        grid[yy][xx] = 0
                if res[0]:
                    return

    rec(0)
    if not res[0]:
        return None, {"nodes": nodes[0], "free": free_cells}
    ci = [i for i, it in enumerate(items) if it[0] == "COULOIR"][0]
    rects = [(c[0] * C, c[1] * C, c[2] * C, c[3] * C) for c in res[0]]
    cor = {(int(round(rects[ci][0] / C)) + a, int(round(rects[ci][1] / C)) + b)
           for a in range(int(round(rects[ci][2] / C)))
           for b in range(int(round(rects[ci][3] / C)))}
    adj = []
    for i, r in enumerate(rects):
        if i == ci:
            adj.append(True)
            continue
        rm = {(int(round(r[0] / C)) + a, int(round(r[1] / C)) + b)
              for a in range(int(round(r[2] / C))) for b in range(int(round(r[3] / C)))}
        adj.append(any((q[0] + dx, q[1] + dy) in cor for q in rm
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    return {"rects": rects, "names": [it[0] for it in items], "circ_idx": ci,
            "rooms_ok": all(adj[:len(ROOMS)]), "adj": adj}, {"nodes": nodes[0]}


PATIOS = [("NE x[7;10] y[6,5;10,5]", (7.0, 6.5, 3.0, 4.0)),
          ("SE x[7;10] y[0;4]", (7.0, 0.0, 3.0, 4.0)),
          ("NO x[0;3] y[6,5;10,5]", (0.0, 6.5, 3.0, 4.0)),
          ("SO x[0;3] y[0;4]", (0.0, 0.0, 3.0, 4.0))]
CORS = [(6, 36), (6, 40), (6, 32), (5, 40), (8, 24), (8, 30), (10, 20), (12, 16),
        (36, 6), (32, 6), (30, 8), (24, 8), (16, 12), (20, 10)]

found = None
tested = 0
for pname, patio in PATIOS:
    for cd in CORS:
        for nf in (1, 2, 3, 4):
            tested += 1
            r, info = solve(patio, cd, nf)
            if r and r["rooms_ok"]:
                found = (pname, cd, nf, r, info)
                break
        if found:
            break
    if found:
        break

print("combinaisons testees :", tested)
if found:
    pname, cd, nf, r, info = found
    print(">>> SOLUTION ETAGE")
    print("  patio    :", pname)
    print("  couloir  : %.2f x %.2f m" % (cd[0] * C, cd[1] * C))
    print("  cloisons : %d rect." % nf, "| noeuds :", info["nodes"])
    for i, rr in enumerate(r["rects"]):
        print("    %-18s %5.2f m2  %.2f x %.2f m @ (%.2f, %.2f)"
              % (r["names"][i], rr[2] * rr[3], rr[2], rr[3], rr[0], rr[1]))
    json.dump({"patio": pname, "patio_rect": dict(PATIOS)[pname], "circ_idx": r["circ_idx"],
               "names": r["names"], "rects": [[x[0], x[1], x[2], x[3]] for x in r["rects"]],
               "adj": r["adj"]},
              open(AGENT + "/_build/_etg_v3.json", "w"), indent=1)
    print("  -> _build/_etg_v3.json")
else:
    print("AUCUNE solution (solveur complet)")
