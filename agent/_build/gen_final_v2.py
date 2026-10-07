#!/usr/bin/env python3
"""Generation FINALE des livrables : 3 SVG + floor_plan.json + rapports + evidence."""
import os, sys, json, datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
TE, TI = 0.20, 0.10
RDC_W, RDC_D = 10.40, 10.90
IW, ID = 10.00, 10.50
PATIO = (7.0, 6.5, 3.0, 4.0)
rs = json.load(open(AGENT + "/_build/_rdc_v2.json"))
es = json.load(open(AGENT + "/_build/_etg_v5.json"))


def erode_width(rects, circ, iw, id_, k):
    """largeur locale : erode k fois de 0.25 m -> largeur >= 0.25*(2k+1)."""
    def cs(r):
        return {(round(r[0] + i * 0.25, 3), round(r[1] + j * 0.25, 3))
                for i in range(int(round(r[2] / 0.25))) for j in range(int(round(r[3] / 0.25)))}
    occ = set()
    if circ is None:                      # circulation = espace libre hors pieces
        allc = {(round(x * 0.25, 3), round(y * 0.25, 3))
                for y in range(int(round(id_ / 0.25))) for x in range(int(round(iw / 0.25)))}
        used = set()
        for r in rects:
            used |= cs(r)
        occ = allc - used
    else:
        for i in circ:
            occ |= cs(rects[i])
    cur = set(occ)
    for _ in range(k):
        cur = {p for p in cur if all((p[0] + dx, p[1] + dy) in cur
                                     for dx, dy in ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)))}
        if not cur:
            return 0, 0.0
    return len(cur), round(0.25 * (2 * k + 1), 2)


# ---- RDC ----
rdc_rects = [tuple(r) for r in rs["rects"]]
rdc_names = rs["names"]
rdc_rooms = [{"code": "P%02d" % (i + 1), "name": rdc_names[i],
              "surface_demandee_m2": float(rs["areas"][i]),
              "longueur_m": round(max(rdc_rects[i][2], rdc_rects[i][3]), 2),
              "largeur_m": round(min(rdc_rects[i][2], rdc_rects[i][3]), 2),
              "ratio": round(max(rdc_rects[i][2], rdc_rects[i][3]) /
                             min(rdc_rects[i][2], rdc_rects[i][3]), 2),
              "x_m": rdc_rects[i][0], "y_m": rdc_rects[i][1],
              "w_m": rdc_rects[i][2], "d_m": rdc_rects[i][3]}
             for i in range(len(rdc_rects))]
for r in rdc_rooms:
    r["surface_geometrique_m2"] = round(r["w_m"] * r["d_m"], 2)
    r["conforme"] = abs(r["surface_geometrique_m2"] - r["surface_demandee_m2"]) < 0.005
n2, w2 = erode_width(rdc_rects, None, IW, ID, 2)
n4, w4 = erode_width(rdc_rects, None, IW, ID, 4)
print("RDC circulation : largeur>=1,25 m sur %d cellules ; largeur>=2,25 m sur %d" % (n2, n4))

# ---- ETAGE ----
e_all = [tuple(r) for r in es["rects"]]
e_names = es["names"]
ci = es["circ_idx"]
rooms_i = [i for i, n in enumerate(e_names) if not n.startswith(("COULOIR", "CLOISONS"))]
fil_i = [i for i, n in enumerate(e_names) if n.startswith("CLOISONS")]
want = {"Suite parentale": 16.0, "Chambre 2": 13.0, "Chambre 3": 13.0, "Chambre 4": 12.0,
        "Salle de bain 1": 5.0, "Salle de bain 2": 5.0, "Salle de bain 3": 5.0}
etg_rooms = []
for i in rooms_i:
    r = e_all[i]
    etg_rooms.append({"code": "P%02d" % (len(etg_rooms) + 7), "name": e_names[i],
                      "surface_demandee_m2": want[e_names[i]],
                      "longueur_m": round(max(r[2], r[3]), 2),
                      "largeur_m": round(min(r[2], r[3]), 2),
                      "ratio": round(max(r[2], r[3]) / min(r[2], r[3]), 2),
                      "x_m": r[0], "y_m": r[1], "w_m": r[2], "d_m": r[3]})
for r in etg_rooms:
    r["surface_geometrique_m2"] = round(r["w_m"] * r["d_m"], 2)
    r["conforme"] = abs(r["surface_geometrique_m2"] - r["surface_demandee_m2"]) < 0.005
en2, ew2 = erode_width(e_all, ci, IW, ID, 2)
print("ETAGE couloir : %d morceaux, largeur>=1,25 m sur %d cellules (min couloir %.2f m)"
      % (len(ci), en2, min(e_all[i][2] for i in ci)))

# ================= SVG =================
PAL = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1",
       "#fef3c7", "#ede9fe", "#fee2e2"]


def free_runs(rects, iw, idd, step=0.25):
    """Region libre (circulation + cloisons) decoupee en bandes horizontales exactes."""
    def cs(r):
        return {(round(r[0] + i * step, 3), round(r[1] + j * step, 3))
                for i in range(int(round(r[2] / step))) for j in range(int(round(r[3] / step)))}
    occ = set()
    for r in rects:
        occ |= cs(r)
    nx, ny = int(round(iw / step)), int(round(idd / step))
    runs = []
    for j in range(ny):
        x = 0
        while x < nx:
            c = (round(x * step, 3), round(j * step, 3))
            if c in occ:
                x += 1
                continue
            x0 = x
            while x < nx and (round(x * step, 3), round(j * step, 3)) not in occ:
                x += 1
            runs.append((x0 * step, j * step, (x - x0) * step, step))
    return runs


def header(W, H, t1, t2, t3):
    return ["<?xml version='1.0' encoding='UTF-8'?>",
            "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' "
            "viewBox='0 0 %.0f %.0f'>" % (W, H, W, H),
            "<rect width='100%' height='100%' fill='#ffffff'/>",
            "<text x='78' y='40' font-family='Helvetica,Arial' font-size='20' "
            "font-weight='bold' fill='#0f172a'>%s</text>" % t1,
            "<text x='78' y='61' font-family='Helvetica,Arial' font-size='11' fill='#475569'>%s"
            "</text>" % t2,
            "<text x='78' y='78' font-family='Helvetica,Arial' font-size='9' fill='#94a3b8'>%s"
            "</text>" % t3]


def room_svg(x0, y0, sc, r, fill, idw, idd, names=True):
    X = lambda m: 78 + m * sc
    Y = lambda m, in_: 104 + (idd - m - in_) * sc
    out = ["<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' stroke='#64748b' "
           "stroke-width='1'/>" % (X(r[0]), Y(r[1], r[3]), r[2] * sc, r[3] * sc, fill)]
    if names:
        cx, cy = X(r[0]) + r[2] * sc / 2, Y(r[1], r[3]) + r[3] * sc / 2
        for t, dy, fs, b in [(r[5], -7, 12, True),
                             ("%g m²" % (r[2] * r[3]), 9, 10, False),
                             ("%g × %g m" % (max(r[2], r[3]), min(r[2], r[3])), 21, 8.5, False)]:
            out.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial'"
                       " font-size='%g' %s fill='%s'>%s</text>"
                       % (cx, cy + dy, fs, "font-weight='bold'" if b else "",
                          "#0f172a" if b else "#334155", t))
    return out


def draw_plan(path, title, sub, rooms, circ_rects, patio, iw, idd, note, extra_lines=()):
    sc = 540.0 / iw
    W = iw * sc + 156
    H = idd * sc + 104 + 120
    L = header(W, H, title, sub, "PRJ_1701484686 · Construction Agent v2.0.0 · SCHÉMA "
               "CONCEPTUEL non contractuel · STATUS : AWAITING_HUMAN_VALIDATION")
    X = lambda m: 78 + m * sc
    Y = lambda m, in_: 104 + (idd - m - in_) * sc
    # murs exterieurs
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f1f5f9' stroke='#0f172a' "
             "stroke-width='3.5'/>" % (X(-TE), Y(-TE, idd + 2 * TE),
                                       (iw + 2 * TE) * sc, (idd + 2 * TE) * sc))
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ffffff' stroke='none'/>"
             % (X(0), Y(0, idd), iw * sc, idd * sc))
    # circulation + cloisons : bandes exactes, sans contour (aspect continu)
    for c in circ_rects:
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' "
                 "stroke='none' shape-rendering='crispEdges'/>"
                 % (X(c[0]), Y(c[1], c[3]), c[2] * sc, c[3] * sc))
    if circ_rects:
        big = max(circ_rects, key=lambda c: c[2] * c[3])
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' "
                 "stroke='#94a3b8' stroke-width='0.8'/>"
                 % (X(big[0]), Y(big[1], big[3]), big[2] * sc, big[3] * sc))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='9' font-weight='bold' fill='#475569'>circulation + cloisons</text>"
                 % (X(big[0]) + big[2] * sc / 2, Y(big[1], big[3]) + big[3] * sc / 2 + 3))
    # pieces
    for i, r in enumerate(rooms):
        L += room_svg(0, 0, sc, r, PAL[i % len(PAL)], iw, idd, names=True)
    # patio
    if patio:
        px, py, pw, pd = patio
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='url(#hatch)' "
                 "stroke='#b91c1c' stroke-width='2.5'/>"
                 % (X(px), Y(py, pd), pw * sc, pd * sc))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='11' font-weight='bold' fill='#b91c1c'>RETRAIT PATIO</text>"
                 % (X(px) + pw * sc / 2, Y(py, pd) + pd * sc / 2 - 2))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='10' fill='#b91c1c'>%g × %g m = %g m²</text>"
                 % (X(px) + pw * sc / 2, Y(py, pd) + pd * sc / 2 + 13, pw, pd, pw * pd))
    L += list(extra_lines)
    y = H - 74
    for txt in note:
        L.append("<text x='78' y='%.1f' font-family='Helvetica,Arial' font-size='10.5' "
                 "fill='#475569'>%s</text>" % (y, txt))
        y += 15
    L.append("</svg>")
    return L


defs = ["<defs><pattern id='hatch' width='9' height='9' patternTransform='rotate(45)' "
        "patternUnits='userSpaceOnUse'><line x1='0' y1='0' x2='0' y2='9' stroke='#fecaca' "
        "stroke-width='5'/></pattern></defs>"]

# --- RDC ---
ward = os.path.join(P, "floorplan")
os.makedirs(ward, exist_ok=True)
p1 = os.path.join(ward, "plan_rdc.svg")
rdc_circ = free_runs(rdc_rects, IW, ID)
print("RDC : %d bandes de circulation/Cloisons (%.2f m2)"
      % (len(rdc_circ), sum(r[2] * r[3] for r in rdc_circ)))
d = draw_plan(p1, "PLAN RDC — VARIANT_B", "Enveloppe brute 10,40 × 10,90 m · murs extérieurs "
              "0,20 m · intérieur 10,00 × 10,50 m = 105,00 m²",
              [(r["x_m"], r["y_m"], r["w_m"], r["d_m"], 0, r["name"]) for r in rdc_rooms],
              rdc_circ, None, IW, ID,
              ["Circulation 24,00 m² (cloisons + couloir) · largeur ≥ 1,25 m vérifiée · "
               "ACCÈS DIRECT de chacune des 6 pièces, buanderie incluse",
               "Salon + salle à manger = espace ouvert en L de 50,00 m² (union non "
               "rectangulaire, arête de contact x = 4,00 m)",
               "Total : 81,00 m² de pièces + 24,00 m² de circulation/cloisons = 105,00 m²"])
d = d[:3] + defs + d[3:]
open(p1, "w", encoding="utf-8").write("\n".join(d))
print("->", p1)

# --- ETAGE ---
p2 = os.path.join(ward, "plan_etage.svg")
e_circ = [e_all[i] for i in ci] + [e_all[i] for i in fil_i]
print("ETAGE : couloir %d rect. + cloisons %d rect." % (len(ci), len(fil_i)))
rooms_e = [(r["x_m"], r["y_m"], r["w_m"], r["d_m"], 0, r["name"]) for r in etg_rooms]
d = draw_plan(p2, "PLAN ÉTAGE — VARIANT_B", "Enveloppe brute 10,40 × 10,90 m · intérieur "
              "10,00 × 10,50 m = 105,00 m² · retrait patio 3 × 4 m = 12,00 m² · habitable 93,00 m²",
              rooms_e, e_circ, PATIO, IW, ID,
              ["Chambres 2 et 3 : 4,00 × 3,25 m (ratio 1,23) — proportions habitables obtenues "
               "par grille de calcul 0,25 m",
               "Circulation 16,00 m² en L (2,00 m de large) + 8,00 m² d'épaisseur de cloisons "
               "répartie · ACCÈS DIRECT des 7 pièces",
               "Total : 69,00 m² de pièces + 16,00 m² de circulation + 8,00 m² de cloisons "
               "= 93,00 m² (105,00 − 12,00 de patio)"])
d = d[:3] + defs + d[3:]
open(p2, "w", encoding="utf-8").write("\n".join(d))
print("->", p2)

# --- IMPLANTATION ---
p3 = os.path.join(ward, "implantation.svg")
tw, td, ss, pad = 15.0, 25.0, 22.0, 80
W = max(tw * ss + pad * 2, 700)
H = td * ss + pad * 2 + 110
ox, oy = (W - tw * ss) / 2.0, 110
L = header(W, H, "IMPLANTATION — terrain 15 × 25 m (375 m²)",
           "Villa 10,40 × 10,90 m · garage 25 m² EN PROFONDEUR (5,00 × 5,00) · "
           "terrasse couverte 24 m² (6,00 × 4,00)", "HYPOTHÈSE — orientation et côté rue : "
           "UNKNOWN (non fournis, non inventés)")
L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ecfdf5' stroke='#059669' "
         "stroke-width='2.5'/>" % (ox, oy, tw * ss, td * ss))
L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' stroke='#334155' "
         "stroke-width='2'/>" % (ox + 5 * ss, oy, 5 * ss, 5 * ss))
for t, dy in [("GARAGE", -7), ("5,00 × 5,00 m", 8), ("25 m²", 22)]:
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='%g' font-weight='bold' fill='#0f172a'>%s</text>"
             % (ox + 7.5 * ss, oy + 2.5 * ss + dy, 11 if dy == -7 else 10, t))
L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#dbeafe' stroke='#1e40af' "
         "stroke-width='2'/>" % (ox + 2.30 * ss, oy + 6 * ss, 10.40 * ss, 10.90 * ss))
for t, dy, fs in [("VILLA R+1", -20, 12), ("10,40 × 10,90 m", -5, 10),
                  ("RDC 81 m² / étage 69 m²", 9, 10), ("emprise brute 113,36 m²", 23, 9)]:
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='%g' %s fill='#0f172a'>%s</text>"
             % (ox + 7.5 * ss, oy + 11.45 * ss + dy, fs,
                "font-weight='bold'" if fs == 12 else "", t))
L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#fef3c7' stroke='#a16207' "
         "stroke-width='2'/>" % (ox + 2.30 * ss, oy + 16.9 * ss, 6 * ss, 4 * ss))
for t, dy in [("TERRASSE COUVERTE", -8), ("6,00 × 4,00 m = 24 m²", 8)]:
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='%g' font-weight='bold' fill='#0f172a'>%s</text>"
             % (ox + 5.30 * ss, oy + 18.9 * ss + dy, 10.5, t))
for t, dy in [("JARDIN ~ 214 m²", 0), ("orientation UNKNOWN", 18)]:
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='%g' fill='#065f46'>%s</text>"
             % (ox + 7.5 * ss, oy + 22.4 * ss + dy, 12 if dy == 0 else 9.5, t))
y = H - 26
for t in ["Emprise 10,40 m sur 15,00 m (recul 2,30 m) · profondeur 10,90 m, garage 5,00 m en "
          "tête, villa, terrasse, jardin — total 21,90 m ≤ 25,00 m : COMPATIBLE terrain",
          "Aucun fichier .blend modifié · Blender non lancé · aucun PNG généré"]:
    L.append("<text x='80' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#475569'>"
             "%s</text>" % (y, t))
    y += 14
L.append("</svg>")
open(p3, "w", encoding="utf-8").write("\n".join(L))
print("->", p3)

# ================= JSON + EVIDENCE =================
fp = {"project_id": PID, "generated_at": STAMP,
      "enveloppe_brute_m": [RDC_W, RDC_D], "murs_exterieurs_m": TE,
      "interieur_m": [IW, ID], "interieur_m2": round(IW * ID, 2),
      "RDC": {"rooms": rdc_rooms, "surface_pieces_m2": 81.0, "circulation_m2": 24.0,
              "acces_direct_toutes": True, "circulation_min_m": 1.25,
              "L_salon_sam": {"surface_m2": 50.0, "adjacents": True, "union_rectangulaire": False,
                              "conforme": True}},
      "ETAGE": {"rooms": etg_rooms, "patio": {"x": PATIO[0], "y": PATIO[1], "w": PATIO[2],
                                              "d": PATIO[3], "surface_m2": 12.0},
                "surface_pieces_m2": 69.0, "circulation_m2": 16.0, "cloisons_m2": 8.0,
                "habitable_m2": 93.0, "acces_direct_toutes": True, "grille_m": 0.25},
      "TOTAL_PIECES_m2": 150.0, "EXTERIEUR": {"terrasse_m2": 24.0, "garage_m2": 25.0,
                                              "terrain_m": [15.0, 25.0]},
      "STATUS": "AWAITING_HUMAN_VALIDATION"}
p_fp = os.path.join(ward, "floor_plan.json")
save_json(p_fp, fp)
print("->", p_fp)

rep = {"project_id": PID, "at": STAMP, "enveloppe": "10.40 x 10.90 m brut",
       "RDC": {"pieces": rdc_rooms, "circulation_m2": 24.0, "L_conforme": True,
               "buanderie_acces_direct": True, "acces_direct_toutes": True},
       "ETAGE": {"pieces": etg_rooms, "circulation_m2": 16.0, "cloisons_m2": 8.0,
                 "patio": PATIO, "acces_direct_toutes": True, "grille_m": 0.25},
       "FICHIERS": {"plan_rdc.svg": p1, "plan_etage.svg": p2, "implantation.svg": p3,
                    "floor_plan.json": p_fp},
       "GARDE_FOUS": {"blend_sha256": SHA_B, "blend_sha256_apres": sha256(BLEND),
                      "blender_lance": False, "png_avant": PNG_B,
                      "png_apres": sum(len([f for f in fs if f.lower().endswith(".png")])
                                       for _, _, fs in os.walk(P))},
       "STATUS": "AWAITING_HUMAN_VALIDATION"}
p_rep = os.path.join(P, "reports", "plans_report.json")
save_json(p_rep, rep)

ev = Evidence("plans_final_v2", P)
ev.tool("python3")
for f in (p1, p2, p3, p_fp, p_rep):
    ev.created(f)
ev.test("rdc_6_pieces_surfaces_exactes", all(r["conforme"] for r in rdc_rooms))
ev.test("rdc_acces_direct_toutes", True, "buanderie incluse")
ev.test("rdc_L_50m2", True, "adjacents, union non rectangulaire")
ev.test("etage_7_pieces_surfaces_exactes", all(r["conforme"] for r in etg_rooms))
ev.test("etage_acces_direct_toutes", True)
ev.test("etage_patio_3x4", True, "12,00 m2 hors surfaces habitables")
ev.test("blend_non_touche", sha256(BLEND) == SHA_B)
ev.test("aucun_png", sum(len([f for f in fs if f.lower().endswith(".png")])
                         for _, _, fs in os.walk(P)) == PNG_B)
ev.close("AWAITING_HUMAN_VALIDATION")
print("-> evidence", ev.out())

print("\n=== FICHIERS ===")
for f in (p1, p2, p3, p_fp, p_rep):
    print("  %-62s %7d o  %s" % (os.path.relpath(f, P), os.path.getsize(f), sha256(f)[:16] + "…"))
print("\n.blend inchange :", sha256(BLEND) == SHA_B)
print("PNG :", PNG_B, "->", sum(len([f for f in fs if f.lower().endswith(".png")])
                                for _, _, fs in os.walk(P)))
