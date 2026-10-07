#!/usr/bin/env python3
"""ETAGE grille 0,25 m — couloir en L/T = 2 rectangles (forme et position libres)."""
import os, json, time

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
RC = [int(round(r[1] / (C * C))) for r in ROOMS]
PATIO = (7.0, 6.5, 3.0, 4.0)
BLOCKED = {(int(PATIO[0] / C) + i, int(PATIO[1] / C) + j)
           for i in range(int(PATIO[2] / C)) for j in range(int(PATIO[3] / C))}
FREE = NW * NH - len(BLOCKED)
NONROOM = FREE - sum(RC)


def cset(r):
    return {(int(round(r[0] / C)) + a, int(round(r[1] / C)) + b)
            for a in range(int(round(r[2] / C))) for b in range(int(round(r[3] / C)))}


def solve(cor_parts, fil_parts, max_nodes, deadline):
    areas = list(cor_parts) + list(fil_parts)
    if any(a <= 0 for a in areas) or sum(areas) != NONROOM:
        return None, {"err": "aire"}
    items = [(r[0], RC[i], r[2]) for i, r in enumerate(ROOMS)]
    ncor = len(cor_parts)
    for i in range(ncor):
        items.append(("COULOIR", cor_parts[i], None))
    for i in range(len(fil_parts)):
        items.append(("CLOISONS", fil_parts[i], None))
    grid = [[1 if (x, y) in BLOCKED else 0 for x in range(NW)] for y in range(NH)]
    used = [False] * len(items)
    cur = [None] * len(items)
    res, nodes = [None], [0]
    circ_idx = list(range(len(ROOMS), len(ROOMS) + ncor))

    def ff():
        for y in range(NH):
            row = grid[y]
            for x in range(NW):
                if row[x] == 0:
                    return x, y
        return None

    def criteria_ok(cur_rects):
        rects_ = [(c[0] * C, c[1] * C, c[2] * C, c[3] * C) for c in cur_rects]
        parts = [cset(rects_[i]) for i in circ_idx]
        allp = set().union(*parts)
        conn = len(parts) == 1
        if not conn:
            start = next(iter(parts[0]))
            seen, st = {start}, [start]
            while st:
                q = st.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (q[0] + dx, q[1] + dy)
                    if n in allp and n not in seen:
                        seen.add(n)
                        st.append(n)
            conn = len(seen) == len(allp)
        if not conn:
            return False, None, None
        cor = allp
        adj = []
        for i, r in enumerate(rects_):
            rm = cset(r)
            adj.append(i in circ_idx or
                       any((q[0] + dx, q[1] + dy) in cor for q in rm
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
        return all(adj[:len(ROOMS)]), adj, rects_

    def rec():
        nodes[0] += 1
        if res[0] or nodes[0] > max_nodes or (nodes[0] % 8192 == 0 and time.time() > deadline):
            return
        p = ff()
        if p is None:
            ok, adj, rr = criteria_ok(cur)          # <-- criteres AU MOMENT du pavage
            if ok:
                res[0] = (rr, adj)
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
                if allowed is None:
                    mn = 5 if items[i][0] == "COULOIR" else 1
                    if min(w, h) < mn:
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
    rects, adj = res[0]
    return ({"rects": rects, "names": [it[0] for it in items], "circ_idx": circ_idx,
             "adj": adj, "rooms_ok": True, "couloir_connexe": True,
             "nodes": nodes[0]}, {"nodes": nodes[0]})


t0 = time.time()
deadline = t0 + 420
found = None
for ct in (240, 256, 224, 272, 288):
    for split in (2, 3):
        base = ct // split
        cor_parts = [base] * (split - 1) + [ct - base * (split - 1)]
        for fil in (1, 2):
            if (NONROOM - ct) % fil:
                continue
            fp = [(NONROOM - ct) // fil] * fil
            r, info = solve(cor_parts, fp, 500000, deadline)
            tag = "OK" if r else "echec"
            print("  couloir %d m2/%d morceaux + cloisons %d -> %s %s"
                  % (ct, split, fil, tag, json.dumps(info)[:60]), flush=True)
            if r and r["rooms_ok"] and r["couloir_connexe"]:
                found = (ct, split, fil, r)
                break
            if time.time() > deadline:
                break
        if found or time.time() > deadline:
            break
    if found or time.time() > deadline:
        break

print("\nduree %.1f s" % (time.time() - t0))
if found:
    ct, split, fil, r = found
    print(">>> SOLUTION ETAGE — couloir %d m2 en %d morceaux" % (ct, split))
    for i, rr in enumerate(r["rects"]):
        print("    %-18s %5.2f m2  %.2f x %.2f m @ (%.2f, %.2f)  acces=%s"
              % (r["names"][i], rr[2] * rr[3], rr[2], rr[3], rr[0], rr[1], r["adj"][i]))
    json.dump({"patio_rect": PATIO, "circ_idx": r["circ_idx"], "names": r["names"],
               "rects": [[x[0], x[1], x[2], x[3]] for x in r["rects"]], "adj": r["adj"]},
              open(AGENT + "/_build/_etg_v5.json", "w"), indent=1)
    print("-> _build/_etg_v5.json")
else:
    print("AUCUNE solution")
