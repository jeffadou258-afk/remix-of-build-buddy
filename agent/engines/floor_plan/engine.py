"""PHASE 6 — FLOOR PLAN. Genere de VRAIS fichiers SVG (stdlib pure)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _core import *

OPERATION = "floor_plan"
SCALE = 42.0   # px par metre
WALL = 0.20    # m
PALETTE = ["#dbeafe", "#dcfce7", "#fef9c3", "#fae8ff", "#ffe4e6", "#e0e7ff", "#ccfbf1"]


def _svg(level, width_m, depth_m, rooms):
    pad = 60
    W = width_m * SCALE + pad * 2
    H = depth_m * SCALE + pad * 2
    b = ["<?xml version='1.0' encoding='UTF-8'?>",
         "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>" % (W, H, W, H),
         "<rect width='100%%' height='100%%' fill='#ffffff'/>",
         "<text x='%.0f' y='30' font-family='Helvetica' font-size='18' font-weight='bold' fill='#111'>%s</text>"
         % (pad, level),
         "<text x='%.0f' y='48' font-family='Helvetica' font-size='11' fill='#666'>Construction Agent v2.0.0 — schema CONCEPTUEL, non contractuel — echelle 1:%d</text>"
         % (pad, int(100 / (SCALE / 100.0)))]
    # enveloppe
    b.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' stroke='#111' stroke-width='%.1f'/>"
             % (pad, pad, width_m * SCALE, depth_m * SCALE, WALL * SCALE))
    x = pad
    y = pad
    row_h = depth_m * SCALE
    for i, r in enumerate(rooms):
        rw = (r["surface_m2"] / depth_m) * SCALE
        if x + rw > pad + width_m * SCALE + 0.5:
            rw = pad + width_m * SCALE - x
        col = PALETTE[i % len(PALETTE)]
        b.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='%s' stroke='#334155' stroke-width='1.2'/>"
                 % (x, y, rw, row_h, col))
        b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='10' fill='#0f172a'>%s</text>"
                 % (x + 6, y + 18, r["code"]))
        b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='9' fill='#334155'>%.1f m2</text>"
                 % (x + 6, y + 32, r["surface_m2"]))
        x += rw + WALL * SCALE
    # cotation
    b.append("<text x='%.1f' y='%.1f' font-family='Helvetica' font-size='11' fill='#111'>largeur %.2f m x profondeur %.2f m</text>"
             % (pad, pad + row_h + 28, width_m, depth_m))
    b.append("</svg>")
    return "\n".join(b)


def run(project_dir):
    ev = Evidence(OPERATION, project_dir)
    log(project_dir, OPERATION, "start")
    dims = load_json(os.path.join(project_dir, "dimensions", "dimensions.json"))
    prog = load_json(os.path.join(project_dir, "program", "program.json"))
    if not dims or not prog:
        ev.block("dimensions.json ou program.json absent")
        ev.out()
        return {"status": "BLOCKED"}
    out_dir = os.path.join(project_dir, "floorplan")
    os.makedirs(out_dir, exist_ok=True)
    doc = {"project_id": os.path.basename(os.path.normpath(project_dir)),
           "created_at": now(), "unit": "m", "levels": []}
    for lv in dims["levels"]:
        rooms = [r for r in prog["rooms"] if r["level"] == lv["level"]]
        if not rooms:
            continue
        svg = _svg(lv["level"], lv["width_m"], lv["depth_m"], rooms)
        f = os.path.join(out_dir, "plan_%s.svg" % lv["level"].lower())
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(svg)
        info = ev.created(f)
        doc["levels"].append({"level": lv["level"], "width_m": lv["width_m"],
                              "depth_m": lv["depth_m"], "wall_thickness_m": WALL,
                              "rooms": rooms, "files": [f],
                              "size_bytes": info["size_bytes"] if info else None})
        ev.test("svg_%s_written" % lv["level"], bool(info and info["size_bytes"] > 500),
                "%s octets" % (info["size_bytes"] if info else "0"))
    p = save_json(os.path.join(project_dir, "floorplan", "floor_plan.json"), doc)
    ev.created(p)
    ev.close("EXECUTED")
    ev.out()
    log(project_dir, OPERATION, "status=EXECUTED levels=%d" % len(doc["levels"]))
    return {"status": "EXECUTED", "floor_plan": p,
            "files": [f for l in doc["levels"] for f in l["files"]]}


if __name__ == "__main__":
    cli(OPERATION, run)
