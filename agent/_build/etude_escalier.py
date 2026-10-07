#!/usr/bin/env python3
"""ETUDE PARAMETRIQUE DE L'ESCALIER — mesure physique dans Blender.
Aucune modification du .blend : les variantes sont SIMULEES comme obstacles.
Geometrie 2D VALIDATED non touchee."""
import bpy, os, json, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
RES, Z_PROBE = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90
SEUIL = 1.20

bpy.ops.wm.open_mainfile(filepath=BASE)
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
try:
    an = json.load(open(os.path.join(PROJ, "reports", "porte_escalier_mesure_v2.json")))
    porte = (an["porte"]["y_min_m"], an["porte"]["y_max_m"])
except Exception:
    porte = (4.90, 6.10)
print("=" * 78)
print("ETUDE PARAMETRIQUE — OPTIMISATION DE L'ESCALIER")
print("fichier : %s (%d objets, sha %s)" % (os.path.basename(BASE), len(bpy.data.objects),
                                            hashlib.sha256(open(BASE, "rb").read()).hexdigest()[:20]))
print("porte d'entree : y[%.2f .. %.2f] | seuil exige : %.2f m" % (porte[0], porte[1], SEUIL))
print("=" * 78)


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


# --- obstacles STATIQUES : tout sauf l'escalier de la version courante ---
statiques = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
        continue
    if o.name.startswith(("MARCHE", "PALIER")):
        continue                                   # l'escalier est traite a part (variantes)
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if z0 - 1e-6 <= Z_PROBE <= z1 + 1e-6:
        statiques.append((x0, y0, x1, y1, o.name))
print("obstacles statiques au niveau z=%.2f : %d" % (Z_PROBE, len(statiques)))

NX = int(round((IX1 - IX0) / RES))
NY = int(round((IY1 - IY0) / RES))


def raster(escalier):
    occ = [[False] * NY for _ in range(NX)]
    objs = [(a, b, c, d) for (a, b, c, d, _n) in statiques]
    if escalier:
        objs.append(escalier)
    for (x0, y0, x1, y1) in objs:
        i0 = max(0, int(math.ceil((x0 - IX0) / RES - 0.5)))
        i1 = min(NX, int(math.floor((x1 - IX0) / RES - 0.5)) + 1)
        j0 = max(0, int(math.ceil((y0 - IY0) / RES - 0.5)))
        j1 = min(NY, int(math.floor((y1 - IY0) / RES - 0.5)) + 1)
        for i in range(i0, i1):
            for j in range(j0, j1):
                occ[i][j] = True
    return occ


def chamfer(occ):
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
    return D


def montants(occ, D):
    """Accessibilite depuis la porte selon le seuil de largeur ; profondeur de la bande."""
    # profondeur de la bande de circulation le long de l'escalier (balayage nord->sud)
    prof = []
    for i in range(int((4.5) / RES), int(10.0 / RES) + 1):
        x = i * RES
        j = int(round((6.65 - IY0) / RES))
        n = 0
        while j >= 0 and not occ[i][j]:
            n += 1
            j -= 1
        prof.append(round(n * RES, 2))
    bande_min = min(prof) if prof else 0.0
    # accessibilite
    res = {}
    for seuil in (1.20, 1.00, 0.90, 0.80, 0.60, 0.40):
        r = seuil / 2.0 / RES
        ok = [[(not occ[i][j]) and D[i][j] >= r for j in range(NY)] for i in range(NX)]
        # depart : meilleure clearance dans l'emprise de la porte
        bs, bd = None, -1
        for i in range(NX):
            for j in range(NY):
                x, y = IX0 + i * RES, IY0 + j * RES
                if 8.8 <= x <= 10.15 and porte[0] - 1e-9 <= y <= porte[1] + 1e-9 and ok[i][j]:
                    if D[i][j] > bd:
                        bd, bs = D[i][j], (i, j)
        if bs is None:
            res[seuil] = (0, [])
            continue
        seen = [[False] * NY for _ in range(NX)]
        st = [bs]
        seen[bs[0]][bs[1]] = True
        while st:
            i, j = st.pop()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < NX and 0 <= nj < NY and ok[ni][nj] and not seen[ni][nj]:
                    seen[ni][nj] = True
                    st.append((ni, nj))
        acc = []
        for rm in fp["RDC"]["rooms"]:
            cx = rm["x_m"] + rm["w_m"] / 2.0
            cy = rm["y_m"] + rm["d_m"] / 2.0
            ci = max(0, min(NX - 1, int(cx / RES)))
            cj = max(0, min(NY - 1, int(cy / RES)))
            acc.append((rm["name"], bool(seen[ci][cj])))
        res[seuil] = (sum(1 for _, v in acc if v), acc)
    return res, bande_min


VARIANTES = [
    ("A — actuelle (v2) : volee droite 1,00 m dans la bande",
     (4.20, 4.70, 8.96, 5.70), "bande, 1,00 m de large"),
    ("B — bande, 0,90 m de large",
     (4.20, 4.70, 8.96, 5.60), "bande, 0,90 m"),
    ("C — bande, 0,80 m de large",
     (4.20, 4.70, 8.96, 5.50), "bande, 0,80 m"),
    ("D — bloc EST x[8,10] y[0,4,5], largeur 1,00 m cale au nord du bloc",
     (8.05, 4.30, 9.05, 5.30), "hors bande (bloc EST)"),
    ("E — bloc EST, emprise pleine 1,95 x 4,25 m",
     (8.05, 0.20, 10.00, 4.45), "hors bande (bloc EST), pleine largeur"),
    ("F — bloc EST, 1,00 m cale a l'ouest x[8,05..9,05] y[0,20..4,45]",
     (8.05, 0.20, 9.05, 4.45), "hors bande (bloc EST)"),
    ("G — aucun escalier (reference haute)",
     None, "reference"),
]

resultats = []
for nom, rect, desc in VARIANTES:
    occ = raster(rect)
    D = chamfer(occ)
    res, bande_min = montants(occ, D)
    n120, acc120 = res[1.20]
    ligne = {"variante": nom, "emprise": desc,
             "emprise_m": ("%.2f x %.2f" % (rect[2] - rect[0], rect[3] - rect[1])) if rect else "-",
             "bande_min_m": bande_min,
             "acces_120": n120, "acces_120_detail": {n: v for n, v in acc120},
             "acces_par_seuil": {str(k): res[k][0] for k in sorted(res, reverse=True)}}
    resultats.append(ligne)
    print("\n--- %s" % nom)
    print("    emprise %s m | profondeur mini de la bande : %.2f m" % (ligne["emprise_m"], bande_min))
    print("    pieces accessibles : %s" % ", ".join("%s=%s" % (n, "O" if v else "NON")
                                                    for n, v in acc120))
    print("    nb accessibles par seuil : %s" % ligne["acces_par_seuil"])

out = {"etude": "optimisation_escalier_circulation", "at":
       datetime.datetime.now().isoformat(timespec="seconds"),
       "fichier_base": os.path.basename(BASE), "sha256_base": hashlib.sha256(open(BASE, "rb").read()).hexdigest(),
       "methode": "rasterisation enveloppe complete maille 0,05 m a z=1,00 m ; chamfer 3-4 ; "
                  "test de seuil de clearance par composante connexe ; balayage de la bande",
       "geometrie_2d_touchee": False, "variantes": resultats, "STATUS": "MEASURED"}
p = os.path.join(PROJ, "reports", "etude_escalier_circulation.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("-> %s" % p)
print("=" * 78)
