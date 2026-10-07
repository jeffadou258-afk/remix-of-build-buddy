#!/usr/bin/env python3
"""Generation FINALE : plan_rdc.svg + plan_etage.svg + implantation.svg + floor_plan.json."""
import os, sys, json, datetime

AGENT = "/Users/mac/ConstructionAgent"
sys.path.insert(0, os.path.join(AGENT, "engines"))
from _core import Evidence, save_json, sha256   # noqa: E402

P = os.path.join(AGENT, "projects", "PRJ_1701484686")
PID = "PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
TE = 0.20
RDC_W, RDC_D = 10.40, 10.90
INT_W, INT_D = RDC_W - 2 * TE, RDC_D - 2 * TE          # 10,00 x 10,50
PATIO = (7.0, 6.5, 3.0, 4.0)

rdc = json.load(open(AGENT + "/_build/_rdc_v2.json"))
etg = json.load(open(AGENT + "/_build/_etg_v5.json"))
S = 48.0


def overlap_check(rects):
    cells = {}
    dup = None
    for i, r in enumerate(rects):
        for a in range(int(round(r[2] / 0.125))):
            for b in range(int(round(r[3] / 0.125))):
                k = (round(r[0] + a * 0.125, 3), round(r[1] + b * 0.125, 3))
                if k in cells:
                    dup = (cells[k], i, k)
                cells[k] = i
    return dup, len(cells)


def adjacency(a, b):
    v = (abs((a[1] + a[3]) - b[1]) < 1e-9 or abs((b[1] + b[3]) - a[1]) < 1e-9) and \
        (min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > 1e-9)
    h = (abs((a[0] + a[2]) - b[0]) < 1e-9 or abs((b[0] + b[2]) - a[0]) < 1e-9) and \
        (min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > 1e-9)
    return v or h


def analyse_zone(rects, circ_idx, intw, intd):
    def cs(r):
        return {(round(r[0] + i * 0.25, 3), round(r[1] + j * 0.25, 3))
                for i in range(int(round(r[2] / 0.25))) for j in range(int(round(r[3] / 0.25)))}
    occ = set()
    for r in rects:
        occ |= cs(r)
    free = {(round(x * 0.25, 3), round(y * 0.25, 3))
            for y in range(int(round(intd / 0.25))) for x in range(int(round(intw / 0.25)))
            if (round(x * 0.25, 3), round(y * 0.25, 3)) not in occ}
    comps, seen = [], set()
    for c in free:
        if c in seen:
            continue
        st, comp = [c], set()
        seen.add(c)
        while st:
            p = st.pop()
            comp.add(p)
            for dx, dy in ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)):
                n = (round(p[0] + dx, 3), round(p[1] + dy, 3))
                if n in free and n not in seen:
                    seen.add(n)
                    st.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    main = comps[0] if comps else set()
    er = {p for p in main if all((p[0] + dx, p[1] + dy) in main for dx, dy in
                                 ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)))}
    if circ_idx is not None:
        circ = set()
        for i in circ_idx:
            circ |= cs(rects[i])
        adj = {i: any((q[0] + dx, q[1] + dy) in circ for q in cs(rects[i])
                      for dx, dy in ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)))
               for i in range(len(rects))}
        cor = circ
    else:
        cor = main
        adj = {i: any((q[0] + dx, q[1] + dy) in main for q in cs(rects[i])
                      for dx, dy in ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)))
               for i in range(len(rects))}
    return {"cases_libres": len(free), "composantes": len(comps), "principale": len(main),
            "erodee": len(er), "largeur_min_m": round(0.25 * 3, 2) if er else None,
            "acces": adj, "circulation_m2": round(len(cor) * 0.0625, 2)}


# ---------- verification RDC ----------
rdc_rects = [tuple(r) for r in rdc["rects"]]
rdc_names = rdc["names"]
dup, ncell = overlap_check(rdc_rects)
rdc_info = analyse_zone(rdc_rects, None, INT_W, INT_D)
print("=== RDC 10,40 x 10,90 (interieur 10,00 x 10,50) ===")
print("  chevauchement :", "AUCUN" if dup is None else dup)
for i, r in enumerate(rdc_rects):
    print("    %-16s %5.2f m2  %.2f x %.2f  @ (%.2f,%.2f)  acces=%s"
          % (rdc_names[i], r[2] * r[3], r[2], r[3], r[0], r[1], rdc_info["acces"][i]))
print("  circulation : %.2f m2, %d composante(s), largeur >= %.2f m"
      % (rdc_info["circulation_m2"], rdc_info["composantes"], rdc_info["largeur_min_m"] or 0))
print("  acces direct toutes pieces :", all(rdc_info["acces"].values()))
A, B = rdc_rects[0], rdc_rects[1]
Ladj = adjacency(A, B)
Lrect = (abs(A[0] - B[0]) < 1e-9 and abs(A[2] - B[2]) < 1e-9) or \
        (abs(A[1] - B[1]) < 1e-9 and abs(A[3] - B[3]) < 1e-9)
print("  L salon+SAM : adjacents=%s union_rectangulaire=%s surface=%.2f -> L=%s"
      % (Ladj, Lrect, A[2] * A[3] + B[2] * B[3], Ladj and not Lrect))

# ---------- verification ETAGE ----------
etg_rects_all = [tuple(r) for r in etg["rects"]]
etg_names = etg["names"]
ci = etg["circ_idx"]
room_idx = [i for i, n in enumerate(etg_names) if not n.startswith(("COULOIR", "CLOISONS"))]
fil_idx = [i for i, n in enumerate(etg_names) if n.startswith("CLOISONS")]
print("\n=== ETAGE 10,40 x 10,90 - patio 3x4 au coin NE (x[7;10] y[6,5;10,5]) ===")
etg_rects = [etg_rects_all[i] for i in room_idx]
dup_e, _ = overlap_check(etg_rects)
print("  chevauchement pieces :", "AUCUN" if dup_e is None else dup_e)
px, py, pw, pd = PATIO
for i in room_idx:
    r = etg_rects_all[i]
    inside = r[0] >= -1e-9 and r[1] >= -1e-9 and r[0] + r[2] <= INT_W + 1e-9 and \
             r[1] + r[3] <= INT_D + 1e-9
    clash = not (r[0] >= px + pw - 1e-9 or r[0] + r[2] <= px + 1e-9 or
                 r[1] >= py + pd - 1e-9 or r[1] + r[3] <= py + 1e-9)
    print("    %-16s %5.2f m2  %.2f x %.2f  @ (%.2f,%.2f)  acces=%s dans_enveloppe=%s hors_patio=%s"
          % (etg_names[i], r[2] * r[3], r[2], r[3], r[0], r[1], etg["adj"][i], inside, not clash))
print("  couloir : %s" % " + ".join("%.2f m2 (%.2f x %.2f @ %.2f,%.2f)"
                                   % (etg_rects_all[i][2] * etg_rects_all[i][3],
                                      etg_rects_all[i][2], etg_rects_all[i][3],
                                      etg_rects_all[i][0], etg_rects_all[i][1]) for i in ci))
print("  cloisons (epaisseur repartie) : %s"
      % " + ".join("%.2f m2" % (etg_rects_all[i][2] * etg_rects_all[i][3]) for i in fil_idx))
tot_e = sum(etg_rects_all[i][2] * etg_rects_all[i][3] for i in room_idx)
print("  somme pieces etage : %.2f m2 (attendu 69,00)" % tot_e)
print("  acces direct toutes pieces :", all(etg["adj"][i] for i in room_idx))
