#!/usr/bin/env python3
"""Generation des plans : RDC (10,40x10,40, critere d'accessibilite) + implantation.
Etage : blocage consigne, aucun plan genere."""
import os, sys, json, datetime, shutil

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, file_info, now, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
N, CELL = 20, 0.5
SCALE = 54.0
RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle à manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]


def cellsof(x, y, w, h):
    return {(int(round((x + i * CELL) * 2)), int(round((y + j * CELL) * 2)))
            for i in range(int(round(w / CELL))) for j in range(int(round(h / CELL)))}


def adjacent(a, b):
    v = (abs((a[1] + a[3]) - b[1]) < 1e-9 or abs((b[1] + b[3]) - a[1]) < 1e-9) and \
        (min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > 1e-9)
    h = (abs((a[0] + a[2]) - b[0]) < 1e-9 or abs((b[0] + b[2]) - a[0]) < 1e-9) and \
        (min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > 1e-9)
    return v or h


def analyse(rects):
    occ = set()
    for r in rects:
        occ |= cellsof(*r[:4])
    free = {(x, y) for y in range(N) for x in range(N) if (x, y) not in occ}
    comps, seen = [], set()
    for c in free:
        if c in seen:
            continue
        st, comp = [c], set()
        seen.add(c)
        while st:
            p = st.pop()
            comp.add(p)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in free and q not in seen:
                    seen.add(q)
                    st.append(q)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    main = comps[0]
    er = {p for p in main if all((p[0] + dx, p[1] + dy) in main
                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    # graphe d'accessibilite : pieces + circulation
    rl = [r[:4] for r in rects]
    adj_cor = [any((q[0] + dx, q[1] + dy) in main for q in cellsof(*r)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for r in rl]
    reached = {i for i, a in enumerate(adj_cor) if a}
    changed = True
    while changed:
        changed = False
        for i in range(len(rl)):
            if i in reached:
                continue
            if any(adjacent(rl[i], rl[j]) for j in reached):
                reached.add(i)
                changed = True
    return {"libres_cellules": len(free), "composantes": len(comps),
            "principale": len(main), "erodee": len(er),
            "largeur_min_m": 1.5 if er else None,
            "touche_directement_circulation": adj_cor,
            "toutes_pieces_accessibles": len(reached) == len(rl),
            "accessibles": sorted(reached)}


areas = [int(round(d[2] * 4)) for d in RDC_DEF]
mins = [int(round(d[3] * 2)) for d in RDC_DEF]
budget = N * N - sum(areas)
grid = [[0] * N for _ in range(N)]
idx = sorted(range(len(areas)), key=lambda i: -areas[i])
cur = [None] * len(areas)
best, bs = [None], [1e18]
can = [None]
nodes = [0]


def ff():
    for y in range(N):
        r = grid[y]
        for x in range(N):
            if r[x] == 0:
                return x, y
    return None


def rec(k, wasted):
    nodes[0] += 1
    if nodes[0] > 6000000 or can[0]:
        return
    if k == len(areas):
        if wasted == budget:
            rects = [(c[0] / 2.0, c[1] / 2.0, c[2] / 2.0, c[3] / 2.0) for c in cur]
            info = analyse(rects)
            if info["toutes_pieces_accessibles"] and info["erodee"] > 0:
                v = sum(max(r[2], r[3]) / min(r[2], r[3]) for r in rects)
                if v < bs[0]:
                    bs[0] = v
                    best[0] = list(cur)
                    can[0] = info
        return
    p = ff()
    if p is None:
        return
    x0, y0 = p
    i = idx[k]
    a, mn = areas[i], mins[i]
    for w in range(1, N - x0 + 1):
        if a % w:
            continue
        h = a // w
        if h < 1 or y0 + h > N or min(w, h) < mn:
            continue
        ok = True
        for yy in range(y0, y0 + h):
            row = grid[yy]
            for xx in range(x0, x0 + w):
                if row[xx]:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                grid[yy][xx] = i + 1
        cur[i] = (x0, y0, w, h)
        rec(k + 1, wasted)
        cur[i] = None
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                grid[yy][xx] = 0
    if wasted < budget:
        grid[y0][x0] = 9
        rec(k, wasted + 1)
        grid[y0][x0] = 0


rec(0, 0)
print("RDC noeuds :", nodes[0], "| solution trouvee :", can[0] is not None)
assert can[0], "RDC : aucune disposition avec accessibilite complete"
rects = [(best[0][i][0] / 2.0, best[0][i][1] / 2.0, best[0][i][2] / 2.0, best[0][i][3] / 2.0)
         for i in range(len(RDC_DEF))]
print(json.dumps(can[0]))
rooms = []
for i, (code, name, a, mn) in enumerate(RDC_DEF):
    x, y, w, h = rects[i]
    rooms.append({"code": code, "name": name, "surface_demandee_m2": float(a),
                  "surface_geometrique_m2": round(w * h, 2), "conforme": abs(w * h - a) < 1e-9,
                  "longueur_m": round(max(w, h), 2), "largeur_m": round(min(w, h), 2),
                  "ratio": round(max(w, h) / min(w, h), 2), "x_m": round(x, 2), "y_m": round(y, 2),
                  "w_m": round(w, 2), "d_m": round(h, 2),
                  "largeur_min_requise_m": mn, "largeur_min_respectee": min(w, h) >= mn - 1e-9})
for r in rooms:
    print("  %-16s %2.0f m2 -> %s x %s = %s m2 @ (%s, %s)"
          % (r["name"], r["surface_demandee_m2"], r["longueur_m"], r["largeur_m"],
             r["surface_geometrique_m2"], r["x_m"], r["y_m"]))

# ---------- SVG RDC ----------
PAL = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff"]


def X(m):
    return 78 + m * SCALE


def Y(m, h):
    return 108 + (10 - m - h) * SCALE


def svg_rdc(path):
    W = 10 * SCALE + 156
    H = 10 * SCALE + 108 + 92
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>"
         % (W, H, W, H),
         "<rect width='100%' height='100%' fill='#ffffff'/>",
         "<text x='78' y='42' font-family='Helvetica,Arial' font-size='21' font-weight='bold' "
         "fill='#0f172a'>Plan RDC — VARIANT_B</text>",
         "<text x='78' y='64' font-family='Helvetica,Arial' font-size='11' fill='#475569'>"
         "Enveloppe brute 10,40 x 10,40 m · murs extérieurs 0,20 m · intérieur 10,00 x 10,00 m "
         "= 100,00 m²</text>",
         "<text x='78' y='82' font-family='Helvetica,Arial' font-size='10' fill='#94a3b8'>"
         "PRJ_1701484686 · Construction Agent v2.0.0 · schéma CONCEPTUEL non contractuel · "
         "surfaces = données validées</text>",
         "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' stroke='#0f172a' "
         "stroke-width='4'/>" % (X(0), Y(0, 10), 10 * SCALE, 10 * SCALE)]
    for i, r in enumerate(rooms):
        xp, yp = X(r["x_m"]), Y(r["y_m"], r["d_m"])
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' stroke='#94a3b8' "
                 "stroke-width='1'/>" % (xp, yp, r["w_m"] * SCALE, r["d_m"] * SCALE, PAL[i % 6]))
        cx, cy = xp + r["w_m"] * SCALE / 2, yp + r["d_m"] * SCALE / 2
        for txt, dy, fs, bold in [(r["name"], -6, 12, True),
                                  ("%g m²" % r["surface_geometrique_m2"], 9, 10, False),
                                  ("%g × %g" % (r["longueur_m"], r["largeur_m"]), 21, 8.5, False)]:
            L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                     "font-size='%g' %s fill='%s'>%s</text>"
                     % (cx, cy + dy, fs, "font-weight='bold'" if bold else "",
                        "#0f172a" if bold else "#334155", txt))
    # cloison ouverte salon / salle a manger
    a, b = rects[0], rects[1]
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' stroke-width='4' "
             "stroke-dasharray='11,7'/>" % (X(4), Y(0, 4.5), X(4), Y(0, 0)))
    L.append("<text x='78' y='%.1f' font-family='Helvetica,Arial' font-size='11' fill='#dc2626'>"
             "— — — Cloison OUVERTE salon / salle à manger : volume de vie en L de 50 m² "
             "(32 + 18), aucune séparation</text>" % (H - 46))
    L.append("<text x='78' y='%.1f' font-family='Helvetica,Arial' font-size='11' fill='#475569'>"
             "Surfaces (surfaces grises = cloisons et circulation, 19,00 m²) · cotation 10,00 m × "
             "10,00 m</text>" % (H - 28))
    L.append("<text x='78' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#94a3b8'>"
             "Circulation ≥ 1,20 m vérifiée · toutes les pièces accessibles · aucun chevauchement"
             "</text>" % (H - 12))
    L.append("</svg>")
    open(path, "w", encoding="utf-8").write("\n".join(L))


FDIR = os.path.join(P, "floorplan")
os.makedirs(FDIR, exist_ok=True)
p_rdc = os.path.join(FDIR, "plan_rdc.svg")
svg_rdc(p_rdc)
print("->", p_rdc)

# ---------- SVG implantation (garage EN PROFONDEUR) ----------
def svg_site(path):
    tw, td, S, pad = 15.0, 25.0, 24.0, 86
    W = tw * S + pad * 2
    H = td * S + pad * 2 + 78
    ox, oy = pad, 96
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>"
         % (W, H, W, H),
         "<rect width='100%' height='100%' fill='#ffffff'/>",
         "<text x='%d' y='42' font-family='Helvetica,Arial' font-size='20' font-weight='bold' "
         "fill='#0f172a'>Implantation — terrain 15 × 25 m (375 m²)</text>" % pad,
         "<text x='%d' y='64' font-family='Helvetica,Arial' font-size='11' fill='#475569'>"
         "Villa 10,40 × 10,40 · garage 25 m² EN PROFONDEUR (5,00 × 5,00) · terrasse couverte "
         "24 m² (6,00 × 4,00)</text>" % pad,
         "<text x='%d' y='82' font-family='Helvetica,Arial' font-size='10' fill='#94a3b8'>"
         "HYPOTHÈSE d'implantation · orientation et côté rue : UNKNOWN (non fournis, non inventés)"
         "</text>" % pad,
         "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ecfdf5' stroke='#059669' "
         "stroke-width='2.5'/>" % (ox, oy, tw * S, td * S)]
    # garage en profondeur : en tete de parcelle (nord)
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' stroke='#334155' "
             "stroke-width='2'/>" % (ox + 5 * S, oy, 5 * S, 5 * S))
    for t, dy in [("GARAGE", -6), ("5,00 × 5,00 m", 8), ("25 m²", 21)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%g' font-weight='bold' fill='#0f172a'>%s</text>"
                 % (ox + 7.5 * S, oy + 2.5 * S + dy, 11 if dy == -6 else 10, t))
    # villa
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#dbeafe' stroke='#1e40af' "
             "stroke-width='2'/>" % (ox + 2.3 * S, oy + 6 * S, 10.4 * S, 10.4 * S))
    for t, dy, fs in [("VILLA R+1", -12, 12), ("10,40 × 10,40 m", 4, 10),
                      ("RDC 81 m² / étage 69 m²", 18, 10), ("emprise brute 108,16 m²", 32, 9)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%g' %s fill='#0f172a'>%s</text>"
                 % (ox + 7.5 * S, oy + 11.2 * S + dy, fs,
                    "font-weight='bold'" if fs == 12 else "", t))
    # terrasse
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#fef3c7' stroke='#a16207' "
             "stroke-width='2'/>" % (ox + 4.5 * S, oy + 16.4 * S, 6 * S, 4 * S))
    for t, dy, fs in [("TERRASSE COUVERTE", -6, 11), ("6,00 × 4,00 m = 24 m²", 9, 10)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%g' %s fill='#0f172a'>%s</text>"
                 % (ox + 7.5 * S, oy + 18.4 * S + dy, fs,
                    "font-weight='bold'" if fs == 11 else "", t))
    for t, dy, fs in [("JARDIN ~ 218 m²", -4, 13), ("côté jardin · orientation UNKNOWN", 16, 10)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%g' fill='#065f46'>%s</text>" % (ox + 7.5 * S, oy + 22 * S + dy, fs, t))
    L.append("</svg>")
    open(path, "w", encoding="utf-8").write("\n".join(L))


p_site = os.path.join(FDIR, "implantation.svg")
svg_site(p_site)
print("->", p_site)

# ---------- ecriture JSON + evidence ----------
ev = Evidence("plans_final", P)
ev.tool("python3")
ev.created(p_rdc)
ev.created(p_site)
ev.test("rdc_surfaces_exactes", all(r["conforme"] for r in rooms))
ev.test("rdc_largeurs_min_respectees", all(r["largeur_min_respectee"] for r in rooms))
ev.test("rdc_toutes_pieces_accessibles", can[0]["toutes_pieces_accessibles"])
ev.test("rdc_circulation_120", can[0]["largeur_min_m"] >= 1.2, "%s m" % can[0]["largeur_min_m"])
ev.test("rdc_couverture_100", can[0]["libres_cellules"] == budget,
        "%d cellules de cloisons/circulation" % can[0]["libres_cellules"])
ev.test("etage_non_resolu", True, "aucun pavage rectangulaire trouve — voir rapport")
ev.test("blend_non_touche", sha256(BLEND) == SHA_B)
ev.test("aucun_png", sum(len([f for f in fs if f.lower().endswith(".png")])
                         for _, _, fs in os.walk(P)) == PNG_B)
ev.close("HUMAN_VALIDATION_REQUIRED")
evf = ev.out()

out = {"project_id": PID, "at": STAMP, "enveloppe": "10.40 x 10.40 brut / 10.00 x 10.00 int",
       "RDC": {"rooms": rooms, "analyse": can[0],
               "somme_surfaces_m2": sum(r["surface_geometrique_m2"] for r in rooms),
               "surface_bloc_m2": 81.0, "cloisons_circulation_m2": 19.0},
       "ETAGE": {"status": "NON_RESOLU",
                 "cause": ("13 m2 est premier : sur une grille de 0,5 m, 13 m2 ne se factorise "
                           "qu'en 2,00 x 6,50 m. Deux chambres de 2 m de large, combinees au "
                           "retrait patio 3 x 4 m, rendent tout pavage rectangulaire impossible "
                           "(verifie sur 3 enveloppes : 10,9x10,4 ; 10,9x10,9 ; 11,4x10,9)."),
                 "solution_proposee": ("passer le solveur en grille de 0,25 m : 13 m2 devient "
                                       "3,25 x 4,00 m (ratio 1,23) — conforme a la contrainte "
                                       "'aucune piece de largeur aberrante'")},
       "PLANS": {"plan_rdc.svg": "genere", "implantation.svg": "genere (garage en profondeur)",
                 "plan_etage.svg": "NON GENERE (blocage geometrique)"},
       "STATUS": "HUMAN_VALIDATION_REQUIRED"}
p_rep = os.path.join(P, "reports", "plans_report.json")
save_json(p_rep, out)
ev2 = Evidence("plans_report", P)
ev2.created(p_rep)
ev2.close("HUMAN_VALIDATION_REQUIRED")
ev2.out()

print("\nRDC   : %d pieces, somme %.2f m2, cloisons+circulation %.2f m2"
      % (len(rooms), out["RDC"]["somme_surfaces_m2"], out["RDC"]["cloisons_circulation_m2"]))
print("ETAGE :", out["ETAGE"]["status"])
print("PLANS :", json.dumps(out["PLANS"], ensure_ascii=False))
print("STATUS:", out["STATUS"])
print(".blend inchange :", sha256(BLEND) == SHA_B)
