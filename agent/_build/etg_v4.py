#!/usr/bin/env python3
"""ETAGE grille 0,25 m — solveur COMPLET, couloir LIBRE (forme choisie par le solveur)."""
import os, json, sys, time

AGENT = "/Users/mac/ConstructionAgent"
C = 0.25
NW, NH = 40, 42                                  # interieur 10,00 x 10,50 m
ROOMS = [("Suite parentale", 16.0, [(16, 16)]),
         ("Chambre 2", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 3", 13.0, [(13, 16), (16, 13)]),
         ("Chambre 4", 12.0, [(12, 16), (16, 12)]),
         ("Salle de bain 1", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 2", 5.0, [(8, 10), (10, 8)]),
         ("Salle de bain 3", 5.0, [(8, 10), (10, 8)])]
RC = [int(round(r[1] / (C * C))) for r in ROOMS]
PATIO = (7.0, 6.5, 3.0, 4.0)                      # coin NE
blocked = {(int(PATIO[0] / C) + i, int(PATIO[1] / C) + j)
           for i in range(int(PATIO[2] / C)) for j in range(int(PATIO[3] / C))}
FREE = NW * NH - len(blocked)                     # 1488 cellules = 93,00 m2
NONROOM = FREE - sum(RC)                          # 384 cellules = 24,00 m2


def solve(cor_cells, n_filler, max_nodes, deadline):
    rest = NONROOM - cor_cells
    if rest < 0 or rest % n_filler or rest // n_filler < 1:
        return None, {"err": "aire"}
    items = [(r[0], RC[i], r[2]) for i, r in enumerate(ROOMS)]
    items.append(("COULOIR", cor_cells, None))    # forme LIBRE
    for i in range(n_filler):
        items.append(("CLOISONS %d" % (i + 1), rest // n_filler, None))
    if sum(it[1] for it in items) != FREE:
        return None, {"err": "somme"}
    grid = [[1 if (x, y) in blocked else 0 for x in range(NW)] for y in range(NH)]
    used = [False] * len(items)
    cur = [None] * len(items)
    res, nodes = [None], [0]
    MIN_COR = 5                                   # couloir >= 1,25 m

    def ff():
        for y in range(NH):
            row = grid[y]
            for x in range(NW):
                if row[x] == 0:
                    return x, y
        return None

    def rec():
        nodes[0] += 1
        if res[0] or nodes[0] > max_nodes or (nodes[0] % 4096 == 0 and time.time() > deadline):
            return
        p = ff()
        if p is None:
            res[0] = list(cur)
            return
        x0, y0 = p
        order = sorted([i for i in range(len(items)) if not used[i]],
                       key=lambda i: -items[i][1])
        for i in order:
            a = items[i][1]
            allowed = items[i][2]
            cands = allowed if allowed else [(w, a // w) for w in range(1, NW - x0 + 1)
                                             if a % w == 0]
            for (w, h) in cands:
                if x0 + w > NW or y0 + h > NH:
                    continue
                if allowed is None and min(w, h) < (MIN_COR if items[i][0] == "COULOIR" else 1):
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
                used[i] = True
                cur[i] = (x0, y0, w, h)
                rec()
                used[i] = False
                cur[i] = None
                if res[0]:
                    return
                for yy in range(y0, y0 + h):
                    for xx in range(x0, x0 + w):
                        grid[yy][xx] = 0

    rec()
    if not res[0]:
        return None, {"nodes": nodes[0]}
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
    return ({"rects": rects, "names": [it[0] for it in items], "circ_idx": ci, "adj": adj,
             "rooms_ok": all(adj[:len(ROOMS)]), "nodes": nodes[0]}, {"nodes": nodes[0]})


t0 = time.time()
deadline = t0 + 480
found = None
best = None
for cor_name, cor_cells in [("15,00", 240), ("14,00", 224), ("16,00", 256), ("13,00", 208),
                            ("12,00", 192), ("17,00", 272), ("18,00", 288)]:
    for nf in (1, 2, 3, 4):
        if (NONROOM - cor_cells) % nf:
            continue
        r, info = solve(cor_cells, nf, 400000, deadline)
        print("  couloir %s m2 x %d cloisons -> %s" % (cor_name, nf, json.dumps(info)[:70]),
              flush=True)
        if r:
            if best is None or info["nodes"] < best[2]["nodes"]:
                best = (cor_name, nf, {"nodes": r["nodes"]})
            if r["rooms_ok"]:
                found = (cor_name, nf, r)
                break
    if found or time.time() > deadline:
        break

print("\nduree : %.1f s" % (time.time() - t0))
if found:
    cor_name, nf, r = found
    print(">>> SOLUTION ETAGE (couloir %s m2, %d cloisons)" % (cor_name, nf))
    for i, rr in enumerate(r["rects"]):
        print("    %-18s %5.2f m2  %.2f x %.2f m @ (%.2f, %.2f)  acces=%s"
              % (r["names"][i], rr[2] * rr[3], rr[2], rr[3], rr[0], rr[1], r["adj"][i]))
    json.dump({"patio_rect": PATIO, "circ_idx": r["circ_idx"], "names": r["names"],
               "rects": [[x[0], x[1], x[2], x[3]] for x in r["rects"]], "adj": r["adj"]},
              open(AGENT + "/_build/_etg_v4.json", "w"), indent=1)
    print("-> _build/_etg_v4.json")
else:
    print("AUCUNE solution avec acces direct de toutes les pieces")
    print("best:", json.dumps(best))
