#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M4 — DATA BINDING FRONTEND.
Supprime les donnees projet codees en dur dans index.html et les remplace par
des valeurs venant de /api/assistant/context (lui-meme alimente par assistant_core.py,
qui lit les fichiers reels du projet).

Flux impose : fichiers reels -> assistant_core.py -> API -> frontend
"""
P = "/Users/mac/ConstructionAgent/web/frontend/index.html"
s = open(P).read()
n0 = len(s)


def rep(old, new, label):
    global s
    c = s.count(old)
    if c != 1:
        raise SystemExit("STOP - ancre '%s' : %d occurrence(s), attendu 1" % (label, c))
    s = s.replace(old, new)
    print("  OK  %-52s (1)" % label)


# ------------------------------------------------------------------ #
# 1. Chargeur de contexte + formatage — UNE seule source de verite
# ------------------------------------------------------------------ #
rep("function toggleMore(e){",
    """/* ===== M4 — DONNEES PROJET : source unique ==========================
   /api/assistant/context est alimente par assistant_core.py, qui lit les
   fichiers reels du projet. Aucune valeur projet n'est codee en dur ici.
   =================================================================== */
let CTX = null;
async function ctxLoad(){
  if(CTX) return CTX;
  try{ CTX = await api("/api/assistant/context"); }catch(e){ CTX = null; }
  return CTX;
}
/* Formate un entier a la francaise : 29753918 -> "29 753 918" */
function fn(n){
  if(n === null || n === undefined) return "UNKNOWN";
  try{ return String(n).replace(/\\B(?=(\\d{3})+(?!\\d))/g, " "); }catch(e){ return String(n); }
}
/* Valeur ou UNKNOWN — jamais 0 ni "undefined" a l'ecran. */
function vu(v){ return (v === null || v === undefined || v === "") ? "UNKNOWN" : v; }

function toggleMore(e){""", "M4 : ctxLoad() + fn() + vu()")

# ------------------------------------------------------------------ #
# 2. .hcaps — "Interactif, 326 elements" devient dynamique
# ------------------------------------------------------------------ #
rep("<div><span class=\"ic\">&#129513;</span><div><b>BIM 3D</b><span>Interactif, 326 elements</span></div></div>",
    "<div><span class=\"ic\">&#129513;</span><div><b>BIM 3D</b><span>Interactif, ${CX?vu(CX.bim.total):\"\\u2026\"} elements</span></div></div>",
    ".hcaps : 326 elements -> ${CX.bim.total}")

# vAccueil doit charger le contexte avant de rendre
rep('function vAccueil(){\n  const [p, s, ph] = await Promise.all(',
    'function vAccueil(){\n  const CX = await ctxLoad();\n  const [p, s, ph] = await Promise.all(',
    "vAccueil : charge CTX")

# ------------------------------------------------------------------ #
# 3. whereAmI() — reconstruit a partir des donnees reelles
# ------------------------------------------------------------------ #
old_where = '''async function whereAmI(){
  const [p, g] = await Promise.all([api("/api/project"), api("/api/gates")]);
  const t = `DOSSIER NUMÉRIQUE — ${p.nom}
✓ programme          ✓ architecture (VARIANTE A VALIDÉE)
✓ BIM (326 objets)    ✓ plans (10) + coupes (2) + façades (4)
✓ métrés v2           ✓ budget v2 (29 753 918 FCFA — estimation)
✓ documentation (13)  ✓ rendus (10)

BLOQUAGES OUVERT
⚿ G2 — Assainissement / exutoire des eaux usées
     → topographe + professionnel assainissement
⚿ G3 — Validation géotechnique et structure
     → géotechnicien + ingénieur structure
     (portance du sol 0,15 MPa = HYPOTHÈSE non vérifiée)

CHANTIER PHYSIQUE — 0 %
Aucun travail physique de construction n'a commencé.

PROCHAINE ACTION
Faire remplir reports/G2_FICHE_COLLECTE.md et reports/G3_FICHE_COLLECTE.md.`;
  alertBox("OÙ EN EST MA MAISON ?", t);
}'''
new_where = '''async function whereAmI(){
  /* M4 — toutes les valeurs viennent de l'API, aucune n'est codee en dur. */
  const [CX, NS] = await Promise.all([ctxLoad(), api("/api/assistant/next-step")]);
  if(!CX){ alertBox("OÙ EN EST MA MAISON ?", "Contexte indisponible : /api/assistant/context n'a pas repondu.\\nAucune valeur n'est affichee plutot que d'en inventer une."); return; }
  const d = CX.documents || {};
  const gates = (CX.human_gates || []).map(x =>
    `${x.statut === "CLOSED" ? "\\u2713" : "\\u26bf"} ${x.id} ${x.statut} — ${x.objet}` +
    (x.professionnel ? `\\n     → ${x.professionnel}` : "")).join("\\n");
  const t = `DOSSIER NUMÉRIQUE — ${vu(CX.project_name)} (${vu(CX.project_id)})
\\u2713 programme ${vu(CX.program && CX.program.data_status)} \\u2014 ${vu(CX.program && CX.program.pieces)} pieces, ${vu(CX.program && CX.program.chambres)} chambres
\\u2713 BIM ${vu(CX.bim && CX.bim.total)} elements \\u2014 source ${vu(CX.bim && CX.bim.source)}
\\u2713 plans ${vu(d.plans)} + coupes ${vu(d.coupes)} + façades ${vu(d.facades)}
\\u2713 métrés ${vu(CX.metre && CX.metre.status)}
\\u2713 budget ${vu(CX.budget && CX.budget.status)} \\u2014 ${fn(CX.budget && CX.budget.total_fcfa)} FCFA (estimation de travail)
\\u2713 documentation ${vu(d.docs)} \\u2713 rendus ${vu(d.renders)}

VALIDATIONS (etat reel)
${gates}

CHANTIER PHYSIQUE — 0 %
Aucun travail physique de construction n'a commence.

PROCHAINE ETAPE
${vu(NS && NS.titre)}
${NS && NS.raison ? NS.raison : ""}
${NS && NS.methode ? "(methode : " + NS.methode + ")" : ""}`;
  alertBox("OÙ EN EST MA MAISON ?", t);
}'''
rep(old_where, new_where, "whereAmI() : 100% donnees API")

# ------------------------------------------------------------------ #
# 4. Descriptions de plans — plus de faits projet codes en dur
# ------------------------------------------------------------------ #
rep('''  const desc = {"P01":"Implantation du bâtiment sur le terrain de 15 × 25 m.",''',
    '''  const CXd = await ctxLoad();
  const _tm = CXd && CXd.site && CXd.site.terrain_m ? CXd.site.terrain_m : null;
  const _ter = _tm ? `${vu(_tm[0])} \\u00d7 ${vu(_tm[1])} m` : "UNKNOWN";
  const _nbch = CXd && CXd.program ? vu(CXd.program.chambres) : "UNKNOWN";
  const desc = {"P01":`Implantation du bâtiment sur le terrain de ${_ter}.`,''' ,
    "loadPlan : terrain et chambres depuis l'API")

rep('''    "P03":"Plan de l'étage : 4 chambres, 3 salles de bain, patio.",''',
    '''    "P03":`Plan de l'étage : ${_nbch} chambres, salles de bain, patio.`,''',
    "loadPlan : P03 chambres depuis l'API")

assert len(s) < 200000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (%+d)" % (n0, len(s), len(s) - n0))
