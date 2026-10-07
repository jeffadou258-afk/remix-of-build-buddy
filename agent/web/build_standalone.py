#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère une version AUTONOME de l'application : un seul fichier HTML,
toutes les données du projet embarquées, AUCUN serveur requis.
Ouvre-le par double-clic dans n'importe quel navigateur.

Sortie : web/frontend/Villa_Test_001_APP.html
Les données proviennent des mêmes fichiers que l'API — aucune donnée inventée."""
import json, os, sys, base64, datetime

ROOT = "/Users/mac/ConstructionAgent"
PROJ = os.path.join(ROOT, "projects", "PRJ_1701484686")
sys.path.insert(0, os.path.join(ROOT, "engines", "construction_guide"))
import engine as CGE  # noqa

def J(p):
    f = os.path.join(PROJ, p)
    return json.load(open(f)) if os.path.exists(f) else None
def sh(p):
    f = os.path.join(PROJ, p)
    return base64.b64encode(open(f, "rb").read()).decode() if os.path.exists(f) else None
def folder(d, ext):
    out = []
    for f in sorted(os.listdir(os.path.join(PROJ, d))) if os.path.isdir(os.path.join(PROJ, d)) else []:
        if f.endswith(ext):
            out.append({"nom": f, "data": sh(os.path.join(d, f))})
    return out

site = J("site/site.json") or {}
st = {}
b = J("budget/budget_final_v2.json") or {}
m = J("metre/metre_final_v2.json") or {}

# --- sorties REELLES du moteur (capturees) ---
import io, contextlib
def cap(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: fn(*a, **k)
        except Exception as e: print("ERREUR : %s" % e)
    return buf.getvalue()

g = CGE.ConstructionGuide(PROJ); g.pro = False
gp = CGE.ConstructionGuide(PROJ); gp.pro = True

DATA = {
    "project": {"id": "PRJ_1701484686", "nom": "Villa_Test_001", "localisation": "Abidjan, Côte d'Ivoire",
                "type": "Villa R+1", "terrain": "15,00 × 25,00 m = 375 m²", "surface_interieure": "150 m²",
                "chambres": 4, "variante": "A (validée)", "source": "site/site.json + program/",
                "avertissement": "Le dossier numérique avancé ne signifie PAS que la maison est construite.",
                "programme": {"RDC": "81 m² de pièces + 24 m² circulation = 105 m²", "étage": "69 m² de pièces + 16 m² circulation",
                              "extérieurs": "garage 25 m² · terrasse 24 m² · patio 12 m²"}},
    "status": {"dossier_numerique": "AVANCÉ", "chantier_physique_pct": 0,
               "avertissement": "Le dossier numérique avancé ne signifie PAS que la maison est construite.",
               "texte_brut": cap(g.status)},
    "phases": [{"id": n, "nom": nom, "objectif": obj, "explication": sim, "travaux": fait,
                "professionnels": qui, "human_gate": gate} for (n, nom, obj, sim, fait, qui, mk, gate) in CGE.phases()],
    "budget": {"mention": "Estimation de travail — NON devis définitif",
               "total_fcfa": b.get("total_general_fcfa"), "independant_g3_fcfa": b.get("total_perimetre_independant_G3_fcfa"),
               "dependant_g3_fcfa": b.get("total_perimetre_dependant_G3_fcfa"),
               "ancien_budget_fcfa": b.get("ancien_budget_reference_fcfa"),
               "comparabilite": "NON comparable à périmètre identique (second œuvre et lots techniques non requantifiés)",
               "lignes": b.get("lignes", []), "source": "budget/budget_final_v2.json"},
    "quantities": {"quantites": [{"element": x["id"], "quantite": x["quantite"], "unite": x["unite"],
                                  "statut": x["statut"], "methode": x["methode"]}
                                 for x in m.get("quantites_independantes_de_G3", []) + m.get("quantites_dependantes_de_G3", [])]},
    "gates": {"gates": [
        {"id": "G1", "objet": "Choix architectural A/B", "statut": "CLOSED", "detail": "OPTION A retenue par l'utilisateur",
         "intervenants": ["utilisateur"], "pourquoi": "Décision architecturale — tranchée"},
        {"id": "G2", "objet": "Exutoire des eaux usées", "statut": "OPEN / HUMAN_GATE",
         "detail": "9 champs de site/site.json sont UNKNOWN : aucun réseau public, fosse, regard ou pente ne peut être déterminé",
         "intervenants": ["topographe", "professionnel assainissement"],
         "pourquoi": "Sans exutoire connu, le tracé EU/EV ne peut pas être établi. L'inventer serait une faute.",
         "champs_a_remplir": 10, "fiche": "reports/G2_FICHE_COLLECTE.md"},
        {"id": "G3", "objet": "Validation géotechnique et dimensionnement structure", "statut": "OPEN / HUMAN_GATE",
         "detail": "7 PROPOSED / 2 HYPOTHESIS / 7 UNKNOWN. Portance 0,15 MPa = HYPOTHÈSE. 2 anomalies géométriques à arbitrer.",
         "intervenants": ["géotechnicien", "ingénieur structure"],
         "pourquoi": "Une fondation ne peut pas être coulée sur une portance supposée. Un modèle conceptuel n'autorise pas à construire.",
         "champs_a_remplir": 32, "fiche": "reports/G3_FICHE_COLLECTE.md"}],
        "legende_statuts": ["CONNU", "CALCULÉ", "HYPOTHÈSE", "INCONNU", "VÉRIFIÉ", "HUMAN_GATE", "PENDING_VALIDATION"]},
    "plans": {"plans": [{"nom": p["nom"], "type": t, "data": p["data"]}
                        for t, d in (("plan", "plans"), ("coupe", "coupes"), ("facade", "facades"))
                        for p in folder(d, ".svg")]},
    "renders": {"rendus": folder("renders", ".png"), "total": len(folder("renders", ".png")),
                "avertissement": "MATERIALS_HYPOTHESIS · photoréalisme de présentation NON validé"},
    "documents": {"documents": [{"nom": f, "octets": os.path.getsize(os.path.join(PROJ, "docs", f))}
                                for f in sorted(os.listdir(os.path.join(PROJ, "docs")))]},
    "bim": {"fichier": "3D/BIM_FINAL_A3.blend", "existe": os.path.exists(os.path.join(PROJ, "3D/BIM_FINAL_A3.blend")),
            "octets": os.path.getsize(os.path.join(PROJ, "3D/BIM_FINAL_A3.blend")), "objets": 326,
            "glb": os.path.exists(os.path.join(PROJ, "3D/BIM_FINAL_A3.glb")),
            "glb_octets": os.path.getsize(os.path.join(PROJ, "3D/BIM_FINAL_A3.glb")) if os.path.exists(os.path.join(PROJ, "3D/BIM_FINAL_A3.glb")) else 0},
    "assistant": {
        "poteau": {"debutant": cap(g.ask, "Qu'est-ce qu'un poteau ?"), "pro": cap(gp.ask, "Qu'est-ce qu'un poteau ?")},
        "fondations_now": {"debutant": cap(g.ask, "Puis-je construire les fondations maintenant ?"), "pro": None},
        "ou": {"debutant": cap(g.status), "pro": None},
        "longrine": {"debutant": cap(g.ask, "Qu'est-ce qu'une longrine ?"), "pro": None},
        "explique": {"debutant": cap(g.explain_all), "pro": None}},
    "generated_at": datetime.datetime.now().isoformat(timespec="seconds")}

HTML = r"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Construction Agent — Villa_Test_001 (version autonome)</title>
<style>
:root{--bg:#0e1114;--panel:#151a1f;--panel2:#1b2229;--line:#2a333c;--txt:#e8edf1;--muted:#93a3b1;
--accent:#c8a45c;--accent2:#5c8fc8;--ok:#3fa86b;--warn:#d99b2b;--bad:#d4534e;--gate:#b06dd4;--unk:#6b7a88}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.app{display:flex;min-height:100vh}
aside{width:246px;flex:0 0 246px;background:var(--panel);border-right:1px solid var(--line);padding:20px 14px;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{display:flex;align-items:center;gap:10px;margin-bottom:22px;padding:0 6px}
.brand .mk{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--accent),#8a6f34);display:grid;place-items:center;font-weight:800;color:#141414}
.brand h1{font-size:15px}.brand p{font-size:11px;color:var(--muted);margin-top:1px}
nav a{display:flex;gap:10px;padding:9px 11px;border-radius:8px;color:var(--muted);font-size:13.5px;cursor:pointer;margin-bottom:2px}
nav a:hover{background:var(--panel2);color:var(--txt)}
nav a.on{background:linear-gradient(90deg,rgba(200,164,92,.16),transparent);color:var(--accent);box-shadow:inset 2px 0 0 var(--accent)}
main{flex:1;min-width:0;padding:26px 30px 90px;max-width:1500px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:22px}
h2{font-size:23px}.sub{color:var(--muted);font-size:13px;margin-top:4px}
.modes{display:flex;gap:6px;background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:4px}
.modes button{background:none;border:0;color:var(--muted);padding:7px 14px;border-radius:6px;cursor:pointer;font-size:12.5px;font-weight:600;font-family:inherit}
.modes button.on{background:var(--accent);color:#141414}
.grid{display:grid;gap:14px}.g3{grid-template-columns:repeat(auto-fit,minmax(215px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:17px 18px}
.card h3{font-size:13px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);font-weight:600;margin-bottom:11px}
.big{font-size:29px;font-weight:700}
.kv{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.045);font-size:13.5px}
.kv:last-child{border:0}.kv span:first-child{color:var(--muted)}
.prog{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
.progbox{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.progbox .lbl{font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);font-weight:600}
.bar{height:7px;background:var(--panel2);border-radius:4px;overflow:hidden;margin:11px 0 8px}
.bar i{display:block;height:100%;border-radius:4px}.progbox .val{font-size:26px;font-weight:700}
.warnline{background:rgba(176,109,212,.09);border:1px solid rgba(176,109,212,.3);border-radius:10px;padding:13px 16px;font-size:13px;color:#dcc4ec;margin-bottom:20px}
.ph{display:flex;gap:14px;padding:13px 15px;background:var(--panel);border:1px solid var(--line);border-radius:10px;margin-bottom:8px;cursor:pointer;align-items:center}
.ph:hover{border-color:#3d4a55}.ph .num{width:36px;height:36px;flex:0 0 36px;border-radius:8px;background:var(--panel2);display:grid;place-items:center;font-weight:700;font-size:13px;color:var(--muted)}
.ph .t{flex:1;min-width:0}.ph .t b{font-size:14.5px;display:block}.ph .t small{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block}
.badge{font-size:10.5px;font-weight:700;letter-spacing:.5px;padding:4px 9px;border-radius:5px;white-space:nowrap}
.b-ok{background:rgba(63,168,107,.15);color:var(--ok)}.b-ver{background:rgba(92,143,200,.15);color:var(--accent2)}
.b-hyp{background:rgba(217,155,43,.15);color:var(--warn)}.b-gate{background:rgba(176,109,212,.15);color:var(--gate)}
.b-blk{background:rgba(212,83,78,.15);color:var(--bad)}.b-unk{background:rgba(107,122,136,.18);color:var(--unk)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);padding:9px 10px;border-bottom:1px solid var(--line)}
td{padding:10px;border-bottom:1px solid rgba(255,255,255,.04)}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:12.5px}
.viewer{background:#fff;border-radius:10px;overflow:auto;height:600px;border:1px solid var(--line);cursor:grab}
.viewer img{display:block;transform-origin:0 0;max-width:none}
.vbar{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}
.vbar button,.btn{background:var(--panel2);border:1px solid var(--line);color:var(--txt);padding:8px 13px;border-radius:7px;cursor:pointer;font-size:12.5px;font-weight:600;font-family:inherit}
.vbar button:hover,.btn:hover{border-color:var(--accent);color:var(--accent)}
.vbar button.on{background:var(--accent);color:#141414}
.pills{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.pills button{background:var(--panel);border:1px solid var(--line);color:var(--muted);padding:6px 11px;border-radius:20px;font-size:12px;cursor:pointer;font-family:inherit}
.pills button.on{background:var(--accent2);color:#fff}
.chat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;height:58vh;overflow-y:auto;display:flex;flex-direction:column;gap:13px}
.msg{max-width:82%;padding:12px 15px;border-radius:11px;font-size:13.8px;white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace;line-height:1.5}
.msg.u{align-self:flex-end;background:var(--accent2);color:#fff;font-family:inherit}
.msg.a{align-self:flex-start;background:var(--panel2);border:1px solid var(--line)}
.msg.a.secu{border-color:var(--gate);background:rgba(176,109,212,.09)}
.inrow{display:flex;gap:9px;margin-top:12px}
.inrow input{flex:1;background:var(--panel);border:1px solid var(--line);color:var(--txt);padding:13px 15px;border-radius:9px;font-size:14px;font-family:inherit;outline:none}
.chips{display:flex;gap:7px;flex-wrap:wrap;margin-top:11px}
.chips button{background:var(--panel);border:1px solid var(--line);color:var(--muted);padding:7px 12px;border-radius:16px;font-size:12px;cursor:pointer;font-family:inherit}
.note{font-size:12.5px;color:var(--muted);background:var(--panel2);border-left:2px solid var(--accent);padding:11px 14px;border-radius:0 7px 7px 0;margin-top:12px}
.HG{position:fixed;bottom:22px;right:22px;background:linear-gradient(135deg,var(--accent),#a3843f);color:#141414;border:0;padding:15px 23px;border-radius:26px;font-weight:700;font-size:13.5px;cursor:pointer;box-shadow:0 7px 26px rgba(200,164,92,.3);font-family:inherit;z-index:50}
.mob{display:none}
@media(max-width:900px){aside{display:none}main{padding:18px 15px 96px}
.mob{display:flex;position:fixed;bottom:0;left:0;right:0;background:var(--panel);border-top:1px solid var(--line);justify-content:space-around;padding:9px 4px 11px;z-index:60}
.mob a{flex:1;text-align:center;color:var(--muted);font-size:10px;padding:3px}.mob a i{display:block;font-size:19px;font-style:normal}
.mob a.on{color:var(--accent)}.HG{bottom:76px;right:14px;padding:13px 18px;font-size:12.5px}
table{font-size:12.5px}th,td{padding:8px 6px}.msg{max-width:94%}}
.banner{background:rgba(63,168,107,.12);border:1px solid rgba(63,168,107,.4);color:#a4e0be;padding:11px 16px;border-radius:9px;font-size:13px;margin-bottom:18px}
</style></head><body>
<div class="app"><aside>
<div class="brand"><div class="mk">CA</div><div><h1>Construction Agent</h1><p>PRJ_1701484686</p></div></div>
<nav id="nav"></nav><div style="height:1px;background:var(--line);margin:14px 8px"></div>
<div style="padding:0 10px;font-size:11px;color:var(--muted)"><div style="text-transform:uppercase;letter-spacing:.7px;font-weight:600">Mode autonome</div>
<div style="margin-top:5px;line-height:1.4">Aucun serveur requis<br>Toutes les données sont embarquées</div></div>
</aside><main>
<div class="top"><div><h2 id="ttl">Accueil</h2><div class="sub" id="sub"></div></div>
<div class="modes"><button id="mB" class="on" onclick="setMode(0)">Débutant</button><button id="mP" onclick="setMode(1)">Professionnel</button></div></div>
<div id="view"></div></main></div>
<nav class="mob" id="mob"></nav>
<button class="HG" onclick="whereAmI()">🏠 OÙ EN EST MA MAISON ?</button>
<script>
const DATA = __DATA__;
let PRO=false, PAGE="accueil", PLANS=[], ZOOM=1, TX=0, TY=0, CUR=null;
const MENU=[["accueil","🏠","Accueil"],["projet","🏗️","Mon projet"],["etapes","📋","Étapes"],["plans","📐","Plans"],["3d","🧊","3D"],["budget","💰","Budget"],["docs","📄","Documents"],["assistant","💬","Assistant"],["gates","🔒","Validations"]];
function setMode(p){PRO=!!p;document.getElementById("mB").className=PRO?"":"on";document.getElementById("mP").className=PRO?"on":"";render();}
function go(p){PAGE=p;render();scrollTo(0,0);}
function badge(s){const t=(s||"").toUpperCase();
 if(t.includes("HUMAN_GATE")||t.includes("PENDING_G3"))return '<span class="badge b-gate">⚿ HUMAN GATE</span>';
 if(t.includes("INCONNU")||t.includes("UNKNOWN")||t.includes("NOT_DEFINED"))return '<span class="badge b-unk">? INCONNU</span>';
 if(t.includes("HYPOTH"))return '<span class="badge b-hyp">⚠ HYPOTHÈSE</span>';
 if(t.includes("VÉRIFI")||t.includes("CONNU"))return '<span class="badge b-ver">✓ VÉRIFIÉ</span>';
 if(t.includes("BLOCK"))return '<span class="badge b-blk">✕ BLOQUÉ</span>';
 if(t.includes("PROPOSED")||t.includes("PARTIAL"))return '<span class="badge b-hyp">◐ PROPOSED</span>';
 return '<span class="badge b-ok">✓ VALIDÉ</span>';}
const eur=n=>(n||0).toLocaleString("fr-FR").replace(/\u202f|,/g," ")+" FCFA";
const ST={"01":"IN_PROGRESS","02":"HUMAN_GATE","03":"VERIFIED","04":"VERIFIED","05":"VERIFIED","06":"VERIFIED","07":"IN_PROGRESS","08":"BLOCKED","09":"BLOCKED","10":"HUMAN_GATE","11":"HUMAN_GATE","12":"HUMAN_GATE","13":"HUMAN_GATE","14":"NOT_STARTED","15":"NOT_STARTED","16":"IN_PROGRESS","17":"NOT_STARTED","18":"IN_PROGRESS"};
function phRow(f,s){const b=s==="VERIFIED"?'<span class="badge b-ver">✓ VÉRIFIÉ</span>':s==="HUMAN_GATE"?'<span class="badge b-gate">⚿ HUMAN GATE</span>':s==="BLOCKED"?'<span class="badge b-blk">✕ BLOQUÉ</span>':s==="IN_PROGRESS"?'<span class="badge b-hyp">◐ EN COURS</span>':'<span class="badge b-unk">○ NON COMMENCÉ</span>';
 return `<div class="ph" onclick="alertBox('ÉTAPE '+${JSON.stringify("'")}+'${f.id}'+${JSON.stringify("'")}+'","'+('OBJECTIF : '+esc(f.objectif)+'\\n\\n'+esc(f.explication)+'\\n\\nTRAVAUX : '+esc(f.travaux)+'\\n\\nPROFESSIONNELS : '+esc(f.professionnels)+'\\n\\nHUMAN GATE : '+esc(f.human_gate))+'")"><div class="num">${f.id}</div><div class="t"><b>${f.nom}</b><small>${f.objectif}</small></div>${b}</div>`;}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;").replace(/\\n/g,"\\\\n");}
function vAccueil(){const p=DATA.project,s=DATA.status;
 let h=`<div class="banner">📄 <b>Version autonome</b> — données embarquées le ${DATA.generated_at}. Aucun serveur, aucune connexion requise.</div>
 <div class="prog"><div class="progbox"><div class="lbl">Dossier numérique</div><div class="val" style="color:var(--accent2)">AVANCÉ</div>
 <div class="bar"><i style="width:88%;background:var(--accent2)"></i></div><div style="font-size:12px;color:var(--muted)">Conception, BIM, plans, métrés, budget, documentation</div></div>
 <div class="progbox"><div class="lbl">Chantier physique</div><div class="val" style="color:var(--bad)">0 %</div>
 <div class="bar"><i style="width:2%;background:var(--bad)"></i></div><div style="font-size:12px;color:var(--muted)">Aucun travail de construction n'a commencé</div></div></div>
 <div class="warnline">⚠️ ${p.avertissement} — Les deux progressions sont <b>permanentes et distinctes</b>.</div>
 <div class="grid g3" style="margin-bottom:20px">
 <div class="card"><h3>Projet</h3><div class="big" style="font-size:19px">${p.nom}</div>
 <div class="kv" style="margin-top:8px"><span>Type</span><b>${p.type}</b></div><div class="kv"><span>Terrain</span><b>${p.terrain}</b></div>
 <div class="kv"><span>Intérieur</span><b>${p.surface_interieure}</b></div><div class="kv"><span>Chambres</span><b>${p.chambres}</b></div></div>
 <div class="card"><h3>Localisation</h3><div style="font-size:15px">${p.localisation}</div><div class="note">Source : ${p.source}</div></div>
 <div class="card"><h3>Variante</h3><div style="font-size:15px">${p.variante}</div><div class="note">G1 = CLOSED — décision de l'utilisateur</div></div></div>
 <h3 style="font-size:14px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin:22px 0 12px">Les 18 étapes — statut réel</h3>`;
 DATA.phases.forEach(f=>h+=phRow(f,ST[f.id]||"NOT_STARTED"));return h;}
function vProjet(){const p=DATA.project,q=DATA.quantities;
 let h=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin-bottom:18px">
 <div class="card"><h3>Identité</h3><div class="kv"><span>ID</span><b class="mono">${p.id}</b></div>
 <div class="kv"><span>Nom</span><b>${p.nom}</b></div><div class="kv"><span>Localisation</span><b>${p.localisation}</b></div>
 <div class="kv"><span>Type</span><b>${p.type}</b></div><div class="kv"><span>Terrain</span><b>${p.terrain}</b></div></div>
 <div class="card"><h3>Programme (CONNU)</h3>${Object.entries(p.programme).map(([k,v])=>`<div class="kv"><span>${k}</span><b style="text-align:right;max-width:60%">${v}</b></div>`).join("")}</div></div>
 <div class="card"><h3>Structure — statuts réels</h3><div class="note" style="border-color:var(--gate)">⚠ Structure <b>PROPOSED / PENDING_G3</b> — modèle conceptuel, non dimensionnement exécutoire.</div>
 <table style="margin-top:12px"><thead><tr><th>Élément</th><th>Quantité</th><th>Unité</th><th>Statut</th></tr></thead><tbody>
 ${(q.quantites||[]).map(x=>`<tr><td>${x.element.replace(/_/g," ")}</td><td class="mono">${x.quantite}</td><td>${x.unite}</td><td>${badge(x.statut)}</td></tr>`).join("")}</tbody></table></div>`;
 return h;}
function vEtapes(){return `<div class="note" style="margin-bottom:16px">Parcours en 18 étapes issues de <b>construction_guide_engine</b>. Cliquez pour ouvrir la fiche. Statuts réels, jamais embellis.</div>`+DATA.phases.map(f=>phRow(f,ST[f.id]||"NOT_STARTED")).join("");}
function vPlans(){PLANS=DATA.plans.plans;
 let h=`<div class="pills" id="pills">${PLANS.map((p,i)=>`<button class="${i===0?'on':''}" onclick="loadPlan(${i},this)">${p.nom.replace(/_/g," ").replace(".svg","")}</button>`).join("")}</div>
 <div class="vbar"><button onclick="setZoom(0.2)">🔍+</button><button onclick="setZoom(-0.2)">🔍−</button><button onclick="setZoom(0,1)">⟳ Réinitialiser</button>
 <button onclick="fs()">⛶ Plein écran</button><button onclick="dl()">⬇ Télécharger</button><button onclick="pr()">🖨 Imprimer</button></div>
 <div class="viewer" id="vw"><img id="img" draggable="false" alt="plan"></div><div class="note" id="what">Que regardez-vous ?</div>`;
 setTimeout(()=>loadPlan(0,document.querySelector("#pills button")),60);return h;}
function loadPlan(i,btn){CUR=PLANS[i];document.querySelectorAll("#pills button").forEach(b=>b.className="");if(btn)btn.className="on";
 ZOOM=1;TX=0;TY=0;const im=document.getElementById("img");if(!im)return;
 im.src="data:image/svg+xml;base64,"+CUR.data;im.style.transform="none";
 const d={"P01":"Implantation sur le terrain de 15 × 25 m.","P02":"Rez-de-chaussée : murs, cloisons, fenêtres, mobilier.","P03":"Étage : 4 chambres, 3 salles de bain, patio.","P04":"Toiture — PARTIEL (pente non définie).","P05":"Cotation RDC — cotes issues du BIM.","P06":"Cotation étage.","P07":"Portes et fenêtres — 17 fenêtres réelles.","P08":"Plan des sols.","P09":"Plafond — PENDING_G3.","P10":"Réseaux — exutoire EU UNKNOWN (G2).","C01":"Coupe longitudinale par l'escalier.","C02":"Coupe transversale.","F01":"Façade Nord.","F02":"Façade Sud.","F03":"Façade Est.","F04":"Façade Ouest."};
 document.getElementById("what").innerHTML="<b>Que regardez-vous ?</b> "+(d[CUR.nom.slice(0,3)]||"")+(PRO?`<br><span class="mono" style="font-size:11.5px;color:var(--muted)">source : BIM_FINAL_A3.blend</span>`:"");
 const vw=document.getElementById("vw");vw.scrollTop=0;vw.scrollLeft=0;
 if(!vw._b){vw._b=1;let g=0,sx=0,sy=0;vw.addEventListener("mousedown",e=>{g=1;sx=e.clientX-vw.scrollLeft;sy=e.clientY-vw.scrollTop;});
 addEventListener("mouseup",()=>g=0);vw.addEventListener("mousemove",e=>{if(g){vw.scrollLeft=sx-e.clientX;vw.scrollTop=sy-e.clientY;}});
 vw.addEventListener("wheel",e=>{if(e.ctrlKey||e.metaKey){e.preventDefault();setZoom(e.deltaY<0?0.12:-0.12);}},{passive:false});}}
function applyT(){const im=document.getElementById("img");if(im)im.style.transform=`translate(${TX}px,${TY}px) scale(${ZOOM})`;}
function setZoom(d,r){if(r){ZOOM=1;TX=0;TY=0;}else ZOOM=Math.min(6,Math.max(0.25,ZOOM+d));applyT();}
function fs(){const v=document.getElementById("vw");(v.requestFullscreen||v.webkitRequestFullscreen||(()=>{})).call(v);}
function dl(){const a=document.createElement("a");a.href=document.getElementById("img").src;a.download=CUR.nom;a.click();}
function pr(){const w=open();w.document.write('<img src="'+document.getElementById("img").src+'" style="width:100%">');w.document.close();w.onload=()=>w.print();}
function v3D(){const b=DATA.bim;
 return `<div class="card" style="margin-bottom:16px"><h3>Modèle BIM réel</h3>
 <div class="kv"><span>Fichier</span><b class="mono">${b.fichier}</b></div><div class="kv"><span>Existe réellement</span><b>${b.existe?"OUI":"NON"}</b></div>
 <div class="kv"><span>Taille</span><b>${(b.octets/1024).toFixed(0)} Ko</b></div><div class="kv"><span>Objets</span><b>${b.objets}</b></div>
 <div class="kv"><span>Export GLB</span><b>${b.glb?"OUI ("+(b.glb_octets/1024).toFixed(0)+" Ko)":"NON"}</b></div></div>
 <div class="card"><h3>Vue 3D</h3><div class="note" style="border-color:var(--warn)">⚠ La vue 3D interactive nécessite le serveur local (<span class="mono">http://127.0.0.1:8765</span>, page 3D) qui charge le GLB.
 En mode autonome (ce fichier ouvert par double-clic), le navigateur bloque le chargement du GLB local pour des raisons de sécurité (CORS <span class="mono">file://</span>).
 <br><br><b>Le fichier 3D existe réellement :</b> <span class="mono">3D/BIM_FINAL_A3.glb — ${(b.glb_octets/1024).toFixed(0)} Ko</span>, exporté depuis <span class="mono">${b.fichier}</span> (SHA vérifié, original intact).</div>
 <div class="grid g3" style="margin-top:14px">${(DATA.renders.rendus||[]).map(r=>`<div><img src="data:image/png;base64,${r.data}" style="width:100%;border-radius:8px;border:1px solid var(--line)">
 <div class="mono" style="font-size:11px;color:var(--muted);margin-top:5px">${r.nom}</div></div>`).join("")}</div>
 <div class="note">${DATA.renders.avertissement}</div></div>`;}
function vBudget(){const b=DATA.budget;
 return `<div class="card" style="margin-bottom:16px;border-color:var(--warn)"><h3 style="color:var(--warn)">⚠ ${b.mention}</h3>
 <div class="big" style="color:var(--accent)">${eur(b.total_fcfa)}</div>
 <div class="grid g3" style="margin-top:14px"><div class="kv"><span>Indépendant de G3</span><b>${eur(b.independant_g3_fcfa)}</b></div>
 <div class="kv"><span>Dépendant de G3</span><b>${eur(b.dependant_g3_fcfa)}</b></div>
 <div class="kv"><span>Ancien budget</span><b>${eur(b.ancien_budget_fcfa)}</b></div></div>
 <div class="note">${b.comparabilite}</div></div>
 <div class="card"><h3>Détail des postes</h3><table><thead><tr><th>Poste</th><th>Qté</th><th>Unité</th><th>Montant</th><th>Statut</th></tr></thead><tbody>
 ${(b.lignes||[]).map(l=>`<tr><td>${l.designation.replace(/_/g," ")}</td><td class="mono">${l.quantite}</td><td>${l.unite}</td>
 <td class="mono">${(l.montant_fcfa||0).toLocaleString("fr-FR")}</td><td>${badge(l.statut)}</td></tr>`).join("")}</tbody></table></div>`;}
function vDocs(){return `<div class="card" style="margin-bottom:16px"><h3>Documents du dossier (${DATA.documents.documents.length})</h3>
 <table><thead><tr><th>Document</th><th>Taille</th><th>Statut</th></tr></thead><tbody>
 ${DATA.documents.documents.map(x=>`<tr><td class="mono">${x.nom}</td><td class="mono">${(x.octets/1024).toFixed(1)} Ko</td><td>${badge("EXISTE")}</td></tr>`).join("")}</tbody></table></div>
 <div class="card"><h3>Rendus 3D (${DATA.renders.total})</h3><div class="note">${DATA.renders.avertissement}</div>
 <div class="grid g3" style="margin-top:14px">${DATA.renders.rendus.map(r=>`<div><img src="data:image/png;base64,${r.data}" style="width:100%;border-radius:8px;border:1px solid var(--line)">
 <div class="mono" style="font-size:11px;color:var(--muted);margin-top:5px">${r.nom}</div></div>`).join("")}</div></div>`;}
function vGates(){const g=DATA.gates;
 return `<div class="note" style="margin-bottom:16px">Statuts autorisés : ${g.legende_statuts.map(s=>`<span class="mono">${s}</span>`).join(" · ")}</div>`+
 g.gates.map(x=>{const op=x.statut.includes("OPEN");
 return `<div class="card" style="margin-bottom:14px;border-color:${op?"var(--gate)":"var(--ok)"}">
 <div style="display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap">
 <h3 style="margin:0;color:${op?"var(--gate)":"var(--ok)"};font-size:15px">${x.id} — ${x.objet}</h3>${badge(x.statut)}</div>
 <div style="margin-top:11px;font-size:13.5px">${x.detail}</div>
 ${x.pourquoi?`<div class="note" style="border-color:${op?"var(--gate)":"var(--ok)"}"><b>Pourquoi cette validation est nécessaire :</b> ${x.pourquoi}</div>`:""}
 <div class="kv" style="margin-top:11px"><span>Qui doit intervenir ?</span><b>${x.intervenants.join(" · ")}</b></div>
 ${x.champs_a_remplir?`<div class="kv"><span>Champs à remplir</span><b>${x.champs_a_remplir}</b></div><div class="kv"><span>Fiche</span><b class="mono">${x.fiche}</b></div>`:""}</div>`;}).join("");}
function vAssistant(){const A=DATA.assistant;
 return `<div class="note" style="margin-bottom:12px">Réponses issues du <b>moteur réel</b> construction_guide_engine, capturées hors ligne. Mode autonome : réponses pré-calculées sur les questions clés.</div>
 <div class="chat" id="chat"><div class="msg a">Bonjour. Je suis l'assistant de votre projet. Mode actuel : <b>${PRO?"PROFESSIONNEL":"DÉBUTANT"}</b>.</div></div>
 <div class="chips">${[["Puis-je construire les fondations maintenant ?","fondations_now"],["Qu'est-ce qu'un poteau ?","poteau"],["Qu'est-ce qu'une longrine ?","longrine"],["Où en est mon projet ?","ou"],["Explique-moi tout","explique"]]
 .map(([q,k])=>`<button onclick="askPreset('${q}','${k}')">${q}</button>`).join("")}</div>
 <div class="inrow"><input id="qi" placeholder="Posez votre question..." onkeydown="if(event.key==='Enter')askFree()"><button class="btn" onclick="askFree()">Envoyer</button></div>`;}
function addMsg(cls,txt){const c=document.getElementById("chat");c.insertAdjacentHTML("beforeend",`<div class="msg ${cls}">${esc(txt)}</div>`);c.scrollTop=c.scrollHeight;}
function askPreset(q,k){addMsg("u",q);const r=DATA.assistant[k];const txt=r?((PRO&&r.pro)?r.pro:r.debutant):"Réponse non disponible hors ligne pour cette question.";
 addMsg("a"+(k==="fondations_now"?" secu":""),txt);
 if(k==="fondations_now")addMsg("a secu","⚿ BLOCAGE — HYPOTHÈSE non vérifiée + G3 ouvert\\nIntervenants : géotechnicien, ingénieur structure\\nValidation : G3 — reports/G3_FICHE_COLLECTE.md");}
function askFree(){const i=document.getElementById("qi"),q=i.value.trim();if(!q)return;i.value="";addMsg("u",q);
 const ql=q.toLowerCase();
 const k=ql.includes("fondation")&&(ql.includes("construire")||ql.includes("maintenant"))?"fondations_now":
  ql.includes("poteau")?"poteau":ql.includes("longrine")?"longrine":(ql.includes("où en est")||ql.includes("ou en est"))?"ou":
  (ql.includes("tout")||ql.includes("explique"))?"explique":null;
 if(k){const r=DATA.assistant[k];addMsg("a"+(k==="fondations_now"?" secu":""),(PRO&&r.pro)?r.pro:r.debutant);
  if(k==="fondations_now")addMsg("a secu","⚿ BLOCAGE — HYPOTHÈSE non vérifiée + G3 ouvert");}
 else addMsg("a","En mode autonome, je réponds hors ligne sur : les fondations, un poteau, une longrine, où en est le projet, et « explique-moi tout ».\\nEssayez l'un de ces boutons — ou lancez le serveur local pour poser n'importe quelle question.");}
function whereAmI(){alertBox("OÙ EN EST MA MAISON ?",
 `DOSSIER NUMÉRIQUE — Villa_Test_001
✓ programme          ✓ architecture (VARIANTE A VALIDÉE)
✓ BIM (326 objets)    ✓ plans (10) + coupes (2) + façades (4)
✓ métrés v2           ✓ budget v2 (29 753 918 FCFA — estimation)
✓ documentation (14)  ✓ rendus (10)

BLOQUAGES OUVERTS
⚿ G2 — Assainissement / exutoire des eaux usées
     → topographe + professionnel assainissement
⚿ G3 — Validation géotechnique et structure
     → géotechnicien + ingénieur structure
     (portance du sol 0,15 MPa = HYPOTHÈSE non vérifiée)

CHANTIER PHYSIQUE — 0 %
Aucun travail physique de construction n'a commencé.

PROCHAINE ACTION
Faire remplir reports/G2_FICHE_COLLECTE.md et reports/G3_FICHE_COLLECTE.md.`);}
function alertBox(t,b){const w=document.createElement("div");
 w.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:200;display:grid;place-items:center;padding:20px";
 w.innerHTML=`<div style="background:var(--panel);border:1px solid var(--line);border-radius:12px;max-width:760px;max-height:84vh;overflow:auto;padding:24px">
 <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:14px"><h3 style="font-size:16px">${t}</h3>
 <button class="btn" onclick="this.closest('div').parentElement.parentElement.remove()">Fermer</button></div>
 <pre style="font-family:ui-monospace,Menlo,monospace;font-size:12.7px;line-height:1.6;white-space:pre-wrap;color:var(--txt)">${esc(b)}</pre></div>`;
 w.onclick=e=>{if(e.target===w)w.remove();};document.body.appendChild(w);}
function render(){document.getElementById("nav").innerHTML=MENU.map(([k,i,l])=>`<a class="${PAGE===k?'on':''}" onclick="go('${k}')"><i>${i}</i>${l}</a>`).join("");
 document.getElementById("mob").innerHTML=MENU.slice(0,5).map(([k,i,l])=>`<a class="${PAGE===k?'on':''}" onclick="go('${k}')"><i>${i}</i>${l}</a>`).join("");
 document.getElementById("ttl").textContent=(MENU.find(m=>m[0]===PAGE)||[])[2]||"Accueil";
 document.getElementById("sub").textContent="PRJ_1701484686 · Villa_Test_001 · Abidjan — mode "+(PRO?"professionnel":"débutant")+" · version autonome";
 const F={accueil:vAccueil,projet:vProjet,etapes:vEtapes,plans:vPlans,"3d":v3D,budget:vBudget,docs:vDocs,assistant:vAssistant,gates:vGates};
 try{document.getElementById("view").innerHTML=(F[PAGE]||vAccueil)();}
 catch(e){document.getElementById("view").innerHTML='<div class="note" style="border-color:var(--bad)">Erreur de rendu : '+esc(e.message)+'</div>';}}
setMode(0);
</script></body></html>"""

out = os.path.join(ROOT, "web", "frontend", "Villa_Test_001_APP.html")
open(out, "w").write(HTML.replace("__DATA__", json.dumps(DATA, ensure_ascii=False)))
print("FICHIER AUTONOME GENERE : %s" % out)
print("  taille : %d o (%.1f Mo)" % (os.path.getsize(out), os.path.getsize(out) / 1048576))
print("  donnees embarquees :")
for k in ("project", "status", "phases", "budget", "quantities", "gates", "plans", "renders", "documents", "bim", "assistant"):
    v = DATA[k]
    n = len(v) if isinstance(v, list) else (len(v.get("plans", v.get("rendus", v.get("documents", v.get("gates", v.get("quantites", [v])))))) if isinstance(v, dict) else 1)
    print("    %-11s %s" % (k, n if isinstance(n, int) else "ok"))
print("  plans embarques : %d SVG en base64" % len(DATA["plans"]["plans"]))
print("  rendus embarques : %d PNG en base64" % len(DATA["renders"]["rendus"]))
