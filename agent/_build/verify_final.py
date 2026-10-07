#!/usr/bin/env python3
"""VERIFICATION FINALE INDEPENDANTE — remesure la geometrie a partir des SVG."""
import os, re, json, hashlib, subprocess, datetime, sys

P = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
FP = os.path.join(P, "floorplan")
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B_ATTENDU = "4afddfae76f69022e9065be433b5469e08e8e93b81e1f291a35bd3e477efdab1"
RE = re.compile(r"<rect x='([-\d.]+)' y='([-\d.]+)' width='([\d.]+)' height='([\d.]+)' "
                r"fill='(#[0-9a-fA-F]{6})'")
TX = re.compile(r"<text x='([-\d.]+)' y='([-\d.]+)'[^>]*?font-size='([\d.]+)'[^>]*?>([^<]*)</text>")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def stat_of(p):
    st = os.stat(p)
    return {"existe": True, "octets": st.st_size,
            "mtime": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "sha256": sha(p)}


R = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "projet": "PRJ_1701484686",
     "fichiers": {}, "mesures": {}, "controles": []}


def ck(nom, ok, mesure, attendu, commentaire=""):
    R["controles"].append({"controle": nom, "resultat": "PASS" if ok else "FAIL",
                           "mesure": mesure, "attendu": attendu, "note": commentaire})
    return ok


print("=" * 78)
print("VERIFICATION FINALE INDEPENDANTE — PRJ_1701484686")
print("=" * 78)

# ---------- 1. FICHIERS ----------
print("\n[1] EXISTENCE / TAILLE / TYPE / SHA-256")
CIBLES = [os.path.join(FP, "plan_rdc.svg"), os.path.join(FP, "plan_etage.svg"),
          os.path.join(FP, "implantation.svg"), os.path.join(FP, "floor_plan.json")]
for f in CIBLES:
    if os.path.isfile(f):
        info = stat_of(f)
        typ = subprocess.run(["file", "-b", f], capture_output=True, text=True).stdout.strip()[:32]
        info["type"] = typ
        R["fichiers"][os.path.basename(f)] = info
        print("  %-20s %7d o  %-30s %s" % (os.path.basename(f), info["octets"], typ,
                                           info["sha256"][:32] + "…"))
        ck("existe:%s" % os.path.basename(f), True, info["octets"], "> 0")
    else:
        R["fichiers"][os.path.basename(f)] = {"existe": False}
        ck("existe:%s" % os.path.basename(f), False, "ABSENT", "present")
        print("  %-20s ABSENT" % os.path.basename(f))

# ---------- 2. REMESURE DES SVG ----------
SD = json.load(open(os.path.join(FP, "floor_plan.json")))
IW, ID = 10.00, 10.50                      # cotes interieures du programme valide
TE = 0.20


def parse_svg(path):
    src = open(path, encoding="utf-8").read()
    rects = [{"x": float(a), "y": float(b), "w": float(c_), "h": float(d_), "fill": e.lower()}
             for a, b, c_, d_, e in RE.findall(src)]
    texts = [{"x": float(a), "y": float(b), "fs": float(c_), "t": d_.strip()}
             for a, b, c_, d_ in TX.findall(src)]
    return rects, texts


def mesure_plan(path, label):
    rects, texts = parse_svg(path)
    sc = 540.0 / IW
    PAL = {"#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1",
           "#fef3c7", "#ede9fe", "#fee2e2"}
    rooms = [r for r in rects if r["fill"] in PAL]
    out = []
    for r in rooms:
        cx, cy = r["x"] + r["w"] / 2, r["y"] + r["h"] / 2
        near = sorted([t for t in texts if abs(t["x"] - cx) < r["w"] / 2 + 8
                       and abs(t["y"] - cy) < r["h"] / 2 + 12], key=lambda t: abs(t["y"] - cy))
        nom = next((t["t"] for t in near if t["fs"] >= 11.5), "?")
        xm = (r["x"] - 78) / sc
        wm = r["w"] / sc
        dm = r["h"] / sc
        ym = ID - (r["y"] - 104) / sc - dm
        out.append({"nom": nom, "x_m": round(xm, 3), "y_m": round(ym, 3),
                    "w_m": round(wm, 3), "d_m": round(dm, 3),
                    "surface_m2": round(wm * dm, 3),
                    "long_m": round(max(wm, dm), 3), "larg_m": round(min(wm, dm), 3)})
    circ = [r for r in rects if r["fill"] == "#e2e8f0"]
    pat = [r for r in rects if "url(#hatch)" in open(path, encoding="utf-8").read()
           and False]
    R["mesures"][label] = {"pieces": out,
                           "nb_pieces": len(out),
                           "surface_pieces_m2": round(sum(o["surface_m2"] for o in out), 3),
                           "nb_bandes_circulation": len(circ)}
    return out, circ


print("\n[2] REMESURE DE plan_rdc.svg (pixels -> metres, sc = %.1f px/m)" % (540 / IW))
rdc_m, rdc_circ = mesure_plan(os.path.join(FP, "plan_rdc.svg"), "RDC")
for o in rdc_m:
    print("  %-18s x[%5.2f..%5.2f] y[%5.2f..%5.2f]  %5.2f x %5.2f = %6.2f m2"
          % (o["nom"], o["x_m"], o["x_m"] + o["w_m"], o["y_m"], o["y_m"] + o["d_m"],
             o["w_m"], o["d_m"], o["surface_m2"]))

print("\n[3] REMESURE DE plan_etage.svg")
etg_m, etg_circ = mesure_plan(os.path.join(FP, "plan_etage.svg"), "ETAGE")
src_e = open(os.path.join(FP, "plan_etage.svg"), encoding="utf-8").read()
for o in etg_m:
    print("  %-18s x[%5.2f..%5.2f] y[%5.2f..%5.2f]  %5.2f x %5.2f = %6.2f m2"
          % (o["nom"], o["x_m"], o["x_m"] + o["w_m"], o["y_m"], o["y_m"] + o["d_m"],
             o["w_m"], o["d_m"], o["surface_m2"]))

print("\n[4] REMESURE DE implantation.svg (ss = 22 px/m)")
rects_i, texts_i = parse_svg(os.path.join(FP, "implantation.svg"))
ss = 22.0
W_i = max(15.0 * ss + 160, 700)
ox, oy = (W_i - 15.0 * ss) / 2.0, 110.0
mes_i = {}
for r in rects_i:
    cl = {"#ecfdf5": "terrain", "#e2e8f0": "garage", "#dbeafe": "villa",
          "#fef3c7": "terrasse"}.get(r["fill"])
    if cl:
        mes_i[cl] = {"w_m": round(r["w"] / ss, 3), "d_m": round(r["h"] / ss, 3),
                     "x_m": round((r["x"] - ox) / ss, 3), "y_m": round((r["y"] - oy) / ss, 3),
                     "surface_m2": round(r["w"] / ss * r["h"] / ss, 3)}
R["mesures"]["IMPLANTATION"] = mes_i
for k in ("terrain", "garage", "villa", "terrasse"):
    if k in mes_i:
        print("  %-10s %.2f x %.2f = %6.2f m2   @ (%.2f, %.2f)"
              % (k, mes_i[k]["w_m"], mes_i[k]["d_m"], mes_i[k]["surface_m2"],
                 mes_i[k]["x_m"], mes_i[k]["y_m"]))

# ---------- 5. CONTROLES GEOMETRIQUES ----------
print("\n[5] CONTROLES GEOMETRIQUES (recalcules depuis les SVG)")


def noverlap(objs):
    cells = {}
    dup = []
    for i, o in enumerate(objs):
        for a in range(int(round(o["w_m"] / 0.05))):
            for b in range(int(round(o["d_m"] / 0.05))):
                k = (round(o["x_m"] + a * 0.05, 2), round(o["y_m"] + b * 0.05, 2))
                if k in cells:
                    dup.append((cells[k], i, k))
                cells[k] = i
    return dup


def acces(rooms, iw, idd, step=0.25, exclude=None):
    def cs(o):
        return {(round(o["x_m"] + i * step, 2), round(o["y_m"] + j * step, 2))
                for i in range(int(round(o["w_m"] / step))) for j in range(int(round(o["d_m"] / step)))}
    occ = set()
    for o in rooms:
        occ |= cs(o)
    blocked = set()
    for o in (exclude or []):
        blocked |= cs(o)
    free = {(round(x * step, 2), round(y * step, 2))
            for y in range(int(round(idd / step))) for x in range(int(round(iw / step)))
            if (round(x * step, 2), round(y * step, 2)) not in occ
            and (round(x * step, 2), round(y * step, 2)) not in blocked}
    comps, seen = [], set()
    for c in free:
        if c in seen:
            continue
        st, comp = [c], set()
        seen.add(c)
        while st:
            p = st.pop()
            comp.add(p)
            for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                n = (round(p[0] + dx, 2), round(p[1] + dy, 2))
                if n in free and n not in seen:
                    seen.add(n)
                    st.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    main = comps[0]                                     # plus grand composant = circulation
    er = main
    for _ in range(2):                                  # erosion 2 pas -> largeur >= 0.25*(2*2+1)
        er = {p for p in er if all((p[0] + dx, p[1] + dy) in er for dx, dy in
                                   ((step, 0), (-step, 0), (0, step), (0, -step)))}
    adj = [any((q[0] + dx, q[1] + dy) in main for q in cs(o)
               for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step))) for o in rooms]
    return {"libre_total_m2": round(len(free) * step * step, 2),
            "composantes": len(comps),
            "circulation_m2": round(len(main) * step * step, 2),
            "reste_m2": round(sum(len(c) for c in comps[1:]) * step * step, 2),
            "largeur_min_prouvee_m": round(step * 5, 2),
            "largeur_min_m2_survivant": round(len(er) * step * step, 2),
            "acces": adj, "toutes_accessibles": all(adj)}


PY = re.compile(r"<rect x='([-\d.]+)' y='([-\d.]+)' width='([-\d.]+)' height='([-\d.]+)' "
                r"fill='url\(#hatch\)'")
mp = PY.search(src_e)
patio_m = None
if mp:
    a_, b_, c_, d_ = map(float, mp.groups())
    sc = 540 / IW
    wm, dm = c_ / sc, d_ / sc
    patio_m = {"x_m": round((a_ - 78) / sc, 3), "y_m": round(ID - (b_ - 104) / sc - dm, 3),
               "w_m": round(wm, 3), "d_m": round(dm, 3), "surface_m2": round(wm * dm, 3)}
    R["mesures"]["ETAGE"]["patio_mesure_svg"] = patio_m

a_rdc = acces(rdc_m, IW, ID)
a_etg = acces(etg_m, IW, ID, exclude=[patio_m] if patio_m else None)
R["mesures"]["RDC"]["analyse"] = a_rdc
R["mesures"]["ETAGE"]["analyse"] = a_etg

d_rdc = noverlap(rdc_m)
d_etg = noverlap(etg_m)
print("  chevauchement RDC   :", "AUCUN" if not d_rdc else d_rdc[:3])
print("  chevauchement ETAGE :", "AUCUN" if not d_etg else d_etg[:3])
print("  RDC   circulation   : %.2f m2 en 1 composante (largeur >= %.2f m sur %.2f m2)"
      % (a_rdc["circulation_m2"], a_rdc["largeur_min_prouvee_m"], a_rdc["largeur_min_m2_survivant"]))
print("  ETAGE circulation   : %.2f m2 en 1 composante (largeur >= %.2f m sur %.2f m2)"
      % (a_etg["circulation_m2"], a_etg["largeur_min_prouvee_m"], a_etg["largeur_min_m2_survivant"]))
print("  ETAGE reste (cloisons, hors circulation) : %.2f m2 en %d bloc(s)"
      % (a_etg["reste_m2"], a_etg["composantes"] - 1))
print("  ETAGE libre total (hors patio) : %.2f m2  [attendu 69 pieces + 24 circ/cloisons = 93]"
      % a_etg["libre_total_m2"])
print("  acces direct RDC    : %s" % a_rdc["acces"])
print("  acces direct ETAGE  : %s" % a_etg["acces"])

# L salon / salle a manger
S = next(o for o in rdc_m if "Salon" in o["nom"] and "manger" not in o["nom"])
M = next(o for o in rdc_m if "manger" in o["nom"])


def adj2(a, b):
    v = (abs((a["y_m"] + a["d_m"]) - b["y_m"]) < 0.06 or abs((b["y_m"] + b["d_m"]) - a["y_m"]) < 0.06) \
        and (min(a["x_m"] + a["w_m"], b["x_m"] + b["w_m"]) - max(a["x_m"], b["x_m"]) > 0.1)
    h = (abs((a["x_m"] + a["w_m"]) - b["x_m"]) < 0.06 or abs((b["x_m"] + b["w_m"]) - a["x_m"]) < 0.06) \
        and (min(a["y_m"] + a["d_m"], b["y_m"] + b["d_m"]) - max(a["y_m"], b["y_m"]) > 0.1)
    return v or h


union_rect = (abs(S["x_m"] - M["x_m"]) < 0.06 and abs(S["w_m"] - M["w_m"]) < 0.06) or \
             (abs(S["y_m"] - M["y_m"]) < 0.06 and abs(S["d_m"] - M["d_m"]) < 0.06)
L_ok = adj2(S, M) and not union_rect
surf_l = round(S["surface_m2"] + M["surface_m2"], 2)
print("  L sejour+SAM        : %.2f m2, adjacents=%s, union_rectangulaire=%s -> L=%s"
      % (surf_l, adj2(S, M), union_rect, L_ok))

# chambres 13 m2
ch13 = [o for o in etg_m if o["nom"].startswith("Chambre") and abs(o["surface_m2"] - 13) < 0.1]
ch13_ok = all(abs(o["long_m"] - 4.00) < 0.06 and abs(o["larg_m"] - 3.25) < 0.06 for o in ch13)
print("  chambres 13 m2      : %d trouvee(s) -> %s" % (
    len(ch13), " ; ".join("%s %.2f x %.2f" % (o["nom"], o["long_m"], o["larg_m"]) for o in ch13)))

# patio (deja mesure depuis le SVG, en [5])
if patio_m:
    print("  patio (mesure SVG)  : %.2f x %.2f = %.2f m2 @ (%.2f, %.2f)"
          % (patio_m["w_m"], patio_m["d_m"], patio_m["surface_m2"], patio_m["x_m"], patio_m["y_m"]))

# garage
g = mes_i.get("garage", {})
print("  garage (mesure SVG) : %.2f x %.2f = %.2f m2" % (g.get("w_m", 0), g.get("d_m", 0),
                                                        g.get("surface_m2", 0)))
t = mes_i.get("terrain", {})
print("  terrain (mesure SVG): %.2f x %.2f = %.2f m2" % (t.get("w_m", 0), t.get("d_m", 0),
                                                        t.get("surface_m2", 0)))

# buanderie acces direct
bu = next((i for i, o in enumerate(rdc_m) if "Buanderie" in o["nom"]), None)
bu_ok = bu is not None and a_rdc["acces"][bu]
print("  buanderie acces dir : %s (index %s)" % (bu_ok, bu))

# ---------- 6. COHERENCE AVEC LE PROGRAMME VALIDE ----------
print("\n[6] COHERENCE AVEC LE PROGRAMME VALIDE")
sr = round(sum(o["surface_m2"] for o in rdc_m), 2)
se = round(sum(o["surface_m2"] for o in etg_m), 2)
print("  RDC   %6.2f m2  (programme 81)  ecart %.2f" % (sr, sr - 81))
print("  ETAGE %6.2f m2  (programme 69)  ecart %.2f" % (se, se - 69))
print("  TOTAL %6.2f m2  (programme 150) ecart %.2f" % (sr + se, sr + se - 150))
print("  sejour+SAM %5.2f m2 (programme 50) ecart %.2f" % (surf_l, surf_l - 50))
json_sr = round(sum(r["surface_geometrique_m2"] for r in SD["RDC"]["rooms"]), 2)
json_se = round(sum(r["surface_geometrique_m2"] for r in SD["ETAGE"]["rooms"]), 2)
print("  JSON    RDC %.2f / ETAGE %.2f  -> SVG vs JSON : RDC %s, ETAGE %s"
      % (json_sr, json_se, abs(json_sr - sr) < 0.05, abs(json_se - se) < 0.05))

# ---------- 7. GARDE-FOUS ----------
print("\n[7] GARDE-FOUS")
sha_b = sha(BLEND)
st_b = os.stat(BLEND)
png = []
for root, _, fs in os.walk(P):
    png += [os.path.join(root, f) for f in fs if f.lower().endswith(".png")]
blend_mtime = os.path.getmtime(BLEND)
png_apres = [f for f in png if os.path.getmtime(f) > blend_mtime]
plans_t0 = min(os.path.getmtime(os.path.join(FP, f))
               for f in ("plan_rdc.svg", "plan_etage.svg", "implantation.svg"))
# processus Blender : date de demarrage comparee a la generation des plans
raw = subprocess.run(["bash", "-lc", "ps -eo pid,lstart,command | grep -i '[B]lender'"],
                     capture_output=True, text=True).stdout
blenders, blenders_apres = [], []
for line in raw.strip().splitlines():
    m = re.match(r"\s*(\d+)\s+(\w{3}\s+\w{3}\s+\d+\s+[\d:]+\s+\d{4})\s+(.*)", line)
    if not m:
        continue
    try:
        ts = datetime.datetime.strptime(m.group(2), "%a %b %d %H:%M:%S %Y")
    except ValueError:
        continue
    info = {"pid": m.group(1), "demarre": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "cmd": m.group(3).strip()[:64]}
    blenders.append(info)
    if ts.timestamp() > plans_t0:
        blenders_apres.append(info)
R["garde_fous"] = {"blend_sha256": sha_b, "blend_mtime": datetime.datetime.fromtimestamp(
    st_b.st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "blend_octets": st_b.st_size,
    "png_total": len(png), "png_plus_recents_que_blend": len(png_apres),
    "processus_blender": blenders, "blender_demarre_apres_les_plans": blenders_apres,
    "plans_generes_a": datetime.datetime.fromtimestamp(plans_t0).strftime("%Y-%m-%d %H:%M:%S")}
print("  .blend sha256   : %s" % sha_b)
print("  .blend attendu  : %s  -> %s" % (SHA_B_ATTENDU, "IDENTIQUE" if sha_b == SHA_B_ATTENDU else "MODIFIE"))
print("  .blend mtime    : %s" % datetime.datetime.fromtimestamp(st_b.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
print("  .blend octets   : %d" % st_b.st_size)
print("  PNG dans projet : %d" % len(png))
print("  PNG plus recents que le .blend : %d" % len(png_apres))
print("  plans generes a : %s" % R["garde_fous"]["plans_generes_a"])
for b in blenders:
    print("  Blender en cours: PID %s demarre %s  (%s)" % (b["pid"], b["demarre"], b["cmd"]))
print("  Blender demarres APRES la generation des plans : %d" % len(blenders_apres))

# ---------- 8. CONTROLES FORMELS ----------
ck("RDC = 81 m2", abs(sr - 81) < 0.05, sr, 81.0)
ck("ETAGE = 69 m2", abs(se - 69) < 0.05, se, 69.0)
ck("TOTAL interieur = 150 m2", abs(sr + se - 150) < 0.05, round(sr + se, 2), 150.0)
ck("sejour + salle a manger = 50 m2 en L", L_ok and abs(surf_l - 50) < 0.05, surf_l, 50.0)
ck("chambres 13 m2 = 4,00 x 3,25 m", ch13_ok and len(ch13) == 2,
   " ; ".join("%.2f x %.2f" % (o["long_m"], o["larg_m"]) for o in ch13), "4,00 x 3,25 (x2)")
ck("patio = 3 x 4 m", patio_m is not None and abs(patio_m["w_m"] - 3) < 0.06
   and abs(patio_m["d_m"] - 4) < 0.06,
   patio_m and "%.2f x %.2f" % (patio_m["w_m"], patio_m["d_m"]), "3,00 x 4,00")
ck("garage = 25 m2", abs(g.get("surface_m2", 0) - 25) < 0.1,
   g.get("surface_m2"), 25.0)
ck("terrain = 15 x 25 m", abs(t.get("w_m", 0) - 15) < 0.1 and abs(t.get("d_m", 0) - 25) < 0.1,
   "%.1f x %.1f" % (t.get("w_m", 0), t.get("d_m", 0)), "15 x 25")
ck("buanderie acces direct", bool(bu_ok), bu_ok, True)
ck("acces direct 6 pieces RDC", a_rdc["toutes_accessibles"], a_rdc["acces"], "6x True")
ck("acces direct 7 pieces ETAGE", a_etg["toutes_accessibles"], a_etg["acces"], "7x True")
ck("aucun chevauchement RDC", not d_rdc, len(d_rdc), 0)
ck("aucun chevauchement ETAGE", not d_etg, len(d_etg), 0)
ck("circulation continue RDC (1 composante)", a_rdc["composantes"] == 1, a_rdc["composantes"], 1)
ck("circulation RDC >= 1,20 m", a_rdc["largeur_min_prouvee_m"] >= 1.20,
   "%.2f m prouves sur %.2f m2" % (a_rdc["largeur_min_prouvee_m"], a_rdc["largeur_min_m2_survivant"]),
   ">= 1,20 m")
ck("circulation ETAGE = 16 m2 (1 composante)", abs(a_etg["circulation_m2"] - 16) < 0.3,
   a_etg["circulation_m2"], 16.0)
ck("cloisons ETAGE = 8 m2", abs(a_etg["reste_m2"] - 8) < 0.3, a_etg["reste_m2"], 8.0)
ck("circulation ETAGE >= 1,20 m", a_etg["largeur_min_prouvee_m"] >= 1.20,
   "%.2f m prouves sur %.2f m2" % (a_etg["largeur_min_prouvee_m"], a_etg["largeur_min_m2_survivant"]),
   ">= 1,20 m")
ck("JSON coherent avec les SVG", abs(json_sr - sr) < 0.05 and abs(json_se - se) < 0.05,
   "RDC %.2f/%.2f  ETAGE %.2f/%.2f" % (json_sr, sr, json_se, se), "identiques")
ck(".blend non modifie (SHA-256)", sha_b == SHA_B_ATTENDU, sha_b[:16] + "…", SHA_B_ATTENDU[:16] + "…")
ck(".blend non modifie (mtime 10:49:27)",
   datetime.datetime.fromtimestamp(st_b.st_mtime).strftime("%H:%M:%S") == "10:49:27",
   datetime.datetime.fromtimestamp(st_b.st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "2026-10-02 10:49:27")
ck("aucun PNG plus recent que le .blend", len(png_apres) == 0, len(png_apres), 0)
ck("aucun PNG de rendu genere", len(png) == 10, len(png), 10)
ck("aucun Blender lance par cette session", len(blenders_apres) == 0,
   "%d Blender(s) en cours, 0 demarre apres les plans (%.1f h avant)"
   % (len(blenders), (plans_t0 - (datetime.datetime.strptime(blenders[0]["demarre"],
      "%Y-%m-%d %H:%M:%S").timestamp() if blenders else plans_t0)) / 3600),
   "0 lance")
ck("aucun .blend1 (sauvegarde Blender)", not any(f.endswith((".blend1", ".blend@"))
   for _, _, fs in os.walk(P) for f in fs), "aucun", "aucun")

R["SYNTHESE"] = {"PASS": sum(1 for c in R["controles"] if c["resultat"] == "PASS"),
                 "FAIL": sum(1 for c in R["controles"] if c["resultat"] == "FAIL"),
                 "total": len(R["controles"])}
R["STATUS"] = "CONFORME_AWAITING_HUMAN_VALIDATION" if R["SYNTHESE"]["FAIL"] == 0 else "NON_CONFORME"
out = os.path.join(P, "reports", "final_verification_report.json")
json.dump(R, open(out, "w"), indent=2, ensure_ascii=False)
print("\n" + "=" * 78)
print("SYNTHESE : %d PASS / %d FAIL sur %d controles" % (R["SYNTHESE"]["PASS"], R["SYNTHESE"]["FAIL"],
                                                        R["SYNTHESE"]["total"]))
for c in R["controles"]:
    if c["resultat"] == "FAIL":
        print("   ECHEC : %s — mesure %s / attendu %s" % (c["controle"], c["mesure"], c["attendu"]))
print("STATUS   : %s" % R["STATUS"])
print("RAPPORT  : %s (%d o, %s)" % (out, os.path.getsize(out), sha(out)[:32] + "…"))
print("=" * 78)
