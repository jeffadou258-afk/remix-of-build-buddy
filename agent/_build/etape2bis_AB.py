#!/usr/bin/env python3
"""ETAPE 2 — construction + mesure des variantes A (couloir central) et B (couloir en L).
Construit un .blend SEPARE par variante puis mesure physiquement les cheminements.
AUCUN fichier officiel n'est modifie."""
import bpy, bmesh, os, json, math, hashlib, datetime, heapq, sys
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
LAY = sys.argv[-1] if sys.argv[-1] in ("A", "B") else "A"
OUT = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION_V2.blend" % LAY)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
OFF, H_WALL, EP, G = 0.20, 3.20, 0.10, 0.05
IX1, IY1 = 10.40, 10.90
NX, NY = int(IX1 / G), int(IY1 / G)
DOOR = 1.35
SHA_BASE = hashlib.sha256(open(BASE, "rb").read()).hexdigest()

# ================= IMPLANTATIONS (coordonnees INTERIEURES, m) =================
# mur: ("h", y, x0, x1, [(a,b),...])  ou  ("v", x, y0, y1, [(a,b),...])
DEF = {
"A": {
  "pieces": {"Salon": [(0, 0, 10, 3.20)], "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 1.25, 7.10)],
             "Cuisine": [(0, 7.10, 3.5294, 10.50)], "Bureau": [(3.5294, 7.10, 6.4706, 10.50)],
             "Buanderie": [(6.4706, 7.10, 8.2353, 10.50)], "WC visiteur": [(8.50, 7.10, 10.00, 9.10)]},
  "circulation": [(1.25, 4.70, 10.00, 7.10), (8.2353, 7.10, 8.50, 10.50), (8.50, 9.10, 10.00, 10.50)],
  "escalier": (3.00, 4.75, 7.76, 5.75),
  "murs": [("h", 7.10, 0.0, 10.0, [(1.55, 2.90), (4.30, 5.65), (6.65, 8.00), (8.55, 9.95)]),
           ("h", 4.70, 1.25, 10.0, [(8.20, 9.55)]),
           ("v", 1.25, 4.70, 7.10, []),
           ("v", 3.5294, 7.10, 10.50, []), ("v", 6.4706, 7.10, 10.50, []),
           ("v", 8.2353, 7.10, 10.50, []), ("v", 8.50, 7.10, 9.10, []),
           ("h", 9.10, 8.50, 10.00, [])],
  "points": {"Salon": (5.00, 1.60), "Salle a manger": (5.00, 3.95), "Cuisine": (1.76, 8.80),
             "Bureau": (5.00, 8.80), "Buanderie": (7.35, 8.80), "WC visiteur": (9.25, 8.10)},
},
"B": {
  "pieces": {"Salon": [(0, 0, 10, 3.20)], "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 1.25, 7.10)],
             "Cuisine": [(0, 7.10, 3.5294, 10.50)], "Bureau": [(3.5294, 7.10, 6.4706, 10.50)],
             "Buanderie": [(6.4706, 7.10, 8.2353, 10.50)], "WC visiteur": [(8.50, 8.50, 10.00, 10.50)]},
  "circulation": [(1.25, 4.70, 10.00, 7.10), (8.2353, 7.10, 10.00, 8.50), (8.2353, 8.50, 8.50, 10.50)],
  "escalier": (3.00, 4.75, 7.76, 5.75),
  "murs": [("h", 7.10, 0.0, 8.50, [(1.55, 2.90), (4.30, 5.65), (6.65, 8.00)]),
           ("h", 4.70, 1.25, 10.0, [(8.20, 9.55)]),
           ("v", 1.25, 4.70, 7.10, []),
           ("v", 3.5294, 7.10, 10.50, []), ("v", 6.4706, 7.10, 10.50, []),
           ("v", 8.2353, 7.10, 10.50, []), ("h", 8.50, 8.50, 10.00, [(8.60, 9.95)])],
  "points": {"Salon": (5.00, 1.60), "Salle a manger": (5.00, 3.95), "Cuisine": (1.76, 8.80),
             "Bureau": (5.00, 8.80), "Buanderie": (7.35, 8.80), "WC visiteur": (9.25, 9.50)},
},
}
lay = DEF[LAY]
A_THEO = {n: round(sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in r), 3)
          for n, r in lay["pieces"].items()}
CIRC = round(sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in lay["circulation"]), 3)
print("=" * 80)
print("VARIANTE %s" % LAY)
s = sum(A_THEO.values())
for n, a in A_THEO.items():
    print("   %-16s %7.3f m2" % (n, a))
print("   %-16s %7.3f m2" % ("circulation", CIRC))
print("   pieces %.3f + circulation %.3f = %.3f  (cible 105,000)" % (s, CIRC, s + CIRC))
assert abs(s - 81.0) < 0.05 and abs(s + CIRC - 105.0) < 0.05


def box(nm, x0, y0, z0, x1, y1, z1):
    m = bpy.data.meshes.new(nm); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(nm, m); bpy.context.collection.objects.link(o)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return o


def decoupe(a, b, trous):
    segs = [(a, b)]
    for (t0, t1) in trous:
        ns = []
        for (s0, s1) in segs:
            if t1 <= s0 or t0 >= s1: ns.append((s0, s1)); continue
            if s0 < t0: ns.append((s0, t0))
            if t1 < s1: ns.append((t1, s1))
        segs = ns
    return [(s0, s1) for (s0, s1) in segs if s1 - s0 > 1e-6]


bpy.ops.wm.open_mainfile(filepath=BASE)
sup = [o.name for o in list(bpy.data.objects)
       if o.type == "MESH" and o.name.startswith(("CLOISON_RDC", "MARCHE", "PALIER", "POTEAU", "PORTE"))]
for o in list(bpy.data.objects):
    if o.name in sup: bpy.data.objects.remove(o, do_unlink=True)
print("   objets RDC retires : %d" % len(sup))

nb = 0
for (typ, c, a, b, trous) in lay["murs"]:
    for (s0, s1) in decoupe(a, b, trous):
        nb += 1
        if typ == "h":
            box("V%s_MUR_%03d" % (LAY, nb), OFF + s0, OFF + c - EP / 2, 0, OFF + s1, OFF + c + EP / 2, H_WALL)
        else:
            box("V%s_MUR_%03d" % (LAY, nb), OFF + c - EP / 2, OFF + s0, 0, OFF + c + EP / 2, OFF + s1, H_WALL)
x0, y0, x1, y1 = lay["escalier"]
run = x1 - x0
for k in range(17):
    a = x0 + k * run / 17; b = x0 + (k + 1) * run / 17
    box("V%s_MARCHE_%02d" % (LAY, k + 1), OFF + a, OFF + y0, 0, OFF + b, OFF + y1, (k + 1) * H_WALL / 17)
print("   murs : %d troncons | escalier : 17 marches (emprise %.2f x 1,00 m)"
      % (nb, run))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
SHA_OUT = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print("   -> %s (%d o, sha %s)" % (os.path.basename(OUT), os.path.getsize(OUT), SHA_OUT[:24]))

# ================= MESURE PHYSIQUE =================
bpy.ops.wm.open_mainfile(filepath=OUT)
occ = [[False] * NY for _ in range(NX)]
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")): continue
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]   # matrix_world -> tient compte du scale
    x0a = min(c.x for c in cs); y0a = min(c.y for c in cs); z0a = min(c.z for c in cs)
    x1a = max(c.x for c in cs); y1a = max(c.y for c in cs); z1a = max(c.z for c in cs)
    if o.name.startswith("V%s_MARCHE" % LAY):
        z1a = 99.0                       # l'escalier se contourne : plein au-dela du nez
    elif not (z0a - 1e-6 <= 1.0 <= z1a + 1e-6):
        continue
    i0 = max(0, int(math.ceil((x0a) / G - 0.5))); i1 = min(NX, int(math.floor((x1a) / G - 0.5)) + 1)
    j0 = max(0, int(math.ceil((y0a) / G - 0.5))); j1 = min(NY, int(math.floor((y1a) / G - 0.5)) + 1)
    for i in range(i0, i1):
        for j in range(j0, j1):
            occ[i][j] = True
lib = [[not occ[i][j] for j in range(NY)] for i in range(NX)]

INF = 10 ** 9
D = [[0 if not lib[i][j] else INF for j in range(NY)] for i in range(NX)]
for i in range(NX):
    for j in range(NY):
        if D[i][j] == 0: continue
        v = D[i][j]
        if i > 0: v = min(v, D[i - 1][j] + 3)
        if j > 0: v = min(v, D[i][j - 1] + 3)
        if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + 4)
        if i > 0 and j + 1 < NY: v = min(v, D[i - 1][j + 1] + 4)
        D[i][j] = v
for i in range(NX - 1, -1, -1):
    for j in range(NY - 1, -1, -1):
        if D[i][j] == 0: continue
        v = D[i][j]
        if i + 1 < NX: v = min(v, D[i + 1][j] + 3)
        if j + 1 < NY: v = min(v, D[i][j + 1] + 3)
        if i + 1 < NX and j + 1 < NY: v = min(v, D[i + 1][j + 1] + 4)
        if i + 1 < NX and j > 0: v = min(v, D[i + 1][j - 1] + 4)
        D[i][j] = v
# porte d'entree : mur EST, y interieur [4.70 ; 5.90] -> point a clearance MAXIMALE
best_e, bd_e = None, -1
for i in range(NX):
    x = i * G
    if x < 9.80 or x > 10.16: continue
    for j in range(int((OFF + 4.75) / G), int((OFF + 5.85) / G)):
        if lib[i][j] and D[i][j] > bd_e:
            bd_e, best_e = D[i][j], (i, j)
ent = best_e
print("   porte d'entree : x=%.2f y=%.2f (clearance %.2f m -> largeur %.2f m)"
      % (ent[0] * G, ent[1] * G, bd_e / 3.0 * G, bd_e / 3.0 * G * 2))
bn = [[-1] * NY for _ in range(NX)]
bn[ent[0]][ent[1]] = D[ent[0]][ent[1]]
pq = [(-D[ent[0]][ent[1]], ent[0], ent[1])]
while pq:
    neg, i, j = heapq.heappop(pq)
    c = -neg
    if c < bn[i][j]: continue
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ni, nj = i + di, j + dj
        if 0 <= ni < NX and 0 <= nj < NY and lib[ni][nj]:
            nc = min(c, D[ni][nj])
            if nc > bn[ni][nj]:
                bn[ni][nj] = nc; heapq.heappush(pq, (-nc, ni, nj))

print("\n   MESURE DES CHEMINEMENTS (piece = obstacle plein ; mesure jusqu'a la porte)")
res = {}
for nom, (px, py) in lay["points"].items():
    i = min(NX - 1, int((OFF + px) / G)); j = min(NY - 1, int((OFF + py) / G))
    v = bn[i][j]
    w = None if v < 0 else round(v / 3.0 * G * 2, 2)
    surf_theo = A_THEO[nom]
    res[nom] = {"surface_theorique_m2": surf_theo, "largeur_chemin_m": w,
                "porte_m": DOOR, "accessible_120": bool(w is not None and w >= 1.20)}
    print("     %-16s surf %7.3f m2 | chemin %s m | porte %.2f m | %s"
          % (nom, surf_theo, ("%.2f" % w) if w else "AUCUN", DOOR,
             "CONFORME" if (w and w >= 1.20) else "*** NON CONFORME ***"))
# largeur du couloir au droit de l'escalier
esc_prof = []
x0e, y0e, x1e, y1e = lay["escalier"]
for k in range(int((x0e + OFF) / G), int((x1e + OFF) / G) + 1):
    j = int((OFF + 7.10 - 0.05 - 0.005) / G); n = 0   # au ras de la face du mur nord
    while j >= 0 and not occ[k][j]:
        n += 1; j -= 1
    esc_prof.append(round(n * G, 3))
lg_esc = min(esc_prof) if esc_prof else 0.0
print("     %-16s passage le long de l'escalier : %.2f m" % ("(escalier)", lg_esc))
ok_all = all(d["accessible_120"] for d in res.values()) and lg_esc >= 1.20
print("\n   >> VARIANTE %s : %s" % (LAY, "ADMISSIBLE (techniquement)" if ok_all else "NON ADMISSIBLE"))

os.makedirs(os.path.join(PROJ, "reports"), exist_ok=True)
rap = {"etude": "etape2bis_variantes_AB_V2", "at": STAMP,
       "variante": LAY, "description": "circulation centrale" if LAY == "A" else "circulation en L",
       "fichier": os.path.basename(OUT), "sha256": SHA_OUT,
       "bim_officiel_reference": os.path.basename(BASE), "sha256_reference": SHA_BASE,
       "surfaces_theoriques": A_THEO, "circulation_m2": CIRC,
       "escalier": {"emprise_m": [round(v, 2) for v in lay["escalier"]], "marches": 17,
                    "passage_le_long_m": lg_esc},
       "portes_m": DOOR, "mesures": res,
       "ADMISSIBLE": bool(ok_all),
       "regles": {"plan_VALIDATED_modifie": False, "bim_officiel_modifie": False,
                  "metre_modifie": False, "budget_modifie": False, "phase8_lancee": False}}
p = os.path.join(PROJ, "reports", "variante_%s_mesure_V2.json" % LAY)
json.dump(rap, open(p, "w"), indent=2, ensure_ascii=False)
print("   -> %s" % p)
