#!/usr/bin/env python3
"""RECHERCHE STRUCTUREE DE RECONFIGURATION DU RDC (etude experimentale).
Generation par BANDES horizontales decoupees en cellules -> affectation des 6 pieces
par surface EXACTE -> le reste = circulation -> mesure physique du cheminement.
Aucune ecriture dans un fichier VALIDATED."""
import json, math, heapq, os, itertools, hashlib, datetime, random, time

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
G = 0.10
W, H = 10.0, 10.5
NX, NY = int(W / G), int(H / G)
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
T0 = time.time()
BUDGET_S = 900

SURF = {"Salon": 32.0, "Salle a manger": 18.0, "Cuisine": 12.0,
        "Bureau": 10.0, "Buanderie": 6.0, "WC visiteur": 3.0}
SEUIL = 1.20
DOOR = 0.90
ENT_Y0, ENT_Y1 = 4.70, 5.90          # porte d'entree, mur EST (interieur)
STAIR = (4.0, 4.5, 8.76, 5.5)        # escalier actuel (interieur), option


def cw(v): return int(round(v / G))


def prix(rect):
    x0, y0, x1, y1 = rect
    return (x1 - x0) * (y1 - y0)


# ---------- 1. generation des structures (bandes x cellules) ----------
def cellules(ycuts, xcuts_par_bande):
    """ycuts: liste de y (interieur) ; xcuts_par_bande: liste (par bande) de listes de x"""
    ys = [0.0] + sorted(ycuts) + [H]
    cells = []
    for b in range(len(ys) - 1):
        y0, y1 = ys[b], ys[b + 1]
        xs = [0.0] + sorted(xcuts_par_bande[b]) + [W]
        for k in range(len(xs) - 1):
            cells.append((xs[k], y0, xs[k + 1], y1))
    return cells


def affectation(cells, surf):
    """backtracking : affecte chaque piece a une cellule de surface exacte"""
    aires = [round(prix(c), 2) for c in cells]
    noms = list(surf.keys())
    noms.sort(key=lambda n: -surf[n])
    sol = []

    def bt(k, dispo, cur):
        if k == len(noms):
            return dict(cur)
        n = noms[k]
        for idx in list(dispo):
            if abs(aires[idx] - surf[n]) <= 0.02:
                cur[n] = idx
                dispo2 = dispo - {idx}
                r = bt(k + 1, dispo2, cur)
                if r: return r
                del cur[n]
        return None

    return bt(0, set(range(len(cells))), {}), aires


def gen_structures():
    YC = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
    XC = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
    out = []
    for ny in (1, 2):
        for yc in itertools.combinations(YC, ny):
            nb = len(yc) + 1
            # options de decoupe en x par bande : 1 ou 2 coupes
            opts = []
            for b in range(nb):
                o = [(x,) for x in XC] + [(a, c) for a in XC for c in XC if a < c]
                opts.append(o)
            # limite : ne combine tout que si nb<=3
            combos = itertools.product(*opts)
            cnt = 0
            for combo in combos:
                cnt += 1
                if cnt > 4000: break
                yield list(yc), combo
            if time.time() - T0 > BUDGET_S:
                return


# ---------- 2. evaluation physique ----------
def raster(rooms_rect, avec_escalier):
    g = [[False] * NY for _ in range(NX)]
    for (x0, y0, x1, y1) in rooms_rect:
        for i in range(max(0, cw(x0)), min(NX, cw(x1))):
            for j in range(max(0, cw(y0)), min(NY, cw(y1))):
                g[i][j] = True
    if avec_escalier:
        x0, y0, x1, y1 = STAIR
        for i in range(max(0, cw(x0)), min(NX, cw(x1))):
            for j in range(max(0, cw(y0)), min(NY, cw(y1))):
                g[i][j] = True
    return g


def mesure(rooms, avec_escalier=True):
    rects = {n: (float(x0) * G, float(y0) * G, float(x1) * G, float(y1) * G)
             for n, (x0, y0, x1, y1) in rooms.items()}
    g = raster(rects.values(), avec_escalier)
    lib = [[not g[i][j] for j in range(NY)] for i in range(NX)]
    # une seule composante connexe reliant entree + toutes les facades ?
    ent = None
    for j in range(cw(ENT_Y0), cw(ENT_Y1)):
        for i in range(NX - 1, -1, -1):
            if lib[i][j]:
                ent = (i, j); break
        if ent: break
    if ent is None: return None
    INF = 10 ** 9
    D = [[0 if not lib[i][j] else INF for j in range(NY)] for i in range(NX)]
    for i in range(NX):
        for j in range(NY):
            if D[i][j] == 0: continue
            v = D[i][j]
            if i > 0: v = min(v, D[i - 1][j] + 3)
            if j > 0: v = min(v, D[i][j - 1] + 3)
            if i > 0 and j > 0: v = min(v, D[i - 1][j - 1] + 4)
            if i > 0 and j + 1 < NY: v = min(v, D[i - 1][j + 1] + 4)
            D[i][j] = v
    for i in range(NX - 1, -1, -1):
        for j in range(NY - 1, -1, -1):
            if D[i][j] == 0: continue
            v = D[i][j]
            if i + 1 < NX: v = min(v, D[i + 1][j] + 3)
            if j + 1 < NY: v = min(v, D[i][j + 1] + 3)
            if i + 1 < NX and j + 1 < NY: v = min(v, D[i + 1][j + 1] + 4)
            if i + 1 < NX and j > 0: v = min(v, D[i + 1][j - 1] + 4)
            D[i][j] = v
    bn = [[-1] * NY for _ in range(NX)]
    si, sj = ent
    bn[si][sj] = D[si][sj]
    pq = [(-D[si][sj], si, sj)]
    while pq:
        neg, i, j = heapq.heappop(pq)
        c = -neg
        if c < bn[i][j]: continue
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < NX and 0 <= nj < NY and lib[ni][nj]:
                nc = min(c, D[ni][nj])
                if nc > bn[ni][nj]:
                    bn[ni][nj] = nc
                    heapq.heappush(pq, (-nc, ni, nj))
    res = {}
    for nom, (x0, y0, x1, y1) in rooms.items():
        X0, Y0, X1, Y1 = cw(x0), cw(y0), cw(x1), cw(y1)
        best = None
        aretes = [("N", X0, Y1, X1 - X0, "h"), ("S", X0, Y0 - 1, X1 - X0, "h"),
                  ("E", X1, Y0, Y1 - Y0, "v"), ("W", X0 - 1, Y0, Y1 - Y0, "v")]
        for (cote, ax, ay, ln, sens) in aretes:
            seg = []
            for k in range(ln):
                i = ax + k if sens == "h" else ax
                j = ay if sens == "h" else ay + k
                if 0 <= i < NX and 0 <= j < NY and lib[i][j]:
                    seg.append((i, j))
            if len(seg) < cw(DOOR): continue
            bb, cur = [], []
            for c in seg:
                if cur and (abs(c[0] - cur[-1][0]) + abs(c[1] - cur[-1][1])) == 1:
                    cur.append(c)
                else:
                    cur = [c]
                if len(cur) > len(bb): bb = list(cur)
            if len(bb) < cw(DOOR): continue
            m = len(bb) // 2
            porte = bb[max(0, m - cw(DOOR) // 2):][:cw(DOOR)]
            vp = min((bn[i][j] for (i, j) in porte if bn[i][j] >= 0), default=-1)
            if vp < 0: continue
            if best is None or vp > best[0]:
                best = (vp, cote, bb[max(0, m - cw(DOOR) // 2)], len(bb))
        res[nom] = None if best is None else {
            "largeur_min_m": round(best[0] * G, 2), "cote_porte": best[1],
            "facade_circulation_m": round(best[3] * G, 2),
            "porte_position_m": [round(best[2][0] * G, 2), round(best[2][1] * G, 2)]}
    circ = sum(1 for i in range(NX) for j in range(NY) if lib[i][j]) * G * G
    return {"pieces": res, "circulation_m2": round(circ, 2)}


def ok(ev, rooms):
    if ev is None: return False, "aucune circulation"
    for n, d in ev["pieces"].items():
        if d is None: return False, "%s sans facade sur la circulation" % n
        if d["largeur_min_m"] < SEUIL - 1e-9:
            return False, "%s : %.2f m < 1,20" % (n, d["largeur_min_m"])
    # salon + salle a manger adjacents (ouverts)
    a = rooms["Salon"]; b = rooms["Salle a manger"]
    ax0, ay0, ax1, ay1 = [v * G for v in a]; bx0, by0, bx1, by1 = [v * G for v in b]
    adj = (abs(ax1 - bx0) < 1e-6 and min(ay1, by1) - max(ay0, by0) > 0) or \
          (abs(bx1 - ax0) < 1e-6 and min(ay1, by1) - max(ay0, by0) > 0) or \
          (abs(ay1 - by0) < 1e-6 and min(ax1, bx1) - max(ax0, bx0) > 0) or \
          (abs(by1 - ay0) < 1e-6 and min(ax1, bx1) - max(ax0, bx0) > 0)
    if not adj: return False, "Salon et Salle a manger non adjacents"
    return True, ""


print("=== RECHERCHE STRUCTUREE ===")
n_struct = n_aff = n_eval = 0
admiss = []
for yc, combo in gen_structures():
    n_struct += 1
    cells = cellules(yc, combo)
    if len(cells) > 9: continue
    aff, aires = affectation(cells, SURF)
    if not aff: continue
    n_aff += 1
    rooms = {n: cells[i] for n, i in aff.items()}
    # cellules = coordonnees interieures -> indices
    ri = {n: (cw(c[0]), cw(c[1]), cw(c[2]), cw(c[3])) for n, c in rooms.items()}
    ev = mesure(ri, avec_escalier=True)
    n_eval += 1
    good, why = ok(ev, ri)
    if good:
        circ = [c for k, c in enumerate(cells) if k not in aff.values()]
        admiss.append({"ycuts": yc, "xcuts": combo,
                       "rooms_m": {n: [round(v, 2) for v in rooms[n]] for n in rooms},
                       "circulation_cells_m": [[round(v, 2) for v in c] for c in circ],
                       "eval": ev, "avec_escalier": True})
    if time.time() - T0 > BUDGET_S:
        print("  (budget de temps atteint)")
        break
print("structures testees : %d | affectations valides : %d | evaluees : %d | ADMISSIBLES : %d"
      % (n_struct, n_aff, n_eval, len(admiss)))
print("duree : %.1f s" % (time.time() - T0))

out = {"etude": "reconfiguration_rdc_search", "at": STAMP,
       "methode": "generation structuree par bandes horizontales decoupees en cellules ; "
                  "affectation des 6 pieces par surface EXACTE ; reste = circulation ; "
                  "mesure par inondation max-min de clearance depuis l'entree, piece = obstacle plein, "
                  "porte 0,90 m sur la plus longue facade mitoyenne de la circulation",
       "enveloppe_interieure_m": [W, H], "maille_m": G, "seuil_m": SEUIL,
       "surfaces_exigees": SURF,
       "regles": {"plan_VALIDATED_modifie": False, "bim_officiel_modifie": False,
                  "metre_modifie": False, "budget_modifie": False, "phase8_lancee": False},
       "structures_testees": n_struct, "affectations_valides": n_aff,
       "evaluees": n_eval, "admissibles": len(admiss),
       "solutions": admiss[:25], "STATUS": "EXPERIMENTAL"}
p = os.path.join(PROJ, "reports", "reconfiguration_rdc_search.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("-> %s" % p)
for k, s in enumerate(admiss[:8]):
    print("\nCANDIDAT %d : pieces %s" % (k + 1, s["rooms_m"]))
    print("   circulation %s" % s["circulation_cells_m"])
    print("   circulation %.2f m2" % s["eval"]["circulation_m2"])
    for n, d in s["eval"]["pieces"].items():
        print("     %-16s %.2f m (porte cote %s, facade %.2f m)"
              % (n, d["largeur_min_m"], d["cote_porte"], d["facade_circulation_m"]))
