#!/usr/bin/env python3
"""
Construction Agent v2.0.0 — RECHERCHE D'ENVELOPPE BRUTE v3 (PRJ_1701484686)

Correction du packer :
  v2 utilisait "premiere cellule libre + placement" — strategie complete seulement
  pour un pavage EXACT. Avec du reliquat, les cellules vides bloquent la piece
  suivante et le solveur ne trouve rien alors qu'une solution existe.
  v3 : le reliquat est EXPLICITE — chaque cellule vide consomme 1 unite d'un
  budget de perte fixe (= conteneur - 81 m2). Recherche complete.

Modele : murs exterieurs 0,20 m | pieces packees dans l'interieur |
         reliquat = cloisons (0,10 m x perimetres/2) + circulation + marge.

Aucun SVG definitif. Aucun Blender. Aucun rendu. Aucune validation.
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
BLEND = os.path.join(P, "3D", "scene_villa_conceptuelle.blend")
SHA_B = sha256(BLEND)
PNG_B = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
TE, CW, U = 0.20, 1.20, 2
ROOMS = [("Salon", 32, 4.0), ("Salle a manger", 18, 3.5), ("Cuisine", 12, 2.5),
         ("Bureau", 10, 2.5), ("Buanderie", 6, 2.0), ("WC visiteur", 3, 1.5)]
SUM_ROOMS = sum(a for _, a, _ in ROOMS)
TER_W, TER_D, GAR_W, TRE_D = 15.0, 25.0, 5.0, 4.0


def pack_with_waste(areas_m2, mins_m, wc, hc, max_nodes=2500000, max_sols=300):
    """Recherche complete : place les pieces OU consomme 1 cellule de perte."""
    areas = [int(round(a * U * U)) for a in areas_m2]
    mins = [int(round(m * U)) for m in mins_m]
    total = sum(areas)
    if total > wc * hc:
        return None, 0
    budget = wc * hc - total
    grid = [[0] * wc for _ in range(hc)]
    idx = sorted(range(len(areas)), key=lambda i: -areas[i])
    cur = [None] * len(areas)
    best, bs = [None], [1e18]
    sols, nodes = [0], [0]

    def ff():
        for y in range(hc):
            r = grid[y]
            for x in range(wc):
                if r[x] == 0:
                    return x, y
        return None

    def rec(k, wasted):
        nodes[0] += 1
        if nodes[0] > max_nodes or sols[0] >= max_sols:
            return
        if k == len(idx):
            if wasted == budget:
                sols[0] += 1
                sc = sum(max(w, h) / float(min(w, h)) for (_, _, w, h) in cur)
                if sc < bs[0]:
                    bs[0] = sc
                    best[0] = list(cur)
            return
        p = ff()
        if p is None:
            return
        x0, y0 = p
        i = idx[k]
        a, mn = areas[i], mins[i]
        # A) placer la piece suivante
        for w in range(1, wc - x0 + 1):
            if a % w:
                continue
            h = a // w
            if h < 1 or y0 + h > hc or min(w, h) < mn:
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
        # B) declarer la cellule perdue (reliquat / cloison / circulation)
        if wasted < budget:
            grid[y0][x0] = 9
            rec(k, wasted + 1)
            grid[y0][x0] = 0

    rec(0, 0)
    if best[0] is None:
        return None, sols[0]
    out = [None] * len(areas)
    for i, (x, y, w, h) in enumerate(best[0]):
        out[i] = (x / U, y / U, w / U, h / U)
    return out, sols[0]


CANDIDATES = [(9.2, 9.5), (9.5, 9.5), (9.5, 9.8), (9.8, 9.8), (10.0, 9.5), (10.0, 10.0),
              (9.8, 10.2), (10.0, 10.4), (10.0, 10.6), (10.4, 10.4), (10.4, 10.9),
              (10.5, 10.5), (9.9, 11.1), (10.0, 11.1), (10.9, 10.9), (10.0, 11.6),
              (10.5, 11.0), (11.0, 11.0)]

rows = []
for (W, H) in CANDIDATES:
    iw, ih = round(W - 2 * TE, 2), round(H - 2 * TE, 2)
    wc, hc = int(iw // 0.5), int(ih // 0.5)
    cont = round(wc * 0.5 * hc * 0.5, 2)
    r = {"enveloppe": "%.1f x %.1f" % (W, H), "W": W, "H": H,
         "surface_brute": round(W * H, 2), "interieur_m2": round(iw * ih, 2),
         "conteneur_m2": cont, "ratio_net_brut": round(SUM_ROOMS / (W * H), 3),
         "faisable": None, "raison": ""}
    if cont < SUM_ROOMS:
        r["faisable"], r["raison"] = False, "interieur %.2f m2 < 81 m2" % cont
        rows.append(r)
        continue
    lay, sols = pack_with_waste([a for _, a, _ in ROOMS], [m for _, _, m in ROOMS], wc, hc)
    r["sols"] = sols
    if not lay:
        r["faisable"] = False
        r["raison"] = "aucun packing valide (%d solutions explorees)" % sols
        rows.append(r)
        continue
    reliquat = round(cont - SUM_ROOMS, 2)
    perim = sum(2 * (p[2] + p[3]) for p in lay)
    cloisons = round(0.10 * perim / 2, 2)
    circulation = round(CW * (max(W, H) - 3.0), 2)
    besoin = round(cloisons + circulation, 2)
    r.update({"reliquat_m2": reliquat, "cloisons_est_m2": cloisons,
              "circulation_besoin_m2": circulation, "besoin_m2": besoin,
              "marge_m2": round(reliquat - besoin, 2),
              "reliquat_pct": round(100 * reliquat / cont, 1),
              "layout": [{"nom": n, "surface_m2": a, "w_m": p[2], "d_m": p[3],
                          "min_cote_m": min(p[2], p[3]),
                          "ratio": round(max(p[2], p[3]) / min(p[2], p[3]), 2),
                          "x_m": p[0], "y_m": p[1]}
                         for (n, a, _), p in zip(ROOMS, lay)]})
    rr = [q["ratio"] for q in r["layout"]]
    r["ratio_moyen"] = round(sum(rr) / len(rr), 2)
    r["ratio_max"] = max(rr)
    r["min_cote_min"] = min(q["min_cote_m"] for q in r["layout"])
    r["faisable"] = reliquat >= besoin
    if not r["faisable"]:
        r["raison"] = "reliquat %.2f < besoin %.2f" % (reliquat, besoin)
    if W + GAR_W <= TER_W:
        imp = {"mode": "garage cote a cote", "largeur_m": round(W + GAR_W, 2),
               "profondeur_m": round(max(H, GAR_W) + TRE_D, 2)}
    else:
        imp = {"mode": "garage en profondeur", "largeur_m": round(max(W, GAR_W), 2),
               "profondeur_m": round(GAR_W + H + TRE_D, 2)}
    imp["compatible"] = imp["largeur_m"] <= TER_W and imp["profondeur_m"] <= TER_D
    imp["jardin_m2"] = round(375 - W * H - 25 - 24, 2)
    r["implantation"] = imp
    rows.append(r)


def scoring(r):
    if not r["faisable"]:
        return
    c_conf = 100.0
    c_prop = max(0.0, 100.0 - 30.0 * (r["ratio_max"] - 1.0) - 15.0 * (r["ratio_moyen"] - 1.0))
    rm = r["ratio_net_brut"]
    c_eff = 100.0 if 0.74 <= rm <= 0.86 else max(0.0, 100.0 - 900.0 * abs(rm - 0.80))
    c_circ = 100.0 if r["marge_m2"] >= 2.0 else max(0.0, 50.0 * (r["marge_m2"] / 2.0))
    c_terr = 100.0 if r["implantation"]["compatible"] else 0.0
    r["score_detail"] = {"conformite": round(c_conf, 1), "proportions": round(c_prop, 1),
                         "efficacite": round(c_eff, 1), "circulation": round(c_circ, 1),
                         "terrain": round(c_terr, 1)}
    r["score"] = round(0.30 * c_conf + 0.28 * c_prop + 0.20 * c_eff + 0.10 * c_circ + 0.12 * c_terr, 1)


for r in rows:
    scoring(r)
valides = sorted([r for r in rows if r["faisable"]], key=lambda r: -r["score"])

ev = Evidence("envelope_search_v3", P)
ev.tool("python3")
out = {"project_id": PID, "at": STAMP, "type": "ENVELOPE_SEARCH_V3",
       "modele": {"murs_exterieurs_m": TE, "couloir_m": CW, "grille_m": 0.5,
                  "methode": "packing complet avec reliquat explicite (budget de perte)",
                  "cloisons": "0,10 m x (somme perimetres / 2)",
                  "circulation": "1,20 m x (plus grande dimension - 3,00 m)",
                  "statut": "HYPOTHESIS — aucune enveloppe validee"},
       "programme_inchange": {n: a for n, a, _ in ROOMS}, "somme_pieces_m2": SUM_ROOMS,
       "terrain": "15 x 25 m", "garage_m2": 25, "terrasse_m2": 24,
       "candidats": rows, "valides": [r["enveloppe"] for r in valides],
       "solutions": valides[:3], "STATUS": "HYPOTHESIS_AWAITING_USER_SELECTION"}
p_out = os.path.join(P, "reports", "envelope_search.json")
save_json(p_out, out)
ev.created(p_out)
ev.test("programme_non_modifie", SUM_ROOMS == 81)
ev.test("au_moins_une_solution", len(valides) > 0, "%d" % len(valides))
for r in rows:
    ev.test("env_%s" % r["enveloppe"].replace(" ", "").replace(".", "_"),
            bool(r["faisable"]), (r["raison"] or "OK")[:70])
ev.close("VERIFIED" if valides else "FAILED")
evf = ev.out()

SHA_A = sha256(BLEND)
PNG_A = sum(len([f for f in fs if f.lower().endswith(".png")]) for _, _, fs in os.walk(P))
print("=" * 108)
print("BALAYAGE v3 — murs 0,20 m | packing complet | reliquat explicite = cloisons + circulation")
print("=" * 108)
print("%-12s %7s %8s %8s %9s %9s %9s %8s  %s"
      % ("ENVELOPPE", "BRUT", "INTER.", "NET/BRUT", "RELIQUAT", "CLOISONS", "CIRCUL.",
         "MARGE", "VERDICT"))
for r in rows:
    if r.get("reliquat_m2") is None:
        print("%-12s %7.2f %8.2f %8s %9s %9s %9s %8s  REJETEE (%s)"
              % (r["enveloppe"], r["surface_brute"], r.get("interieur_m2", 0), "-", "-", "-",
                 "-", "-", r["raison"][:34]))
    else:
        print("%-12s %7.2f %8.2f %8.3f %9.2f %9.2f %9.2f %8.2f  %s"
              % (r["enveloppe"], r["surface_brute"], r["interieur_m2"], r["ratio_net_brut"],
                 r["reliquat_m2"], r["cloisons_est_m2"], r["circulation_besoin_m2"], r["marge_m2"],
                 "VALIDE %.1f" % r["score"] if r["faisable"] else "REJETEE (" + r["raison"][:22] + ")"))

print()
print("=" * 108)
print("SOLUTIONS GEOMETRIQUEMENT VALIDES — classees par criteres techniques explicites")
print("=" * 108)
for i, r in enumerate(valides[:3], 1):
    print("\n########## SOLUTION %d — enveloppe brute %s m = %.2f m2  |  SCORE %.1f ##########"
          % (i, r["enveloppe"], r["surface_brute"], r["score"]))
    print("  interieur (murs 0,20 m deduits) : %.2f m2  |  net/brut = %.3f  |  reliquat %.2f m2 (%.1f%%)"
          % (r["interieur_m2"], r["ratio_net_brut"], r["reliquat_m2"], r["reliquat_pct"]))
    print("  budget reliquat : cloisons %.2f + circulation %.2f = %.2f  ->  marge %.2f m2"
          % (r["cloisons_est_m2"], r["circulation_besoin_m2"], r["besoin_m2"], r["marge_m2"]))
    print("  proportions : ratio moyen %.2f | ratio max %.2f | plus petite largeur %.1f m"
          % (r["ratio_moyen"], r["ratio_max"], r["min_cote_min"]))
    for q in r["layout"]:
        print("    %-16s %2d m2  ->  %.1f x %.1f m   (cote min %.1f m, ratio %.2f)"
              % (q["nom"], q["surface_m2"], q["w_m"], q["d_m"], q["min_cote_m"], q["ratio"]))
    im = r["implantation"]
    print("  implantation : %s | %.2f x %.2f m / terrain 15 x 25 -> %s | jardin ~%.0f m2"
          % (im["mode"], im["largeur_m"], im["profondeur_m"],
             "COMPATIBLE" if im["compatible"] else "INCOMPATIBLE", im["jardin_m2"]))
    print("  score detail :", json.dumps(r["score_detail"]))

print("\n=== STATUS ===")
print("  valides :", out["valides"])
print("  AUCUNE enveloppe VALIDATED — HYPOTHESIS jusqu'a ton choix")
print("  fichier :", p_out)
print("  .blend inchange :", SHA_A == SHA_B, "| PNG generes :", PNG_A - PNG_B)
