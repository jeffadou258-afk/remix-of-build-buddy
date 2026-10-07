#!/usr/bin/env python3
"""TEST DECISIF : region accessible depuis la porte en exigeant une clearance >= seuil.
Repond a : 'peut-on atteindre chaque piece en gardant une largeur >= 1,20 m ?'"""
import bpy, os, json, math, hashlib, sys

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = sys.argv[-1] if sys.argv[-1].endswith(".blend") else os.path.join(
    PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
RES, Z_PROBE = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90   # ENVELOPPE COMPLETE (murs inclus)
SEUIL = 1.20                                   # largeur exigee

bpy.ops.wm.open_mainfile(filepath=BIM)
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


mesh = [o for o in bpy.data.objects if o.type == "MESH"]
NX = int(round((IX1 - IX0) / RES))
NY = int(round((IY1 - IY0) / RES))
occ = [[False] * NY for _ in range(NX)]
qui = [[None] * NY for _ in range(NX)]
for o in mesh:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if not o.name.startswith(("MARCHE", "PALIER")) and not (z0 - 1e-6 <= Z_PROBE <= z1 + 1e-6):
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
            qui[i][j] = o.name

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


def cell(x, y):
    return (max(0, min(NX - 1, int((x - IX0) / RES))), max(0, min(NY - 1, int((y - IY0) / RES))))


# depart = point du passage devant la porte ayant la MEILLEURE clearance (axe median),
# et non un point colle au mur (qui donnerait une clearance quasi nulle)
PY0, PY1 = 4.90, 6.10                       # emprise reelle de la porte en Y
best_start, bd = None, -1
for i in range(NX):
    for j in range(NY):
        x, y = IX0 + i * RES, IY0 + j * RES
        if x < 8.80 or x > 10.20 or not (PY0 - 1e-9 <= y <= PY1 + 1e-9):
            continue
        if not occ[i][j] and D[i][j] > bd:
            bd = D[i][j]
            best_start = (i, j)
start = best_start
print("=" * 78)
print("TEST D'ACCESSIBILITE AVEC CLEARANCE >= %.2f m" % SEUIL)
print("fichier : %s (%d objets)" % (os.path.basename(BIM), len(mesh)))
print("porte   : depart = axe median du passage devant la porte (x=%.2f y=%.2f, clearance %.2f m)"
      % (IX0 + start[0] * RES, IY0 + start[1] * RES, D[start[0]][start[1]] * RES))
print("=" * 78)
for seuil in (1.20, 1.10, 1.00, 0.90, 0.80, 0.60, 0.40):
    r = seuil / 2.0 / RES                       # clearance en cellules
    ok = [[(not occ[i][j]) and D[i][j] >= r for j in range(NY)] for i in range(NX)]
    if not ok[start[0]][start[1]]:
        print("  seuil %.2f m : la PORTE ELLE-MEME n'est pas accessible" % seuil)
        continue
    seen = [[False] * NY for _ in range(NX)]
    st = [start]
    seen[start[0]][start[1]] = True
    while st:
        i, j = st.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < NX and 0 <= nj < NY and ok[ni][nj] and not seen[ni][nj]:
                seen[ni][nj] = True
                st.append((ni, nj))
    acc = []
    for rm in fp["RDC"]["rooms"]:
        cx = IX0 + rm["x_m"] + rm["w_m"] / 2.0
        cy = IY0 + rm["y_m"] + rm["d_m"] / 2.0
        ci, cj = cell(cx, cy)
        acc.append((rm["name"], seen[ci][cj]))
    n_ok = sum(1 for _, v in acc if v)
    print("  seuil %.2f m : %d/6 pieces accessibles  -> %s"
          % (seuil, n_ok, ", ".join("%s%s" % (n, "" if v else " (NON)") for n, v in acc)))
    if seuil == 1.20:
        json.dump({"seuil_m": seuil, "pieces": {n: bool(v) for n, v in acc},
                   "nb_accessibles": n_ok, "nb_total": len(acc),
                   "surface_accessible_m2": round(sum(1 for i in range(NX) for j in range(NY)
                                                      if seen[i][j]) * RES * RES, 2),
                   "fichier": os.path.basename(BIM),
                   "sha256": hashlib.sha256(open(BIM, "rb").read()).hexdigest()},
                  open(os.path.join(PROJ, "reports", "accessibilite_120_v2.json"), "w"), indent=2)
print("\n-> reports/accessibilite_120_v2.json")
