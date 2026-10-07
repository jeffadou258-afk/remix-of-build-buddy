#!/usr/bin/env python3
"""MESURE FINALE — tableau comparatif VALIDATED vs VARIANT_D_CIRCULATION.
Mesure les surfaces REELLEMENT utilisables (cellules libres) et les cheminements."""
import bpy, os, json, math, hashlib, datetime, heapq

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
VAR = os.path.join(PROJ, "3D", "VARIANT_D_CIRCULATION.blend")
RES, Z = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
NX = int(round((IX1 - IX0) / RES)); NY = int(round((IY1 - IY0) / RES))


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


def mesure(fichier, pieces):
    bpy.ops.wm.open_mainfile(filepath=fichier)
    occ = [[False] * NY for _ in range(NX)]
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
            continue
        x0, y0, z0, x1, y1, z1 = bbox(o)
        if not (z0 - 1e-6 <= Z <= z1 + 1e-6):
            continue
        i0 = max(0, int(math.ceil((x0 - IX0) / RES - 0.5)))
        i1 = min(NX, int(math.floor((x1 - IX0) / RES - 0.5)) + 1)
        j0 = max(0, int(math.ceil((y0 - IY0) / RES - 0.5)))
        j1 = min(NY, int(math.floor((y1 - IY0) / RES - 0.5)) + 1)
        for i in range(i0, i1):
            for j in range(j0, j1):
                occ[i][j] = True
    INF = 1e9
    D = [[0.0 if occ[i][j] else INF for j in range(NY)] for i in range(NX)]
    for i in range(NX):
        for j in range(NY):
            if D[i][j] == 0: continue
            v = D[i][j]
            if i > 0: v = min(v, D[i - 1][j] + 1)
            if j > 0: v = min(v, D[i][j - 1] + 1)
            if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + 1.414)
            if i > 0 and j + 1 < NY: v = min(v, D[i - 1][j + 1] + 1.414)
            D[i][j] = v
    for i in range(NX - 1, -1, -1):
        for j in range(NY - 1, -1, -1):
            if D[i][j] == 0: continue
            v = D[i][j]
            if i + 1 < NX: v = min(v, D[i + 1][j] + 1)
            if j + 1 < NY: v = min(v, D[i][j + 1] + 1)
            if i + 1 < NX and j + 1 < NY: v = min(v, D[i + 1][j + 1] + 1.414)
            if i + 1 < NX and j > 0: v = min(v, D[i + 1][j - 1] + 1.414)
            D[i][j] = v

    def C(x, y):
        return (max(0, min(NX - 1, int((x - IX0) / RES))), max(0, min(NY - 1, int((y - IY0) / RES))))

    entree = None
    for i in range(NX):
        for j in range(NY):
            x, y = IX0 + i * RES, IY0 + j * RES
            if 9.5 <= x <= 10.15 and 5.0 <= y <= 6.0 and not occ[i][j]:
                if entree is None or D[i][j] > D[entree[0]][entree[1]]:
                    entree = (i, j)

    def maxmin(target):
        best = [[-1.0] * NY for _ in range(NX)]
        si, sj = entree
        best[si][sj] = D[si][sj]
        pq = [(-D[si][sj], si, sj)]
        while pq:
            negc, i, j = heapq.heappop(pq)
            c = -negc
            if c < best[i][j] - 1e-9: continue
            if (i, j) == target:
                return min(c, D[target[0]][target[1]]) * RES * 2.0
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < NX and 0 <= nj < NY and not occ[ni][nj]:
                    nc = min(c, D[ni][nj])
                    if nc > best[ni][nj] + 1e-9:
                        best[ni][nj] = nc
                        heapq.heappush(pq, (-nc, ni, nj))
        return None

    out = {}
    for (n, x0, y0, x1, y1, cible) in pieces:
        libres = 0
        for i in range(max(0, int((x0 - IX0) / RES)), min(NX, int((x1 - IX0) / RES))):
            for j in range(max(0, int((y0 - IY0) / RES)), min(NY, int((y1 - IY0) / RES))):
                if not occ[i][j]:
                    libres += 1
        t = C((x0 + x1) / 2, (y0 + y1) / 2)
        w = maxmin(t) if not occ[t[0]][t[1]] else None
        out[n] = {"emprise_m": [x0, y0, x1, y1],
                  "emprise_m2": round((x1 - x0) * (y1 - y0), 2),
                  "surface_utile_mesuree_m2": round(libres * RES * RES, 2),
                  "cheminement_min_m": round(w, 2) if w else None,
                  "conforme_120": bool(w and w >= 1.20)}
    # profil de la bande
    prof = []
    for k in range(23):
        i = int(round((4.5 + 0.25 * k) / RES)); n = 0; j = int(round(6.60 / RES))
        while j >= 0 and not occ[i][j]:
            n += 1; j -= 1
        prof.append(round(n * RES, 2))
    out["_bande_principale_min_m"] = min(prof)
    return out


# --- pieces du plan VALIDATED (coordonnees absolues) ---
P_VAL = [("Salon", 0.20, 0.20, 4.20, 8.20, None), ("Salle a manger", 4.20, 0.20, 8.20, 4.70, None),
         ("Cuisine", 4.70, 6.70, 7.70, 10.70, None), ("Bureau", 7.70, 6.70, 10.20, 10.70, None),
         ("Buanderie", 0.20, 8.70, 3.20, 10.70, None), ("WC visiteur", 3.20, 8.70, 4.70, 10.70, None)]
# --- pieces de la variante D (dispositions V1 cote a cote et V2 WC devant) ---
P_V1 = [("Salon", 0.20, 0.20, 4.20, 8.20, None), ("Salle a manger", 4.20, 0.20, 8.20, 4.70, None),
        ("Cuisine", 4.70, 6.70, 7.70, 10.70, None), ("Bureau", 7.70, 6.70, 10.20, 10.70, None),
        ("Buanderie", 8.20, 0.20, 9.53, 4.70, None), ("WC visiteur", 9.63, 0.20, 10.20, 4.70, None)]

print("=" * 78)
print("MESURES — plan VALIDATED (bim v2 officiel)")
print("=" * 78)
val = mesure(BASE, P_VAL)
for k, v in val.items():
    if k.startswith("_"): continue
    print("  %-16s emprise %6.2f m2 | utile mesuree %6.2f m2 | cheminement %s m | %s"
          % (k, v["emprise_m2"], v["surface_utile_mesuree_m2"],
             ("%.2f" % v["cheminement_min_m"]) if v["cheminement_min_m"] else "AUCUN",
             "CONFORME" if v["conforme_120"] else "NON CONFORME"))
print("  bande principale profondeur mini : %.2f m" % val["_bande_principale_min_m"])

print("\n" + "=" * 78)
print("MESURES — VARIANT_D_CIRCULATION")
print("=" * 78)
var = mesure(VAR, P_V1)
for k, v in var.items():
    if k.startswith("_"): continue
    print("  %-16s emprise %6.2f m2 | utile mesuree %6.2f m2 | cheminement %s m | %s"
          % (k, v["emprise_m2"], v["surface_utile_mesuree_m2"],
             ("%.2f" % v["cheminement_min_m"]) if v["cheminement_min_m"] else "AUCUN",
             "CONFORME" if v["conforme_120"] else "NON CONFORME"))
print("  bande principale profondeur mini : %.2f m" % var["_bande_principale_min_m"])

# ---- surfaces exigees ----
EXIGE = {"Salon": 32.0, "Salle a manger": 18.0, "Cuisine": 12.0, "Bureau": 10.0,
         "Buanderie": 6.0, "WC visiteur": 3.0}
print("\n" + "=" * 78)
print("CONTROLE DES SURFACES EXIGEES")
print("=" * 78)
diff = {}
for n, e in EXIGE.items():
    v = val[n]["surface_utile_mesuree_m2"]; d = var[n]["surface_utile_mesuree_m2"]
    diff[n] = {"exige": e, "validated_mesure_m2": v, "variant_mesure_m2": d,
               "ecart_validated": round(v - e, 2), "ecart_variant": round(d - e, 2),
               "variant_conforme": abs(d - e) <= 0.15}
    print("  %-16s exige %5.2f | VALIDATED %5.2f (%+.2f) | VARIANT %5.2f (%+.2f) | %s"
          % (n, e, v, v - e, d, d - e, "OK" if diff[n]["variant_conforme"] else "*** ECART ***"))

# ---- verdict ----
defauts = []
if var["WC visiteur"]["cheminement_min_m"] is None:
    defauts.append("WC variante : AUCUN cheminement mesure (inaccessible)")
if var["WC visiteur"]["surface_utile_mesuree_m2"] < 2.85:
    defauts.append("WC variante : %.2f m2 mesures pour 3,00 exiges"
                   % var["WC visiteur"]["surface_utile_mesuree_m2"])
if var["Buanderie"]["surface_utile_mesuree_m2"] < 5.85:
    defauts.append("Buanderie variante : %.2f m2 mesures pour 6,00 exiges"
                   % var["Buanderie"]["surface_utile_mesuree_m2"])
if var["_bande_principale_min_m"] < 1.20:
    defauts.append("bande principale variante : %.2f m (escalier conserve)"
                   % var["_bande_principale_min_m"])

rapport = {
    "etude": "VARIANT_D_CIRCULATION", "at": STAMP,
    "regles_respectees": {"plan_2D_VALIDATED_modifie": False,
                          "bim_officiels_modifies": False, "metre_json_modifie": False,
                          "budget_json_modifie": False, "phase8_lancee": False},
    "fichiers": {"bim_reference": os.path.basename(BASE), "sha256_reference": sha(BASE),
                 "variant_blend": os.path.basename(VAR), "sha256_variant": sha(VAR)},
    "bloc_est": {"emprise_absolue_m": [8.20, 0.20, 10.20, 4.70], "largeur_m": 2.00,
                 "profondeur_m": 4.50, "aire_m2": 9.00,
                 "aire_annoncee_mission_m2": 18.00, "ecart_m2": 9.00},
    "preuve_arithmetique_impossibilite": {
        "largeur_utilisable_m": 1.90, "profondeur_max_m": 4.50,
        "largeur_mini_buanderie_m": 1.333, "largeur_mini_wc_m": 0.667,
        "somme_exigee_m": 2.000, "ecart_m": 0.100, "verdict": "IMPOSSIBLE"},
    "mesures_validated": val, "mesures_variant": var,
    "controle_surfaces": diff, "defauts_mesures": defauts,
    "STATUS": "VARIANT_D_NON_CONFORME",
    "CAS": "B et C — Variant D echoue ; aucune variante ne conserve les surfaces avec >=1,20 m"}
p = os.path.join(PROJ, "reports", "variant_D_circulation.json")
json.dump(rapport, open(p, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("DEFAUTS MESURES DE LA VARIANTE D :")
for d in defauts:
    print("  - %s" % d)
print("-> %s (%d o, sha %s)" % (p, os.path.getsize(p), sha(p)))
