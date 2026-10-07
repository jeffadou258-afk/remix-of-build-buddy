#!/usr/bin/env python3
"""ETAPE 2 — VARIANTES EXPERIMENTALES A (circulation centrale) et B (circulation en L).
Construit un .blend SEPARE par variante, puis mesure physiquement les cheminements.
Ne modifie AUCUN fichier officiel."""
import bpy, bmesh, os, json, math, hashlib, datetime, heapq, sys

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BASE = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
LAY = sys.argv[-1] if sys.argv[-1] in ("A", "B") else "A"
OUT = os.path.join(PROJ, "3D", "VARIANT_%s_CIRCULATION.blend" % LAY)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
OFF = 0.20                                   # decalage interieur -> absolu
H_WALL = 3.20
EP = 0.10                                    # epaisseur de cloison
G = 0.05                                     # maille de mesure
IX0, IY0, IX1, IY1 = 0.0, 0.0, 10.40, 10.90
NX, NY = int((IX1 - IX0) / G), int((IY1 - IY0) / G)
DOOR = 1.20
SHA_BASE = hashlib.sha256(open(BASE, "rb").read()).hexdigest()


# ============ DEFINITION DES DEUX IMPLANTATIONS (coordonnees INTERIEURES) ============
# Chaque piece : liste de rectangles (x0,y0,x1,y1) ; aire = somme
DEF = {
 "A": {
   "pieces": {
     "Salon":          [(0, 0, 10, 3.20)],
     "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 1.3636, 6.90)],
     "Cuisine":        [(0, 6.90, 3.333, 10.50)],
     "Bureau":         [(3.333, 6.90, 6.111, 10.50)],
     "Buanderie":      [(6.111, 6.90, 7.778, 10.50)],
     "WC visiteur":    [(8.80, 6.90, 10.00, 9.40)],
   },
   "circulation": [(1.3636, 4.70, 10.00, 6.90), (7.778, 6.90, 8.80, 10.50),
                   (8.80, 9.40, 10.00, 10.50)],
   "escalier": (2.60, 4.70, 7.36, 5.70),
   "entree_y": (4.70, 5.90),
   "portes": [("Salle a manger", "S", 5.20, 6.40),
              ("Cuisine", "S", 1.00, 2.20), ("Bureau", "S", 4.30, 5.50),
              ("Buanderie", "S", 6.30, 7.50), ("WC visiteur", "S", 8.80, 10.00)],
   "porte_salon_est": ("E", 1.3636, 5.20, 6.40),
 },
 "B": {
   "pieces": {
     "Salon":          [(0, 0, 10, 3.20)],
     "Salle a manger": [(0, 3.20, 10, 4.70), (0, 4.70, 3.00, 5.70)],
     "Cuisine":        [(0, 5.70, 3.00, 9.70)],
     "Bureau":         [(3.00, 6.90, 5.778, 10.50)],
     "Buanderie":      [(5.778, 6.90, 7.444, 10.50)],
     "WC visiteur":    [(7.444, 6.90, 8.80, 9.114)],
   },
   "circulation": [(3.00, 4.70, 10.00, 6.90), (8.80, 6.90, 10.00, 10.50),
                   (0, 9.70, 3.00, 10.50), (7.444, 9.114, 8.80, 10.50)],
   "escalier": (3.00, 4.70, 7.76, 5.70),
   "entree_y": (4.70, 5.90),
   "portes": [("Salle a manger", "N", 8.20, 9.40),
              ("Cuisine", "E", 5.70, 6.90), ("Bureau", "S", 3.90, 5.10),
              ("Buanderie", "S", 6.00, 7.20), ("WC visiteur", "S", 7.444, 8.644)],
   "porte_salon_est": None,
 },
}

lay = DEF[LAY]
A_THEO = {n: round(sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in r), 3)
          for n, r in lay["pieces"].items()}
CIRC_THEO = round(sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in lay["circulation"]), 3)
print("=" * 78)
print("VARIANTE %s — implantation theorique" % LAY)
for n, a in A_THEO.items():
    print("   %-16s %6.3f m2" % (n, a))
print("   %-16s %6.3f m2" % ("circulation", CIRC_THEO))
print("   TOTAL pieces %.3f + circulation %.3f = %.3f (cible 105,000)"
      % (sum(A_THEO.values()), CIRC_THEO, sum(A_THEO.values()) + CIRC_THEO))
assert abs(sum(A_THEO.values()) - 81.0) < 0.05, "surfaces de pieces non conformes"
assert abs(sum(A_THEO.values()) + CIRC_THEO - 105.0) < 0.05, "total != 105"


# ============ CONSTRUCTION DANS UN .BLEND SEPARE ============
def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


def box(name, x0, y0, z0, x1, y1, z1):
    m = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(name, m)
    bpy.context.collection.objects.link(o)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return o


def mur_h(y, x0, x1, trous):
    """mur horizontal (le long de x) a l'ordonnee y, avec trous = [(xa,xb)]"""
    segs = [(x0, x1)]
    for (a, b) in trous:
        ns = []
        for (s0, s1) in segs:
            if b <= s0 or a >= s1:
                ns.append((s0, s1)); continue
            if s0 < a: ns.append((s0, a))
            if b < s1: ns.append((b, s1))
        segs = ns
    out = []
    for k, (s0, s1) in enumerate(segs):
        if s1 - s0 < 1e-6: continue
        out.append(box("V%s_MURH_%02d" % (LAY, k), OFF + s0, OFF + y - EP / 2, 0,
                       OFF + s1, OFF + y + EP / 2, H_WALL).name)
    return out


def mur_v(x, y0, y1, trous):
    segs = [(y0, y1)]
    for (a, b) in trous:
        ns = []
        for (s0, s1) in segs:
            if b <= s0 or a >= s1:
                ns.append((s0, s1)); continue
            if s0 < a: ns.append((s0, a))
            if b < s1: ns.append((b, s1))
        segs = ns
    out = []
    for k, (s0, s1) in enumerate(segs):
        if s1 - s0 < 1e-6: continue
        out.append(box("V%s_MURV_%02d" % (LAY, k), OFF + x - EP / 2, OFF + s0, 0,
                       OFF + x + EP / 2, OFF + s1, H_WALL).name)
    return out


bpy.ops.wm.open_mainfile(filepath=BASE)
# 1. supprimer cloisons RDC + escalier + poteaux RDC (geometrie de l'essai)
sup = []
for o in list(bpy.data.objects):
    if o.type != "MESH": continue
    nm = o.name
    if nm.startswith(("CLOISON_RDC", "MARCHE", "PALIER", "POTEAU", "PORTE")):
        sup.append(nm); bpy.data.objects.remove(o, do_unlink=True)
print("objets retires : %d" % len(sup))

# 2. murs de la variante
murs = []
for (nom, cote, a, b) in lay["portes"]:
    pass
trous_sud = []
for (nom, cote, a, b) in lay["portes"]:
    if cote == "S" or cote == "N":
        trous_sud.append((a, b))
# mur de separation couloir / pieces nord : y = 6.90
if LAY == "A":
    murs += mur_h(6.90, 0.0, 10.0, [(a, b) for (_n, c, a, b) in lay["portes"]])
    # limite nord du couloir cote ouest (renfoncement SAM) : x = 1.3636
    murs += mur_v(1.3636, 4.70, 6.90, [(5.20, 6.40)])
    # limite sud du couloir : y = 4.70 de x=1.3636 a 10 avec porte est
    murs += mur_h(4.70, 1.3636, 10.0, [(8.20, 9.40)])
    # cloisons entre pieces nord
    for x in (3.333, 6.111):
        murs += mur_v(x, 6.90, 10.50, [])
    murs += mur_v(7.778, 6.90, 10.50, [])
    murs += mur_v(8.80, 6.90, 10.50, [(6.90, 9.40)])   # facade WC -> couloir
    murs += mur_h(9.40, 8.80, 10.00, [])               # fond du WC
else:
    murs += mur_h(6.90, 0.0, 10.0, [(a, b) for (_n, c, a, b) in lay["portes"]])
    murs += mur_h(4.70, 3.00, 10.0, [(8.20, 9.40)])
    murs += mur_v(3.00, 4.70, 10.50, [(5.70, 6.90)])   # limite ouest couloir + facade cuisine
    murs += mur_v(5.778, 6.90, 10.50, [])
    murs += mur_v(7.444, 6.90, 10.50, [])
    murs += mur_v(8.80, 6.90, 10.50, [])
    murs += mur_h(9.114, 7.444, 8.80, [])
    murs += mur_h(9.70, 0.0, 3.00, [])
# escalier : 17 marches
x0, y0, x1, y1 = lay["escalier"]
n_marches = 17
long_m = x1 - x0
for k in range(n_marches):
    a = x0 + k * long_m / n_marches
    b = x0 + (k + 1) * long_m / n_marches
    h = (k + 1) * H_WALL / n_marches
    box("V%s_MARCHE_%02d" % (LAY, k + 1), OFF + a, OFF + y0, 0, OFF + b, OFF + y1, h)
print("murs construits : %d | escalier : %d marches" % (len(murs), n_marches))

bpy.ops.wm.save_as_mainfile(filepath=OUT)
SHA_OUT = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print("-> %s (%d o, sha %s)" % (os.path.basename(OUT), os.path.getsize(OUT), SHA_OUT[:24]))
print("NB : le .blend officiel %s n'a pas ete modifie (sha %s)"
      % (os.path.basename(BASE), SHA_BASE[:16]))
