#!/usr/bin/env python3
"""Localise le goulot de largeur minimale sur le parcours depuis la porte (v2)."""
import bpy, os, json, math, heapq, hashlib, sys

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = sys.argv[-1] if sys.argv[-1].endswith(".blend") else os.path.join(
    PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
RES, Z_PROBE = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90   # ENVELOPPE COMPLETE (murs inclus)

bpy.ops.wm.open_mainfile(filepath=BIM)


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


mesh = [o for o in bpy.data.objects if o.type == "MESH"]
print("fichier : %s (%d objets, sha %s)" % (os.path.basename(BIM), len(mesh),
                                            hashlib.sha256(open(BIM, "rb").read()).hexdigest()[:24]))
NX = int(round((IX1 - IX0) / RES))
NY = int(round((IY1 - IY0) / RES))
occ = [[False] * NY for _ in range(NX)]
proprietaire = [[None] * NY for _ in range(NX)]
for o in mesh:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    est_esc = o.name.startswith(("MARCHE", "PALIER"))
    if not est_esc and not (z0 - 1e-6 <= Z_PROBE <= z1 + 1e-6):
        continue
    if o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
        continue
    i0 = max(0, int(math.ceil((x0 - IX0) / RES - 0.5)))
    i1 = min(NX, int(math.floor((x1 - IX0) / RES - 0.5)) + 1)
    j0 = max(0, int(math.ceil((y0 - IY0) / RES - 0.5)))
    j1 = min(NY, int(math.floor((y1 - IY0) / RES - 0.5)) + 1)
    for i in range(i0, i1):
        for j in range(j0, j1):
            occ[i][j] = True
            proprietaire[i][j] = o.name

INF = 1e9
D = [[0.0 if occ[i][j] else INF for j in range(NY)] for i in range(NX)]
for i in range(NX):
    for j in range(NY):
        if D[i][j] == 0:
            continue
        v = D[i][j]
        if i > 0: v = min(v, D[i - 1][j] + 1)
        if j > 0: v = min(v, D[i][j - 1] + 1)
        if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + 1.414)
        if i > 0 and j + 1 < NY: v = min(v, D[i - 1][j + 1] + 1.414)
        D[i][j] = v
for i in range(NX - 1, -1, -1):
    for j in range(NY - 1, -1, -1):
        if D[i][j] == 0:
            continue
        v = D[i][j]
        if i + 1 < NX: v = min(v, D[i + 1][j] + 1)
        if j + 1 < NY: v = min(v, D[i][j + 1] + 1)
        if i + 1 < NX and j + 1 < NY: v = min(v, D[i + 1][j + 1] + 1.414)
        if i + 1 < NX and j > 0: v = min(v, D[i + 1][j - 1] + 1.414)
        D[i][j] = v


def c(x, y):
    return (max(0, min(NX - 1, int((x - IX0) / RES))), max(0, min(NY - 1, int((y - IY0) / RES))))


start = c(10.10, 5.50)
best = [[-1.0] * NY for _ in range(NX)]
pq = [(-(D[start[0]][start[1]] * RES * 2), start[0], start[1])]
best[start[0]][start[1]] = D[start[0]][start[1]] * RES * 2
while pq:
    nw, i, j = heapq.heappop(pq)
    w = -nw
    if w < best[i][j] - 1e-9:
        continue
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ni, nj = i + di, j + dj
        if 0 <= ni < NX and 0 <= nj < NY and not occ[ni][nj]:
            v = min(w, D[ni][nj] * RES * 2)
            if v > best[ni][nj] + 1e-9:
                best[ni][nj] = v
                heapq.heappush(pq, (-v, ni, nj))

reach = [(best[i][j], i, j) for i in range(NX) for j in range(NY) if best[i][j] > 0]
reach.sort()
print("\n--- 12 cellules les plus etroites atteignables depuis la porte ---")
vus = []
for w, i, j in reach[:4000]:
    x, y = IX0 + i * RES, IY0 + j * RES
    if any(abs(x - a) < 0.30 and abs(y - b) < 0.30 for a, b in vus):
        continue
    vus.append((x, y))
    voisins = set()
    for di in range(-2, 3):
        for dj in range(-2, 3):
            ii, jj = i + di, j + dj
            if 0 <= ii < NX and 0 <= jj < NY and proprietaire[ii][jj]:
                voisins.add(proprietaire[ii][jj])
    print("  largeur %.2f m  a x=%5.2f y=%5.2f   obstacles : %s"
          % (w, x, y, ", ".join(sorted(voisins)[:4])))
    if len(vus) >= 12:
        break

largeurs = sorted(set(round(w, 2) for w, _, _ in reach))
print("\nlargeurs distinctes les plus faibles : %s" % largeurs[:8])
n10 = sum(1 for w, _, _ in reach if w < 0.35)
print("cellules atteignables de largeur < 0,35 m : %d (%.3f m2 sur %.2f m2)"
      % (n10, n10 * RES * RES, len(reach) * RES * RES))
out = {"fichier": os.path.basename(BIM), "sha256": hashlib.sha256(open(BIM, "rb").read()).hexdigest(),
       "largeur_min_m": round(min(w for w, _, _ in reach), 3),
       "cellules_sous_035m": n10, "cellules_atteignables": len(reach)}
json.dump(out, open(os.path.join(PROJ, "reports", "goulot_circulation_v2.json"), "w"), indent=2)
print("-> reports/goulot_circulation_v2.json")
