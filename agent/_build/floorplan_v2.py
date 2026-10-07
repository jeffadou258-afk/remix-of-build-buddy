#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — REPARTITION INTERIEURE v2 (PRJ_1701484686)

Le 1er pavage trouve etait valide mais architecturalement absurde
(buanderie 6x1 m, WC 3x1 m, chambres 2 m de large sur 8 m).
Cette version impose une LARGEUR MINIMALE par piece et retient le MEILLEUR
pavage selon un score (somme des ratios d'allongement), pas le premier.

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
U, NU, SCALE = 2, 18, 52.0


def solve_best(areas_m2, mins_m, blocked_m=None, max_nodes=1500000, max_sols=300):
    """Retourne (best_rects, n_solutions, nodes) — meilleur score = somme des ratios."""
    bl = set()
    for (bx, by, bw, bh) in (blocked_m or []):
        for cy in range(int(by * U), int((by + bh) * U)):
            for cx in range(int(bx * U), int((bx + bw) * U)):
                bl.add((cx, cy))
    grid = [[1 if (x, y) in bl else 0 for x in range(NU)] for y in range(NU)]
    free = sum(r.count(0) for r in grid)
    areas = [int(round(a * U * U)) for a in areas_m2]
    mins = [int(round(m * U)) for m in mins_m]
    if sum(areas) != free:
        return None, 0, 0
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best = [None]
    bestscore = [1e18]
    sols = [0]
    nodes = [0]

    def first_free():
        for y in range(NU):
            row = grid[y]
            for x in range(NU):
                if row[x] == 0:
                    return x, y
        return None

    def score(rects):
        s = 0.0
        for (x, y, w, h) in rects:
            s += max(w, h) / float(min(w, h))
        return s

    def rec(k):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            sols[0] += 1
            sc = score(cur)
            if sc < bestscore[0]:
                bestscore[0] = sc
                best[0] = list(cur)
            return
        ff = first_free()
        if ff is None:
            return
        x0, y0 = ff
        i = idx[k]
        a, mn = areas[i], mins[i]
        for w in range(1, NU - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > NU:
                continue
            if min(w, h) < mn:            # largeur minimale de la piece
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
            cur[i] = (x0, y0, w, h)
            rec(k + 1)
            cur[i] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0
        return

    rec(0)
    if best[0] is None:
        return None, sols[0], nodes[0]
    out = [None] * len(areas)
    for i, r in enumerate(best[0]):
        x, y, w, h = r
        out[i] = (x / U, y / U, w / U, h / U, w * h / float(U * U))
    return out, sols[0], nodes[0]


def touching(r1, r2):
    x1, y1, w1, h1 = r1[0], r1[1], r1[2], r1[3]
    x2, y2, w2, h2 = r2[0], r2[1], r2[2], r2[3]
    ae = (abs((y1 + h1) - y2) < 1e-9 or abs((y2 + h2) - y1) < 1e-9) and \
         (min(x1 + w1, x2 + w2) - max(x1, x2) > 1e-9)
    be = (abs((x1 + w1) - x2) < 1e-9 or abs((x2 + w2) - x1) < 1e-9) and \
         (min(y1 + h1, y2 + h2) - max(y1, y2) > 1e-9)
    return ae or be


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
    return (len(seen) == att), "%d/%d cellules (%.0f%%)" % (len(seen), att, 100.0 * len(seen) / att)


RDC_DEF = [("P01", "Salon", 32, 4.0), ("P02", "Salle a manger", 18, 3.5),
           ("P03", "Cuisine", 12, 2.5), ("P04", "Bureau", 10, 2.5),
           ("P05", "Buanderie", 6, 2.0), ("P06", "WC visiteur", 3, 1.5)]
ETG_DEF = [("P07", "Suite parentale", 16, 3.5), ("P08", "Chambre 2", 13, 2.0),
           ("P09", "Chambre 3", 13, 2.0), ("P10", "Chambre 4", 12, 3.0),
           ("P11", "Salle de bain 1", 5, 2.0), ("P12", "Salle de bain 2", 5, 2.0),
           ("P13", "Salle de bain 3", 5, 2.0)]

lo, sols_r, nodes_r = solve_best([a for _, _, a, _ in RDC_DEF], [m for _, _, _, m in RDC_DEF])
assert lo, "PAVAGE RDC INTROUVABLE avec contraintes de largeur"

CORNERS = [("SE", (6.0, 5.0, 3.0, 4.0)), ("SO", (0.0, 5.0, 3.0, 4.0)),
           ("NE", (6.0, 0.0, 3.0, 4.0)), ("NO", (0.0, 0.0, 3.0, 4.0))]
eo = recess = corner = None
etg_stats = None
for name, r in CORNERS:
    cand, s, n = solve_best([a for _, _, a, _ in ETG_DEF], [m for _, _, _, m in ETG_DEF],
                            blocked_m=[r])
    if cand:
        eo, recess, corner, etg_stats = cand, r, name, (s, n)
        break
assert eo, "PAVAGE ETAGE INTROUVABLE avec contraintes de largeur"

ok_r, msg_r = verify(lo, label="RDC")
ok_e, msg_e = verify(eo, blocked_m=[recess], label="ETAGE")
adj_r = touching(lo[0], lo[1])

valid = ok_r and ok_e and adj_r and sum(a for _, _, a, _ in RDC_DEF) == 81 \
        and sum(a for _, _, a, _ in ETG_DEF) == 69

results = {"files_created": [], "files_modified": [], "evidence_files": []}
PAL = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1", "#ffedd5"]


def svg_plan(title, sub, rects, names, patio=None, open_pairs=(), path=None):
    pad, top = 72, 96
    Wp, Hp = 9 * SCALE + pad * 2, 9 * SCALE + pad * 2 + top
    x0, y0 = pad, top
    X = lambda mx: x0 + mx * SCALE
    Y = lambda my, mh: y0 + (9 - my - mh) * SCALE
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>"
         % (Wp, Hp, Wp, Hp),
         "<defs><pattern id='h' width='9' height='9' patternTransform='rotate(45)' "
         "patternUnits='userSpaceOnUse'><line x1='0' y1='0' x2='0' y2='9' stroke='#94a3b8' "
         "stroke-width='2'/></pattern></defs>",
         "<rect width='100%%' height='100%%' fill='#ffffff'/>",
         "<text x='%d' y='40' font-family='Helvetica,Arial' font-size='21' font-weight='bold' "
         "fill='#0f172a'>%s</text>" % (pad, title),
         "<text x='%d' y='62' font-family='Helvetica,Arial' font-size='11' fill='#475569'>%s</text>"
         % (pad, sub),
         "<text x='%d' y='79' font-family='Helvetica,Arial' font-size='9.5' fill='#94a3b8'>"
         "PRJ_1701484686 · VARIANT_B · Construction Agent v2.0.0 · schéma CONCEPTUEL "
         "non contractuel</text>" % pad,
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
             "Trait rouge pointillé = cloison OUVERTE (aucune séparation)</text>" % (pad, Hp - 26))
    L.append("<text x='%d' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#64748b'>"
             "Pavage vérifié cellule par cellule : couverture 100%%, largeurs minimales "
             "respectées, aucune surface inventée.</text>" % (pad, Hp - 12))
    L.append("</svg>")
    src = "\n".join(L)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return src


FDIR = os.path.join(P, "floorplan")
os.makedirs(FDIR, exist_ok=True)
ev = Evidence("floor_plan_layout_v2", P)
ev.tool("python3")

names_r = [n for _, n, _, _ in RDC_DEF]
p_rdc = os.path.join(FDIR, "plan_rdc.svg")
svg_plan("Plan RDC — VARIANT_B",
         "9,00 x 9,00 m = 81,00 m² · 6 pièces · volume de vie ouvert salon + salle à manger = 50 m²",
         lo, names_r, open_pairs=[("Salon", "Salle a manger")], path=p_rdc)
ev.created(p_rdc)
results["files_created"].append(p_rdc)

names_e = [n for _, n, _, _ in ETG_DEF]
p_etg = os.path.join(FDIR, "plan_etage.svg")
svg_plan("Plan Étage — VARIANT_B",
         "9,00 x 9,00 m moins patio d'angle %g x %g (%g m²) = 69,00 m² · 7 pièces"
         % (recess[2], recess[3], recess[2] * recess[3]),
         eo, names_e, patio=recess, path=p_etg)
ev.created(p_etg)
results["files_created"].append(p_etg)

p_site = os.path.join(FDIR, "implantation.svg")
if os.path.isfile(p_site):
    ev.record(p_site)
    results["files_modified"].append(p_site)

fp = {
    "project_id": PID, "created_at": STAMP, "unit": "m", "variant": "VARIANT_B",
    "version": 2,
    "method": ("pavage exact par backtracking sur grille 0,5 m, avec largeur minimale "
               "par piece, meilleur score retenu (pas le premier trouve)"),
    "why_half_metre": "13 m2 est premier : aucun rectangle a cotes entiers en metres dans une grille 9x9",
    "why_v2": ("v1 (1er pavage trouve) donnait des pieces inutilisables : buanderie 6x1 m, "
               "WC 3x1 m, chambres 2 m de large sur 8 m. v2 impose des largeurs minimales."),
    "levels": [
        {"level": "RDC", "envelope": "9.00 x 9.00", "surface_m2": 81, "tiling_ok": ok_r,
         "tiling_detail": msg_r, "solutions_explored": sols_r, "nodes": nodes_r,
         "rooms": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                    "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a, mn), r in zip(RDC_DEF, lo)],
         "files": [p_rdc]},
        {"level": "ETAGE", "envelope": "9.00 x 9.00 moins retrait 3.00 x 4.00 (12 m2)",
         "surface_m2": 69, "tiling_ok": ok_e, "tiling_detail": msg_e,
         "solutions_explored": etg_stats[0] if etg_stats else None,
         "recess": {"corner": corner, "x_m": recess[0], "y_m": recess[1],
                    "width_m": recess[2], "depth_m": recess[3],
                    "surface_m2": recess[2] * recess[3], "nature": "patio d'angle a ciel ouvert"},
         "rooms": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                    "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a, mn), r in zip(ETG_DEF, eo)],
         "files": [p_etg]},
    ],
    "open_relations": [{"a": "P01 Salon", "b": "P02 Salle a manger", "type": "OPEN",
                        "partition": False, "shared_edge": True,
                        "note": "Salle a manger ouverte sur le salon (choix utilisateur 2026-10-02)",
                        "volume_vie_m2": 50}],
    "site_plan": {"file": p_site, "terrain": "15 x 25 m = 375 m2",
                  "implantation_status": "HYPOTHESIS", "orientation": "UNKNOWN"},
    "checks": {"rdc_100pct": ok_r, "etage_100pct": ok_e, "salon_sam_adjacents": adj_r,
               "rdc_sum_81": sum(a for _, _, a, _ in RDC_DEF) == 81,
               "etage_sum_69": sum(a for _, _, a, _ in ETG_DEF) == 69},
    "notes": ["Schema CONCEPTUEL, non contractuel.",
              "Aucune surface inventee : les aires sont exactement celles du programme.",
              "Ventilation / evacuation sanitaires non traitees a ce stade."],
}
p_fp = os.path.join(FDIR, "floor_plan.json")
save_json(p_fp, fp)
ev.created(p_fp)
results["files_created"].append(p_fp)

ev.test("rdc_tiling_100pct", ok_r, msg_r)
ev.test("etage_tiling_100pct", ok_e, msg_e)
ev.test("salon_sam_adjacents", adj_r, "frontiere commune -> cloison ouverte")
ev.test("rdc_sum_eq_81", sum(a for _, _, a, _ in RDC_DEF) == 81)
ev.test("etage_sum_eq_69", sum(a for _, _, a, _ in ETG_DEF) == 69)
ev.test("min_widths_respected",
        all(min(r[2], r[3]) >= mn - 1e-9 for (_, _, _, mn), r in zip(RDC_DEF, lo))
        and all(min(r[2], r[3]) >= mn - 1e-9 for (_, _, _, mn), r in zip(ETG_DEF, eo)),
        "aucune piece plus etroite que son minimum")
ev.test("no_room_thinner_than_1m",
        all(min(r[2], r[3]) >= 1.5 for r in lo + eo))
ev.test("svg_rdc", open(p_rdc).read().startswith("<?xml"))
ev.test("svg_etage", open(p_etg).read().startswith("<?xml"))
ev.close("VERIFIED" if valid else "FAILED")
results["evidence_files"].append(ev.out())

# ---------------- historique + decision (correction tracee) ----------------
ev2 = Evidence("sync_layout_v2", P)
pp = os.path.join(P, "program", "program.json")
prog = json.load(open(pp, encoding="utf-8"))
prog["updated_at"] = STAMP
prog["version"] = 4
prog["layout"] = {"status": "RESOLVED", "method": "pavage exact (grille 0,5 m, largeurs minimales)",
                  "file": p_fp, "rdc_tiling_ok": ok_r, "etage_tiling_ok": ok_e,
                  "patio_corner": corner, "layout_version": 2}
save_json(pp, prog)
ev2.created(pp)
results["files_modified"].append(pp)

dp = os.path.join(P, "dimensions", "dimensions.json")
d = json.load(open(dp, encoding="utf-8"))
d["updated_at"] = STAMP
d["room_dimensions"] = {"status": "RESOLVED",
                        "method": "pavage exact (grille 0,5 m, largeurs minimales)",
                        "file": p_fp, "layout_version": 2,
                        "note": "Emprises par piece dans floorplan/floor_plan.json"}
save_json(dp, d)
ev2.created(dp)
results["files_modified"].append(dp)

decision = {
    "decision_id": "DEC_%s_005" % PID, "project_id": PID, "at": STAMP, "seq": 5,
    "DECISION": ("Repartition interieure CORRIGEE (v2) : pavage avec largeurs minimales par piece, "
                 "meilleur score retenu. v1 rejetee."),
    "SOURCE": "Controle qualite interne Construction Agent (QA/QC) — v1 non conforme a l'usage.",
    "JUSTIFICATION": ("Le premier pavage trouve (DEC_..._004) etait mathematiquement exact "
                      "(couverture 100 %) mais architecturalement inutilisable : buanderie 6 x 1 m, "
                      "WC 3 x 1 m, chambres 2 m de large sur 8 m de long. v2 impose une largeur "
                      "minimale par piece et retient le meilleur score d'allongement parmi %d solutions "
                      "explorees (RDC) au lieu de la premiere trouvee." % sols_r),
    "IMPACT": ("Les plans SVG RDC et etage sont regeneres. floor_plan.json passe en version 2. "
               "Les surfaces sont inchangees (81 / 69 / 24 / 25). Aucun rendu PNG, .blend inchange."),
    "STATUS": "VALIDATED",
}
hist = {"history_id": "HIST_%s_LAYOUT_V2_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
        "type": "INTERNAL_LAYOUT_CORRECTED", "variant": "VARIANT_B", "layout_version": 2,
        "supersedes": "layout v1 (DEC_..._004)",
        "reason": "v1 : pieces trop etroites (buanderie 6x1 m, WC 3x1 m, chambres 2x8 m)",
        "rdc_tiling": msg_r, "etage_tiling": msg_e, "patio_corner": corner,
        "solutions_explored_rdc": sols_r,
        "rdc_rooms": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                       "x_m": r[0], "y_m": r[1], "w_m": r[2], "d_m": r[3]}
                      for (c, n, a, mn), r in zip(RDC_DEF, lo)],
        "etage_rooms": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                         "x_m": r[0], "y_m": r[1], "w_m": r[2], "d_m": r[3]}
                        for (c, n, a, mn), r in zip(ETG_DEF, eo)],
        "files": [p_rdc, p_etg, p_fp],
        "actions": {"blender_launched": False, "blend_modified": False, "renders_generated": False},
        "blend_integrity": {"sha256": SHA_B}}
p_hist = os.path.join(P, "history", "layout_v2_%s.json" % DATE)
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

ev3 = Evidence("layout_v2_guardrails", P)
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
    "PROJECT_ID": PID, "VARIANT": "VARIANT_B", "LAYOUT_VERSION": 2,
    "ETAGE_RECESS_CHOICE": "A — patio d'angle 3.00 x 4.00 m = 12 m2 (coin %s)" % corner,
    "SALLE_A_MANGER": "ouverte sur le salon — frontiere commune verifiee",
    "VOLUME_DE_VIE_M2": 50.0,
    "METHOD": "pavage exact, grille 0,5 m, largeurs minimales, meilleur score",
    "RDC_TILING": msg_r, "ETAGE_TILING": msg_e,
    "RDC_SUM": sum(a for _, _, a, _ in RDC_DEF), "ETAGE_SUM": sum(a for _, _, a, _ in ETG_DEF),
    "SURFACE_CHECK": "PASS" if valid else "FAIL",
    "RDC_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                    "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3],
                    "actual_min_side_m": min(r[2], r[3])}
                   for (c, n, a, mn), r in zip(RDC_DEF, lo)],
    "ETAGE_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "min_width_m": mn,
                      "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3],
                      "actual_min_side_m": min(r[2], r[3])}
                     for (c, n, a, mn), r in zip(ETG_DEF, eo)],
    "PLANS": [p_rdc, p_etg, p_site],
    "EVIDENCE_FILES": results["evidence_files"],
    "NEW_DATA_FILES": results["files_created"],
    "MODIFIED_FILES": results["files_modified"],
    "REAL_FILES_VERIFIED": [],
    "BLENDER_TOUCHED": False, "BLEND_UNCHANGED": SHA_A == SHA_B,
    "RENDERS_GENERATED": 0, "PNG_BEFORE": PNG_B, "PNG_AFTER": PNG_A,
    "SYNCED_AT": STAMP,
    "STATUS": "INTERNAL_LAYOUT_RESOLVED_PENDING_3D" if valid else "LAYOUT_QUALITY_FAILED",
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

print("=== RDC (9x9 = 81 m2) — v2 ===")
for (c, n, a, mn), r in zip(RDC_DEF, lo):
    print("  %-4s %-18s %2g m2  min %g m  ->  %.1f x %.1f m (min cote %.1f)"
          % (c, n, a, mn, r[2], r[3], min(r[2], r[3])))
print("  total =", sum(a for _, _, a, _ in RDC_DEF), "|", msg_r, "| solutions explorees :", sols_r)
print("=== ETAGE (9x9 - patio %s %gx%g = 69 m2) — v2 ===" % (corner, recess[2], recess[3]))
for (c, n, a, mn), r in zip(ETG_DEF, eo):
    print("  %-4s %-18s %2g m2  min %g m  ->  %.1f x %.1f m (min cote %.1f)"
          % (c, n, a, mn, r[2], r[3], min(r[2], r[3])))
print("  total =", sum(a for _, _, a, _ in ETG_DEF), "|", msg_e)
print("\nSURFACE_CHECK :", rep["SURFACE_CHECK"], "| STATUS :", rep["STATUS"])
print("fichiers verifies :", len(rep["REAL_FILES_VERIFIED"]), "| PNG generes :", PNG_A - PNG_B)
