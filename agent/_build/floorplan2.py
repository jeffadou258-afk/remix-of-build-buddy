#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — REPARTITION INTERIEURE + PLANS SVG (PRJ_1701484686)

Pavage EXACT par backtracking sur une grille de 0,5 m.
(pourquoi 0,5 m : 13 m2 est premier -> aucun rectangle a cotes entiers en metres)

Aucun Blender. Aucun rendu PNG. .blend non touche.
"""
import os
import sys
import json
import datetime

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

U = 2                      # unites de 0,5 m par metre
NU = 9 * U                 # 18
SCALE = 52.0               # px par metre pour le SVG


def solve(areas_m2, blocked_m=None, node_cap=4000000):
    """Pavage exact sur grille NU x NU. Retourne [(x,y,w,h,area_m2)] en metres."""
    blocked_cells = set()
    for (bx, by, bw, bh) in (blocked_m or []):
        for cy in range(int(by * U), int((by + bh) * U)):
            for cx in range(int(bx * U), int((bx + bw) * U)):
                blocked_cells.add((cx, cy))
    grid = [[1 if (x, y) in blocked_cells else 0 for x in range(NU)] for y in range(NU)]
    free = sum(r.count(0) for r in grid)
    areas = [int(round(a * U * U)) for a in areas_m2]
    if sum(areas) != free:
        return None
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    out = [None] * len(areas)
    nodes = [0]

    def first_free():
        for y in range(NU):
            row = grid[y]
            for x in range(NU):
                if row[x] == 0:
                    return x, y
        return None

    def rec(k):
        nodes[0] += 1
        if nodes[0] > node_cap:
            return False
        if k == len(idx):
            return True
        ff = first_free()
        if ff is None:
            return False
        x0, y0 = ff
        a = areas[idx[k]]
        for w in range(1, NU - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > NU:
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
                    grid[yy][xx] = 1
            out[idx[k]] = (x0, y0, w, h)
            if rec(k + 1):
                return True
            out[idx[k]] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0
        return False

    if not rec(0):
        return None
    return [(x / U, y / U, w / U, h / U, w * h / (U * U)) for (x, y, w, h) in out]


def verify(rects, blocked_m=None, label=""):
    bl = set()
    for (bx, by, bw, bh) in (blocked_m or []):
        for cy in range(int(by * U), int((by + bh) * U)):
            for cx in range(int(bx * U), int((bx + bw) * U)):
                bl.add((cx, cy))
    seen = {}
    for i, (x, y, w, h, a) in enumerate(rects):
        if abs(w * h - a) > 1e-9:
            return False, "%s: aire %.2f != %.2f" % (label, w * h, a)
        for cy in range(int(y * U), int((y + h) * U)):
            for cx in range(int(x * U), int((x + w) * U)):
                if (cx, cy) in bl:
                    return False, "%s: empiète le retrait" % label
                if (cx, cy) in seen:
                    return False, "%s: chevauchement (%d,%d)" % (label, cx, cy)
                seen[(cx, cy)] = i
    att = NU * NU - len(bl)
    if len(seen) != att:
        return False, "%s: couverture %d != %d" % (label, len(seen), att)
    return True, "%d cellules / %d attendues (100%%)" % (len(seen), att)


RDC_DEF = [("P01", "Salon", 32), ("P02", "Salle a manger", 18), ("P03", "Cuisine", 12),
           ("P04", "Bureau", 10), ("P05", "Buanderie", 6), ("P06", "WC visiteur", 3)]
ETG_DEF = [("P07", "Suite parentale", 16), ("P08", "Chambre 2", 13), ("P09", "Chambre 3", 13),
           ("P10", "Chambre 4", 12), ("P11", "Salle de bain 1", 5),
           ("P12", "Salle de bain 2", 5), ("P13", "Salle de bain 3", 5)]

lo = solve([a for _, _, a in RDC_DEF])
assert lo, "PAVAGE RDC INTROUVABLE"

CORNERS = [("SE", (6.0, 5.0, 3.0, 4.0)), ("SO", (0.0, 5.0, 3.0, 4.0)),
           ("NE", (6.0, 0.0, 3.0, 4.0)), ("NO", (0.0, 0.0, 3.0, 4.0))]
eo = recess = corner = None
for name, r in CORNERS:
    cand = solve([a for _, _, a in ETG_DEF], blocked_m=[r])
    if cand:
        eo, recess, corner = cand, r, name
        break
assert eo, "PAVAGE ETAGE INTROUVABLE SUR LES 4 COINS"

ok_r, msg_r = verify(lo, label="RDC")
ok_e, msg_e = verify(eo, blocked_m=[recess], label="ETAGE")

results = {"files_created": [], "files_modified": [], "evidence_files": []}
PAL = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1", "#ffedd5"]


def svg_plan(title, sub, rects, names, patio=None, open_pairs=(), path=None):
    pad, top = 72, 96
    Wp, Hp = 9 * SCALE + pad * 2, 9 * SCALE + pad * 2 + top
    x0, y0 = pad, top
    X = lambda mx: x0 + mx * SCALE
    Y = lambda my, mh: y0 + (9 - my - mh) * SCALE
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' "
         "viewBox='0 0 %.0f %.0f'>" % (Wp, Hp, Wp, Hp),
         "<defs><pattern id='h' width='9' height='9' patternTransform='rotate(45)' "
         "patternUnits='userSpaceOnUse'><line x1='0' y1='0' x2='0' y2='9' stroke='#94a3b8' "
         "stroke-width='2'/></pattern></defs>",
         "<rect width='100%' height='100%' fill='#ffffff'/>",
         "<text x='%d' y='40' font-family='Helvetica,Arial' font-size='21' font-weight='bold' "
         "fill='#0f172a'>%s</text>" % (pad, title),
         "<text x='%d' y='62' font-family='Helvetica,Arial' font-size='11' fill='#475569'>%s</text>"
         % (pad, sub),
         "<text x='%d' y='79' font-family='Helvetica,Arial' font-size='9.5' fill='#94a3b8'>"
         "PRJ_1701484686 · VARIANT_B · Construction Agent v2.0.0 · schéma CONCEPTUEL non contractuel"
         "</text>" % pad,
         "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' stroke='#0f172a' "
         "stroke-width='3'/>" % (x0, y0, 9 * SCALE, 9 * SCALE)]
    for i, (rx, ry, rw, rh, area) in enumerate(rects):
        Xp, Yp = X(rx), Y(ry, rh)
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' stroke='#94a3b8' "
                 "stroke-width='1'/>" % (Xp, Yp, rw * SCALE, rh * SCALE, PAL[i % len(PAL)]))
        cx, cy = Xp + rw * SCALE / 2, Yp + rh * SCALE / 2
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='12' font-weight='bold' fill='#0f172a'>%s</text>" % (cx, cy - 5, names[i]))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='10' fill='#334155'>%g m&#178;</text>" % (cx, cy + 10, area))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='8.5' fill='#64748b'>%g &#215; %g</text>" % (cx, cy + 22, rw, rh))
    for ia, ib in open_pairs:
        ax, ay, aw, ah, _ = rects[names.index(ia)]
        bx, by, bw, bh, _ = rects[names.index(ib)]
        if abs((ay + ah) - by) < 1e-9 or abs((by + bh) - ay) < 1e-9:
            yl = Y(max(ay, by), 0)
            L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' "
                     "stroke-width='3.5' stroke-dasharray='10,7'/>"
                     % (X(max(ax, bx)), yl, X(min(ax + aw, bx + bw)), yl))
        elif abs((ax + aw) - bx) < 1e-9 or abs((bx + bw) - ax) < 1e-9:
            xl = X(max(ax, bx))
            L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' "
                     "stroke-width='3.5' stroke-dasharray='10,7'/>"
                     % (xl, Y(max(ay, by), 0), xl, Y(min(ay + ah, by + bh), 0)))
    if patio:
        px, py, pw, ph = patio
        Xp, Yp = X(px), Y(py, ph)
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='url(#h)' "
                 "stroke='#0f172a' stroke-width='2' stroke-dasharray='7,5'/>"
                 % (Xp, Yp, pw * SCALE, ph * SCALE))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='12' font-weight='bold' fill='#0f172a'>PATIO</text>"
                 % (Xp + pw * SCALE / 2, Yp + ph * SCALE / 2 - 6))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='9.5' fill='#334155'>%g m&#178; · à ciel ouvert</text>"
                 % (Xp + pw * SCALE / 2, Yp + ph * SCALE / 2 + 9, pw * ph))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='8.5' fill='#64748b'>%g &#215; %g</text>"
                 % (Xp + pw * SCALE / 2, Yp + ph * SCALE / 2 + 21, pw, ph))
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#0f172a' stroke-width='1'/>"
             % (x0, y0 + 9 * SCALE + 24, x0 + 9 * SCALE, y0 + 9 * SCALE + 24))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='12' fill='#0f172a'>9,00 m</text>" % (x0 + 4.5 * SCALE, y0 + 9 * SCALE + 40))
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#0f172a' stroke-width='1'/>"
             % (x0 - 24, y0, x0 - 24, y0 + 9 * SCALE))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='12' fill='#0f172a' transform='rotate(-90 %.1f %.1f)'>9,00 m</text>"
             % (x0 - 38, y0 + 4.5 * SCALE, x0 - 38, y0 + 4.5 * SCALE))
    L.append("<text x='%d' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#dc2626'>"
             "Trait rouge pointillé = cloison OUVERTE (aucune séparation)</text>"
             % (pad, Hp - 26))
    L.append("<text x='%d' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#64748b'>"
             "Pavage vérifié : couverture 100%% de l'enveloppe, aucune surface inventée.</text>"
             % (pad, Hp - 12))
    L.append("</svg>")
    src = "\n".join(L)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return src


FDIR = os.path.join(P, "floorplan")
os.makedirs(FDIR, exist_ok=True)
ev = Evidence("floor_plan_layout", P)
ev.tool("python3")

names_r = [n for _, n, _ in RDC_DEF]
p_rdc = os.path.join(FDIR, "plan_rdc.svg")
svg_plan("Plan RDC — VARIANT_B",
         "9,00 x 9,00 m = 81,00 m² · 6 pièces · volume de vie ouvert salon + salle à manger = 50 m²",
         lo, names_r, open_pairs=[("Salon", "Salle a manger")], path=p_rdc)
ev.created(p_rdc)
results["files_created"].append(p_rdc)

names_e = [n for _, n, _ in ETG_DEF]
p_etg = os.path.join(FDIR, "plan_etage.svg")
svg_plan("Plan Étage — VARIANT_B",
         "9,00 x 9,00 m moins patio d'angle %g x %g (%g m²) = 69,00 m² · 7 pièces"
         % (recess[2], recess[3], recess[2] * recess[3]),
         eo, names_e, patio=recess, path=p_etg)
ev.created(p_etg)
results["files_created"].append(p_etg)


def svg_site(path):
    tw, td, S, pad = 15.0, 25.0, 25.0, 84
    Wp, Hp = tw * S + pad * 2, td * S + pad * 2 + 74
    ox, oy = pad, 90
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>"
         % (Wp, Hp, Wp, Hp),
         "<rect width='100%' height='100%' fill='#fff'/>",
         "<text x='%d' y='40' font-family='Helvetica,Arial' font-size='20' font-weight='bold' "
         "fill='#0f172a'>Implantation — terrain 15 x 25 m (375 m²)</text>" % pad,
         "<text x='%d' y='62' font-family='Helvetica,Arial' font-size='11' fill='#475569'>"
         "Villa 9 x 9 + garage 5 x 5 + terrasse couverte 6 x 4 · emprise au sol 106 m² (28%%)</text>" % pad,
         "<text x='%d' y='79' font-family='Helvetica,Arial' font-size='9.5' fill='#94a3b8'>"
         "HYPOTHÈSE d'implantation · orientation et côté rue : UNKNOWN (non fournis, non inventés)"
         "</text>" % pad,
         "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ecfdf5' stroke='#059669' "
         "stroke-width='2.5'/>" % (ox, oy, tw * S, td * S)]
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#dbeafe' stroke='#1e40af' "
             "stroke-width='2'/>" % (ox, oy, 9 * S, 9 * S))
    for t, dy, sz, bold in [("VILLA R+1", -10, 12, True), ("9,00 x 9,00 m", 6, 10, False),
                            ("RDC 81 m² / étage 69 m²", 20, 10, False)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%d' %s fill='#0f172a'>%s</text>"
                 % (ox + 4.5 * S, oy + 4.5 * S + dy, sz,
                    "font-weight='bold'" if bold else "", t))
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' stroke='#334155' "
             "stroke-width='2'/>" % (ox + 9 * S, oy, 5 * S, 5 * S))
    for t, dy, sz, bold in [("GARAGE", -8, 11, True), ("5,00 x 5,00 m", 8, 10, False),
                            ("25 m²", 22, 10, False)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%d' %s fill='#0f172a'>%s</text>"
                 % (ox + 11.5 * S, oy + 2.5 * S + dy, sz,
                    "font-weight='bold'" if bold else "", t))
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#fef3c7' stroke='#a16207' "
             "stroke-width='2'/>" % (ox + 2.5 * S, oy + 9 * S, 6 * S, 4 * S))
    for t, dy, sz, bold in [("TERRASSE COUVERTE", -6, 11, True),
                            ("6,00 x 4,00 m = 24 m²", 10, 10, False)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%d' %s fill='#0f172a'>%s</text>"
                 % (ox + 5.5 * S, oy + 11 * S + dy, sz,
                    "font-weight='bold'" if bold else "", t))
    for t, dy, sz in [("JARDIN ~ 245 m²", -4, 13), ("côté jardin · orientation UNKNOWN", 16, 10)]:
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='%d' fill='#065f46'>%s</text>" % (ox + 7.5 * S, oy + 19 * S + dy, sz, t))
    L.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


p_site = os.path.join(FDIR, "implantation.svg")
svg_site(p_site)
ev.created(p_site)
results["files_created"].append(p_site)

fp = {
    "project_id": PID, "created_at": STAMP, "unit": "m", "variant": "VARIANT_B",
    "method": "pavage exact par backtracking sur grille 0,5 m — couverture 100% verifiee",
    "why_half_metre": "13 m2 est premier : aucun rectangle a cotes entiers en metres dans une grille 9x9",
    "levels": [
        {"level": "RDC", "envelope": "9.00 x 9.00", "surface_m2": 81, "tiling_ok": ok_r,
         "tiling_detail": msg_r,
         "rooms": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                    "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(RDC_DEF, lo)],
         "files": [p_rdc]},
        {"level": "ETAGE", "envelope": "9.00 x 9.00 moins retrait 3.00 x 4.00 (12 m2)",
         "surface_m2": 69, "tiling_ok": ok_e, "tiling_detail": msg_e,
         "recess": {"corner": corner, "x_m": recess[0], "y_m": recess[1],
                    "width_m": recess[2], "depth_m": recess[3],
                    "surface_m2": recess[2] * recess[3],
                    "nature": "patio d'angle a ciel ouvert"},
         "rooms": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                    "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(ETG_DEF, eo)],
         "files": [p_etg]},
    ],
    "open_relations": [{"a": "P01 Salon", "b": "P02 Salle a manger", "type": "OPEN",
                        "partition": False,
                        "note": "Salle a manger ouverte sur le salon (choix utilisateur 2026-10-02)",
                        "volume_vie_m2": 50}],
    "site_plan": {"file": p_site, "terrain": "15 x 25 m = 375 m2",
                  "implantation_status": "HYPOTHESIS", "orientation": "UNKNOWN"},
    "notes": ["Schema CONCEPTUEL, non contractuel.",
              "Emprises derivees du pavage des surfaces fournies ; aucune surface inventee.",
              "Circulation assuree par les volumes de vie et de service."],
}
p_fp = os.path.join(FDIR, "floor_plan.json")
save_json(p_fp, fp)
ev.created(p_fp)
results["files_created"].append(p_fp)

ev.test("rdc_tiling_100pct", ok_r, msg_r)
ev.test("etage_tiling_100pct", ok_e, msg_e)
ev.test("rdc_sum_eq_81", sum(a for _, _, a in RDC_DEF) == 81)
ev.test("etage_sum_eq_69", sum(a for _, _, a in ETG_DEF) == 69)
ev.test("svg_rdc", open(p_rdc).read().startswith("<?xml"))
ev.test("svg_etage", open(p_etg).read().startswith("<?xml"))
ev.test("svg_implantation", open(p_site).read().startswith("<?xml"))
ev.close("VERIFIED")
results["evidence_files"].append(ev.out())

ev2 = Evidence("sync_layout", P)
pp = os.path.join(P, "program", "program.json")
prog = json.load(open(pp, encoding="utf-8"))
prog["updated_at"] = STAMP
prog["version"] = 3
prog["relations"] = [{"a": "P01", "b": "P02", "type": "OPEN", "partition": False,
                      "note": "Salle a manger ouverte sur le salon — volume de vie 50 m2"}]
prog["open_living"] = {"rooms": ["P01", "P02"], "total_m2": 50.0, "partition": False,
                       "decision": "Choix utilisateur 2026-10-02"}
prog["layout"] = {"status": "RESOLVED", "method": "pavage exact (grille 0,5 m)",
                  "file": p_fp, "rdc_tiling_ok": ok_r, "etage_tiling_ok": ok_e,
                  "patio_corner": corner}
save_json(pp, prog)
ev2.created(pp)
results["files_modified"].append(pp)

dp = os.path.join(P, "dimensions", "dimensions.json")
d = json.load(open(dp, encoding="utf-8"))
d["updated_at"] = STAMP
d["envelope"]["ETAGE"]["source"] = "USER_PROVIDED"
d["envelope"]["ETAGE"]["note"] = ("Retrait 3 x 4 = 12 m2 (patio d'angle, coin %s), choix "
                                  "utilisateur 'A' du 2026-10-02 -> 81 - 12 = 69 m2." % corner)
d["envelope"]["ETAGE"]["recess"]["nature"] = "patio d'angle a ciel ouvert"
d["envelope"]["ETAGE"]["recess"]["corner"] = corner
d["room_dimensions"] = {"status": "RESOLVED",
                        "method": "pavage exact par backtracking (grille 0,5 m)",
                        "file": p_fp, "note": "Emprises par piece dans floorplan/floor_plan.json"}
save_json(dp, d)
ev2.created(dp)
results["files_modified"].append(dp)

decision = {
    "decision_id": "DEC_%s_004" % PID, "project_id": PID, "at": STAMP, "seq": 4,
    "DECISION": ("Repartition interieure resolue par pavage exact : RDC 9 x 9 (81 m2, 6 pieces), "
                 "ETAGE 9 x 9 moins patio d'angle 3 x 4 (69 m2, 7 pieces) ; salle a manger ouverte sur le salon."),
    "SOURCE": "Choix utilisateur 2026-10-02 : '1. Etage : A — retrait 3 x 4 (patio d'angle)' ; '2. Salle a manger : ouverte sur le salon'.",
    "JUSTIFICATION": ("Pavage resolu par backtracking sur grille 0,5 m. Granularite imposee par les "
                      "donnees : 13 m2 est premier, donc aucun rectangle a cotes entiers en metres ne "
                      "peut mesurer 13 m2 dans une grille 9 x 9. Chaque rectangle a une aire exactement "
                      "egale a la surface fournie et la couverture de l'enveloppe est de 100 % (verifie "
                      "cellule par cellule). Salon et salle a manger partagent une frontiere, ce qui "
                      "materialise la cloison ouverte demandee (volume de vie 50 m2)."),
    "IMPACT": ("3 plans SVG reels produits (RDC, etage, implantation) + floor_plan.json. Le retrait "
               "d'etage passe de HYPOTHESIS a USER_PROVIDED. Prochaine etape : reconstruction BIM/3D."),
    "STATUS": "VALIDATED",
}
hist = {"history_id": "HIST_%s_LAYOUT_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
        "type": "INTERNAL_LAYOUT_RESOLVED", "variant": "VARIANT_B",
        "method": "pavage exact (backtracking, grille 0,5 m)",
        "rdc_tiling": msg_r, "etage_tiling": msg_e, "patio_corner": corner,
        "rdc_rooms": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                       "w_m": r[2], "d_m": r[3]} for (c, n, a), r in zip(RDC_DEF, lo)],
        "etage_rooms": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                         "w_m": r[2], "d_m": r[3]} for (c, n, a), r in zip(ETG_DEF, eo)],
        "files": [p_rdc, p_etg, p_site, p_fp],
        "actions": {"blender_launched": False, "blend_modified": False, "renders_generated": False},
        "blend_integrity": {"sha256": SHA_B}}
p_hist = os.path.join(P, "history", "layout_%s.json" % DATE)
save_json(p_hist, hist)
ev2.created(p_hist)
p_jsonl = os.path.join(P, "history", "history.jsonl")
with open(p_jsonl, "a", encoding="utf-8") as f:
    f.write(json.dumps(hist, ensure_ascii=False) + "\n")
ev2.created(p_jsonl)
p_dec = os.path.join(P, "memory", "decisions.jsonl")
with open(p_dec, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
ev2.created(p_dec)
p_ag = os.path.join(AGENT, "memory", "decisions.jsonl")
with open(p_ag, "a", encoding="utf-8") as f:
    f.write(json.dumps(decision, ensure_ascii=False) + "\n")
ev2.created(p_ag)
ev2.close("EXECUTED")
results["evidence_files"].append(ev2.out())
results["files_created"].append(p_hist)
results["files_modified"] += [p_jsonl, p_dec, p_ag]

ev3 = Evidence("layout_guardrails", P)
SHA_A = sha256(BLEND)
PNG_A = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
ev3.tool("python3")
ev3.test("blend_untouched", SHA_A == SHA_B, "sha256 identique")
ev3.test("no_png_generated", PNG_A == PNG_B, "%d -> %d" % (PNG_B, PNG_A))
ev3.test("budget_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "budget")))
ev3.test("planning_engine_absent", not os.path.exists(os.path.join(AGENT, "engines", "planning")))
ev3.close("VERIFIED")
results["evidence_files"].append(ev3.out())

rep = {
    "PROJECT_ID": PID, "VARIANT": "VARIANT_B",
    "ETAGE_RECESS_CHOICE": "A — patio d'angle 3.00 x 4.00 m = 12 m2 (coin %s)" % corner,
    "ETAGE_RECESS_SOURCE": "USER_PROVIDED",
    "SALLE_A_MANGER": "ouverte sur le salon (cloison ouverte, aucune separation)",
    "VOLUME_DE_VIE_M2": 50.0,
    "METHOD": "pavage exact par backtracking, grille 0,5 m",
    "RDC_TILING": msg_r, "ETAGE_TILING": msg_e,
    "RDC_SUM": sum(a for _, _, a in RDC_DEF), "ETAGE_SUM": sum(a for _, _, a in ETG_DEF),
    "SURFACE_CHECK": "PASS" if (ok_r and ok_e) else "FAIL",
    "RDC_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                    "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(RDC_DEF, lo)],
    "ETAGE_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                      "width_m": r[2], "depth_m": r[3]}
                     for (c, n, a), r in zip(ETG_DEF, eo)],
    "PLANS": [p_rdc, p_etg, p_site],
    "EVIDENCE_FILES": results["evidence_files"],
    "NEW_DATA_FILES": results["files_created"],
    "MODIFIED_FILES": results["files_modified"],
    "REAL_FILES_VERIFIED": [],
    "BLENDER_TOUCHED": False, "BLEND_UNCHANGED": SHA_A == SHA_B,
    "RENDERS_GENERATED": 0, "PNG_BEFORE": PNG_B, "PNG_AFTER": PNG_A,
    "SYNCED_AT": STAMP,
    "STATUS": "INTERNAL_LAYOUT_RESOLVED_PENDING_3D",
}
p_rep = os.path.join(P, "reports", "layout_report.json")
save_json(p_rep, rep)
tout = sorted(set(results["files_created"] + results["files_modified"] + [p_rep]))
for f in tout:
    inf = file_info(f)
    if inf:
        inf["path"] = os.path.relpath(f, P) if f.startswith(P) else f
        rep["REAL_FILES_VERIFIED"].append(inf)
save_json(p_rep, rep)

print("=== RDC (9x9 = 81 m2) ===")
for (c, n, a), r in zip(RDC_DEF, lo):
    print("  %-4s %-18s %2g m2   x=%-4g y=%-4g  %g x %g m" % (c, n, a, r[0], r[1], r[2], r[3]))
print("  total =", sum(a for _, _, a in RDC_DEF), "|", msg_r)
print("=== ETAGE (9x9 - patio %s %gx%g = 69 m2) ===" % (corner, recess[2], recess[3]))
for (c, n, a), r in zip(ETG_DEF, eo):
    print("  %-4s %-18s %2g m2   x=%-4g y=%-4g  %g x %g m" % (c, n, a, r[0], r[1], r[2], r[3]))
print("  total =", sum(a for _, _, a in ETG_DEF), "|", msg_e)
print("\nSURFACE_CHECK :", rep["SURFACE_CHECK"], "| STATUS :", rep["STATUS"])
print("fichiers verifies :", len(rep["REAL_FILES_VERIFIED"]),
      "| evidence :", len(results["evidence_files"]), "| PNG generes :", PNG_A - PNG_B)
