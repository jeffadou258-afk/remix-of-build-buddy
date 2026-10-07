#!/usr/bin/env python3
"""Balayage de faisabilite : a partir de quelle largeur minimale un pavage exact existe-t-il ?
32 m2 oblige un rectangle 4 x 8 m, ce qui laisse une bande de 1 m."""
import itertools

U, NU = 2, 18


def solve(areas_m2, mins_m, blocked_m=None, max_nodes=400000, max_sols=60):
    bl = set()
    for (bx, by, bw, bh) in (blocked_m or []):
        for cy in range(int(by * U), int((by + bh) * U)):
            for cx in range(int(bx * U), int((bx + bw) * U)):
                bl.add((cx, cy))
    grid = [[1 if (x, y) in bl else 0 for x in range(NU)] for y in range(NU)]
    if sum(int(round(a * 4)) for a in areas_m2) != sum(r.count(0) for r in grid):
        return None, 0
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * U)) for m in mins_m]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(NU):
            r = grid[y]
            for x in range(NU):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            sc = sum(max(w, h) / float(min(w, h)) for (_, _, w, h) in cur)
            if sc < bs[0]:
                bs[0] = sc
                best[0] = list(cur)
            return
        p = ff()
        if p is None:
            return
        x0, y0 = p
        i = idx[k]
        a, mn = areas[i], mins[i]
        for w in range(1, NU - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > NU or min(w, h) < mn:
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
            cur[i] = (x0, y0, w, h)
            rec(k + 1)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0

    rec(0)
    if best[0] is None:
        return None, sols[0]
    res = [None] * len(areas)
    for i, (x, y, w, h) in enumerate(best[0]):
        res[i] = (x / 2, y / 2, w / 2, h / 2, w * h / 4.0)
    return res, sols[0]


RDC = [("Salon", 32), ("Salle a manger", 18), ("Cuisine", 12),
       ("Bureau", 10), ("Buanderie", 6), ("WC", 3)]
ETG = [("Suite parentale", 16), ("Chambre 2", 13), ("Chambre 3", 13), ("Chambre 4", 12),
       ("SdB 1", 5), ("SdB 2", 5), ("SdB 3", 5)]
RECESS = [(6.0, 5.0, 3.0, 4.0)]

print("=" * 74)
print("BALAYAGE RDC — enveloppe 9 x 9 = 81 m2, 6 pieces")
print("=" * 74)
for t in [3.0, 2.5, 2.2, 2.0, 1.8, 1.5, 1.2, 1.0]:
    r, s = solve([a for _, a in RDC], [t] * 6)
    if r:
        dims = " | ".join("%s %.1fx%.1f" % (n, x[2], x[3]) for (n, _), x in zip(RDC, r))
        print("  min %4.1f m : FAISABLE   (%d sol.)  %s" % (t, s, dims))
        break
    else:
        print("  min %4.1f m : INFAISABLE" % t)

print()
print("=" * 74)
print("BALAYAGE ETAGE — 9 x 9 moins patio d'angle 3 x 4 = 69 m2, 7 pieces")
print("=" * 74)
for t in [3.0, 2.5, 2.2, 2.0, 1.8, 1.5, 1.2, 1.0]:
    r, s = solve([a for _, a in ETG], [t] * 7, blocked_m=RECESS)
    if r:
        dims = " | ".join("%s %.1fx%.1f" % (n, x[2], x[3]) for (n, _), x in zip(ETG, r))
        print("  min %4.1f m : FAISABLE   (%d sol.)  %s" % (t, s, dims))
        break
    else:
        print("  min %4.1f m : INFAISABLE" % t)

print()
print("=" * 74)
print("POURQUOI : les seules factorisations possibles dans une grille 9x9 (cotes <= 9 m)")
print("=" * 74)
for n, a in RDC:
    f = []
    for w in range(1, 19):
        if a * 4 % w == 0:
            h = a * 4 // w
            if 1 <= h <= 18:
                f.append((w / 2.0, h / 2.0))
    f = sorted(set(f), key=lambda t: -min(t))
    print("  %-16s %2d m2 : %s" % (n, a, "  ".join("%.1f x %.1f" % t for t in f[:4])))
print()
print("  -> 32 m2 n'a QUE 4.0 x 8.0 ou 8.0 x 4.0 : laisse forcement une bande de 1 m")
print("  -> aucune piece du programme ne mesure 1 m de large (mini realiste 1.5 m)")
print("  -> donc : un pavage rectangulaire EXACT de 81 m2 en 9x9 est IMPOSSIBLE")
print("     avec des pieces toutes habitables.")
