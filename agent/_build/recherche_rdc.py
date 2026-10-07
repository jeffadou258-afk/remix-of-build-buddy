#!/usr/bin/env python3
"""RECHERCHE AUTOMATIQUE DE RECONFIGURATION DU RDC — etude experimentale.
Ne touche AUCUN fichier VALIDATED. Genere des implantations a surfaces EXACTES puis
mesure le cheminement reel (largeur) depuis l'entree jusqu'a chaque piece.
Une piece = obstacle plein ; la circulation = espace libre ; mesure = inondation
"maximiser le minimum de clearance" depuis l'entree (une passe pour toutes les portes).
"""
import random, math, json, heapq, os, hashlib, datetime, itertools

PROJ = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
G = 0.10                                   # maille de recherche
W, H = 10.0, 10.5                          # interieur RDC
NX, NY = int(W / G), int(H / G)            # 100 x 105
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
random.seed(20261002)

SURF = {"Salon": 32.0, "Salle a manger": 18.0, "Cuisine": 12.0,
        "Bureau": 10.0, "Buanderie": 6.0, "WC visiteur": 3.0}
# dimensions possibles (m) par piece — toutes > largeur mini praticable
DIMS = {
    "Salon":        [(4, 8), (8, 4), (5, 6.4), (6.4, 5), (3.2, 10), (10, 3.2)],
    "Salle a manger": [(4.5, 4), (4, 4.5), (6, 3), (3, 6), (2, 9), (9, 2)],
    "Cuisine":      [(3, 4), (4, 3), (6, 2), (2, 6), (5, 2.4), (2.4, 5)],
    "Bureau":       [(2.5, 4), (4, 2.5), (5, 2), (2, 5)],
    "Buanderie":    [(3, 2), (2, 3), (1.5, 4), (4, 1.5), (1.2, 5)],
    "WC visiteur":  [(1.5, 2), (2, 1.5), (3, 1), (1, 3), (1.2, 2.5)],
}
MIN_W = {"Salon": 2.0, "Salle a manger": 2.0, "Cuisine": 2.0, "Bureau": 2.0,
         "Buanderie": 1.2, "WC visiteur": 1.0}      # largeur mini de piece
STAIR = (4.0, 4.5, 8.76, 5.5)                        # emprise escalier actuel (interieur)
ENT_Y0, ENT_Y1 = 4.70, 5.90                          # porte d'entree, mur EST
DOOR = 0.90


def cw(v): return int(round(v / G))


# --- cellules de chaque variante de dimension ---
BLOCKS = {}
for n, lst in DIMS.items():
    bl = []
    for (a, b) in lst:
        wc, hc = cw(a), cw(b)
        if abs(wc * hc * G * G - SURF[n]) > 0.02:      # surface exacte exigee
            continue
        if min(a, b) < MIN_W[n]:
            continue
        bl.append((wc, hc, a, b))
        bl.append((hc, wc, b, a)) if wc != hc else None
    # deduplique
    vus = set(); B = []
    for x in bl:
        if x[:2] not in vus:
            vus.add(x[:2]); B.append(x)
    BLOCKS[n] = B
print("variantes dimensionnelles (surfaces exactes) :")
for n in SURF:
    print("  %-16s %.1f m2 -> %s" % (n, SURF[n], ["%.2fx%.2f" % (x[2], x[3]) for x in BLOCKS[n]]))


def place(rooms):
    """grille d'occupation (0=libre, id piece>0)"""
    g = [[0] * NY for _ in range(NX)]
    for r, (x, y, w, h) in rooms.items():
        for i in range(x, x + w):
            for j in range(y, y + h):
                g[i][j] = 1
    return g


def chevauche(rooms, x, y, w, h):
    for (rx, ry, rw, rh) in rooms.values():
        if x < rx + rw and rx < x + w and y < ry + rh and ry < y + h:
            return True
    return False


def partage_bord(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    if abs((ax + aw) - bx) < 1e-9 or abs((bx + bw) - ax) < 1e-9:
        return min(ay + ah, by + bh) - max(ay, by) > 0
    if abs((ay + ah) - by) < 1e-9 or abs((by + bh) - ay) < 1e-9:
        return min(ax + aw, bx + bw) - max(ax, bx) > 0
    return False


def genere():
    """genere une implantation aleatoire a surfaces exactes"""
    rooms = {}
    # 1. Salon
    wc, hc, aw, ah = random.choice(BLOCKS["Salon"])
    x = random.randint(0, NX - wc); y = random.randint(0, NY - hc)
    rooms["Salon"] = (x, y, wc, hc)
    # 2. Salle a manger adjacente au Salon (espace ouvert de 50 m2)
    ok = False
    for _ in range(60):
        wc, hc, aw, ah = random.choice(BLOCKS["Salle a manger"])
        sx, sy, sw, sh = rooms["Salon"]
        cotes = []
        if sx - wc >= 0: cotes.append((sx - wc, sy + random.randint(-hc + 1, sh - 1)))
        if sx + sw + wc <= NX: cotes.append((sx + sw, sy + random.randint(-hc + 1, sh - 1)))
        if sy - hc >= 0: cotes.append((sx + random.randint(-wc + 1, sw - 1), sy - hc))
        if sy + sh + hc <= NY: cotes.append((sx + random.randint(-wc + 1, sw - 1), sy + sh))
        random.shuffle(cotes)
        for (cx, cy) in cotes:
            if cx < 0 or cy < 0 or cx + wc > NX or cy + hc > NY: continue
            if not chevauche(rooms, cx, cy, wc, hc):
                rooms["Salle a manger"] = (cx, cy, wc, hc); ok = True; break
        if ok: break
    if not ok: return None
    # 3. autres pieces
    for nom in ("Cuisine", "Bureau", "Buanderie", "WC visiteur"):
        placed = False
        for _ in range(120):
            wc, hc, aw, ah = random.choice(BLOCKS[nom])
            if random.random() < 0.5: wc, hc = max(wc, hc), min(wc, hc)
            x = random.randint(0, NX - wc); y = random.randint(0, NY - hc)
            if not chevauche(rooms, x, y, wc, hc):
                rooms[nom] = (x, y, wc, hc); placed = True; break
        if not placed: return None
    return rooms


def cellules_libres(rooms, avec_escalier=True):
    g = place(rooms)
    if avec_escalier:
        x0, y0, x1, y1 = STAIR
        for i in range(cw(x0), cw(x1)):
            for j in range(cw(y0), cw(y1)):
                if 0 <= i < NX and 0 <= j < NY:
                    g[i][j] = 1
    lib = [[g[i][j] == 0 for j in range(NY)] for i in range(NX)]
    return g, lib


def evaluer(rooms, avec_escalier=True):
    """mesure : pour chaque piece, largeur mini du chemin depuis l'entree jusqu'a sa porte"""
    g, lib = cellules_libres(rooms, avec_escalier)
    # entree : cellule libre sur le mur EST dans l'emprise de la porte
    ent = None
    for j in range(cw(ENT_Y0), cw(ENT_Y1)):
        for i in range(NX - 1, -1, -1):
            if lib[i][j]:
                if ent is None or i > ent[0]: ent = (i, j)
                break
    if ent is None: return None
    # transformee de distance (chamfer 3-4) sur les cellules libres
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
    # inondation "maximiser la clearance minimale" depuis l'entree (une passe)
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
    # pour chaque piece : trouver les aretes mitoyennes de la circulation, poser une porte
    res = {}
    for nom, (x, y, w, h) in rooms.items():
        meilleur = None
        aretes = [("N", x, y + h, w, "h"), ("S", x, y - 1, w, "h"),
                  ("E", x + w, y, h, "v"), ("W", x - 1, y, h, "v")]
        for (cote, ax, ay, ln, sens) in aretes:
            seg = []
            for k in range(ln):
                i = ax + k if sens == "h" else ax
                j = ay if sens == "h" else ay + k
                if 0 <= i < NX and 0 <= j < NY and lib[i][j]:
                    seg.append((i, j))
            if not seg: continue
            # plus longue suite contigue
            best, cur = [], []
            for k, c in enumerate(seg):
                if cur and (abs(c[0] - cur[-1][0]) + abs(c[1] - cur[-1][1])) == 1:
                    cur.append(c)
                else:
                    cur = [c]
                if len(cur) > len(best): best = list(cur)
            if len(best) < cw(DOOR): continue
            m = len(best) // 2
            d0 = max(0, m - cw(DOOR) // 2)
            porte = best[d0:d0 + cw(DOOR)]
            v = min(bn[i][j] for (i, j) in best if bn[i][j] >= 0) if any(bn[i][j] >= 0 for (i, j) in best) else -1
            vp = min((bn[i][j] for (i, j) in porte if bn[i][j] >= 0), default=-1)
            if vp < 0: continue
            if meilleur is None or vp > meilleur[0]:
                meilleur = (vp, cote, porte[0], len(best))
        if meilleur is None:
            res[nom] = None
        else:
            vp, cote, p0, ln = meilleur
            res[nom] = {"largeur_min_m": round(vp * G, 2), "cote": cote,
                        "longueur_facade_circulation_m": round(ln * G, 2),
                        "position_porte": [round(p0[0] * G, 2), round(p0[1] * G, 2)]}
    return {"entree": [round(ent[0] * G, 2), round(ent[1] * G, 2)], "pieces": res,
            "circulation_m2": round(sum(1 for i in range(NX) for j in range(NY) if lib[i][j]) * G * G, 2)}


def admissible(ev):
    if ev is None: return False
    for n, d in ev["pieces"].items():
        if d is None or d["largeur_min_m"] < 1.20:
            return False
    return True


print("\n=== RECHERCHE ===")
N_TRIALS = 4000
tries = complets = admiss = 0
solutions = []
for t in range(N_TRIALS):
    rooms = genere()
    if rooms is None: continue
    complets += 1
    ev = evaluer(rooms, avec_escalier=True)
    tries += 1
    if admissible(ev):
        admiss += 1
        solutions.append({"rooms": {k: list(v) for k, v in rooms.items()}, "eval": ev,
                          "avec_escalier": True})
print("essais : %d | implantations completes : %d | evaluees : %d | ADMISSIBLES : %d"
      % (N_TRIALS, complets, tries, admiss))

print("\n=== memes implantations SANS escalier (reference) ===")
admiss_sans = 0
for s in solutions[:0]:
    pass
n_sans = 0
for t in range(1500):
    rooms = genere()
    if rooms is None: continue
    ev = evaluer(rooms, avec_escalier=False)
    if admissible(ev):
        admiss_sans += 1
        if n_sans < 8:
            solutions.append({"rooms": {k: list(v) for k, v in rooms.items()}, "eval": ev,
                              "avec_escalier": False})
        n_sans += 1
print("ADMISSIBLES sans escalier : %d / 1500" % admiss_sans)

out = {"etude": "reconfiguration_rdc_search", "at": STAMP,
       "enveloppe_interieure_m": [W, H], "maille_m": G,
       "surfaces_exigees": SURF, "seuil_cheminement_m": 1.20,
       "algorithme": "generation aleatoire a surfaces exactes + inondation max-min de clearance "
                     "depuis l'entree ; piece = obstacle plein ; porte 0,90 m sur la plus longue "
                     "facade mitoyenne de la circulation",
       "regles": {"plan_VALIDATED_modifie": False, "bim_officiel_modifie": False,
                  "metre_modifie": False, "budget_modifie": False, "phase8_lancee": False},
       "essais": N_TRIALS, "implantations_completes": complets, "evaluees": tries,
       "admissibles_avec_escalier": admiss, "admissibles_sans_escalier": admiss_sans,
       "solutions": solutions[:40], "STATUS": "EXPERIMENTAL"}
os.makedirs(os.path.join(PROJ, "reports"), exist_ok=True)
p = os.path.join(PROJ, "reports", "reconfiguration_rdc_search.json")
json.dump(out, open(p, "w"), indent=2, ensure_ascii=False)
print("\n-> %s" % p)
for k, s in enumerate(solutions[:6]):
    print("\nCANDIDAT %d (%s escalier) — circulation %.2f m2"
          % (k + 1, "avec" if s["avec_escalier"] else "sans", s["eval"]["circulation_m2"]))
    for n, d in s["eval"]["pieces"].items():
        print("   %-16s %s" % (n, ("%.2f m (facade %.2f m)" % (d["largeur_min_m"],
              d["longueur_facade_circulation_m"])) if d else "AUCUN"))
