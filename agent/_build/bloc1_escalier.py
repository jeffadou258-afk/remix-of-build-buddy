#!/usr/bin/env python3
"""BLOC 1 — VERIFICATION PHYSIQUE DE L'ESCALIER ET DE LA TREMIE.
Mesure l'escalier reel, verifie Blondel, et teste parametriquement les positions
qui evacuent tout recouvrement avec l'etage VALIDATED. Ne modifie rien."""
import bpy, os, json, math, hashlib, datetime
from mathutils import Vector

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
OFF, G = 0.20, 0.05
NX, NY = int(10.40 / G), int(10.90 / G)
H_NIVEAU = 3.20
STAMP = datetime.datetime.now().isoformat(timespec="seconds")


def bb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs),
            max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))


fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
etg = fp["ETAGE"]["rooms"]
print("=" * 78)
print("BLOC 1 — ESCALIER ET TREMIE")
print("=" * 78)

# ---------- 1. MESURE DE L'ESCALIER REEL DANS A_V2 ----------
B = os.path.join(PROJ, "3D", "VARIANT_A_CIRCULATION_V2.blend")
bpy.ops.wm.open_mainfile(filepath=B)
marches = []
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("VA_MARCHE"):
        marches.append((o.name, bb(o)))
marches.sort()
print("\n1. ESCALIER REEL (%s) — %d objets MARCHE" % (os.path.basename(B), len(marches)))
x0 = min(m[1][0] for m in marches); x1 = max(m[1][3] for m in marches)
y0 = min(m[1][1] for m in marches); y1 = max(m[1][4] for m in marches)
zmax = max(m[1][5] for m in marches)
giro = [round(m[1][3] - m[1][0], 4) for m in marches]
haut = [round(m[1][5], 4) for m in marches]
print("   emprise X[%.3f..%.3f] Y[%.3f..%.3f]  =  %.3f x %.3f m" % (x0, x1, y0, y1, x1 - x0, y1 - y0))
print("   hauteur totale atteinte : %.4f m" % zmax)
print("   girons : min %.4f / max %.4f / moy %.4f m" % (min(giro), max(giro), sum(giro) / len(giro)))
risers = [round(haut[k] - (haut[k - 1] if k else 0.0), 4) for k in range(len(haut))]
print("   contremarches : %d valeurs, min %.4f / max %.4f" % (len(risers), min(risers), max(risers)))
H = H_NIVEAU / (len(marches) + 1)      # 17 marches -> 18 contremarches jusqu'au niveau
g = (x1 - x0) / len(marches)
blondel = 2 * H + g
print("   lecture : %d marches (girons) -> %d contremarches de %.4f m pour un niveau de %.2f m"
      % (len(marches), len(marches) + 1, H, H_NIVEAU))
print("   BLONDEL : 2h + g = 2(%.4f) + %.4f = %.4f m  -> %s (cible 0,60-0,64)"
      % (H, g, blondel, "CONFORME" if 0.60 <= blondel <= 0.64 else "HORS PLAGE"))
print("   pente : %.1f deg" % math.degrees(math.atan(H / g)))

# ---------- 2. PASSAGE LIBRE AUTOUR DE L'ESCALIER ----------
occ = [[False] * NY for _ in range(NX)]
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(("SOL_TERRAIN", "DALLAGE")): continue
    a, b, c, d, e, f = bb(o)
    if o.name.startswith("VA_MARCHE"): f = 99.0
    elif not (c - 1e-6 <= 1.0 <= f + 1e-6): continue
    for i in range(max(0, int(math.ceil(a / G - .5))), min(NX, int(math.floor(d / G - .5)) + 1)):
        for j in range(max(0, int(math.ceil(b / G - .5))), min(NY, int(math.floor(e / G - .5)) + 1)):
            occ[i][j] = True
jm = int((OFF + 7.10 - 0.055) / G); n = 0; j = jm
while j >= 0 and not occ[int((x0 + x1) / 2 / G)][j]:
    n += 1; j -= 1
passage = round(n * G, 2)
print("   passage libre le long de l'escalier (cote nord) : %.2f m" % passage)

# ---------- 3. ARRIVEE A L'ETAGE : RECOUVREMENT ----------
def recouvre(rect, x_a, x_b, y_a, y_b):
    ox = max(0, min(x_b, rect["x_m"] + rect["w_m"]) - max(x_a, rect["x_m"]))
    oy = max(0, min(y_b, rect["y_m"] + rect["d_m"]) - max(y_a, rect["y_m"]))
    return round(ox * oy, 3), round(ox, 3), round(oy, 3)


xi0, yi0, xi1, yi1 = round(x0 - OFF, 3), round(y0 - OFF, 3), round(x1 - OFF, 3), round(y1 - OFF, 3)
print("\n2. ARRIVEE A L'ETAGE — emprise interieure du haut d'escalier : x[%.2f..%.2f] y[%.2f..%.2f]" % (xi0, xi1, yi0, yi1))
rec = {}
for r in etg:
    s, ox, oy = recouvre(r, xi0, xi1, yi0, yi1)
    if s > 0.005:
        rec[r["name"]] = {"surface_m2": s, "dx_m": ox, "dy_m": oy}
        print("   !! recouvrement avec %-18s : %.2f x %.2f = %.2f m2" % (r["name"], ox, oy, s))
if not rec: print("   aucun recouvrement")
print("   TREMIE actuelle = emprise escalier + jeu : x[%.2f..%.2f] y[%.2f..%.2f]" % (xi0 - .05, xi1 + .05, yi0 - .05, yi1 + .05))

# ---------- 4. RECHERCHE PARAMETRIQUE DE POSITIONS SANS RECOUVREMENT ----------
print("\n3. RECHERCHE PARAMETRIQUE (translation de l'escalier le long du couloir)")
larg_corridor_x0 = 1.25          # limite ouest du couloir (mur du renfoncement SAM)
cands = []
run_actuel = xi1 - xi0
a = larg_corridor_x0
while a + run_actuel <= 10.0 + 1e-9:
    s_tot = 0.0; det = {}
    for r in etg:
        s, ox, oy = recouvre(r, round(a, 3), round(a + run_actuel, 3), yi0, yi1)
        if s > 0.005: s_tot += s; det[r["name"]] = s
    # le passage nord reste-t-il >= 1,20 ? (l'escalier ne change pas de bande Y)
    cands.append({"x_debut": round(a, 3), "x_fin": round(a + run_actuel, 3),
                  "recouvrement_m2": round(s_tot, 3), "detail": det})
    a += 0.05
propres = [c for c in cands if c["recouvrement_m2"] == 0]
print("   positions testees : %d | sans aucun recouvrement : %d" % (len(cands), len(propres)))
if propres:
    c = propres[0]
    print("   >>> premiere position propre : escalier x[%.2f..%.2f]  (recouvrement 0 m2)"
          % (c["x_debut"], c["x_fin"]))
    print("       deplacement : %.2f m vers l'ouest" % (xi0 - c["x_debut"]))
    print("       giron indispensable : %.4f m (17 girons sur %.3f m)" % ((c["x_fin"] - c["x_debut"]) / 17, c["x_fin"] - c["x_debut"]))
    h2 = H_NIVEAU / 18
    print("       Blondel a ce giron : 2(%.4f) + %.4f = %.4f m" % (h2, (c["x_fin"] - c["x_debut"]) / 17, 2 * h2 + (c["x_fin"] - c["x_debut"]) / 17))
    print("       emprise escalier x[%.2f..%.2f] y[%.2f..%.2f] -> surface %.3f m2" % (c["x_debut"], c["x_fin"], yi0, yi1, (c["x_fin"] - c["x_debut"]) * (yi1 - yi0)))

out = {"etude": "bloc1_escalier_tremie", "at": STAMP,
       "fichier_mesure": os.path.basename(B), "sha256": hashlib.sha256(open(B, "rb").read()).hexdigest(),
       "escalier_mesure": {"objets_marche": len(marches), "emprise_m": [round(x1 - x0, 3), round(y1 - y0, 3)],
                           "emprise_interieure_m": [xi0, yi0, xi1, yi1], "hauteur_atteinte_m": round(zmax, 4),
                           "giron_m": round(g, 4), "contremarche_m": round(H, 4),
                           "nb_contremarches": len(marches) + 1, "blondel_m": round(blondel, 4),
                           "blondel_conforme": bool(0.60 <= blondel <= 0.64),
                           "pente_deg": round(math.degrees(math.atan(H / g)), 1),
                           "passage_libre_m": passage},
       "etage_recouvrement": rec, "tremie_actuelle": [round(xi0 - .05, 3), round(yi0 - .05, 3), round(xi1 + .05, 3), round(yi1 + .05, 3)],
       "positions_testees": len(cands), "positions_sans_recouvrement": len(propres),
       "position_proposee": propres[0] if propres else None,
       "STATUS": "VERIFIED" if not rec else "HUMAN_GATE"}
p = os.path.join(PROJ, "reports", "bloc1_escalier_tremie.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("\n-> %s" % p)
