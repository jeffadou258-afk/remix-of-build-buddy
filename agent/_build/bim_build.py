#!/usr/bin/env python3
"""PHASE 2 — BIM / MODELE 3D. Construit le modele depuis la geometrie VALIDATED.
Ne touche JAMAIS a scene_villa_conceptuelle.blend (ancien modele conceptuel)."""
import bpy, os, json, math, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
OUT = os.path.join(PROJ, "3D", "BIM_villa_R1_VALIDATED.blend")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")

fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
lock = json.load(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json")))
sc = json.load(open(os.path.join(PROJ, "structure", "structural_concept.json")))

# ---- parametres (issus de la geometrie verrouillee + phase 1) ----
EB_X, EB_Y = 10.40, 10.90
TE = 0.20                       # mur exterieur
IX0, IY0 = TE, TE
IX1, IY1 = EB_X - TE, EB_Y - TE          # 10.20, 10.70  (interieur)
H_RDC, H_ETG = 3.20, 3.20
E_DALLE = 0.15
B_POT = H_POT = 0.30
B_POU, H_POU = 0.25, 0.35
E_CLOISON = 0.10
PATIO = (7.20, 6.70, 10.20, 10.70)       # absolu, coin NE
ANC = 0.80                               # HYPOTHESIS : ancrage des fondations
SEM = 1.20                               # semelle 1,20 x 1,20 (portance 0,15 MPa HYPOTHESE)
H_SEM, E_LONG = 0.25, 0.30
Z_RDC_FF, Z_ETG_FF, Z_ROOF_FF = 0.00, H_RDC, H_RDC + H_ETG     # 0 / 3,20 / 6,40
Z_SEM_TOP = -ANC
Z_LONG_TOP = -0.45
ACRO_H, ACRO_E = 1.00, 0.15

print("=" * 78)
print("PHASE 2 — BIM / MODELE 3D")
print("geometrie source : floor_plan.json %s (VALIDATED)"
      % lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"][:16] + "…")
print("=" * 78)

# ---- scene vierge ----
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

MATS = {}


def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = 0.9
    MATS[name] = m
    return m


M_BETON = mat("Beton_arme", (0.62, 0.62, 0.60))
M_MAÇON = mat("Maconnerie", (0.85, 0.78, 0.66))
M_DALLE = mat("Dallage", (0.72, 0.72, 0.70))
M_FOND = mat("Fondation", (0.52, 0.50, 0.48))
M_PATIO = mat("Patio_exterieur", (0.80, 0.74, 0.58))

OBJ = []


def box(name, x0, y0, z0, x1, y1, z1, m, group):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(m)
    bpy.context.collection.objects.link(ob)
    OBJ.append({"name": name, "group": group,
                "vol_m3": round((x1 - x0) * (y1 - y0) * (z1 - z0), 4)})
    return ob


def wall(name, axis, fixed, a0, a1, z0, z1, e, m, group):
    if axis == "H":
        box(name, a0, fixed - e / 2, z0, a1, fixed + e / 2, z1, m, group)
    else:
        box(name, fixed - e / 2, a0, z0, fixed + e / 2, a1, z1, m, group)


# ---- 1. FONDATIONS ----
for c in sc["poteaux"]:
    cx, cy = IX0 + c["x"], IY0 + c["y"]
    s = SEM / 2
    box("SEMELLE_%s" % c["ref"], cx - s, cy - s, Z_SEM_TOP - H_SEM, cx + s, cy + s, Z_SEM_TOP,
        M_FOND, "FONDATION")
# longrines peripheriques + interieures sur les files
NX = [IX0 + v for v in sc["trame"]["X"]]
NY = [IY0 + v for v in sc["trame"]["Y"]]
for y in NY:
    wall("LONGRINE_Y_%.2f" % y, "H", y, IX0, IX1, Z_LONG_TOP - E_LONG, Z_LONG_TOP, 0.20,
         M_FOND, "FONDATION")
for x in NX:
    wall("LONGRINE_X_%.2f" % x, "V", x, IY0, IY1, Z_LONG_TOP - E_LONG, Z_LONG_TOP, 0.20,
         M_FOND, "FONDATION")

# ---- 2. POTEAUX (continus de la semelle a la toiture) ----
Z_POT_TOP = Z_ROOF_FF - E_DALLE
_px0, _py0, _px1, _py1 = PATIO
pot_dans_patio = []
for c in sc["poteaux"]:
    cx, cy = IX0 + c["x"], IY0 + c["y"]
    # poteau dont l'axe tombe dans l'emprise du patio : il porte la dalle d'etage
    # et s'arrete la (la toiture ne couvre pas le patio)
    if _px0 - 1e-6 <= cx <= _px1 + 1e-6 and _py0 - 1e-6 <= cy <= _py1 + 1e-6:
        ztop = Z_ETG_FF
        pot_dans_patio.append(c["ref"])
    else:
        ztop = Z_POT_TOP
    box("POTEAU_%s" % c["ref"], cx - B_POT / 2, cy - B_POT / 2, Z_SEM_TOP,
        cx + B_POT / 2, cy + B_POT / 2, ztop, M_BETON, "STRUCTURE")
print("  poteaux arretes au niveau etage (dans le patio) : %s" % (pot_dans_patio or "aucun"))

# ---- 3. POUTRES (2 niveaux : sous dalle etage et sous dalle toiture) ----
# niveau N2 : les poutres sont limitees a l'emprise de toiture (hors patio)
for lvl, ztop in (("N1", Z_ETG_FF - E_DALLE), ("N2", Z_ROOF_FF - E_DALLE)):
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

# ---- 4. DALLES ----
# dallage RDC (sur terre-plein)
box("DALLAGE_RDC", 0.0, 0.0, Z_RDC_FF - E_DALLE, EB_X, EB_Y, Z_RDC_FF, M_DALLE, "DALLE")
# plancher etage : pleine emprise (le patio est une terrasse exterieure du meme niveau)
box("DALLE_ETAGE", 0.0, 0.0, Z_ETG_FF - E_DALLE, EB_X, EB_Y, Z_ETG_FF, M_DALLE, "DALLE")
# plancher toiture : emprise MOINS le patio
px0, py0, px1, py1 = PATIO
box("DALLE_TOIT_1", 0.0, 0.0, Z_ROOF_FF - E_DALLE, EB_X, py0, Z_ROOF_FF, M_BETON, "DALLE")
box("DALLE_TOIT_2", 0.0, py0, Z_ROOF_FF - E_DALLE, px0, EB_Y, Z_ROOF_FF, M_BETON, "DALLE")

# ---- 5. MURS EXTERIEURS ----
wall("MUR_S_RDC", "H", 0.10, 0.0, EB_X, 0.0, H_RDC, TE, M_MAÇON, "MUR_EXT")
wall("MUR_N_RDC", "H", EB_Y - 0.10, 0.0, EB_X, 0.0, H_RDC, TE, M_MAÇON, "MUR_EXT")
wall("MUR_O_RDC", "V", 0.10, 0.0, EB_Y, 0.0, H_RDC, TE, M_MAÇON, "MUR_EXT")
wall("MUR_E_RDC", "V", EB_X - 0.10, 0.0, EB_Y, 0.0, H_RDC, TE, M_MAÇON, "MUR_EXT")
Z0E, Z1E = H_RDC, Z_ROOF_FF
wall("MUR_S_ETG", "H", 0.10, 0.0, EB_X, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")
wall("MUR_N_ETG", "H", EB_Y - 0.10, 0.0, px0, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")
wall("MUR_O_ETG", "V", 0.10, 0.0, EB_Y, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")
wall("MUR_E_ETG", "V", EB_X - 0.10, 0.0, py0, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")
wall("MUR_PATIO_S", "H", py0 + 0.10, px0 - TE, EB_X, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")
wall("MUR_PATIO_O", "V", px0 + 0.10, py0, EB_Y, Z0E, Z1E, TE, M_MAÇON, "MUR_EXT")

# ---- 6. CLOISONS INTERIEURES (derivees du plan valide) ----
OPEN_PAIRS = [("Salon", "Salle à manger")]      # espace ouvert


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
            continue                                    # sur l'enveloppe
        if ax == "V" and (abs(fixed - IX0) < 0.01 or abs(fixed - IX1) < 0.01):
            continue
        if any(sorted([owners[0], o]) in [sorted(p) for p in OPEN_PAIRS] for o in owners[1:]):
            continue                                    # espace ouvert (L)
        parts = [(a0, a1)]
        if patio:
            pxc0, pyc0, pxc1, pyc1 = patio
            if ax == "H" and (abs(fixed - pyc0) < 0.01 or abs(fixed - pyc1) < 0.01):
                parts = []                              # bord du patio : mur exterieur, pas cloison
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
                    parts = []                          # entierement dans le patio : neant
        for (b0, b1) in parts:
            if b1 - b0 > 0.01:
                out.append((ax, fixed, b0, b1))
    for i, (ax, fixed, a0, a1) in enumerate(out, 1):
        wall("CLOISON_%s_%02d" % (suffix, i), ax, fixed, a0, a1, z0, z1, E_CLOISON,
             M_MAÇON, "CLOISON")
    return len(out)


n_rdc = partitions(fp["RDC"]["rooms"], 0.0, H_RDC, "RDC")
n_etg = partitions(fp["ETAGE"]["rooms"], H_RDC, Z_ROOF_FF, "ETG", patio=PATIO)
print("  cloisons RDC : %d | cloisons étage : %d" % (n_rdc, n_etg))

# ---- 7. ACROTERE (toiture) + garde-corps patio ----
wall("ACRO_S", "H", 0.10, 0.0, EB_X, Z_ROOF_FF, Z_ROOF_FF + ACRO_H, ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_N", "H", EB_Y - 0.10, 0.0, px0, Z_ROOF_FF, Z_ROOF_FF + ACRO_H, ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_O", "V", 0.10, 0.0, EB_Y, Z_ROOF_FF, Z_ROOF_FF + ACRO_H, ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_E", "V", EB_X - 0.10, 0.0, py0, Z_ROOF_FF, Z_ROOF_FF + ACRO_H, ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_PATIO_S", "H", py0 + 0.05, px0 - ACRO_E, EB_X, Z_ROOF_FF, Z_ROOF_FF + ACRO_H,
     ACRO_E, M_BETON, "ACROTERE")
wall("ACRO_PATIO_O", "V", px0 + 0.05, py0, EB_Y, Z_ROOF_FF, Z_ROOF_FF + ACRO_H,
     ACRO_E, M_BETON, "ACROTERE")

# ---- 7b. GARDE-CORPS DE LA TERRASSE-PATIO (niveau etage, bords ouverts E et N) ----
wall("GARDE_PATIO_E", "V", EB_X - 0.05, py0, EB_Y, Z_ETG_FF, Z_ETG_FF + 1.00, 0.10,
     M_MAÇON, "GARDE_CORPS")
wall("GARDE_PATIO_N", "H", EB_Y - 0.05, px0, EB_X, Z_ETG_FF, Z_ETG_FF + 1.00, 0.10,
     M_MAÇON, "GARDE_CORPS")

# ---- 8. SOL + PATIO ----
box("SOL_TERRAIN", -3.0, -3.0, -1.30, EB_X + 3.0, EB_Y + 3.0, -1.25, M_PATIO, "SITE")
box("TERRASSE_PATIO", px0 - TE + 0.02, py0 - TE + 0.02, Z_ETG_FF - 0.05,
    px1 + TE, py1 + TE, Z_ETG_FF + 0.02, M_PATIO, "SITE")

# ---- 9. SAUVEGARDE + STATISTIQUES ----
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)

grp = {}
for o in OBJ:
    g = grp.setdefault(o["group"], {"nb": 0, "vol_m3": 0.0})
    g["nb"] += 1
    g["vol_m3"] += o["vol_m3"]
tot_v = sum(o["vol_m3"] for o in OBJ)
bbox = [min(min(o["vol_m3"], 0) for o in OBJ), 0]
xs = []; ys = []; zs = []
for o in bpy.data.objects:
    if o.type == "MESH":
        for v in o.data.vertices:
            xs.append(v.co.x); ys.append(v.co.y); zs.append(v.co.z)
stats = {"at": STAMP, "blender": bpy.app.version_string,
         "fichier": os.path.basename(OUT), "octets": os.path.getsize(OUT),
         "objets": len([o for o in bpy.data.objects if o.type == "MESH"]),
         "groupes": {k: {"nb": v["nb"], "volume_m3": round(v["vol_m3"], 3)}
                     for k, v in sorted(grp.items())},
         "volume_beton_total_m3": round(tot_v, 3),
         "bbox_m": {"x": [round(min(xs), 3), round(max(xs), 3)],
                    "y": [round(min(ys), 3), round(max(ys), 3)],
                    "z": [round(min(zs), 3), round(max(zs), 3)]},
         "geometrie_source": {"file": "floor_plan.json",
                              "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"]},
         "hypotheses": {"portance_sol_MPa": 0.15, "ancrage_fondation_m": ANC,
                        "semelle_m": SEM, "statut": "HYPOTHESIS"},
         "non_modelise": ["ouvertures (portes/fenetres) — phase 4",
                          "escalier — phase 4", "reseaux — phase 5",
                          "armatures", "toiture/forme de pente detaillee"],
         "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
p_st = os.path.join(PROJ, "3D", "bim_model_stats.json")
json.dump(stats, open(p_st, "w"), indent=2, ensure_ascii=False)

print("\n  .blend  -> %s (%d octets)" % (OUT, os.path.getsize(OUT)))
print("  objets  : %d" % stats["objets"])
for k, v in stats["groupes"].items():
    print("    %-12s %3d objets   %8.3f m3" % (k, v["nb"], v["volume_m3"]))
print("  volume BA total : %.3f m3" % stats["volume_beton_total_m3"])
print("  bbox : x %s  y %s  z %s" % (stats["bbox_m"]["x"], stats["bbox_m"]["y"],
                                     stats["bbox_m"]["z"]))
print("  STATS -> %s" % p_st)
print("STATUS : %s" % stats["STATUS"])
