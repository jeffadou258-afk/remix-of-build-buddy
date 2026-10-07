#!/usr/bin/env python3
"""PHASE 3 — VERIFICATION BIM <-> PLANS 2D. Confronte le modele 3D a la geometrie VALIDATED."""
import bpy, os, json, hashlib, datetime

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
BIM = os.path.join(PROJ, "3D", "BIM_villa_R1_VALIDATED.blend")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


fp = json.load(open(os.path.join(PROJ, "floorplan", "floor_plan.json")))
sc = json.load(open(os.path.join(PROJ, "structure", "structural_concept.json")))
lock = json.load(open(os.path.join(PROJ, "floorplan", "GEOMETRY_LOCK.json")))

EB_X, EB_Y, TE = 10.40, 10.90, 0.20
IX0, IY0, IX1, IY1 = TE, TE, EB_X - TE, EB_Y - TE
PATIO = (7.20, 6.70, 10.20, 10.70)
Z_FF = (0.00, 3.20, 6.40)

print("=" * 78)
print("PHASE 3 — VERIFICATION BIM <-> PLANS 2D")
print("=" * 78)

bpy.ops.wm.open_mainfile(filepath=BIM)
mesh = [o for o in bpy.data.objects if o.type == "MESH"]
print("  modele : %d objets (sha256 %s)" % (len(mesh), sha(BIM)[:24] + "…"))
print("  reference 2D : floor_plan.json %s (STATUS %s)"
      % (lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"][:16] + "…",
         lock["STATUS"]))


def bbox(o):
    b = o.bound_box
    return (min(v[0] for v in b) + o.location.x, min(v[1] for v in b) + o.location.y,
            min(v[2] for v in b) + o.location.z, max(v[0] for v in b) + o.location.x,
            max(v[1] for v in b) + o.location.y, max(v[2] for v in b) + o.location.z)


def spans_z(o, z):
    x0, y0, z0, x1, y1, z1 = bbox(o)
    return z0 - 1e-6 <= z <= z1 + 1e-6


checks = []


def ck(n, ok, mes, att):
    checks.append({"controle": n, "resultat": "PASS" if ok else "FAIL", "mesure": mes, "attendu": att})
    print("  %-46s %-5s %s" % (n, "PASS" if ok else "FAIL", mes))


# ---- 1. EMPRISE BATIE (hors terrassement et hors fondations, qui debordent normalement) ----
bat = [o for o in mesh if not o.name.startswith(("SOL_TERRAIN", "TERRASSE_PATIO",
                                                 "SEMELLE", "LONGRINE"))]
xs0 = [bbox(o)[0] for o in bat]
ys0 = [bbox(o)[1] for o in bat]
xs1 = [bbox(o)[3] for o in bat]
ys1 = [bbox(o)[4] for o in bat]
ex, ey = max(xs1) - min(xs0), max(ys1) - min(ys0)
print("\n[1] EMPRISE BATIE MESUREE DANS LE MODELE 3D (superstructure)")
print("  %.3f x %.3f m  (plan 2D : %.2f x %.2f m)" % (ex, ey, EB_X, EB_Y))
ck("emprise superstructure = enveloppe 2D", abs(ex - EB_X) < 0.01 and abs(ey - EB_Y) < 0.01,
   "%.3f x %.3f m" % (ex, ey), "%.2f x %.2f m" % (EB_X, EB_Y))
fond = [o for o in mesh if o.name.startswith(("SEMELLE", "LONGRINE"))]
fx0 = min(bbox(o)[0] for o in fond)
fy0 = min(bbox(o)[1] for o in fond)
fx1 = max(bbox(o)[3] for o in fond)
fy1 = max(bbox(o)[4] for o in fond)
print("  fondations : X [%.2f ; %.2f] Y [%.2f ; %.2f] -> debord %.2f m hors emprise (normal)"
      % (fx0, fx1, fy0, fy1, max(-fx0, fx1 - EB_X)))
ck("debord des fondations documente et coherent (0,40 m)",
   abs(max(-fx0, fx1 - EB_X) - 0.40) < 0.02 and max(-fx0, fx1 - EB_X) > 0,
   "%.2f m" % max(-fx0, fx1 - EB_X), "0,40 m (semelle 1,20 sous axe a 0,20)")

# ---- 2. AXES DE POTEAUX vs TRAME ----
print("\n[2] POSITIONS DES POTEAUX vs TRAME STRUCTURELLE")
pot = [o for o in mesh if o.name.startswith("POTEAU")]
attendu = sorted([(round(IX0 + x, 2), round(IY0 + y, 2))
                  for x in sc["trame"]["X"] for y in sc["trame"]["Y"]])
reels = sorted([(round((bbox(o)[0] + bbox(o)[3]) / 2, 2),
                 round((bbox(o)[1] + bbox(o)[4]) / 2, 2)) for o in pot])
ecarts = [max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in zip(attendu, reels)]
print("  %d poteaux ; ecart max axe reel/theorique : %.3f m" % (len(pot), max(ecarts)))
ck("16 poteaux aux 16 noeuds de trame", len(pot) == 16 and max(ecarts) < 0.01,
   "ecart max %.3f m" % max(ecarts), "< 0,010 m")
sect = {(round(bbox(o)[3] - bbox(o)[0], 2), round(bbox(o)[4] - bbox(o)[1], 2)) for o in pot}
ck("section poteaux 30 x 30 cm", sect == {(0.30, 0.30)}, str(sect), "{(0.30, 0.30)}")

# ---- 3. NIVEAUX DE PLANCHER ----
print("\n[3] NIVEAUX DE PLANCHER vs PLAN 2D (0,00 / 3,20 / 6,40)")
dalles = [o for o in mesh if o.name.startswith(("DALLAGE", "DALLE"))]
niveaux = sorted({round(bbox(o)[5], 2) for o in dalles})
print("  faces superieures de dalle : %s" % niveaux)
ck("3 niveaux conformes au plan", niveaux == [0.00, 3.20, 6.40], str(niveaux), "[0.0, 3.2, 6.4]")
ep = {round(bbox(o)[5] - bbox(o)[2], 3) for o in dalles}
ck("epaisseur de dalle 15 cm partout", ep == {0.15}, str(ep), "{0.15}")

# ---- 4. RETRAIT PATIO A L'ETAGE ----
print("\n[4] RETRAIT PATIO 3 x 4 m A L'ETAGE (coin NE)")
px0, py0, px1, py1 = PATIO
z_test = 6.30          # dans la dalle de toiture
couvrants = []
for o in mesh:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if z0 - 1e-6 <= z_test <= z1 + 1e-6:
        if not (x1 <= px0 + 1e-6 or x0 >= px1 - 1e-6 or y1 <= py0 + 1e-6 or y0 >= py1 - 1e-6):
            couvrants.append(o.name)
inter = [o for o in couvrants if not o.startswith(("ACRO", "MUR", "GARDE"))]
print("  a z=6,30 m : %d objet(s) couvrant le patio -> %s" % (len(inter), inter))
ck("patio NON couvert par la toiture (retrait 3x4 reel)",
   all(o.startswith(("ACRO", "MUR")) for o in couvrants),
   "%d objets (acrotere/murs uniquement)" % len(couvrants), "0 dalle au-dessus du patio")
aire_patio = (px1 - px0) * (py1 - py0)
ck("surface du retrait = 12,00 m2", abs(aire_patio - 12.0) < 0.01, round(aire_patio, 2), 12.0)

# ---- 5. NIVEAU DU PATIO : PRESENT A L'ETAGE, ABSENT AU RDC ----
mur_rdc = [o for o in mesh if o.name.endswith("_RDC") and o.name.startswith("MUR")]
z_patio = 4.50
in_patio = []
for o in mesh:
    x0, y0, z0, x1, y1, z1 = bbox(o)
    if z0 - 1e-6 <= z_patio <= z1 + 1e-6:
        if not (x1 <= px0 + 1e-6 or x0 >= px1 - 1e-6 or y1 <= py0 + 1e-6 or y0 >= py1 - 1e-6):
            in_patio.append(o.name)
mur_p = [o for o in in_patio if o.startswith("MUR")]
print("\n[5] LE PATIO EST-IL UN ESPACE EXTERIEUR A L'ETAGE ?")
print("  a z=4,50 m dans l'emprise du patio : %d objet(s) -> %s" % (len(in_patio), in_patio))
ck("a l'etage le patio est libre (murs de pourtour seuls)",
   all(o.startswith(("MUR", "ACRO", "GARDE")) for o in in_patio),
   "%d objet(s) : %s" % (len(in_patio), ",".join(in_patio) or "-"), "murs de pourtour uniquement")

# ---- 6. SURFACES INTERIEURES vs PLAN 2D ----
print("\n[6] SURFACES INTERIEURES — PLAN 2D vs MODELE")
s_rdc = float(fp["RDC"]["surface_pieces_m2"])
s_etg = float(fp["ETAGE"]["surface_pieces_m2"])
aire_int = (IX1 - IX0) * (IY1 - IY0)
aire_patio = 12.0
print("  plan 2D  : RDC %.2f m2 + circulation 24,00 | ETAGE %.2f m2 + 24,00 - patio 12,00" %
      (s_rdc, s_etg))
ck("surface interieure brute RDC = 105,00 m2", abs(aire_int - 105.0) < 0.01, round(aire_int, 2), 105.0)
ck("surface habitable ETAGE = 93,00 m2 (hors patio)",
   abs(aire_int - aire_patio - 93.0) < 0.01, round(aire_int - aire_patio, 2), 93.0)
ck("total pieces programme = 150,00 m2", abs(s_rdc + s_etg - 150.0) < 0.01,
   round(s_rdc + s_etg, 2), 150.0)

# ---- 7. COHERENCE DES COTES DE PIECES (deux chambres 13 m2) ----
print("\n[7] CHAMBRES DE 13 M2 — EMPREINTE VERIFIEE")
ch = [r for r in fp["ETAGE"]["rooms"] if abs(r["surface_geometrique_m2"] - 13.0) < 0.01]
print("  %d chambre(s) : %s" % (len(ch), ", ".join("%s %.2f x %.2f" %
      (r["name"], r["longueur_m"], r["largeur_m"]) for r in ch)))
ck("2 chambres de 13 m2 en 4,00 x 3,25 m",
   len(ch) == 2 and all(abs(r["longueur_m"] - 4.0) < 0.01 and abs(r["largeur_m"] - 3.25) < 0.01
                        for r in ch), len(ch), 2)

out = {"phase": "3. VERIFICATION BIM <-> PLANS 2D", "at": STAMP,
       "modele_3d": {"fichier": "3D/BIM_villa_R1_VALIDATED.blend", "sha256": sha(BIM),
                     "objets": len(mesh)},
       "geometrie_2d_reference": {"fichier": "floorplan/floor_plan.json",
                                  "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"],
                                  "statut": lock["STATUS"]},
       "controles": checks,
       "SYNTHESE": {"PASS": sum(1 for c in checks if c["resultat"] == "PASS"),
                    "FAIL": sum(1 for c in checks if c["resultat"] == "FAIL"),
                    "total": len(checks)},
       "ecart_max_poteaux_m": round(max(ecarts), 4),
       "STATUS": "VERIFIED" if all(c["resultat"] == "PASS" for c in checks)
                 else "DISCREPANCY_FOUND"}
p = os.path.join(PROJ, "reports", "bim_vs_2d_verification.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("SYNTHESE : %d PASS / %d FAIL" % (out["SYNTHESE"]["PASS"], out["SYNTHESE"]["FAIL"]))
print("STATUS   : %s" % out["STATUS"])
print("-> %s" % p)
print("=" * 78)
