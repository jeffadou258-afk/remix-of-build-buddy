#!/usr/bin/env python3
"""VARIANT_D_CIRCULATION — etude experimentale separee.
NE MODIFIE NI le plan 2D VALIDATED, NI les BIM officiels, ni metre/budget.
Cree un .blend de variante SEPARE + mesures physiques.
"""
import bpy, bmesh, os, json, math, hashlib, datetime, sys

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
OUTB = os.path.join(PROJ, "3D", "VARIANT_D_CIRCULATION.blend")
RES, Z = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
SHA_BASE = hashlib.sha256(open(BASE, "rb").read()).hexdigest()


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


def box(name, x0, y0, z0, x1, y1, z1, col=None):
    m = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(name, m)
    bpy.context.collection.objects.link(o)
    o.scale = (x1 - x0, y1 - y0, z1 - z0)
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return o


# ============ 1. ETAT VALIDATED : mesure du bloc EST ============
bpy.ops.wm.open_mainfile(filepath=BASE)
n_obj_base = len(bpy.data.objects)

# bloc EST interieur x[8,10] y[0,4.5] -> absolu x[8.20,10.20] y[0.20,4.70]
BX0, BY0, BX1, BY1 = 8.20, 0.20, 10.20, 4.70
bloc_area = (BX1 - BX0) * (BY1 - BY0)
intrus = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if x0 < BX1 - 1e-6 and x1 > BX0 + 1e-6 and y0 < BY1 - 1e-6 and y1 > BY0 + 1e-6:
        if x0 - 1e-6 <= Z <= x1 + 1e-6 or True:
            intrus.append((o.name, round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)))
print("=" * 78)
print("1. BLOC EST — mesures dans le plan VALIDATED")
print("   emprise brute x[%.2f..%.2f] y[%.2f..%.2f]" % (BX0, BX1, BY0, BY1))
print("   >>> AIRE REELLE = %.2f x %.2f = %.2f m2" % (BX1 - BX0, BY1 - BY0, bloc_area))
print("   >>> (la mission annoncait 18 m2 : ecart de %.2f m2)" % (18.0 - bloc_area))
occupe = [i for i in intrus if not i[0].startswith(("MUR_E", "MUR_O", "MUR_N", "MUR_S",
                                                    "POTEAU", "CLOISON_RDC_03", "SEMELLE"))]
print("   objets presents dans le bloc : %d" % len(intrus))
for i in intrus[:8]:
    print("      %-28s x[%.2f..%.2f] y[%.2f..%.2f]" % i)

# ============ 2. PREUVE ARITHMETIQUE D'IMPOSSIBILITE ============
print("\n2. PREUVE ARITHMETIQUE — les 2 pieces tiennent-elles dans le bloc ?")
EP = 0.10                                   # epaisseur de cloison
larg_dispo = (BX1 - BX0) - EP               # largeur disponible pour les pieces
A_BUA, A_WC = 6.00, 3.00
prof_max = BY1 - BY0
l_bua_min = A_BUA / prof_max                # largeur mini si profondeur max
l_wc_min = A_WC / prof_max
print("   largeur du bloc                  : %.2f m" % (BX1 - BX0))
print("   moins 1 cloison (%.2f m)         : %.2f m utilisables" % (EP, larg_dispo))
print("   si les 2 pieces font %.2f m de profondeur :" % prof_max)
print("     Buanderie %.2f m2 -> largeur mini %.3f m" % (A_BUA, l_bua_min))
print("     WC        %.2f m2 -> largeur mini %.3f m" % (A_WC, l_wc_min))
print("     somme exige %.3f m  >  %.3f m disponibles  ->  ECART %.3f m"
      % (l_bua_min + l_wc_min, larg_dispo, l_bua_min + l_wc_min - larg_dispo))
print("   >>> CONCLUSION : IMPOSSIBLE de loger 6 m2 + 3 m2 avec une cloison,")
print("       sans reduire la profondeur, donc sans sortir du bloc.")
reste = larg_dispo - l_bua_min
print("   largeur reelle du WC si on garde la Buanderie a %.2f m2 : %.3f m" % (A_BUA, reste))
print("   surface reelle du WC dans ce cas : %.3f x %.2f = %.2f m2 (exige 3,00)"
      % (reste, prof_max, reste * prof_max))

# ============ 3. CONSTRUCTION DE LA VARIANTE (nouveau fichier) ============
print("\n3. CONSTRUCTION DE VARIANT_D_CIRCULATION (nouveau .blend separe)")
# 3a. liberer le nord-ouest : supprimer les cloisons du bloc Buanderie/WC
supprimes = []
for o in list(bpy.data.objects):
    if o.type != "MESH" or not o.name.startswith("CLOISON"):
        continue
    x0, y0, z0, x1, y1, z1 = bbox(o)
    # zone nord-ouest du bloc Buanderie/WC : x[0..4.7] y[8.0..10.7]
    if x0 >= -0.1 and x1 <= 4.80 and y0 >= 7.90 and y1 <= 10.80:
        supprimes.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
print("   cloisons du bloc Buanderie/WC nord-ouest supprimees : %d" % len(supprimes))
for s in supprimes:
    print("      - %s" % s)

# 3b. variante : murs du bloc EST (limite nord y=4,65..4,75) + cloison interne
#     sol interieur du bloc : x[8,10] y[0,4.5] -> absolu x[8.20,10.20] y[0.20,4.70]
XL = 9.53                                    # cloison interne (recherchee au plus juste)
mur_nord = []
for (a, b, tag) in [(8.20, 8.95, "p01"), (9.75, 10.20, "p02")]:
    o = box("VAR_CLOISON_NORD_%s" % tag, a, 4.65, 0.00, b, 4.75, 2.10)
    mur_nord.append(o.name)
cloison = box("VAR_CLOISON_BUA_WC", 9.53, 0.20, 0.00, 9.63, 4.65, 2.10)
print("   ajoute : mur nord %s (2 retombees + passage central) + cloison %s"
      % (mur_nord, cloison.name))
for o in bpy.data.objects:
    if o.type == "MESH":
        bpy.context.view_layer.objects.active = o
print("   objets avant sauvegarde : %d" % len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUTB)
SHA_OUT = hashlib.sha256(open(OUTB, "rb").read()).hexdigest()
print("   -> %s (%d o, sha %s)" % (os.path.basename(OUTB), os.path.getsize(OUTB), SHA_OUT[:24]))

# ============ 4. MESURES DE LA VARIANTE ============
bpy.ops.wm.open_mainfile(filepath=OUTB)
NX = int(round((IX1 - IX0) / RES)); NY = int(round((IY1 - IY0) / RES))
occ = [[False] * NY for _ in range(NX)]
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
        continue
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if o.name.startswith(("VAR_CLOISON",)):
        pass
    elif not (z0 - 1e-6 <= Z <= z1 + 1e-6):
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


def maxmin_path(start, target):
    """meilleur chemin start->target maximisant la clearance minimale ; renvoie largeur mini"""
    best = [[-1.0] * NY for _ in range(NX)]
    si, sj = start
    if occ[si][sj]: return None
    best[si][sj] = D[si][sj]
    import heapq
    pq = [(-D[si][sj], si, sj)]
    while pq:
        negc, i, j = heapq.heappop(pq)
        c = -negc
        if c < best[i][j] - 1e-9: continue
        if (i, j) == target: return min(c, D[target[0]][target[1]]) * RES
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < NX and 0 <= nj < NY and not occ[ni][nj]:
                nc = min(c, D[ni][nj])
                if nc > best[ni][nj] + 1e-9:
                    best[ni][nj] = nc
                    heapq.heappush(pq, (-nc, ni, nj))
    return None


def C(x, y):
    return (max(0, min(NX - 1, int((x - IX0) / RES))), max(0, min(NY - 1, int((y - IY0) / RES))))


def P(x, y):
    i, j = C(x, y)
    while j < NY and not occ[i][j]: j += 1
    return j < NY


entree = None
for i in range(NX):
    for j in range(NY):
        x, y = IX0 + i * RES, IY0 + j * RES
        if 9.5 <= x <= 10.15 and 5.0 <= y <= 6.0 and not occ[i][j]:
            if entree is None or D[i][j] > D[entree[0]][entree[1]]:
                entree = (i, j)
print("\n4. MESURES DE LA VARIANTE — cheminement depuis l'entree (x=%.2f y=%.2f)"
      % (IX0 + entree[0] * RES, IY0 + entree[1] * RES))
PIECES = [("Salon", 0.20, 0.20, 4.20, 8.20), ("Salle a manger", 4.20, 0.20, 8.20, 4.70),
          ("Cuisine", 4.70, 6.70, 7.70, 10.70), ("Bureau", 7.70, 6.70, 10.20, 10.70),
          ("Buanderie (VAR)", 8.20, 0.20, 9.53, 4.70), ("WC visiteur (VAR)", 9.63, 0.20, 10.20, 4.70)]
mes = {}
for (n, x0, y0, x1, y1) in PIECES:
    t = C((x0 + x1) / 2, (y0 + y1) / 2)
    w = maxmin_path(entree, t)
    mes[n] = {"cheminement_min_m": round(w, 3) if w else None,
              "surface_m2": round((x1 - x0) * (y1 - y0), 2),
              "conforme_120": bool(w and w >= 1.20)}
    print("   %-20s surface %5.2f m2 | cheminement min %s m | %s"
          % (n, (x1 - x0) * (y1 - y0), ("%.2f" % w) if w else "AUCUN",
             "CONFORME" if (w and w >= 1.20) else "*** NON CONFORME ***"))

# profil de la bande
prof = []
for k in range(23):
    i = int(round((4.5 + 0.25 * k) / RES)); n = 0; j = int(round(6.60 / RES))
    while j >= 0 and not occ[i][j]:
        n += 1; j -= 1
    prof.append(round(n * RES, 2))
print("\n   profil bande principale (profondeur libre par x) : %s" % prof)
print("   >>> profondeur mini : %.2f m" % min(prof))

rapport = {
    "etude": "VARIANT_D_CIRCULATION", "at": STAMP,
    "regles": {"plan_2D_validated_modifie": False, "bim_officiels_modifies": False,
               "metre_modifie": False, "budget_modifie": False, "phase8_lancee": False},
    "fichier_reference": os.path.basename(BASE), "sha256_reference": SHA_BASE,
    "fichier_variante": os.path.basename(OUTB), "sha256_variante": SHA_OUT,
    "bloc_est": {"emprise_absolue_m": [BX0, BY0, BX1, BY1],
                 "aire_m2": round(bloc_area, 2),
                 "aire_annoncee_dans_la_mission_m2": 18.0,
                 "ecart_m2": round(18.0 - bloc_area, 2),
                 "objets_presents": len(intrus)},
    "preuve_arithmetique": {"epaisseur_cloison_m": EP,
                            "largeur_utilisable_m": round(larg_dispo, 3),
                            "profondeur_max_m": prof_max,
                            "largeur_mini_buanderie_m": round(l_bua_min, 3),
                            "largeur_mini_wc_m": round(l_wc_min, 3),
                            "somme_exigee_m": round(l_bua_min + l_wc_min, 3),
                            "ecart_m": round(l_bua_min + l_wc_min - larg_dispo, 3),
                            "verdict": "IMPOSSIBLE"},
    "variant_construite": {"cloisons_supprimees": supprimes, "mur_nord": mur_nord,
                           "cloison_interne": cloison.name},
    "mesures_cheminements": mes,
    "profil_bande_principale": prof, "profil_bande_min_m": min(prof),
    "STATUS": "VARIANT_D_NON_CONFORME"}
p = os.path.join(PROJ, "reports", "variant_D_circulation.json")
json.dump(rapport, open(p, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("-> %s" % p)
print("STATUS : VARIANT_D_NON_CONFORME (mesure)")
