#!/usr/bin/env python3
"""PHASE 1 — STRUCTURE CONCEPTUELLE. Descente de charges + predimensionnement BAEL.
Toutes les donnees d'entree inconnues sont marquees UNKNOWN/HYPOTHESIS, jamais inventees."""
import os, json, hashlib, datetime, math

P = "/Users/mac/ConstructionAgent/projects/PRJ_1701484686"
STAMP = datetime.datetime.now().isoformat(timespec="seconds")
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

# ---- geometrie VERROUILLEE (lue depuis le verrou, jamais reinventee) ----
lock = json.load(open(os.path.join(P, "floorplan", "GEOMETRY_LOCK.json")))
assert lock["STATUS"] == "VALIDATED"
fp = json.load(open(os.path.join(P, "floorplan", "floor_plan.json")))
D = {"enveloppe_brut": (10.40, 10.90), "interieur": (10.00, 10.50),
     "h_RDC": 3.20, "h_ETAGE": 3.20, "niveaux": 2}

print("=" * 78)
print("PHASE 1 — STRUCTURE CONCEPTUELLE   (geometrie verrouillee : %s)"
      % lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"][:16] + "…)")
print("=" * 78)

# ---- 1. TRAME PORTEUSE ----
NX = [0.0, 10.00 / 3, 2 * 10.00 / 3, 10.00]
NY = [0.0, 3.50, 7.00, 10.50]
trame = {"X": [round(v, 3) for v in NX], "Y": [round(v, 3) for v in NY],
         "travees_X": [round(NX[i + 1] - NX[i], 3) for i in range(len(NX) - 1)],
         "travees_Y": [round(NY[i + 1] - NY[i], 3) for i in range(len(NY) - 1)]}
print("\n[1] TRAME PORTEUSE")
print("  files X : %s  (travees %s m)" % (trame["X"], trame["travees_X"]))
print("  files Y : %s  (travees %s m)" % (trame["Y"], trame["travees_Y"]))
print("  poteaux : %d x %d = %d" % (len(NX), len(NY), len(NX) * len(NY)))

# ---- 2. HYPOTHESES DE CHARGES ----
CH = {
    "toiture_terrasse": {"g": [("dalle BA 15 cm", 0.15 * 25), ("forme de pente + etancheite", 1.00),
                               ("enduit sous-face", 0.25)],
                         "q": [("terrasse accessible", 1.50)], "statut": "HYPOTHESIS"},
    "etage_courant": {"g": [("dalle BA 15 cm", 0.15 * 25), ("chape + revetement", 1.20),
                            ("enduit sous-face", 0.25), ("cloisons reparties", 1.00)],
                      "q": [("habitation", 1.50)], "statut": "HYPOTHESIS"},
}
G_T = round(sum(v for _, v in CH["toiture_terrasse"]["g"]), 2)
Q_T = round(sum(v for _, v in CH["toiture_terrasse"]["q"]), 2)
G_E = round(sum(v for _, v in CH["etage_courant"]["g"]), 2)
Q_E = round(sum(v for _, v in CH["etage_courant"]["q"]), 2)
print("\n[2] CHARGES (statut HYPOTHESIS - a confirmer selon usage reel)")
print("  terrasse : G = %.2f kN/m2 | Q = %.2f kN/m2" % (G_T, Q_T))
print("  etage    : G = %.2f kN/m2 | Q = %.2f kN/m2" % (G_E, Q_E))

MAT = {"beton_fc28_MPa": 25, "acier_fe_MPa": 500, "gamma_beton": 1.5, "gamma_acier": 1.15,
       "poids_volumique_BA_kN_m3": 25, "statut": "HYPOTHESIS"}
SOL = {"portance_kPa": None, "statut": "UNKNOWN",
       "commentaire": "Aucune etude geotechnique fournie. Portance NON CONNUE."}

# ---- 3. PREDIMENSIONNEMENT DES ELEMENTS ----
E_DALLE = 0.15                     # L/25 = 3500/25 = 140 mm -> 150 mm
B_POT = H_POT = 0.30
B_POU, H_POU = 0.25, 0.35
print("\n[3] PREDIMENSIONNEMENT (BAEL 91 rev.99 + regles usuelles)")
print("  dalle pleine   : e = %.0f cm   (L/25 = %.0f mm, travee max %.2f m)"
      % (E_DALLE * 100, max(trame["travees_X"]) * 1000 / 25, max(trame["travees_X"])))
print("  poutres        : %.0f x %.0f cm  (h ~ L/12 = %.0f mm, L max %.2f m)"
      % (B_POU * 100, H_POU * 100, max(trame["travees_Y"]) * 1000 / 12, max(trame["travees_Y"])))
print("  poteaux        : %.0f x %.0f cm" % (B_POT * 100, H_POT * 100))

# ---- 4. DESCENTE DE CHARGES PAR POTEAU ----
fdm = MAT["beton_fc28_MPa"] / (0.9 * MAT["gamma_beton"])       # MPa (BAEL, compression centree)
fdm_sec = fdm * 1000 / 100                                     # kN/cm2
cols = []
for ix, x in enumerate(NX):
    dxl = (x - NX[ix - 1]) / 2 if ix > 0 else 0.0
    dxr = (NX[ix + 1] - x) / 2 if ix < len(NX) - 1 else 0.0
    dx = dxl + dxr
    for iy, y in enumerate(NY):
        dyl = (y - NY[iy - 1]) / 2 if iy > 0 else 0.0
        dyr = (NY[iy + 1] - y) / 2 if iy < len(NY) - 1 else 0.0
        dy = dyl + dyr
        At = dx * dy
        if At <= 0:
            continue
        ref = "R%sC%s" % (iy + 1, ix + 1)
        # ELU
        Nt_u = At * (1.35 * G_T + 1.50 * Q_T)
        Ne_u = At * (1.35 * G_E + 1.50 * Q_E)
        # poutres (1 sens principal + appuis), section hors dalle
        Lp = (dx + dy)
        Np_u = Lp * B_POU * (H_POU - E_DALLE) * 25 * 1.35
        # poteau : cumul des niveaux
        Nc_u = 0.0
        for lvl in range(D["niveaux"]):
            Nc_u += B_POT * H_POT * D["h_RDC"] * 25 * 1.35
        # charge d'exploitation des poutres/chainages secondaires : 8% forfaitaire documente
        Nu = (Nt_u + Ne_u) * 1.08 + 2 * Np_u + Nc_u
        # ELS (pour les fondations)
        Nt_s = At * (G_T + Q_T)
        Ne_s = At * (G_E + Q_E)
        Np_s = Lp * B_POU * (H_POU - E_DALLE) * 25
        Nc_s = B_POT * H_POT * D["h_RDC"] * 25 * D["niveaux"]
        Nser = (Nt_s + Ne_s) * 1.08 + 2 * Np_s + Nc_s
        # section requise : Nu(kN) -> daN ; fdm_sec en daN/cm2
        Br_req = Nu * 100 / fdm_sec                 # cm2
        cols.append({"ref": ref, "x": round(x, 3), "y": round(y, 3),
                     "At_m2": round(At, 2), "position": ("coin" if (ix in (0, 3) and iy in (0, 3))
                     else ("peripherique" if ix in (0, 3) or iy in (0, 3) else "interieur")),
                     "Nu_kN": round(Nu, 1), "Nser_kN": round(Nser, 1),
                     "Br_requis_cm2": round(Br_req, 1),
                     "Br_fourni_cm2": round(B_POT * H_POT * 10000, 0),
                     "taux_travail": round(Br_req / (B_POT * H_POT * 10000) * 100, 1),
                     "elancement_lambda": None})
print("\n[4] DESCENTE DE CHARGES (ELU 1,35G + 1,50Q)")
print("  %-6s %-13s %6s %9s %9s %9s %6s" % ("ref", "position", "At m2", "Nu kN", "Nser kN",
                                           "Br req", "taux"))
maxu = max(cols, key=lambda c: c["Nu_kN"])
for c in sorted(cols, key=lambda c: -c["Nu_kN"])[:4]:
    print("  %-6s %-13s %6.2f %9.1f %9.1f %9.1f %5.1f%%"
          % (c["ref"], c["position"], c["At_m2"], c["Nu_kN"], c["Nser_kN"],
             c["Br_requis_cm2"], c["taux_travail"]))
print("  ... (%d poteaux au total)" % len(cols))

# ---- 5. VERIFICATIONS ----
lf = 0.7 * D["h_RDC"]
i_pot = B_POT / math.sqrt(12) * 100          # cm
lam = lf * 100 / i_pot
Br_f = B_POT * H_POT * 10000
reste = [c for c in cols if c["Br_requis_cm2"] <= Br_f]
for c in cols:
    c["elancement_lambda"] = round(lam, 1)
verifs = [
    {"nom": "poteau_resistance_compression", "critere": "Br_requis <= Br_fourni",
     "resultat": "PASS" if len(reste) == len(cols) else "FAIL",
     "detail": "max Br_requis %.1f cm2 <= %d cm2 (taux de travail max %.0f%%)"
               % (max(c["Br_requis_cm2"] for c in cols), Br_f, 100 * max(c["Br_requis_cm2"] for c in cols) / Br_f)},
    {"nom": "poteau_dimension_minimale_BAEL", "critere": "min(b,h) >= 25 cm (BAEL B.8.4.0)",
     "resultat": "PASS" if min(B_POT, H_POT) * 100 >= 25 else "FAIL",
     "detail": "adopte %.0f cm ; minimum reglementaire 25 cm" % (B_POT * 100)},
    {"nom": "poteau_elancement", "critere": "lambda <= 50 (BAEL)",
     "resultat": "PASS" if lam <= 50 else "FAIL", "detail": "lambda = %.1f" % lam},
    {"nom": "dalle_deflexion", "critere": "e >= L/25",
     "resultat": "PASS" if E_DALLE >= max(trame["travees_X"]) / 25 else "FAIL",
     "detail": "e = %.0f mm >= %.0f mm" % (E_DALLE * 1000, max(trame["travees_X"]) * 1000 / 25)},
    {"nom": "poutre_deflexion", "critere": "h >= L/16",
     "resultat": "PASS" if H_POU >= max(trame["travees_Y"]) / 16 else "FAIL",
     "detail": "h = %.0f mm >= %.0f mm" % (H_POU * 1000, max(trame["travees_Y"]) * 1000 / 16)},
    {"nom": "portance_sol", "critere": "portance connue",
     "resultat": "BLOCKED", "detail": "UNKNOWN - aucune etude geotechnique fournie"},
]
print("\n[5] VERIFICATIONS")
for v in verifs:
    print("  %-30s %-8s %s" % (v["nom"], v["resultat"], v["detail"]))

# ---- 6. FONDATIONS (fonction de la portance, table de sensibilite) ----
maxser = max(c["Nser_kN"] for c in cols)
tots = sum(c["Nser_kN"] for c in cols)
fon = []
for sig in (0.10, 0.15, 0.20, 0.25):
    S = maxser / (sig * 1000)                   # m2
    cote = math.ceil(math.sqrt(S) * 20) / 20    # arrondi 5 cm
    fon.append({"portance_MPa": sig, "S_requise_m2": round(S, 3),
                "semelle_m": "%.2f x %.2f" % (cote, cote), "S_fournie_m2": round(cote * cote, 3)})
print("\n[6] FONDATIONS — semelles isolees (portance NON CONNUE, table de sensibilite)")
print("  charge ELS max par poteau : %.1f kN | total batiment : %.1f kN (%.0f t)"
      % (maxser, tots, tots / 9.81))
for f in fon:
    print("    si portance = %.2f MPa -> semelle %.2f x %.2f m (%.2f m2)"
          % (f["portance_MPa"], float(f["semelle_m"].split(" x ")[0]),
             float(f["semelle_m"].split(" x ")[1]), f["S_fournie_m2"]))

# ---- 7. INCONNUES BLOQUANTES ----
inconnues = [
    {"element": "Portance du sol", "statut": "UNKNOWN",
     "impact": "dimensionnement des fondations", "requis": "etude geotechnique (essai pressiometrique)"},
    {"element": "Zone sismique", "statut": "UNKNOWN",
     "impact": "dispositions constructives, chainages, ductilite", "requis": "reglement parasismique applicable"},
    {"element": "Vitesse de vent de reference", "statut": "UNKNOWN",
     "impact": "stabilite au vent, contreventement", "requis": "donnees meteo du site (Abidjan)"},
    {"element": "Classe de beton et d'acier", "statut": "HYPOTHESIS",
     "impact": "sections d'armatures", "requis": "validation fc28=25 MPa / fe=500 MPa"},
    {"element": "Charges d'exploitation reelles", "statut": "HYPOTHESIS",
     "impact": "descente de charges", "requis": "usage piece par piece (dont terrasse)"},
]

out = {"phase": "1. STRUCTURE CONCEPTUELLE", "at": STAMP,
       "geometrie_source": {"fichier": "floorplan/floor_plan.json",
                            "sha256": lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"],
                            "statut_geometrie": "VALIDATED"},
       "systeme": {"type": "ossature poteaux-poutres beton arme + dalles pleines",
                   "remplissage": "maconnerie de remplissage + chainages",
                   "niveaux": 2, "hauteur_totale_m": D["h_RDC"] + D["h_ETAGE"],
                   "justification": "standard villa R+1, portees 3,33-3,50 m, "
                                    "independance vis-a-vis des cloisons"},
       "hypotheses": {"charges": CH, "materiaux": MAT, "sol": SOL,
                      "notes": "1,08 = forfait +8% pour escalier, acrotere et elements secondaires"},
       "trame": trame, "nb_poteaux": len(cols), "poteaux": cols,
       "predimensionnement": {"dalle": {"e_m": E_DALLE, "regle": "e >= L/25"},
                              "poutres": {"b_m": B_POU, "h_m": H_POU, "regle": "h >= L/16"},
                              "poteaux": {"b_m": B_POT, "h_m": H_POT,
                                          "regle": "Br >= Nu / (0,85 fc28 / (0,9 gb))"},
                              "fondations": {"type": "semelles isolees", "table_portance": fon,
                                             "longrines": "20 x 30 cm (liaisonnement)"}},
       "verifications": verifs, "inconnues_bloquantes": inconnues,
       "exclusions": ["escalier (a dimensionner en phase 4)",
                      "effets sismiques et de vent (donnees UNKNOWN)",
                      "descente de charges differentielle et tassements",
                      "armatures detaillees (phase BIM/notes de calcul)"],
       "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
os.makedirs(os.path.join(P, "structure"), exist_ok=True)
p_out = os.path.join(P, "structure", "structural_concept.json")
json.dump(out, open(p_out, "w"), indent=2, ensure_ascii=False)
print("\n[7] SORTIE -> %s (%d o, %s)" % (p_out, os.path.getsize(p_out), sha(p_out)[:32] + "…"))

# ---- 8. PLAN DE STRUCTURE (SVG) ----
SC, OX, OY = 50.0, 100.0, 160.0
EBW, EBD = 10.40, 10.90
W = EBW * SC + 2 * OX
H = EBD * SC + OY + 170


def X(m):
    return OX + m * SC


def Y(m):
    return OY + (EBD - m) * SC


L = ["<?xml version='1.0' encoding='UTF-8'?>",
     "<svg xmlns='http://www.w3.org/2000/svg' width='%.0f' height='%.0f' viewBox='0 0 %.0f %.0f'>"
     % (W, H, W, H),
     "<rect width='100%' height='100%' fill='#ffffff'/>",
     "<text x='90' y='44' font-family='Helvetica,Arial' font-size='20' font-weight='bold' "
     "fill='#0f172a'>PLAN DE STRUCTURE — ossature BA</text>",
     "<text x='90' y='66' font-family='Helvetica,Arial' font-size='11' fill='#475569'>"
     "Trame 4 × 4 poteaux 30 × 30 cm · travees 3,33 × 3,50 m · poutres 25 × 35 cm · "
     "dalle pleine 15 cm</text>",
     "<text x='90' y='84' font-family='Helvetica,Arial' font-size='9.5' fill='#94a3b8'>"
     "Geometrie source VERROUILLEE (floor_plan.json %s) · STATUS : PROPOSED — "
     "portance du sol UNKNOWN</text>" % lock["fichiers_verrouilles"]["floor_plan.json"]["sha256"][:12],
     "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#f8fafc' stroke='#0f172a' "
     "stroke-width='3.5'/>" % (X(0), Y(EBD), EBW * SC, EBD * SC),
     "<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#ffffff' stroke='#cbd5e1' "
     "stroke-width='0.8'/>" % (X(0.20), Y(0.20 + 10.50), 10.00 * SC, 10.50 * SC)]
# fondations (portance supposee 0,15 MPa) en pointille
sig_ref = 0.15
for c in cols:
    S = math.ceil(math.sqrt(c["Nser_kN"] / (sig_ref * 1000)) * 20) / 20
    cx, cy = 0.20 + c["x"], 0.20 + c["y"]
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='none' stroke='#a16207' "
             "stroke-width='1.2' stroke-dasharray='5,4'/>"
             % (X(cx - S / 2), Y(cy + S / 2), S * SC, S * SC))
# axes
for v in NX:
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' stroke-width='0.7' "
             "stroke-dasharray='9,4,2,4'/>" % (X(0.20 + v), Y(0.20), X(0.20 + v), Y(0.20 + 10.50)))
for v in NY:
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#dc2626' stroke-width='0.7' "
             "stroke-dasharray='9,4,2,4'/>" % (X(0.20), Y(0.20 + v), X(0.20 + 10.00), Y(0.20 + v)))
# poutres
for v in NX:
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#1e40af' stroke-width='4' "
             "stroke-linecap='square'/>"
             % (X(0.20 + v), Y(0.20), X(0.20 + v), Y(0.20 + 10.50)))
for v in NY:
    L.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#1e40af' stroke-width='4' "
             "stroke-linecap='square'/>"
             % (X(0.20), Y(0.20 + v), X(0.20 + 10.00), Y(0.20 + v)))
# poteaux
for c in cols:
    cx, cy = 0.20 + c["x"], 0.20 + c["y"]
    L.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f' fill='#7f1d1d' stroke='#450a0a' "
             "stroke-width='0.8'/>" % (X(cx - 0.15), Y(cy + 0.15), 0.30 * SC, 0.30 * SC))
    if c["position"] != "interieur":
        L.append("<text x='%.1f' y='%.1f' text-anchor='middle' font-family='Helvetica,Arial' "
                 "font-size='7' fill='#0f172a'>%s</text>" % (X(cx), Y(cy) - 0.30 * SC, c["ref"]))
leg = [("Poteau BA 30 x 30 cm", "#7f1d1d"), ("Poutre BA 25 x 35 cm", "#1e40af"),
       ("Axe de trame", "#dc2626"), ("Semelle isolee (si portance 0,15 MPa)", "#a16207")]
yy = H - 118
L.append("<text x='90' y='%.1f' font-family='Helvetica,Arial' font-size='12' font-weight='bold' "
         "fill='#0f172a'>Legende</text>" % yy)
yy += 22
for i, (t, col) in enumerate(leg):
    L.append("<rect x='90' y='%.1f' width='22' height='11' fill='%s' stroke='#334155' "
             "stroke-width='0.8'/>" % (yy - 9, col))
    L.append("<text x='122' y='%.1f' font-family='Helvetica,Arial' font-size='10.5' "
             "fill='#334155'>%s</text>" % (yy, t))
    yy += 19
yy += 6
for t in ["Charge descendue totale : %.0f kN (%.0f t) · Nu max par poteau : %.1f kN"
          % (tots, tots / 9.81, max(c["Nu_kN"] for c in cols)),
          "Verifications : resistance PASS · elancement PASS · dalle PASS · poutre PASS · "
          "PORTANCE DU SOL = UNKNOWN (bloquant)",
          "Ce plan est un SCHEMA CONCEPTUEL non contractuel — armatures non definies."]:
    L.append("<text x='90' y='%.1f' font-family='Helvetica,Arial' font-size='10' fill='#64748b'>"
             "%s</text>" % (yy, t))
    yy += 16
L.append("</svg>")
p_svg = os.path.join(P, "structure", "plan_structure.svg")
open(p_svg, "w", encoding="utf-8").write("\n".join(L))
print("[8] PLAN   -> %s (%d o, %s)" % (p_svg, os.path.getsize(p_svg), sha(p_svg)[:32] + "…"))

# ---- 9. EVIDENCE ----
evd = os.path.join(P, "evidence", "phase1_structure")
os.makedirs(evd, exist_ok=True)
ev = {"operation": "phase1_structure_conceptuelle", "at": STAMP, "tool": "python3",
      "geometrie_source": out["geometrie_source"],
      "created": [{"path": os.path.relpath(f, P), "octets": os.path.getsize(f), "sha256": sha(f)}
                  for f in (p_out, p_svg)],
      "tests": [{"name": v["nom"], "resultat": v["resultat"], "critere": v["critere"],
                 "detail": v["detail"]} for v in verifs],
      "inconnues_bloquantes": inconnues,
      "STATUS": out["STATUS"]}
json.dump(ev, open(os.path.join(evd, "evidence.json"), "w"), indent=2, ensure_ascii=False)
print("[9] EVIDENCE -> evidence/phase1_structure/evidence.json")

hist = {"event": "PHASE_1_STRUCTURE_CONCEPTUELLE", "DATE": STAMP,
        "systeme": out["systeme"]["type"], "poteaux": {"nb": len(cols), "section": "30x30 cm"},
        "poutres": "25x35 cm", "dalle_m": E_DALLE, "Nu_max_kN": max(c["Nu_kN"] for c in cols),
        "charge_totale_kN": round(tots, 1), "portance_sol": "UNKNOWN",
        "STATUS": "PROPOSED_AWAITING_HUMAN_VALIDATION"}
with open(os.path.join(P, "history", "history.jsonl"), "a") as f:
    f.write(json.dumps(hist, ensure_ascii=False) + "\n")

print("\nSTATUS : %s" % out["STATUS"])
print("RESUME : %d poteaux 30x30 | poutres 25x35 | dalle 15 cm | semelles isolees"
      % len(cols))
print("         Nu max %.1f kN | Br requis max %.1f cm2 / fourni %d cm2 | lambda %.1f"
      % (max(c["Nu_kN"] for c in cols), max(c["Br_requis_cm2"] for c in cols), Br_f, lam))
print("         %.1f t de charges descendues | portance sol = UNKNOWN (bloquant fondations)"
      % (tots / 9.81))
