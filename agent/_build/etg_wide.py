#!/usr/bin/env python3
"""ETAGE grille 0,25 m — recherche large : patio 4 coins x couloirs x cloisons libres."""
import os, json, itertools

AGENT = "/Users/mac/ConstructionAgent"
C = 0.25
NW, NH = 40, 42
ROOMS = [("Suite parentale", 16.0, [(16, 16)]),
         ("Chambre 2", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 3", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 4", 12.0, [(12, 16), (16, 12)]),
         ("Salle de bain 1", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 2", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 3", 5.0, [(8, 10), (10, 8)])]
AREAS = [int(round(r[1] / (C * C))) for r in ROOMS]
FREE = NW * NH - 192


def analyse(rects, ci):
    occ = set()
    for r in rects:
        for i in range(int(round(r[2] / C))):
            for j in range(int(round(r[3] / C))):
                occ.add((int(round(r[0] / C)) + i, int(round(r[1] / C)) + j))
    cor = {(int(round(rects[ci][0] / C)) + i, int(round(rects[ci][1] / C)) + j)
           for i in range(int(round(rects[ci][2] / C)))
           for j in range(int(round(rects[ci][3] / C)))}
    adj = []
    for i, r in enumerate(rects):
        if i == ci:
            adj.append(True)
            continue
        rm = {(int(round(r[0] / C)) + a, int(round(r[1] / C)) + b)
              for a in range(int(round(r[2] / C))) for b in range(int(round(r[3] / C)))}
        adj.append(any((q[0] + dx, q[1] + dy) in cor for q in rm
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    return adj


def try_layout(patio, cor_dims, filler_parts, blocked, max_nodes=2000000):
    entries = [(r[0], r[1], r[2]) for r in ROOMS]
    cor_cells = cor_dims[0] * cor_dims[1] * C * C
    entries.append(("COULOIR", cor_cells, [cor_dims]))
    filler_cells = FREE - sum(AREAS) - cor_dims[0] * cor_dims[1]
    if filler_cells <= 0:
        return None, "filler negatif"
    if filler_cells % filler_parts:
        return None, "filler non divisible"
    each = filler_cells // filler_parts
    for _ in range(filler_parts):
        entries.append(("CLOISONS", each * C * C, None))
    grid = [[1 if (x, y) in blocked else 0 for x in range(NW)] for y in range(NH)]
    csel = [int(round(e[1] / (C * C))) for e in entries]
    idx = sorted(range(len(csel)), key=lambda i: -csel[i])
    cur = [None] * len(csel)
    res, nodes = [None], [0]

    def ff():
        for y in range(NH):
            row = grid[y]
            for x in range(NW):
                if row[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if res[0] or nodes[0] > max_nodes:
            return
        if k == len(idx):
            rects = [(c[0] * C, c[1] * C, c[2] * C, c[3] * C) for c in cur]
            ci = [i for i, e in enumerate(entries) if e[0] == "COULOIR"][0]
            a = analyse(rects, ci)
            if all(a):
                res[0] = (rects, ci, a)
            return
        p = ff()
        if p is None:
            return
        x0, y0 = p
        i = idx[k]
        a = csel[i]
        allowed = entries[i][2]
        cands = allowed if allowed else [(w, a // w) for w in range(1, NW - x0 + 1) if a % w == 0]
        for (w, h) in cands:
            if x0 + w > NW or y0 + h > NH:
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
    return (res[0][0], res[0][1]) if res[0] else None, {"nodes": nodes[0]}


PATIOS = {"NE x[7;10] y[6,5;10,5]": (7.0, 6.5, 3.0, 4.0),
          "SE x[7;10] y[0;4]": (7.0, 0.0, 3.0, 4.0),
          "NO x[0;3] y[6,5;10,5]": (0.0, 6.5, 3.0, 4.0),
          "SO x[0;3] y[0;4]": (0.0, 0.0, 3.0, 4.0)}
CORS = [(5, 40), (5, 39), (6, 36), (6, 40), (6, 32), (8, 24), (8, 30), (10, 20), (12, 16),
        (40, 5), (39, 5), (36, 6), (32, 6), (24, 8), (30, 8), (20, 10), (16, 12)]

found = None
tried = 0
for pname, (px, py, pw, pd) in PATIOS.items():
    blocked = {(int(px / C) + i, int(py / C) + j)
               for i in range(int(pw / C)) for j in range(int(pd / C))}
    if len(blocked) != 192:
        continue
    for cd in CORS:
        fcell = FREE - sum(AREAS) - cd[0] * cd[1]
        if fcell <= 0:
            continue
        for parts in (1, 2, 3, 4):
            if fcell % parts:
                continue
            each = fcell // parts
            ok_dims = any(each % w == 0 and each // w <= NH and w <= NW
                          for w in range(1, NW + 1))
            if not ok_dims:
                continue
            tried += 1
            r, info = try_layout(pname, cd, parts, blocked)
            if r:
                found = (pname, cd, parts, r[0], r[1], info)
                break
        if found:
            break
    if found:
        break

print("combinaisons testees :", tried)
if found:
    pname, cd, parts, rects, ci, info = found
    print("SOLUTION TROUVEE")
    print("  patio      :", pname)
    print("  couloir    : %d x %d cellules = %.2f x %.2f m" % (cd[0], cd[1], cd[0] * C, cd[1] * C))
    print("  cloisons   : %d rectangle(s)" % parts)
    print("  noeuds     :", info["nodes"])
    names = [r[0] for r in ROOMS] + ["COULOIR"] + ["CLOISONS"] * parts
    for i, r in enumerate(rects):
        print("    %-18s %5.2f m2  %.2f x %.2f m @ (%.2f, %.2f)"
              % (names[i], r[2] * r[3], r[2], r[3], r[0], r[1]))
    json.dump({"patio": pname, "patio_rect": PATIOS[pname], "couloir_rect": rects[ci],
               "circ_idx": ci, "names": names,
               "rects": [[r[0], r[1], r[2], r[3]] for r in rects]},
              open(AGENT + "/_build/_etg_v2.json", "w"), indent=1)
    print("  -> _build/_etg_v2.json")
else:
    print("AUCUNE solution")
