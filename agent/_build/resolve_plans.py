#!/usr/bin/env python3
"""Resolution de la repartition — couloir scinde, plusieurs decoupes testees."""
import os, sys, json, itertools

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))

N = 20
CELL = 0.5

RDC_ROOMS = [("P01", "Salon", 32, 4.0), ("P02", "Salle a manger", 18, 3.5),
             ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
             ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]
ETG_ROOMS = [("P07", "Suite parentale", 16, 3.5), ("P08", "Chambre 2", 13, 2.0),
             ("P09", "Chambre 3", 13, 2.0), ("P10", "Chambre 4", 12, 3.0),
             ("P11", "Salle de bain 1", 5, 2.0), ("P12", "Salle de bain 2", 5, 2.0),
             ("P13", "Salle de bain 3", 5, 2.0)]
RECESS = (6.0, 5.0, 3.0, 4.0)

# decoupes du couloir (somme = 19 m2, chaque segment >= 1,2 m de large)
SPLITS = [
    [(2.0, 6.0), (2.0, 3.5)], [(2.0, 5.0), (2.0, 4.5)],
    [(2.5, 4.0), (2.0, 4.5)], [(3.0, 4.0), (2.0, 3.5)],
    [(2.5, 6.0), (2.0, 2.0)], [(2.0, 8.0), (2.0, 1.5)],
    [(2.5, 3.0), (2.5, 3.0), (2.0, 2.0)],
    [(2.0, 4.0), (2.0, 3.0), (2.0, 2.5)],
]


def cellsof(x, y, w, h):
    return {(int(round((x + i * CELL) * 2)), int(round((y + j * CELL) * 2)))
            for i in range(int(round(w / CELL))) for j in range(int(round(h / CELL)))}


def solve_exact(areas_m2, mins_m, blocked, max_nodes=6000000, max_sols=150):
    bl = blocked
    free = N * N - len(bl)
    areas = [int(round(a * 4)) for a in areas_m2]
    mins = [int(round(m * 2)) for m in mins_m]
    if sum(areas) != free:
        return None, 0
    grid = [[1 if (x, y) in bl else 0 for x in range(N)] for y in range(N)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(N):
            r = grid[y]
            for x in range(N):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            v = sum(max(w, h) / float(min(w, h)) for (_, _, w, h) in cur)
            if v < bs[0]:
                bs[0] = v
                best[0] = list(cur)
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
            rec(k + 1)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0

    rec(0)
    if best[0] is None:
        return None, sols[0]
    return [(x / 2.0, y / 2.0, w / 2.0, h / 2.0) for (x, y, w, h) in best[0]], sols[0]


def adjacent(r1, r2):
    x1, y1, w1, h1 = r1[:4]
    x2, y2, w2, h2 = r2[:4]
    v = (abs((y1 + h1) - y2) < 1e-9 or abs((y2 + h2) - y1) < 1e-9) and \
        (min(x1 + w1, x2 + w2) - max(x1, x2) > 1e-9)
    hz = (abs((x1 + w1) - x2) < 1e-9 or abs((x2 + w2) - x1) < 1e-9) and \
         (min(y1 + h1, y2 + h2) - max(y1, y2) > 1e-9)
    return v or hz


def connected(rects_circ):
    """Les segments de couloir forment-ils UN reseau connexe ?"""
    if len(rects_circ) == 1:
        return True
    seen = {0}
    stack = [0]
    while stack:
        i = stack.pop()
        for j in range(len(rects_circ)):
            if j not in seen and adjacent(rects_circ[i], rects_circ[j]):
                seen.add(j)
                stack.append(j)
    return len(seen) == len(rects_circ)


def try_floor(rooms, split, blocked_m):
    entries = [(c, n, a, m, "piece") for c, n, a, m in rooms]
    entries += [("C%02d" % (i + 1), "Circulation %d" % (i + 1), round(w * d, 2),
                 min(w, d), "circulation") for i, (w, d) in enumerate(split)]
    areas = [e[2] for e in entries]
    mins = [e[3] for e in entries]
    bl = set()
    for (bx, by, bw, bh) in blocked_m:
        bl |= cellsof(bx, by, bw, bh)
    lay, sols = solve_exact(areas, mins, bl)
    if not lay:
        return None, sols
    rects = [(lay[i][0], lay[i][1], lay[i][2], lay[i][3], entries[i][2],
              entries[i][4], entries[i][1]) for i in range(len(entries))]
    circ = [r for r in rects if r[5] == "circulation"]
    if not connected(circ):
        return None, sols
    okadj = all(r[5] == "circulation" or any(adjacent(c, r) for c in circ) for r in rects)
    if not okadj:
        return None, sols
    return rects, sols


def run(label, rooms, blocked_m):
    for si, split in enumerate(SPLITS):
        rects, sols = try_floor(rooms, split, blocked_m)
        if rects:
            print("%-6s -> decoupe couloir n°%d %s (sols=%d)" % (label, si + 1, split, sols))
            return rects, split
        print("%-6s -> decoupe n°%d %s : ECHEC (sols=%d)" % (label, si + 1, split, sols))
    return None, None


rdc, rdc_split = run("RDC", RDC_ROOMS, [])
etg, etg_split = run("ETAGE", ETG_ROOMS, [RECESS])

if rdc and etg:
    json.dump({"rdc": [[r[0], r[1], r[2], r[3], r[4], r[5], r[6]] for r in rdc],
               "etg": [[r[0], r[1], r[2], r[3], r[4], r[5], r[6]] for r in etg],
               "rdc_split": rdc_split, "etg_split": etg_split},
              open(AGENT + "/_build/_plans_solved.json", "w"), indent=1)
    print("\n--- RDC ---")
    for r in rdc:
        print("  %-16s %5.2f m2  %.1f x %.1f m @ (%.1f, %.1f) %s"
              % (r[6], r[4], r[2], r[3], r[0], r[1], r[5]))
    print("--- ETAGE ---")
    for r in etg:
        print("  %-16s %5.2f m2  %.1f x %.1f m @ (%.1f, %.1f) %s"
              % (r[6], r[4], r[2], r[3], r[0], r[1], r[5]))
    print("\n-> _plans_solved.json ecrit")
else:
    print("\nECHEC : rdc=%s etg=%s" % (bool(rdc), bool(etg)))
    sys.exit(1)
