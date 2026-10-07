#!/usr/bin/env python3
"""Test : l'enveloppe 10,9 x 10,4 (interieur 10,5 x 10,0 = 105 m2) permet-elle
   un pavage AVEC circulation continue >= 1,2 m touchant toutes les pieces ?"""
import json

RECESS = (6.0, 5.0, 3.0, 4.0)
RDC = [("Salon", 32, 4.0), ("Salle a manger", 18, 3.5), ("Cuisine", 12, 2.5),
       ("Bureau", 10, 2.5), ("Buanderie", 6, 2.0), ("WC visiteur", 3, 1.5)]
ETG = [("Suite parentale", 16, 3.5), ("Chambre 2", 13, 2.0), ("Chambre 3", 13, 2.0),
       ("Chambre 4", 12, 3.0), ("SdB 1", 5, 2.0), ("SdB 2", 5, 2.0), ("SdB 3", 5, 2.0)]


def test(label, NW, NH, rooms, blocked_m=None, max_nodes=3000000, max_sols=200):
    blocked_m = blocked_m or []
    blocked = set()
    for (bx, by, bw, bh) in blocked_m:
        for i in range(int(bw * 2)):
            for j in range(int(bh * 2)):
                blocked.add((int(bx * 2) + i, int(by * 2) + j))
    areas = [int(round(a * 4)) for _, a, _ in rooms]
    mins = [int(round(m * 2)) for _, _, m in rooms]
    free = NW * NH - len(blocked)
    budget = free - sum(areas)
    if budget < 0:
        return False, {"err": "surface insuffisante"}
    grid = [[1 if (x, y) in blocked else 0 for x in range(NW)] for y in range(NH)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best = [None]
    bs = [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(NH):
            r = grid[y]
            for x in range(NW):
                if r[x] == 0:
                    return x, y
        return None

    def cells(x, y, w, h):
        return {(x + i, y + j) for i in range(w) for j in range(h)}

    def corridor_ok(rects):
        occ = set()
        for r in rects:
            occ |= cells(*r)
        fr = {(x, y) for y in range(NH) for x in range(NW)
              if (x, y) not in occ and (x, y) not in blocked}
        comps, seen = [], set()
        for c in fr:
            if c in seen:
                continue
            st, comp = [c], set()
            seen.add(c)
            while st:
                p = st.pop()
                comp.add(p)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (p[0] + dx, p[1] + dy)
                    if q in fr and q not in seen:
                        seen.add(q)
                        st.append(q)
            comps.append(comp)
        comps.sort(key=len, reverse=True)
        main = comps[0]
        er = {p for p in main if all((p[0] + dx, p[1] + dy) in main
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        adj = [any((q[0] + dx, q[1] + dy) in main for q in cells(*r)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for r in rects]
        return all(adj) and len(er) > 0, {"libres": len(fr), "principale": len(main),
                                          "erodee": len(er), "touche_toutes": all(adj),
                                          "detail": adj}

    def rec(k, wasted):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols or best[0]:
            return
        if k == len(areas):
            if wasted == budget:
                sols[0] += 1
                ok, info = corridor_ok(cur)
                if ok:
                    best[0] = (list(cur), info)
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
    return (best[0] is not None), {"sols": sols[0], "nodes": nodes[0],
                                   "info": best[0][1] if best[0] else None,
                                   "rects": best[0][0] if best[0] else None}


CASES = [
    ("RDC  10,40x10,40 (int 10,0x10,0)", 20, 20, RDC, None),
    ("RDC  10,40x10,90 (int 10,0x10,5)", 20, 21, RDC, None),
    ("RDC  10,90x10,40 (int 10,5x10,0)", 21, 20, RDC, None),
    ("RDC  10,90x10,90 (int 10,5x10,5)", 21, 21, RDC, None),
    ("ETG  10,90x10,40 (int 10,5x10,0)", 21, 20, ETG, [RECESS]),
    ("ETG  10,90x10,90 (int 10,5x10,5)", 21, 21, ETG, [RECESS]),
    ("ETG  11,40x10,90 (int 11,0x10,5)", 22, 21, ETG, [RECESS]),
]
print("%-36s %s" % ("CAS", "RESULTAT"))
for label, nw, nh, rooms, blk in CASES:
    ok, info = test(label, nw, nh, rooms, blk)
    print("%-36s %s" % (label, "FAISABLE" if ok else "IMPOSSIBLE"))
    print("      %s" % json.dumps({k: v for k, v in info.items() if k != "rects"}))
    if ok:
        for i, r in enumerate(info["rects"]):
            print("        %-16s %.1f x %.1f m @ (%.1f, %.1f)"
                  % (rooms[i][0], r[2] / 2.0, r[3] / 2.0, r[0] / 2.0, r[1] / 2.0))
