#!/usr/bin/env python3
"""ETAGE — grille 0,25 m, couloir EXPLICITE (pavage exact), 13 m2 = 3,25 x 4,00 m."""
import os, sys, json

AGENT = "/Users/mac/ConstructionAgent"
C = 0.25
NW, NH = 40, 42                        # 10,00 x 10,50 m
PATIO = (7.0, 6.5, 3.0, 4.0)           # x, y, w, d  (12 m2, coin)
DEF = [("P07", "Suite parentale", 16.0, 3.0, [(16, 16)]),
       ("P08", "Chambre 2", 13.0, 2.5, [(13, 16), (16, 13)]),
       ("P09", "Chambre 3", 13.0, 2.5, [(13, 16), (16, 13)]),
       ("P10", "Chambre 4", 12.0, 3.0, [(12, 16), (16, 12)]),
       ("P11", "Salle de bain 1", 5.0, 2.0, [(8, 10), (10, 8)]),
       ("P12", "Salle de bain 2", 5.0, 2.0, [(8, 10), (10, 8)]),
       ("P13", "Salle de bain 3", 5.0, 2.0, [(8, 10), (10, 8)])]


def bl():
    s = set()
    for i in range(int(PATIO[2] / C)):
        for j in range(int(PATIO[3] / C)):
            s.add((int(PATIO[0] / C) + i, int(PATIO[1] / C) + j))
    return s


BLOCKED = bl()
FREE = NW * NH - len(BLOCKED)


def cells(x, y, w, h):
    return {(int(round(x / C)) + i, int(round(y / C)) + j)
            for i in range(int(round(w / C))) for j in range(int(round(h / C)))}


def analyse(rects, circ_idx):
    occ = set()
    for r in rects:
        occ |= cells(*r)
    free = {(x, y) for y in range(NH) for x in range(NW)
            if (x, y) not in occ and (x, y) not in BLOCKED}
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
    circ_rect = rects[circ_idx]
    cor = cells(*circ_rect)
    adj = []
    for i, r in enumerate(rects):
        if i == circ_idx:
            adj.append(True)
            continue
        rm = cells(*r)
        touch = any((q[0] + dx, q[1] + dy) in cor for q in rm
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        adj.append(touch)
    return {"libres": len(free), "composantes": len(comps), "principale": len(main),
            "erodee": len(er), "largeur_couloir_m": round(min(circ_rect[2], circ_rect[3]), 2),
            "acces_direct_toutes": all(adj), "detail_acces": adj}


def solve_exact(entries, max_nodes=6000000, max_sols=60):
    """entries = [(nom, area_m2, dims_autorisees|None)] ; dims_autorisees en cellules."""
    cells_area = [int(round(a / (C * C))) for _, a, _ in entries]
    if sum(cells_area) != FREE:
        return None, {"err": "somme %d != libre %d" % (sum(cells_area), FREE)}
    grid = [[1 if (x, y) in BLOCKED else 0 for x in range(NW)] for y in range(NH)]
    idx = sorted(range(len(cells_area)), key=lambda i: -cells_area[i])
    cur = [None] * len(cells_area)
    best, bs = [None], [1e18]
    can = [None]
    sols, nodes = [0], [0]
    entry_by_i = entries

    def ff():
        for y in range(NH):
            r = grid[y]
            for x in range(NW):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or can[0] or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            rects = [(c[0] * C, c[1] * C, c[2] * C, c[3] * C) for c in cur]
            ci = [i for i, e in enumerate(entry_by_i) if e[0] == "COULOIR"][0]
            info = analyse(rects, ci)
            if info["acces_direct_toutes"] and info["erodee"] > 0:
                v = sum(max(r[2], r[3]) / min(r[2], r[3])
                        for i, r in enumerate(rects) if i != ci)
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
        a = cells_area[i]
        allowed = entries[i][2]
        cands = []
        if allowed:
            cands = [(w, h) for (w, h) in allowed]
        else:
            for w in range(1, NW - x0 + 1):
                if a % w == 0:
                    cands.append((w, a // w))
        for (w, h) in cands:
            if w < 1 or h < 1 or x0 + w > NW or y0 + h > NH:
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
        return None, {"sols": sols[0], "nodes": nodes[0]}
    rects = [(c[0] * C, c[1] * C, c[2] * C, c[3] * C) for c in best[0]]
    ci = [i for i, e in enumerate(entry_by_i) if e[0] == "COULOIR"][0]
    return rects, {"sols": sols[0], "nodes": nodes[0], "info": can[0], "circ_idx": ci}


COMBOS = [
    ("couloir 1,50 x 9,00 + cloisons 168", (6, 36), (12, 14)),
    ("couloir 1,50 x 8,00 + cloisons 192", (6, 32), (12, 16)),
    ("couloir 1,25 x 10,00 + cloisons 184", (5, 40), (8, 23)),
    ("couloir 1,50 x 10,00 + cloisons 144", (6, 40), (12, 12)),
    ("couloir 1,50 x 6,00 + cloisons 264", (6, 24), (12, 22)),
]
print("ETAGE — interieur 10,00 x 10,50 (grille 0,25 m) - patio 3x4 en (7,0 ; 6,5)")
print("libre : %d cellules = %.2f m2 | pieces 69 m2 = %d cellules | reste : %d cellules"
      % (FREE, FREE * C * C, sum(int(round(d[2] / (C * C))) for d in DEF),
         FREE - sum(int(round(d[2] / (C * C))) for d in DEF)))
res = None
for label, cd, fd in COMBOS:
    entries = [(d[1], d[2], d[4]) for d in DEF]
    entries.append(("COULOIR", cd[0] * cd[1] * C * C, [cd]))
    entries.append(("CLOISONS", fd[0] * fd[1] * C * C, [fd]))
    tot = sum(int(round(e[1] / (C * C))) for e in entries)
    if tot != FREE:
        print("  %-42s SKIP (somme %d != %d)" % (label, tot, FREE))
        continue
    rects, info = solve_exact(entries)
    print("  %-42s %s" % (label, ("OK" if rects else "echec") + " " +
                          json.dumps({k: v for k, v in info.items() if k != "info"})[:80]))
    if rects:
        res = (label, entries, rects, info)
        break

if res:
    label, entries, rects, info = res
    print("\nSOLUTION ETAGE :", label)
    print("  ", json.dumps(info["info"]))
    for i, e in enumerate(entries):
        r = rects[i]
        print("    %-16s %5.2f m2  %.2f x %.2f m @ (%.2f, %.2f)"
              % (e[0], r[2] * r[3], r[2], r[3], r[0], r[1]))
    json.dump({"label": label, "rects": [[r[0], r[1], r[2], r[3]] for r in rects],
               "names": [e[0] for e in entries], "areas": [e[1] for e in entries],
               "patio": PATIO, "info": info["info"], "circ_idx": info["circ_idx"]},
              open(AGENT + "/_build/_etg.json", "w"), indent=1)
    print("-> _build/_etg.json")
else:
    print("\nAUCUNE combinaison ne fonctionne")
