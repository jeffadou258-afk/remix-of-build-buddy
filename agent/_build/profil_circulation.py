#!/usr/bin/env python3
"""MESURE PHYSIQUE DES BRANCHES DE CIRCULATION — dans le .blend, sans le modifier.
But : identifier QUEL element limite la clearance a moins de 1,20 m."""
import bpy, os, json, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
RES, Z = 0.05, 1.00
IX0, IY0, IX1, IY1 = 0.00, 0.00, 10.40, 10.90
bpy.ops.wm.open_mainfile(filepath=BASE)
fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
NX = int(round((IX1 - IX0) / RES)); NY = int(round((IY1 - IY0) / RES))


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


occ = [[False] * NY for _ in range(NX)]
qui = [[None] * NY for _ in range(NX)]
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")):
        continue
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if o.name.startswith(("MARCHE", "PALIER")):
        pass                                  # l'escalier compte (on mesure l'etat reel)
    elif not (z0 - 1e-6 <= Z <= z1 + 1e-6):
        continue
    i0 = max(0, int(math.ceil((x0 - IX0) / RES - 0.5)))
    i1 = min(NX, int(math.floor((x1 - IX0) / RES - 0.5)) + 1)
    j0 = max(0, int(math.ceil((y0 - IY0) / RES - 0.5)))
    j1 = min(NY, int(math.floor((y1 - IY0) / RES - 0.5)) + 1)
    for i in range(i0, i1):
        for j in range(j0, j1):
            occ[i][j] = True
            qui[i][j] = o.name


def run_h(y, x_from, x_to):
    """plus grande suite libre en x a l'ordonnee y, dans [x_from,x_to]"""
    j = int(round(y / RES))
    best = n = 0
    for i in range(int(x_from / RES), int(x_to / RES) + 1):
        if 0 <= i < NX and 0 <= j < NY and not occ[i][j]:
            n += 1
            best = max(best, n)
        else:
            n = 0
    return round(best * RES, 2)


def run_v(x, y_from, y_to):
    """plus grande suite libre en y a l'abscisse x, dans [y_from,y_to]"""
    i = int(round(x / RES))
    best = n = 0
    for j in range(int(y_from / RES), int(y_to / RES) + 1):
        if 0 <= i < NX and 0 <= j < NY and not occ[i][j]:
            n += 1
            best = max(best, n)
        else:
            n = 0
    return round(best * RES, 2)


print("=" * 78)
print("PROFIL DE LARGEUR DES BRANCHES DE CIRCULATION (mesure reelle dans le .blend)")
print("fichier : %s" % os.path.basename(BASE))
print("=" * 78)

# A. BANDE PRINCIPALE ouest->est : profondeur libre en y a chaque abscisse
print("\nA. BANDE PRINCIPALE  x[4,5..10,0]  (profondeur libre en y)")
prof = []
for x in [round(4.5 + 0.25 * k, 2) for k in range(23)]:
    p = run_v(x, 4.45, 6.70)
    prof.append(p)
print("   profondeur par x : %s" % prof)
print("   >>> profondeur MINIMALE de la bande : %.2f m" % (min(prof) if prof else 0))
# ou exactement
imin = [round(4.5 + 0.25 * k, 2) for k in range(23)][prof.index(min(prof))] if prof else None
print("   >>> atteinte a x = %s m" % imin)
i = int(round(imin / RES)); j = int(round(4.45 / RES))
jbloc = None
while j < NY and not occ[i][j]:
    j += 1
print("   >>> premier obstacle au sud de la bande a cet x : %s" % (qui[i][j] if j < NY else "?"))
i2 = int(round(imin / RES)); j2 = int(round(6.70 / RES))
while j2 >= 0 and not occ[i2][j2]:
    j2 -= 1
print("   >>> premier obstacle au nord de la bande a cet x : %s" % (qui[i2][j2] if j2 >= 0 else "?"))

# B. BRAS OUEST : largeur libre en x de y=4,5 a y=8,5
print("\nB. BRAS OUEST vers Buanderie/WC (largeur libre en x)")
bras = []
for y in [round(4.6 + 0.2 * k, 2) for k in range(20)]:
    bras.append(run_h(y, 3.95, 5.00))
print("   largeur par y : %s" % bras)
print("   >>> largeur MINIMALE du bras ouest : %.2f m" % (min(bras) if bras else 0))

# C. BANDE NORD (devant Buanderie/WC) : profondeur libre en y
print("\nC. BANDE NORD y[8,0..8,5] devant Buanderie/WC (profondeur libre en y)")
nord = []
for x in [round(0.3 + 0.3 * k, 2) for k in range(15)]:
    nord.append(run_v(x, 7.80, 8.70))
print("   profondeur par x : %s" % nord)
print("   >>> profondeur MINIMALE de la bande nord : %.2f m" % (min(nord) if nord else 0))

# D. SORTIE DE L'ESCALIER vers la bande (le long de l'escalier)
print("\nD. PASSAGE LE LONG DE L'ESCALIER (profondeur libre en y, cote nord de l'escalier)")
esc = []
for x in [round(4.3 + 0.3 * k, 2) for k in range(16)]:
    esc.append(run_v(x, 5.40, 6.70))
print("   profondeur par x : %s" % esc)
print("   >>> passage MINIMAL le long de l'escalier : %.2f m" % (min(esc) if esc else 0))

# E. PORTE : rappel
print("\nE. PASSAGE DEVANT LA PORTE (rappel mesure precedente) : 1.25 m (CONFORME)")

reste = {"A_bande_principale_min_m": min(prof) if prof else None,
         "B_bras_ouest_min_m": min(bras) if bras else None,
         "C_bande_nord_min_m": min(nord) if nord else None,
         "D_le_long_escalier_min_m": min(esc) if esc else None,
         "E_porte_min_m": 1.25,
         "seuil_requis_m": 1.20}
print("\n" + "=" * 78)
print("SYNTHESE DES BRANCHES")
for k, v in reste.items():
    if k.endswith("_m") and v is not None:
        print("   %-32s %.2f m   %s" % (k, v, "CONFORME" if v >= 1.20 else "*** NON CONFORME ***"))
print("=" * 78)
out = {"etude": "profil_largeur_branches_circulation",
       "at": datetime.datetime.now().isoformat(timespec="seconds"),
       "fichier_base": os.path.basename(BASE),
       "sha256_base": hashlib.sha256(open(BASE, "rb").read()).hexdigest(),
       "methode": "balayage des suites libres (x et y) sur la rasterisation de l'enveloppe "
                  "complete, maille 0,05 m, niveau z=1,00 m",
       "mesures": reste, "profil_bande": prof, "profil_bras_ouest": bras,
       "profil_bande_nord": nord, "profil_le_long_escalier": esc,
       "geometrie_2d_touchee": False, "STATUS": "MEASURED"}
p = os.path.join(PROJ, "reports", "profil_circulation_v2.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("-> %s" % p)
