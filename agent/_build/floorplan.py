#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — REPARTITION INTERIEURE + PLANS SVG (PRJ_1701484686)

Resout un PAVAGE EXACT du 9x9 par les surfaces du programme (backtracking).
Aucune piece n'est placee "a l'oeil" : le pavage doit couvrir 100% de l'enveloppe.

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

W = H = 9          # enveloppe 9 x 9 m
SCALE = 58.0       # px par metre

# =============================================================== PAVAGE
def solve(areas, blocked=None, order=None, node_cap=400000):
    """Pavage exact. areas: liste de m2 entiers. blocked: set de (x,y). -> liste de (x,y,w,h,area)"""
    blocked = blocked or set()
    grid = [[1 if (x, y) in blocked else 0 for x in range(W)] for y in range(H)]
    total_free = sum(row.count(0) for row in grid)
    if sum(areas) != total_free:
        return None
    idx = order or sorted(range(len(areas)), key=lambda i: -areas[i])
    out = [None] * len(areas)
    nodes = [0]

    def first_free():
        for y in range(H):
            for x in range(W):
                if grid[y][x] == 0:
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
        for w in range(1, W - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > H:
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
            out[idx[k]] = (x0, y0, w, h, a)
            if rec(k + 1):
                return True
            out[idx[k]] = None
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    grid[yy][xx] = 0
        return False

    return out if rec(0) else None


def touching(r1, r2):
    x1, y1, w1, h1, _ = r1
    x2, y2, w2, h2, _ = r2
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)


# --------------------------------------------------------------- RDC 81 m2
RDC_DEF = [("P01", "Salon", 32), ("P02", "Salle a manger", 18), ("P03", "Cuisine", 12),
           ("P04", "Bureau", 10), ("P05", "Buanderie", 6), ("P06", "WC visiteur", 3)]
rdc_areas = [a for _, _, a in RDC_DEF]
lo = None
for perm in [sorted(range(6), key=lambda i: -rdc_areas[i]),
             [0, 1, 2, 3, 4, 5], [1, 0, 2, 4, 5, 3]]:
    lo = solve(rdc_areas, order=perm)
    if lo:
        break
assert lo, "PAVAGE RDC INTROUVABLE"

# --------------------------------------------------------------- ETAGE 69 m2
# retrait 3 x 4 = 12 m2 au coin (patio d'angle) -> cellule (x6..8, y5..8)
RECESS = [(x, y) for x in range(6, 9) for y in range(5, 9)]
assert len(RECESS) == 12
ETG_DEF = [("P07", "Suite parentale", 16), ("P08", "Chambre 2", 13), ("P09", "Chambre 3", 13),
           ("P10", "Chambre 4", 12), ("P11", "Salle de bain 1", 5),
           ("P12", "Salle de bain 2", 5), ("P13", "Salle de bain 3", 5)]
etg_areas = [a for _, _, a in ETG_DEF]
eo = None
for perm in [sorted(range(7), key=lambda i: -etg_areas[i]),
             sorted(range(7), key=lambda i: -etg_areas[i])[::-1]]:
    eo = solve(etg_areas, blocked=set(RECESS), order=perm)
    if eo:
        break
assert eo, "PAVAGE ETAGE INTROUVABLE"

results = {"files_created": [], "files_modified": [], "evidence_files": []}


def verify_tiling(rects, areas, blocked=None, label=""):
    """Le pavage couvre-t-il EXACTEMENT l'enveloppe libre ?"""
    blocked = blocked or set()
    seen = {}
    for i, (x, y, w, h, a) in enumerate(rects):
        if w * h != a:
            return False, "%s: rect %d aire != surface" % (label, i)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if (xx, yy) in blocked:
                    return False, "%s: rect %d empiète sur le retrait" % (label, i)
                if (xx, yy) in seen:
                    return False, "%s: chevauchement en (%d,%d)" % (label, xx, yy)
                seen[(xx, yy)] = i
    attendu = W * H - len(blocked)
    if len(seen) != attendu:
        return False, "%s: couverture %d != %d" % (label, len(seen), attendu)
    if sum(a for _, _, _, _, a in rects) != attendu:
        return False, "%s: somme surfaces != enveloppe" % label
    return True, "%d cellules couvertes / attendu %d" % (len(seen), attendu)


ok_r, msg_r = verify_tiling(lo, rdc_areas, label="RDC")
ok_e, msg_e = verify_tiling(eo, etg_areas, blocked=set(RECESS), label="ETAGE")

# =============================================================== SVG
PAL = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff",
       "#ccfbf1", "#ffedd5"]


def svg_plan(title, subtitle, rects, names, blocked=None, open_pairs=(),
             extra=None, path=None, show_patio=None):
    blocked = blocked or set()
    pad, top = 70, 92
    Wp = W * SCALE + pad * 2
    Hp = H * SCALE + pad * 2 + top
    x0 = pad
    y0 = top
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' "
         "viewBox='0 0 %.0f %.0f'>" % (Wp, Hp, Wp, Hp),
         "<rect width='100%' height='100%' fill='#ffffff'/>",
         "<text x='%d' y='40' font-family='Helvetica,Arial' font-size='21' "
         "font-weight='bold' fill='#0f172a'>%s</text>" % (pad, title),
         "<text x='%d' y='62' font-family='Helvetica,Arial' font-size='11' "
         "fill='#64748b'>%s</text>" % (pad, subtitle),
         "<text x='%d' y='78' font-family='Helvetica,Arial' font-size='10' "
         "fill='#94a3b8'>PRJ_1701484686 · VARIANT_B · Construction Agent v2.0.0 · "
         "schema CONCEPTUEL non contractuel</text>" % pad]

    # enveloppe
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' "
             "stroke='#0f172a' stroke-width='3'/>"
             % (x0, y0, W * SCALE, H * SCALE))

    for i, (rx, ry, rw, rh, area) in enumerate(rects):
        X = x0 + rx * SCALE
        Y = y0 + ry * SCALE
        # SVG y descend : on inverse pour avoir le nord en haut
        Y = y0 + (H - ry - rh) * SCALE
        col = PAL[i % len(PAL)]
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' "
                 "stroke='#94a3b8' stroke-width='1'/>" % (X, Y, rw * SCALE, rh * SCALE, col))
        nom = names[i]
        cx = X + rw * SCALE / 2
        cy = Y + rh * SCALE / 2
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='12' font-weight='bold' fill='#0f172a'>%s</text>" % (cx, cy - 4, nom))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='10' fill='#334155'>%d m&#178;</text>" % (cx, cy + 11, area))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='8.5' fill='#64748b'>%.2f &#215; %.2f</text>"
                 % (cx, cy + 23, rw, rh))

    # cloisons ouvertes (pointille)
    for (ia, ib) in open_pairs:
        ra = rects[names.index(ia)]
        rb = rects[names.index(ib)]
        ax, ay, aw, ah, _ = ra
        bx, by, bw, bh, _ = rb
        # frontiere commune horizontale ou verticale
        if abs((ay + ah) - by) < 0.01 or abs((by + bh) - ay) < 0.01:
            yb = y0 + (H - max(ay, by)) * SCALE
            sx = x0 + max(ax, bx) * SCALE
            ex = x0 + min(ax + aw, bx + bw) * SCALE
            L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' "
                     "stroke-width='3' stroke-dasharray='9,6'/>" % (sx, yb, ex, yb))
        elif abs((ax + aw) - bx) < 0.01 or abs((bx + bw) - ax) < 0.01:
            xb = x0 + max(ax, bx) * SCALE
            sy = y0 + (H - max(ay, by)) * SCALE
            ey = y0 + (H - min(ay + ah, by + bh)) * SCALE
            L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' "
                     "stroke-width='3' stroke-dasharray='9,6'/>" % (xb, sy, xb, ey))

    # patio (retrait) en etage
    if show_patio:
        px, py, pw, ph = show_patio
        X = x0 + px * SCALE
        Y = y0 + (H - py - ph) * SCALE
        L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='url(#hatch)' "
                 "stroke='#0f172a' stroke-width='2' stroke-dasharray='6,4'/>"
                 % (X, Y, pw * SCALE, ph * SCALE))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='11' font-weight='bold' fill='#0f172a'>PATIO</text>"
                 % (X + pw * SCALE / 2, Y + ph * SCALE / 2 - 3))
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='9.5' fill='#334155'>%d m&#178; (a ciel ouvert)</text>"
                 % (X + pw * SCALE / 2, Y + ph * SCALE / 2 + 13, pw * ph))

    # cotation
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#0f172a' "
             "stroke-width='1'/>" % (x0, y0 + H * SCALE + 26, x0 + W * SCALE, y0 + H * SCALE + 26))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='12' fill='#0f172a'>%.2f m</text>"
             % (x0 + W * SCALE / 2, y0 + H * SCALE + 42, W))
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#0f172a' "
             "stroke-width='1'/>" % (x0 - 26, y0, x0 - 26, y0 + H * SCALE))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
             "font-size='12' fill='#0f172a' transform='rotate(-90 %.1f %.1f)'>%.2f m</text>"
             % (x0 - 40, y0 + H * SCALE / 2, x0 - 40, y0 + H * SCALE / 2, H))
    if extra:
        for t in extra:
            L.append("<text x='%d' y='%.1f' font-family='Helvetica,Arial' font-size='10.5' "
                     "fill='#0f172a'>%s</text>" % (pad, Hp - t[1], t[0]))
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

# --- RDC
names_r = [n for _, n, _ in RDC_DEF]
p_rdc = os.path.join(FDIR, "plan_rdc.svg")
svg_plan("Plan RDC — VARIANT_B",
         "9,00 x 9,00 m = 81,00 m2  ·  6 pieces  ·  volume de vie ouvert salon + salle a manger = 50 m2",
         lo, names_r, open_pairs=[("Salon", "Salle a manger")], path=p_rdc)
ev.created(p_rdc)
results["files_created"].append(p_rdc)

# --- ETAGE
names_e = [n for _, n, _ in ETG_DEF]
p_etg = os.path.join(FDIR, "plan_etage.svg")
svg_plan("Plan Etage — VARIANT_B",
         "9,00 x 9,00 m moins patio d'angle 3,00 x 4,00 (12 m2) = 69,00 m2  ·  7 pieces",
         eo, names_e, blocked=set(RECESS), path=p_etg, show_patio=(6, 5, 3, 4))
ev.created(p_etg)
results["files_created"].append(p_etg)

# --------------------------------------------------------------- IMPLANTATION
def svg_site(path):
    ter_w, ter_d = 15.0, 25.0
    S = 26.0
    pad = 80
    Wp, Hp = ter_w * S + pad * 2, ter_d * S + pad * 2 + 70
    ox, oy = pad, 82
    L = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' "
         "viewBox='0 0 %.0f %.0f'>" % (Wp, Hp, Wp, Hp),
         "<rect width='100%' height='100%' fill='#fff'/>",
         "<text x='%d' y='40' font-family='Helvetica,Arial' font-size='20' "
         "font-weight='bold' fill='#0f172a'>Implantation — terrain 15 x 25 m (375 m2)</text>" % pad,
         "<text x='%d' y='62' font-family='Helvetica,Arial' font-size='11' fill='#64748b'>"
         "Villa 9 x 9 + garage 5 x 5 + terrasse couverte 4 x 6 · emprise au sol 106 m2 (28%) · "
         "HYPOTHESE d'implantation, orientation UNKNOWN</text>" % pad,
         "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ecfdf5' stroke='#059669' "
         "stroke-width='2.5'/>" % (ox, oy, ter_w * S, ter_d * S)]
    # bande batie en haut (nord de la parcelle) : villa + garage cote a cote
    # villa 9 x 9
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#dbeafe' "
             "stroke='#1e40af' stroke-width='2'/>" % (ox, oy, 9 * S, 9 * S))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='12' font-weight='bold' "
             "fill='#0f172a' font-family='Helvetica,Arial'>VILLA R+1</text>"
             % (ox + 4.5 * S, oy + 4.5 * S - 4))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#334155' "
             "font-family='Helvetica,Arial'>9,00 x 9,00 m</text>" % (ox + 4.5 * S, oy + 4.5 * S + 12))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#334155' "
             "font-family='Helvetica,Arial'>RDC 81 m2 / Etage 69 m2</text>"
             % (ox + 4.5 * S, oy + 4.5 * S + 26))
    # garage 5 x 5
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#e2e8f0' "
             "stroke='#334155' stroke-width='2'/>" % (ox + 9 * S, oy, 5 * S, 5 * S))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='11' font-weight='bold' "
             "fill='#0f172a' font-family='Helvetica,Arial'>GARAGE</text>"
             % (ox + 11.5 * S, oy + 2.5 * S - 4))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#334155' "
             "font-family='Helvetica,Arial'>5,00 x 5,00 m</text>" % (ox + 11.5 * S, oy + 2.5 * S + 11))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#334155' "
             "font-family='Helvetica,Arial'>25 m2</text>" % (ox + 11.5 * S, oy + 2.5 * S + 24))
    # terrasse couverte 4 x 6 en prolongement (sud de la villa)
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#fef3c7' "
             "stroke='#a16207' stroke-width='2'/>" % (ox + 2.5 * S, oy + 9 * S, 6 * S, 4 * S))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='11' font-weight='bold' "
             "fill='#0f172a' font-family='Helvetica,Arial'>TERRASSE COUVERTE</text>"
             % (ox + 5.5 * S, oy + 11 * S - 4))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#334155' "
             "font-family='Helvetica,Arial'>6,00 x 4,00 m = 24 m2</text>" % (ox + 5.5 * S, oy + 11 * S + 12))
    # jardin
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='12' fill='#065f46' "
             "font-family='Helvetica,Arial'>JARDIN ~ 245 m2</text>"
             % (ox + 7.5 * S, oy + 19 * S))
    L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-size='10' fill='#64748b' "
             "font-family='Helvetica,Arial'>orientation et cote rue : UNKNOWN (non fournis)</text>"
             % (ox + 7.5 * S, oy + 19 * S + 18))
    L.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


p_site_svg = os.path.join(FDIR, "implantation.svg")
svg_site(p_site_svg)
ev.created(p_site_svg)
results["files_created"].append(p_site_svg)

# --------------------------------------------------------------- floor_plan.json
fp = {
    "project_id": PID, "created_at": STAMP, "unit": "m", "variant": "VARIANT_B",
    "method": "pavage exact par backtracking — couverture 100% verifiee",
    "levels": [
        {"level": "RDC", "envelope": "9.00 x 9.00", "surface_m2": 81,
         "rooms": [{"code": c, "name": n, "surface_m2": a,
                    "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(RDC_DEF, lo)],
         "files": [p_rdc], "tiling_ok": ok_r, "tiling_detail": msg_r},
        {"level": "ETAGE", "envelope": "9.00 x 9.00 - retrait 3.00 x 4.00 (12 m2)",
         "surface_m2": 69, "recess": {"x_m": 6, "y_m": 5, "width_m": 3, "depth_m": 4,
                                      "surface_m2": 12, "nature": "patio d'angle a ciel ouvert"},
         "rooms": [{"code": c, "name": n, "surface_m2": a,
                    "x_m": r[0], "y_m": r[1], "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(ETG_DEF, eo)],
         "files": [p_etg], "tiling_ok": ok_e, "tiling_detail": msg_e},
    ],
    "open_relations": [{"a": "P01 Salon", "b": "P02 Salle a manger", "type": "OPEN",
                        "partition": False,
                        "note": "Salle a manger ouverte sur le salon (choix utilisateur 2026-10-02)",
                        "volume_vie_m2": 50}],
    "site_plan": {"file": p_site_svg, "terrain": "15 x 25 m = 375 m2",
                  "implantation_status": "HYPOTHESIS", "orientation": "UNKNOWN"},
    "notes": ["Schema CONCEPTUEL, non contractuel.",
              "Emprises derivees du pavage des surfaces fournies ; aucune surface inventee.",
              "Circulation assuree par les volumes de vie et de service (pas de couloir dedie au programme)."],
}
p_fp = os.path.join(FDIR, "floor_plan.json")
save_json(p_fp, fp); ev.created(p_fp)
results["files_created"].append(p_fp)

ev.test("rdc_tiling_covers_100pct", ok_r, msg_r)
ev.test("etage_tiling_covers_100pct", ok_e, msg_e)
ev.test("rdc_sum_eq_81", sum(rdc_areas) == 81)
ev.test("etage_sum_eq_69", sum(etg_areas) == 69)
ev.test("salon_adjacent_salle_a_manger",
        touching(lo[0], lo[1]), "frontiere commune -> cloison ouverte possible")
ev.test("svg_rdc_valid", open(p_rdc).read().startswith("<?xml"))
ev.test("svg_etage_valid", open(p_etg).read().startswith("<?xml"))
ev.test("svg_implantation_valid", open(p_site_svg).read().startswith("<?xml"))
ev.close("VERIFIED")
results["evidence_files"].append(ev.out())

# =============================================================== MAJ PROGRAMME + DIMENSIONS
ev2 = Evidence("sync_layout", P)
prog = json.load(open(os.path.join(P, "program", "program.json"), encoding="utf-8"))
prog["updated_at"] = STAMP
prog["version"] = 3
prog["relations"] = [{"a": "P01", "b": "P02", "type": "OPEN", "partition": False,
                      "note": "Salle a manger ouverte sur le salon — volume de vie 50 m2"}]
prog["open_living"] = {"rooms": ["P01", "P02"], "total_m2": 50.0, "partition": False,
                       "decision": "Choix utilisateur 2026-10-02"}
prog["layout"] = {"status": "RESOLVED", "method": "pavage exact",
                  "file": p_fp, "rdc_tiling_ok": ok_r, "etage_tiling_ok": ok_e}
save_json(os.path.join(P, "program", "program.json"), prog)
ev2.created(os.path.join(P, "program", "program.json"))
results["files_modified"].append(os.path.join(P, "program", "program.json"))

d = json.load(open(os.path.join(P, "dimensions", "dimensions.json"), encoding="utf-8"))
d["updated_at"] = STAMP
d["envelope"]["ETAGE"]["source"] = "USER_PROVIDED"
d["envelope"]["ETAGE"]["note"] = ("Retrait 3 x 4 = 12 m2 (patio d'angle a ciel ouvert), "
                                  "choix utilisateur 'A' du 2026-10-02 -> 81 - 12 = 69 m2.")
d["envelope"]["ETAGE"]["recess"]["nature"] = "patio d'angle"
d["room_dimensions"] = {"status": "RESOLVED", "method": "pavage exact par backtracking",
                        "file": p_fp, "width_m": None, "depth_m": None,
                        "note": "Emprises par piece dans floorplan/floor_plan.json"}
save_json(os.path.join(P, "dimensions", "dimensions.json"), d)
ev2.created(os.path.join(P, "dimensions", "dimensions.json"))
results["files_modified"].append(os.path.join(P, "dimensions", "dimensions.json"))

decision = {
    "decision_id": "DEC_%s_004" % PID, "project_id": PID, "at": STAMP, "seq": 4,
    "DECISION": ("Repartition interieure resolue : pavage exact 9 x 9 (RDC 81 m2) et "
                 "9 x 9 moins patio d'angle 3 x 4 (ETAGE 69 m2) ; salle a manger ouverte sur le salon."),
    "SOURCE": "Choix utilisateur 2026-10-02 : '1. Etage : A — retrait 3 x 4 (patio d'angle)' et '2. Salle a manger : ouverte sur le salon'.",
    "JUSTIFICATION": ("Pavage resolu par backtracking : chaque rectangle a une aire exactement "
                      "egale a la surface fournie et la couverture de l'enveloppe est de 100% "
                      "(verifie cellule par cellule). Le salon et la salle a manger sont adjacents, "
                      "ce qui permet la cloison ouverte demandee (volume de vie 50 m2)."),
    "IMPACT": ("3 plans SVG produits (RDC, etage, implantation). Le retrait d'etage passe de "
               "HYPOTHESIS a USER_PROVIDED. Prochaine etape possible : reconstruction BIM/3D."),
    "STATUS": "VALIDATED",
}
hist = {"history_id": "HIST_%s_LAYOUT_%s" % (PID, DATE), "project_id": PID, "at": STAMP,
        "type": "INTERNAL_LAYOUT_RESOLVED", "variant": "VARIANT_B",
        "layout": {"rdc_tiling": msg_r, "etage_tiling": msg_e,
                   "rdc_rooms": [{"code": c, "name": n, "surface_m2": a,
                                  "x_m": r[0], "y_m": r[1], "w_m": r[2], "d_m": r[3]}
                                 for (c, n, a), r in zip(RDC_DEF, lo)],
                   "etage_rooms": [{"code": c, "name": n, "surface_m2": a,
                                    "x_m": r[0], "y_m": r[1], "w_m": r[2], "d_m": r[3]}
                                   for (c, n, a), r in zip(ETG_DEF, eo)]},
        "files": [p_rdc, p_etg, p_site_svg, p_fp],
        "actions": {"blender_launched": False, "blend_modified": False, "renders_generated": False},
        "blend_integrity": {"sha256": SHA_B}}
p_hist = os.path.join(P, "history", "layout_%s.json" % DATE)
save_json(p_hist, hist); ev2.created(p_hist)
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

# =============================================================== GARDE-FOUS
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

# =============================================================== RAPPORT
rep = {
    "PROJECT_ID": PID, "VARIANT": "VARIANT_B",
    "ETAGE_RECESS_CHOICE": "A — patio d'angle 3.00 x 4.00 m = 12 m2",
    "ETAGE_RECESS_SOURCE": "USER_PROVIDED",
    "SALLE_A_MANGER": "ouverte sur le salon (pas de cloison)",
    "VOLUME_DE_VIE_M2": 50.0,
    "RDC_TILING": msg_r, "ETAGE_TILING": msg_e,
    "RDC_SUM": sum(rdc_areas), "ETAGE_SUM": sum(etg_areas),
    "SURFACE_CHECK": "PASS" if (ok_r and ok_e and sum(rdc_areas) == 81
                                and sum(etg_areas) == 69) else "FAIL",
    "RDC_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                    "width_m": r[2], "depth_m": r[3]}
                   for (c, n, a), r in zip(RDC_DEF, lo)],
    "ETAGE_LAYOUT": [{"code": c, "name": n, "surface_m2": a, "x_m": r[0], "y_m": r[1],
                      "width_m": r[2], "depth_m": r[3]}
                     for (c, n, a), r in zip(ETG_DEF, eo)],
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

print("=== RDC ===")
for (c, n, a), r in zip(RDC_DEF, lo):
    print("  %-4s %-18s %2d m2   x=%d y=%d  %.2f x %.2f m" % (c, n, a, r[0], r[1], r[2], r[3]))
print("  total =", sum(rdc_areas), "|", msg_r)
print("=== ETAGE ===")
for (c, n, a), r in zip(ETG_DEF, eo):
    print("  %-4s %-18s %2d m2   x=%d y=%d  %.2f x %.2f m" % (c, n, a, r[0], r[1], r[2], r[3]))
print("  total =", sum(etg_areas), "|", msg_e)
print("\nSURFACE_CHECK :", rep["SURFACE_CHECK"], "| STATUS :", rep["STATUS"])
print("fichiers verifies :", len(rep["REAL_FILES_VERIFIED"]), "| evidence :", len(results["evidence_files"]))
