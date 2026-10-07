#!/usr/bin/env python3
"""PHASE 4 — BIM COMPLET : ouvertures (portes/fenetres), escalier, toiture, materiaux.
Part de la geometrie VALIDATED. Produit un NOUVEAU .blend (les precedents restent intacts)."""
import bpy, os, json, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
OUT = os.path.join(PROJ, "3D", "BIM_villa_R1_COMPLET_v2.blend")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")

fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
lock = json.load(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json")))
sc = json.load(open(os.path.join(PROJ, "structure", "structural_concept.json")))
assert lock["STATUS"] == "VALIDATED"

EB_X, EB_Y, TE = 10.40, 10.90, 0.20
IX0, IY0, IX1, IY1 = TE, TE, EB_X - TE, EB_Y - TE
H_RDC, H_ETG = 3.20, 3.20
E_DALLE, B_POT, H_POT = 0.15, 0.30, 0.30
B_POU, H_POU, E_CLOISON = 0.25, 0.35, 0.10
PATIO = (7.20, 6.70, 10.20, 10.70)
ANC, SEM, H_SEM, E_LONG = 0.80, 1.20, 0.25, 0.30
Z_RDC, Z_ETG, Z_ROOF = 0.00, 3.20, 6.40
Z_SEM_TOP, Z_LONG_TOP = -ANC, -0.45
ACRO_H, ACRO_E = 1.00, 0.15
H_PORTE, H_FEN, L_FEN = 2.10, 1.20, 0.90
SEUIL_FEN = 0.90
H_ETANCHE, E_FORME = 0.02, 0.075

print("=" * 78); print("PHASE 4 — BIM COMPLET (materiaux, portes, fenetres, escalier, toiture)")
print("geometrie source : %s (VALIDATED)" % lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"][:16])
print("=" * 78)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
MATS = {}


def mat(n, rgb, rough=0.9):
    m = bpy.data.materials.new(n); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    MATS[n] = m; return m


M_BETON = mat("Beton_arme", (0.62, 0.62, 0.60))
M_MAÇON = mat("Agglos_15_creux", (0.85, 0.78, 0.66))
M_DALLE = mat("Dallage", (0.72, 0.72, 0.70))
M_FOND = mat("Fondation", (0.52, 0.50, 0.48))
M_PATIO = mat("Revetement_exterieur", (0.80, 0.74, 0.58))
M_ALU = mat("Menuiserie_aluminium", (0.75, 0.78, 0.82), 0.4)
M_BOIS = mat("Menuiserie_bois", (0.55, 0.36, 0.20))
M_ESC = mat("Escalier_BA", (0.68, 0.68, 0.66))
M_TOIT = mat("Etancheite_toiture", (0.35, 0.35, 0.38), 0.6)
M_GARDE = mat("Garde_corps_metal", (0.45, 0.46, 0.48), 0.5)

OBJ = []


def box(name, x0, y0, z0, x1, y1, z1, m, group):
    if x1 - x0 < 0.005 or y1 - y0 < 0.005 or z1 - z0 < 0.005:
        return None
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    bpy.context.collection.objects.link(ob)
    OBJ.append({"name": name, "group": group, "mat": m.name,
                "vol_m3": round((x1 - x0) * (y1 - y0) * (z1 - z0), 5)})
    return ob


def wall(name, axis, fixed, a0, a1, z0, z1, e, m, group):
    if axis == "H":
        box(name, a0, fixed - e / 2, z0, a1, fixed + e / 2, z1, m, group)
    else:
        box(name, fixed - e / 2, a0, z0, fixed + e / 2, a1, z1, m, group)


def wall_ouvertures(name, axis, fixed, a0, a1, z0, z1, e, m, group, ouv=None):
    """Mur avec ouvertures : (d0, d1, zbas, zhaut) le long de l'axe."""
    ouv = sorted(ouv or [])
    parts, cur = [], a0
    for (d0, d1, zb, zh) in ouv:
        d0, d1 = max(d0, a0), min(d1, a1)
        if d1 - d0 < 0.02:
            continue
        if d0 > cur + 0.005:
            parts.append((cur, d0, z0, z1))
        if zb > z0 + 0.005:
            parts.append((d0, d1, z0, zb))          # allege sous linteau
        if zh < z1 - 0.005:
            parts.append((d0, d1, zh, z1))          # linteau
        cur = d1
    if cur < a1 - 0.005:
        parts.append((cur, a1, z0, z1))
    for i, (b0, b1, zz0, zz1) in enumerate(parts, 1):
        wall("%s_p%02d" % (name, i), axis, fixed, b0, b1, zz0, zz1, e, m, group)


# ================= 1. FONDATIONS =================
for c in sc["poteaux"]:
    cx, cy = IX0 + c["x"], IY0 + c["y"]
    s = SEM / 2
    box("SEMELLE_%s" % c["ref"], cx - s, cy - s, Z_SEM_TOP - H_SEM, cx + s, cy + s, Z_SEM_TOP,
        M_FOND, "FONDATION")
NX = [IX0 + v for v in sc["trame"]["X"]]
NY = [IY0 + v for v in sc["trame"]["Y"]]
for y in NY:
    wall("LONGRINE_Y_%.2f" % y, "H", y, IX0, IX1, Z_LONG_TOP - E_LONG, Z_LONG_TOP, TE,
         M_FOND, "FONDATION")
for x in NX:
    wall("LONGRINE_X_%.2f" % x, "V", x, IY0, IY1, Z_LONG_TOP - E_LONG, Z_LONG_TOP, TE,
         M_FOND, "FONDATION")

# ================= 2. POTEAUX =================
_px0, _py0, _px1, _py1 = PATIO
Z_POT_TOP = Z_ROOF - E_DALLE
pot_patio = []
for c in sc["poteaux"]:
    cx, cy = IX0 + c["x"], IY0 + c["y"]
    if _px0 - 1e-6 <= cx <= _px1 + 1e-6 and _py0 - 1e-6 <= cy <= _py1 + 1e-6:
        ztop = Z_ETG; pot_patio.append(c["ref"])
    else:
        ztop = Z_POT_TOP
    box("POTEAU_%s" % c["ref"], cx - B_POT / 2, cy - B_POT / 2, Z_SEM_TOP,
        cx + B_POT / 2, cy + B_POT / 2, ztop, M_BETON, "STRUCTURE")
print("  poteaux arretes au niveau etage (patio) : %s" % (pot_patio or "aucun"))

# ================= 3. POUTRES =================
for lvl, ztop in (("N1", Z_ETG - E_DALLE), ("N2", Z_ROOF - E_DALLE)):
    for y in NY:
        if lvl == "N2" and y > _py0 + 1e-6:
            wall("POUTRE_%s_Y_%.2f" % (lvl, y), "H", y, IX0 - B_POT / 2, _px0,
                 ztop - H_POU, ztop, B_POU, M_BETON, "STRUCTURE")
        else:
            wall("POUTRE_%s_Y_%.2f" % (lvl, y), "H", y, IX0 - B_POT / 2, IX1 + B_POT / 2,
                 ztop - H_POU, ztop, B_POU, M_BETON, "STRUCTURE")
    for x in NX:
        if lvl == "N2" and x > _px0 + 1e-6:
            wall("POUTRE_%s_X_%.2f" % (lvl, x), "V", x, IY0 - B_POT / 2, _py0,
                 ztop - H_POU, ztop, B_POU, M_BETON, "STRUCTURE")
        else:
            wall("POUTRE_%s_X_%.2f" % (lvl, x), "V", x, IY0 - B_POT / 2, IY1 + B_POT / 2,
                 ztop - H_POU, ztop, B_POU, M_BETON, "STRUCTURE")

# ================= 4. DALLES + TOITURE =================
box("DALLAGE_RDC", 0.0, 0.0, Z_RDC - E_DALLE, EB_X, EB_Y, Z_RDC, M_DALLE, "DALLE")
box("DALLE_ETAGE", 0.0, 0.0, Z_ETG - E_DALLE, EB_X, EB_Y, Z_ETG, M_DALLE, "DALLE")
box("DALLE_TOIT_1", 0.0, 0.0, Z_ROOF - E_DALLE, EB_X, _py0, Z_ROOF, M_BETON, "DALLE")
box("DALLE_TOIT_2", 0.0, _py0, Z_ROOF - E_DALLE, _px0, EB_Y, Z_ROOF, M_BETON, "DALLE")
# toiture : forme de pente + etancheite (couches conceptuelles, aire toiture mesuree)
roof_cells = (EB_X * _py0) + (_px0 * (EB_Y - _py0))
box("FORME_PENTE", 0.02, 0.02, Z_ROOF, EB_X - 0.02, _py0 - 0.02, Z_ROOF + E_FORME, M_BETON,
    "TOITURE")
box("FORME_PENTE_2", 0.02, _py0, Z_ROOF, _px0 - 0.02, EB_Y - 0.02, Z_ROOF + E_FORME, M_BETON,
    "TOITURE")
box("ETANCHEITE", 0.0, 0.0, Z_ROOF + E_FORME, EB_X, _py0, Z_ROOF + E_FORME + H_ETANCHE,
    M_TOIT, "TOITURE")
box("ETANCHEITE_2", 0.0, _py0, Z_ROOF + E_FORME, _px0, EB_Y, Z_ROOF + E_FORME + H_ETANCHE,
    M_TOIT, "TOITURE")
print("  aire de toiture : %.2f m2 (emprise hors patio)" % roof_cells)

# ================= 5. MURS EXTERIEURS AVEC OUVERTURES =================
def rooms_on_facade(rooms, side, coord):
    """Pieces touchent la facade : side in (S,N,O,E)."""
    out = []
    for r in rooms:
        x, y = IX0 + r["x_m"], IY0 + r["y_m"]
        w, d = r["w_m"], r["d_m"]
        if side in ("S", "N"):
            c = y if side == "S" else y + d
            if abs(c - coord) < 0.02:
                out.append((x, x + w, r["name"], w))
        else:
            c = x if side == "O" else x + w
            if abs(c - coord) < 0.02:
                out.append((y, y + d, r["name"], d))
    return sorted(out)


def fenetres(facade, z0, z1):
    """1 fenetre par piece sur la facade, largeur = 55% du nu, plafonnee."""
    ouv = []
    for (a0, a1, nom, nu) in facade:
        L = min(max(0.60, round(nu * 0.55, 2)), 2.40)
        c = (a0 + a1) / 2
        ouv.append((c - L / 2, c + L / 2, z0 + SEUIL_FEN, z0 + SEUIL_FEN + H_FEN))
    return ouv


rdc_rooms = fp["RDC"]["rooms"]
etg_rooms = fp["ETAGE"]["rooms"]
F_RDC = {"S": rooms_on_facade(rdc_rooms, "S", IY0), "N": rooms_on_facade(rdc_rooms, "N", IY1),
         "O": rooms_on_facade(rdc_rooms, "O", IX0), "E": rooms_on_facade(rdc_rooms, "E", IX1)}
F_ETG = {"S": rooms_on_facade(etg_rooms, "S", IY0), "N": rooms_on_facade(etg_rooms, "N", IY1),
         "O": rooms_on_facade(etg_rooms, "O", IX0), "E": rooms_on_facade(etg_rooms, "E", IX1)}
print("\n  RDC pieces par facade :", {k: [r[2] for r in v] for k, v in F_RDC.items()})
print("  ETG pieces par facade :", {k: [r[2] for r in v] for k, v in F_ETG.items()})

nb_fen = 0
# --- position de la porte d'entree : calculee AVANT de construire les murs ---
occ = set()
for r in rdc_rooms:
    for i in range(int(round(r["w_m"] / 0.5))):
        for j in range(int(round(r["d_m"] / 0.5))):
            occ.add((round(IX0 + r["x_m"] + i * 0.5, 2), round(IY0 + r["y_m"] + j * 0.5, 2)))
libre = [(round(x * 0.5, 2), round(y * 0.5, 2)) for y in range(int(round(10.5 / 0.5)) + 1)
         for x in range(int(round(10.0 / 0.5)) + 1)
         if (round(IX0 + x * 0.5, 2), round(IY0 + y * 0.5, 2)) not in occ]
cx_m, cy_m = (IX0 + IX1) / 2, (IY0 + IY1) / 2
bord = [p for p in libre if min(p[0] - IX0, p[1] - IY0, IX1 - p[0], IY1 - p[1]) < 0.6]
porte = min(bord, key=lambda p: (p[0] - cx_m) ** 2 + (p[1] - cy_m) ** 2)
D_POR = 1.20
if abs(porte[1] - IY0) < 0.6:
    face_p, c_door = "S", porte[0]
elif abs(porte[0] - IX0) < 0.6:
    face_p, c_door = "O", porte[1]
elif abs(porte[1] - IY1) < 0.6:
    face_p, c_door = "N", porte[0]
else:
    face_p, c_door = "E", porte[1]
position_porte = "facade %s, %.2f m" % ({"S": "SUD x=", "N": "NORD x=", "O": "OUEST y=",
                                         "E": "EST y="}[face_p], c_door)
ouv_door = (c_door - D_POR / 2, c_door + D_POR / 2, 0.0, H_PORTE)

# --- chaque facade est construite UNE SEULE FOIS, avec fenetres + porte eventuelle ---
for lvl, F, z0, z1 in (("RDC", F_RDC, 0.0, H_RDC), ("ETG", F_ETG, H_RDC, Z_ROOF)):
    ovS = list(fenetres(F["S"], z0, z1)); nb_fen += len(ovS)
    ovO = list(fenetres(F["O"], z0, z1)); nb_fen += len(ovO)
    if lvl == "RDC" and face_p == "S":
        ovS.append((ouv_door[0], ouv_door[1], z0, z0 + H_PORTE))
    if lvl == "RDC" and face_p == "O":
        ovO.append((ouv_door[0], ouv_door[1], z0, z0 + H_PORTE))
    wall_ouvertures("MUR_S_%s" % lvl, "H", 0.10, 0.0, EB_X, z0, z1, TE, M_MAÇON, "MUR_EXT", ovS)
    wall_ouvertures("MUR_O_%s" % lvl, "V", 0.10, 0.0, EB_Y, z0, z1, TE, M_MAÇON, "MUR_EXT", ovO)
    if lvl == "RDC":
        ovN = list(fenetres(F["N"], z0, z1)); nb_fen += len(ovN)
        ovE = list(fenetres(F["E"], z0, z1)); nb_fen += len(ovE)
        if face_p == "N":
            ovN.append((ouv_door[0], ouv_door[1], z0, z0 + H_PORTE))
        if face_p == "E":
            ovE.append((ouv_door[0], ouv_door[1], z0, z0 + H_PORTE))
        wall_ouvertures("MUR_N_%s" % lvl, "H", EB_Y - 0.10, 0.0, EB_X, z0, z1, TE, M_MAÇON,
                        "MUR_EXT", ovN)
        wall_ouvertures("MUR_E_%s" % lvl, "V", EB_X - 0.10, 0.0, EB_Y, z0, z1, TE, M_MAÇON,
                        "MUR_EXT", ovE)
    else:
        ovN = list(fenetres(F["N"], z0, z1)); nb_fen += len(ovN)
        ovE = list(fenetres(F["E"], z0, z1)); nb_fen += len(ovE)
        wall_ouvertures("MUR_N_%s" % lvl, "H", EB_Y - 0.10, 0.0, _px0, z0, z1, TE, M_MAÇON,
                        "MUR_EXT", ovN)
        wall_ouvertures("MUR_E_%s" % lvl, "V", EB_X - 0.10, 0.0, _py0, z0, z1, TE, M_MAÇON,
                        "MUR_EXT", ovE)
        wall("MUR_PATIO_S", "H", _py0 + 0.10, _px0 - TE, EB_X, z0, z1, TE, M_MAÇON, "MUR_EXT")
        wall("MUR_PATIO_O", "V", _px0 + 0.10, _py0, EB_Y, z0, z1, TE, M_MAÇON, "MUR_EXT")
print("  fenetres creees : %d" % nb_fen)
print("  porte d'entree 1,20 x 2,10 : %s" % position_porte)

# ================= 6. CLOISONS AVEC PORTES =================
OPEN_PAIRS = [("Salon", "Salle à manger")]


def partitions(rooms, z0, z1, suffix, patio=None):
    segs = {}
    for r in rooms:
        x, y = IX0 + r["x_m"], IY0 + r["y_m"]
        w, d = r["w_m"], r["d_m"]
        for e in (("H", round(y, 3), round(x, 3), round(x + w, 3)),
                  ("H", round(y + d, 3), round(x, 3), round(x + w, 3)),
                  ("V", round(x, 3), round(y, 3), round(y + d, 3)),
                  ("V", round(x + w, 3), round(y, 3), round(y + d, 3))):
            segs.setdefault(e, []).append(r["name"])
    out = []
    for (ax, fixed, a0, a1), owners in segs.items():
        if ax == "H" and (abs(fixed - IY0) < 0.01 or abs(fixed - IY1) < 0.01):
            continue
        if ax == "V" and (abs(fixed - IX0) < 0.01 or abs(fixed - IX1) < 0.01):
            continue
        if any(sorted([owners[0], o]) in [sorted(p) for p in OPEN_PAIRS] for o in owners[1:]):
            continue
        parts = [(a0, a1)]
        if patio:
            pxc0, pyc0, pxc1, pyc1 = patio
            if ax == "H" and (abs(fixed - pyc0) < 0.01 or abs(fixed - pyc1) < 0.01):
                parts = []
                if a0 < pxc0 - 0.01:
                    parts.append((a0, min(a1, pxc0)))
                if a1 > pxc1 + 0.01:
                    parts.append((max(a0, pxc1), a1))
            elif ax == "V" and (abs(fixed - pxc0) < 0.01 or abs(fixed - pxc1) < 0.01):
                parts = []
                if a0 < pyc0 - 0.01:
                    parts.append((a0, min(a1, pyc0)))
                if a1 > pyc1 + 0.01:
                    parts.append((max(a0, pyc1), a1))
            else:
                dedans = ((ax == "H" and pxc0 - 0.01 <= a0 and a1 <= pxc1 + 0.01
                           and pyc0 - 0.01 <= fixed <= pyc1 + 0.01) or
                          (ax == "V" and pyc0 - 0.01 <= a0 and a1 <= pyc1 + 0.01
                           and pxc0 - 0.01 <= fixed <= pxc1 + 0.01))
                if dedans:
                    parts = []
        for (b0, b1) in parts:
            if b1 - b0 > 0.01:
                out.append((ax, fixed, b0, b1))
    nd = 0
    for i, (ax, fixed, a0, a1) in enumerate(out, 1):
        Ld = min(0.90, max(0.60, (a1 - a0) * 0.35))
        c = (a0 + a1) / 2
        ouv = [(c - Ld / 2, c + Ld / 2, z0, z0 + H_PORTE)] if (a1 - a0) >= 1.20 else []
        if ouv:
            nd += 1
        wall_ouvertures("CLOISON_%s_%02d" % (suffix, i), ax, fixed, a0, a1, z0, z1,
                        E_CLOISON, M_MAÇON, "CLOISON", ouv)
    return len(out), nd


n_rdc, d_rdc = partitions(rdc_rooms, 0.0, H_RDC, "RDC")
n_etg, d_etg = partitions(etg_rooms, H_RDC, Z_ROOF, "ETG", patio=PATIO)
print("  cloisons : RDC %d (%d portes) | etage %d (%d portes)" % (n_rdc, d_rdc, n_etg, d_etg))

# ================= 7. ESCALIER =================
n_m = 18
h_m = H_RDC / n_m
g_m = 0.28
RUN = (n_m - 1) * g_m                       # 4,76 m pour une volee droite
S = 0.5                                     # maille de recherche
NXc, NYc = int(10.0 / S), int(10.5 / S)
occ = [[0] * (NYc + 1) for _ in range(NXc + 1)]
for r in rdc_rooms:
    for i in range(int(round(r["w_m"] / S))):
        for j in range(int(round(r["d_m"] / S))):
            occ[int(round(r["x_m"] / S)) + i][int(round(r["y_m"] / S)) + j] = 1
P = [[0] * (NYc + 2) for _ in range(NXc + 2)]      # sommes prefixees
for i in range(NXc):
    for j in range(NYc):
        P[i + 1][j + 1] = P[i][j + 1] + P[i + 1][j] - P[i][j] + occ[i][j]


def libre(x0, y0, w, h):
    return (P[x0 + w][y0 + h] - P[x0][y0 + h] - P[x0 + w][y0] + P[x0][y0]) == 0


gmax = (0, None)                                   # plus grand rectangle libre (info)
for w in range(1, NXc + 1):
    for h in range(1, NYc + 1):
        for x0 in range(NXc - w + 1):
            for y0 in range(NYc - h + 1):
                if w * h > gmax[0] and libre(x0, y0, w, h):
                    gmax = (w * h, (x0, y0, w, h))
print("\n  plus grande zone libre RDC : %.2f x %.2f m (%.2f m2)"
      % (gmax[1][2] * S, gmax[1][3] * S, gmax[0] * S * S))

# (a) volee droite : run >= 4,76 m (10 cellules) et largeur >= 1,00 m (2 cellules)
best_d = None
for w in range(int(math.ceil(RUN / S)), NXc + 1):
    for h in range(2, 5):
        for x0 in range(NXc - w + 1):
            for y0 in range(NYc - h + 1):
                if libre(x0, y0, w, h):
                    aire = w * h
                    if best_d is None or aire > best_d[4]:
                        best_d = (x0, y0, w, h, aire)
# (b) escalier a 2 volees + palier : emprise 2,70 x 2,40 m (6 x 5 cellules)
best_t = None
for w in range(6, NXc + 1):
    for h in range(5, 7):
        for x0 in range(NXc - w + 1):
            for y0 in range(NYc - h + 1):
                if libre(x0, y0, w, h):
                    aire = w * h
                    if best_t is None or aire > best_t[4]:
                        best_t = (x0, y0, w, h, aire)
print("  candidat volee droite (>= %.2f x 1,00 m) : %s"
      % (RUN, "%.2f x %.2f m a (%.2f, %.2f)" % (best_d[2] * S, best_d[3] * S,
                                                 best_d[0] * S, best_d[1] * S) if best_d else "AUCUN"))
print("  candidat 2 volees + palier (2,70 x 2,40 m) : %s"
      % ("%.2f x %.2f m a (%.2f, %.2f)" % (best_t[2] * S, best_t[3] * S,
                                           best_t[0] * S, best_t[1] * S) if best_t else "AUCUN"))

esc_info = {"nb_marches": n_m, "hauteur_marche_m": round(h_m, 3), "giron_m": g_m,
            "largeur_m": 1.00, "position": None, "type": None, "emprise_m": None,
            "plus_grande_zone_libre_m": "%.2f x %.2f" % (gmax[1][2] * S, gmax[1][3] * S)}
if best_d:
    x0, y0 = IX0 + best_d[0] * S, IY0 + best_d[1] * S
    W = min(best_d[3] * S, 2.0)
    RUN = (n_m - 1) * g_m                   # 17 girons = 4,76 m (18 montees)
    for i in range(n_m - 1):                # 17 marches visibles (la 18e montee = plancher etage)
        z = (i + 1) * h_m
        xa = x0 + g_m * i
        xb = x0 + g_m * (i + 1)
        box("MARCHE_%02d" % (i + 1), xa, y0, max(0.0, z - h_m * 1.4), xb, y0 + 1.00, z,
            M_ESC, "ESCALIER")
    # tremie d'escalier dans la dalle d'etage : NON MODELEE (a ajouter)
    esc_info.update({"type": "volee droite %d montees / %d marches (h=%.3f m, g=%.2f m)"
                             % (n_m, n_m - 1, h_m, g_m),
                     "position": "x=%.2f y=%.2f (origine interieure)" % (x0, y0),
                     "emprise_m": "%.2f x 1.00" % RUN,
                     "tremie_dalle_etage": "NON MODELEE",
                     "longueur_totale_m": round(RUN, 3)})
    print("  >>> ESCALIER : %d marches, emprise %.2f x 1,00 m a (%.2f, %.2f)"
          % (n_m - 1, RUN, x0, y0))
else:
    esc_info["STATUS"] = ("BLOCKED — aucune zone libre de %.2f x 1,00 m dans la circulation RDC "
                          "(plus grande zone : %s)" % (RUN, esc_info["plus_grande_zone_libre_m"]))
    print("  >>> ESCALIER : BLOCKED")

# ================= 8. ACROTERE + GARDE-CORPS =================
for nm, ax, fx, a0, a1 in (("ACRO_S", "H", 0.10, 0.0, EB_X), ("ACRO_N", "H", EB_Y - 0.10, 0.0, _px0),
                           ("ACRO_O", "V", 0.10, 0.0, EB_Y), ("ACRO_E", "V", EB_X - 0.10, 0.0, _py0)):
    wall(nm, ax, fx, a0, a1, Z_ROOF, Z_ROOF + ACRO_H, ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_PATIO_S", "H", _py0 + 0.05, _px0 - ACRO_E, EB_X, Z_ROOF, Z_ROOF + ACRO_H, ACRO_E,
     M_BETON, "ACROTERE")
wall("ACRO_PATIO_O", "V", _px0 + 0.05, _py0, EB_Y, Z_ROOF, Z_ROOF + ACRO_H, ACRO_E, M_BETON,
     "ACROTERE")
wall("GARDE_PATIO_E", "V", EB_X - 0.05, _py0, EB_Y, Z_ETG, Z_ETG + 1.00, 0.05, M_GARDE,
     "GARDE_CORPS")
wall("GARDE_PATIO_N", "H", EB_Y - 0.05, _px0, EB_X, Z_ETG, Z_ETG + 1.00, 0.05, M_GARDE,
     "GARDE_CORPS")
if best_d:
    xg = IX0 + best_d[0] * S
    wall("GARDE_ESCALIER", "H", IY0 + best_d[1] * S + 1.00, xg, xg + RUN, 0.0, H_RDC, 0.05,
         M_GARDE, "GARDE_CORPS")

# ================= 9. SOL + PATIO =================
box("SOL_TERRAIN", -3.0, -3.0, -1.30, EB_X + 3.0, EB_Y + 3.0, -1.25, M_PATIO, "SITE")
box("TERRASSE_PATIO", _px0 - TE + 0.02, _py0 - TE + 0.02, Z_ETG - 0.05, _px1 + TE, _py1 + TE,
    Z_ETG + 0.02, M_PATIO, "SITE")

# ================= 10. SAUVEGARDE + STATS =================
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
grp = {}
for o in OBJ:
    g = grp.setdefault(o["group"], {"nb": 0, "vol_m3": 0.0, "mats": set()})
    g["nb"] += 1
    g["vol_m3"] += o["vol_m3"]
    g["mats"].add(o["mat"])
xs = []
ys = []
zs = []
for o in bpy.data.objects:
    if o.type == "MESH":
        for v in o.data.vertices:
            xs.append(v.co.x); ys.append(v.co.y); zs.append(v.co.z)
stats = {"at": STAMP, "blender": bpy.app.version_string, "fichier": os.path.basename(OUT),
         "octets": os.path.getsize(OUT), "objets": len([o for o in bpy.data.objects if o.type == "MESH"]),
         "groupes": {k: {"nb": v["nb"], "volume_m3": round(v["vol_m3"], 3),
                         "materiaux": sorted(v["mats"])} for k, v in sorted(grp.items())},
         "bbox_m": {"x": [round(min(xs), 2), round(max(xs), 2)],
                    "y": [round(min(ys), 2), round(max(ys), 2)],
                    "z": [round(min(zs), 2), round(max(zs), 2)]},
         "ouvertures": {"fenetres": nb_fen, "porte_entree": position_porte,
                        "portes_interieures": d_rdc + d_etg},
         "escalier": esc_info,
         "toiture": {"type": "toiture-terrasse accessible + forme de pente + etancheite",
                     "aire_m2": round(roof_cells, 2), "forme_pente_m": E_FORME,
                     "etancheite_m": H_ETANCHE, "acrotere_m": ACRO_H},
         "geometrie_source": {"file": "floor_plan.json",
                              "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"],
                              "statut": "VALIDATED"},
         "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
p_st = os.path.join(PROJ, "3D", "bim_complet_stats.json")
json.dump(stats, open(p_st, "w"), indent=2, ensure_ascii=False)
print("\n  .blend -> %s (%d octets) | %d objets" % (OUT, os.path.getsize(OUT), stats["objets"]))
for k, v in stats["groupes"].items():
    print("    %-12s %3d obj  %9.3f m3" % (k, v["nb"], v["volume_m3"]))
print("STATS -> %s" % p_st)
print("STATUS : %s" % stats["STATUS"])
