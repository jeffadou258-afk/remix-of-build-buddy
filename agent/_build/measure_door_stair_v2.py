#!/usr/bin/env python3
"""MESURE PHYSIQUE dans le .blend : porte d'entree <-> escalier + largeur de passage.
Methode : rasterisation du niveau de marche z=1,00 m + transformee de distance (chamfer)
          + recherche du chemin a goulot maximal (max-min Dijkstra)."""
import bpy, os, json, math, hashlib, datetime, heapq

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
OUT = os.path.join(PROJ, "reports", "porte_escalier_mesure_v2.json")
RES = 0.05
Z_PROBE = 1.00                      # niveau de marche
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90   # ENVELOPPE COMPLETE (murs inclus)

bpy.ops.wm.open_mainfile(filepath=BIM)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


mesh = [o for o in bpy.data.objects if o.type == "MESH"]
print("=" * 78)
print("MESURE PHYSIQUE — PORTE D'ENTREE / ESCALIER")
print("fichier : %s (%d o, sha %s)" % (os.path.basename(BIM), os.path.getsize(BIM),
                                       sha(BIM)[:24] + "…"))
print("nb objets : %d  |  niveau de mesure : z = %.2f m" % (len(mesh), Z_PROBE))
print("=" * 78)

# ---------- 1. PORTE D'ENTREE : trou reel dans le mur EST ----------
murs = [o for o in mesh if o.name.startswith("MUR_E_RDC")]
seg = []
for o in murs:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    seg.append((y0, y1, z0, z1, o.name))
seg.sort()
print("\n[1] MUR EST (RDC) — segments reels lus dans le .blend")
for (y0, y1, z0, z1, n) in seg:
    print("    %-22s y[%6.2f .. %6.2f]  z[%5.2f .. %5.2f]" % (n, y0, y1, z0, z1))
# le trou de porte : intervalle de y sans mur entre z=0 et z=2,10
ypass = []
for (y0, y1, z0, z1, n) in seg:
    if z0 < 2.00 and z1 > 0.10:            # segment pleine hauteur
        ypass.append((y0, y1))
ypass.sort()
gaps = []
cur = IY0
for (a, b) in ypass:
    if a - cur > 0.05:
        gaps.append((round(cur, 3), round(a, 3)))
    cur = max(cur, b)
if IY1 - cur > 0.05:
    gaps.append((round(cur, 3), round(IY1, 3)))
porte = max(gaps, key=lambda g: g[1] - g[0]) if gaps else None
print("    trous detectes dans le mur EST : %s" % gaps)
print("    >>> PORTE D'ENTREE : y[%.2f .. %.2f]  largeur %.2f m  (z 0 -> 2,10)"
      % (porte[0], porte[1], porte[1] - porte[0]))
porte_x = 10.20                            # face interieure du mur EST
D_POR = round(porte[1] - porte[0], 3)
porte_cy = round((porte[0] + porte[1]) / 2, 3)

# ---------- 2. ESCALIER : emprise reelle ----------
esc = [o for o in mesh if o.name.startswith(("MARCHE", "PALIER"))]
ex0 = min(bbox(o)[0] for o in esc); ey0 = min(bbox(o)[1] for o in esc)
ex1 = max(bbox(o)[3] for o in esc); ey1 = max(bbox(o)[4] for o in esc)
ez0 = min(bbox(o)[2] for o in esc); ez1 = max(bbox(o)[5] for o in esc)
print("\n[2] ESCALIER — %d objets" % len(esc))
print("    emprise X[%.2f .. %.2f]  Y[%.2f .. %.2f]  Z[%.2f .. %.2f]"
      % (ex0, ex1, ey0, ey1, ez0, ez1))
print("    longueur %.2f m | largeur %.2f m | hauteur %.2f m"
      % (ex1 - ex0, ey1 - ey0, ez1 - ez0))
m_pal = [o for o in esc if o.name.startswith("PALIER")]
if m_pal:
    px0, py0, pz0, px1, py1, pz1 = bbox(m_pal[0])
    print("    palier : X[%.2f .. %.2f] Y[%.2f .. %.2f]" % (px0, px1, py0, py1))

# ---------- 3. DISTANCE DIRECTE PORTE <-> ESCALIER ----------
dy_overlap = min(porte[1], ey1) - max(porte[0], ey0)
dist_x = porte_x - ex1
print("\n[3] DISTANCE PORTE <-> EMPRISE ESCALIER")
print("    recouvrement en Y entre la porte et l'escalier : %.2f m" %
      (dy_overlap if dy_overlap > 0 else 0))
print("    ecart en X (face interieure du mur EST - bord EST de l'escalier) : %.2f m" % dist_x)
if dy_overlap > 0:
    print("    >>> distance libre porte -> escalier = %.2f m (mesure perpendiculaire)" % dist_x)
else:
    print("    >>> distance = %.2f m" % math.hypot(dist_x, -dy_overlap))

# ---------- 4. RASTERISATION DU NIVEAU z=1,00 m ----------
NX = int(round((IX1 - IX0) / RES))
NY = int(round((IY1 - IY0) / RES))
occ = [[False] * NY for _ in range(NX)]
detail = {}
for o in mesh:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    # l'escalier occupe le sol du RDC sur toute son emprise (on le contourne, on ne le traverse pas)
    est_escalier = o.name.startswith(("MARCHE", "PALIER"))
    if not est_escalier and not (z0 - 1e-6 <= Z_PROBE <= z1 + 1e-6):
        continue
    if o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
        continue
    i0 = max(0, int(math.ceil((x0 - IX0) / RES - 0.5)))
    i1 = min(NX, int(math.floor((x1 - IX0) / RES - 0.5)) + 1)
    j0 = max(0, int(math.ceil((y0 - IY0) / RES - 0.5)))
    j1 = min(NY, int(math.floor((y1 - IY0) / RES - 0.5)) + 1)
    grp = o.name.split("_")[0]
    detail[grp] = detail.get(grp, 0) + 1
    for i in range(i0, i1):
        for j in range(j0, j1):
            occ[i][j] = True
print("\n[4] RASTERISATION z=%.2f m : grille %d x %d (maille %.2f m)" % (Z_PROBE, NX, NY, RES))
print("    objets obstruant ce niveau : %s" % detail)
n_free = sum(1 for i in range(NX) for j in range(NY) if not occ[i][j])
print("    cellules libres : %d (%.2f m2)" % (n_free, n_free * RES * RES))

# ---------- 5. TRANSFORMEE DE DISTANCE (chamfer 3-4) ----------
INF = 1e9
D = [[0.0 if occ[i][j] else INF for j in range(NY)] for i in range(NX)]
A, B, C = 1.0, 1.414, 1.0
for i in range(NX):
    for j in range(NY):
        if D[i][j] == 0:
            continue
        v = D[i][j]
        if i > 0: v = min(v, D[i - 1][j] + A)
        if j > 0: v = min(v, D[i][j - 1] + A)
        if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + B)
        if i > 0 and j + 1 < NY: v = min(v, D[i - 1][j + 1] + B)
        D[i][j] = v
for i in range(NX - 1, -1, -1):
    for j in range(NY - 1, -1, -1):
        if D[i][j] == 0:
            continue
        v = D[i][j]
        if i + 1 < NX: v = min(v, D[i + 1][j] + A)
        if j + 1 < NY: v = min(v, D[i][j + 1] + A)
        if i + 1 < NX and j + 1 < NY: v = min(v, D[i + 1][j + 1] + B)
        if i + 1 < NX and j > 0: v = min(v, D[i + 1][j - 1] + B)
        D[i][j] = v

# ---------- 6. CHEMIN A GOULOT MAXIMAL depuis la porte ----------
def cell(x, y):
    return (max(0, min(NX - 1, int((x - IX0) / RES))),
            max(0, min(NY - 1, int((y - IY0) / RES))))


start = cell(porte_x - 0.10, porte_cy)
best = [[-1.0] * NY for _ in range(NX)]
pq = [(-(D[start[0]][start[1]] * RES * 2), start[0], start[1])]
best[start[0]][start[1]] = D[start[0]][start[1]] * RES * 2
while pq:
    negw, i, j = heapq.heappop(pq)
    w = -negw
    if w < best[i][j] - 1e-9:
        continue
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ni, nj = i + di, j + dj
        if 0 <= ni < NX and 0 <= nj < NY and not occ[ni][nj]:
            nw = min(w, D[ni][nj] * RES * 2)
            if nw > best[ni][nj] + 1e-9:
                best[ni][nj] = nw
                heapq.heappush(pq, (-nw, ni, nj))
reach = [(i, j, best[i][j]) for i in range(NX) for j in range(NY) if best[i][j] > 0]
print("\n[5] ACCESSIBILITE DEPUIS LA PORTE")
print("    cellules atteignables depuis la porte : %d (%.2f m2)"
      % (len(reach), len(reach) * RES * RES))
if reach:
    goulot = min(w for (_, _, w) in reach)
    i_max, j_max, w_max = max(reach, key=lambda t: t[2])
    print("    largeur MINIMALE rencontree sur le parcours depuis la porte : %.2f m" % goulot)
    print("    point le plus degage : x=%.2f y=%.2f (largeur %.2f m)"
          % (IX0 + i_max * RES, IY0 + j_max * RES, w_max))

# ---------- 6bis. GOULOT REEL : clearance max-min vers le CENTRE DE CHAQUE PIECE ----------
# Une "largeur de cellule" = 2 x distance a l'obstacle le plus proche n'a de sens que sur l'axe
# median : les cellules collees aux murs donnent 0,10 m sans qu'il y ait un passage.
# Metrique retenue : pour chaque piece, le meilleur chemin depuis la porte maximise la clearance
# minimale => le chemin passe par le MILIEU des passages. Le goulot = la clearance min rencontree.
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
dests = []
for r in fp["RDC"]["rooms"]:
    cx = IX0 + r["x_m"] + r["w_m"] / 2.0
    cy = IY0 + r["y_m"] + r["d_m"] / 2.0
    ci, cj = cell(cx, cy)
    if 0 <= ci < NX and 0 <= cj < NY and best[ci][cj] > 0:
        dests.append((r["name"], round(cx, 2), round(cy, 2), best[ci][cj]))
print("\n[5] GOULOT RÉEL — chemin à clearance maximale (axe médian) depuis la porte")
print("    %-18s %-16s %s" % ("piece", "centre (x,y)", "passage le plus etroit du trajet"))
pire = None
for (n, cx, cy, w) in sorted(dests, key=lambda t: t[3]):
    print("    %-18s (%5.2f, %5.2f)   %.2f m" % (n, cx, cy, w))
    if pire is None:
        pire = (n, w)
print("    >>> goulot le plus contraignant : %.2f m (vers %s)" % (pire[1], pire[0]))
goulot_reel = pire[1]
print("    (metrique ECARTEE car mal posee : 'largeur minimale sur les cellules atteignables'"
      " = %.2f m — elle capture les cellules collees aux murs/poteaux, pas un passage)"
      % min(w for (_, _, w) in reach))
bande = []
for k in range(int(round((porte[1] - porte[0]) / RES)) + 1):
    y = porte[0] + k * RES
    i, j = cell(porte_x - 0.02, y)
    # balayage vers l'ouest jusqu'au 1er obstacle
    c = 0
    ii = i
    while ii >= 0 and not occ[ii][j]:
        c += 1
        ii -= 1
    bande.append(round(c * RES, 2))
passage_min = min(bande) if bande else 0
print("\n[6] LARGEUR DE PASSAGE DEVANT LA PORTE (balayage vers l'ouest, sur toute la largeur)")
print("    largeur libre par abscisse : %s" % bande)
print("    >>> passage MINIMUM devant la porte : %.2f m" % passage_min)

res = {"at": datetime.datetime.now().isoformat(timespec="seconds"),
       "fichier_mesure": os.path.basename(BIM), "sha256_blend": sha(BIM),
       "methode": "rasterisation z=1,00 m maille 0,05 m + chamfer + max-min Dijkstra",
       "porte": {"facade": "EST (RDC)", "y_min_m": porte[0], "y_max_m": porte[1],
                 "largeur_m": D_POR, "hauteur_m": 2.10, "face_interieure_x_m": porte_x,
                 "centre_y_m": porte_cy},
       "escalier": {"emprise_x_m": [round(ex0, 3), round(ex1, 3)],
                    "emprise_y_m": [round(ey0, 3), round(ey1, 3)],
                    "longueur_m": round(ex1 - ex0, 3), "largeur_m": round(ey1 - ey0, 3),
                    "nb_objets": len(esc)},
       "distance_porte_escalier_m": round(dist_x, 3),
       "recouvrement_y_m": round(max(0.0, dy_overlap), 3),
       "passage_minimum_devant_porte_m": passage_min,
       "goulot_reel_axe_median_m": round(goulot_reel, 3),
       "goulot_reel_vers_piece": pire[0],
       "passage_par_piece_m": {n: round(w, 3) for (n, _x, _y, w) in dests},
              "largeur_min_sur_parcours_m": round(min(w for (_, _, w) in reach), 3) if reach else None,
       "note_largeur_min": "indicateur ECARTE (mal pose) : la largeur d'une cellule = 2 x distance "
                           "au plus proche obstacle n'a de sens que sur l'axe median ; les cellules "
                           "collees aux murs donnent 0,10 m sans que ce soit un passage. Metrique "
                           "retenue : balayage perpendiculaire + clearance sur l'axe median.",
       "cellules_libres_m2": round(n_free * RES * RES, 2),
       "cellules_atteignables_m2": round(len(reach) * RES * RES, 2),
       "exigence_circulation_m": 1.20,
       "conforme_circulation": (passage_min >= 1.20),
       "STATUS": "MEASURED"}
json.dump(res, open(OUT, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("SYNTHESE : passage minimum devant la porte = %.2f m  (exigence : 1,20 m) -> %s"
      % (passage_min, "CONFORME" if passage_min >= 1.20 else "NON CONFORME"))
print("-> %s" % OUT)
print("=" * 78)
