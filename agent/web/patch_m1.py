#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M1 — palette + header + navigation. Sauvegarde faite dans /tmp. Assertions strictes."""
P = "/Users/mac/ConstructionAgent/web/frontend/index.html"
s = open(P).read()
n0 = len(s)


def rep(old, new, label):
    global s
    c = s.count(old)
    if c != 1:
        raise SystemExit("STOP - ancre '%s' : %d occurrence(s), attendu 1" % (label, c))
    s = s.replace(old, new)
    print("  OK  %-36s (1)" % label)


# ---------- 1. PALETTE ----------
rep("--bg:#0e1114; --panel:#151a1f; --panel2:#1b2229; --line:#2a333c;",
    "--bg:#0b1220; --panel:#111a2b; --panel2:#17233a; --line:#22314d;", "palette : fonds")
rep("--txt:#e8edf1; --muted:#93a3b1; --accent:#c8a45c; --accent2:#5c8fc8;",
    "--txt:#f2f5f9; --muted:#93a5c0; --accent:#ff6a1f; --accent2:#1f4e8c;", "palette : accent -> ORANGE")

# ---------- 2. CSS HEADER ----------
rep(".app{display:flex;min-height:100vh}",
    """.app{display:flex;min-height:100vh}
/* ===== M1 : HEADER HORIZONTAL STICKY ===== */
.hd{position:sticky;top:0;z-index:80;display:flex;align-items:center;gap:20px;
  padding:0 26px;height:62px;background:rgba(11,18,32,.94);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line)}
.hd .brand{display:flex;align-items:center;gap:10px;text-decoration:none;cursor:pointer;flex:0 0 auto}
.hd .mk{width:32px;height:32px;border-radius:7px;background:linear-gradient(135deg,var(--accent),#b2460f);
  display:grid;place-items:center;font-weight:800;color:#fff;font-size:14px}
.hd .nm{font-size:14.5px;font-weight:800;color:var(--txt);letter-spacing:-.2px;line-height:1}
.hd .nm small{display:block;font-size:9.5px;color:var(--accent);letter-spacing:1.6px;font-weight:700;margin-top:2px}
.hd nav{display:flex;gap:2px;flex:1;min-width:0;overflow-x:auto;scrollbar-width:none}
.hd nav::-webkit-scrollbar{display:none}
.hd nav a{display:flex;align-items:center;gap:6px;padding:8px 12px;border-radius:7px;color:var(--muted);
  font-size:13.5px;font-weight:600;cursor:pointer;white-space:nowrap;transition:.13s}
.hd nav a:hover{background:var(--panel2);color:var(--txt)}
.hd nav a.on{background:rgba(255,106,31,.13);color:var(--accent)}
.hd .cta{flex:0 0 auto;background:var(--accent);color:#fff;border:0;padding:9px 16px;border-radius:8px;
  font-weight:700;font-size:13px;cursor:pointer;font-family:inherit;transition:.13s}
.hd .cta:hover{background:#ff8347;transform:translateY(-1px)}
.hd .cta:focus-visible{outline:2px solid #fff;outline-offset:2px}
.hd .more{flex:0 0 auto;background:transparent;border:1px solid var(--line);color:var(--muted);
  padding:8px 11px;border-radius:7px;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600}
.hd .more:hover{border-color:var(--accent);color:var(--accent)}
.hdmenu{position:absolute;right:26px;top:58px;background:var(--panel);border:1px solid var(--line);
  border-radius:9px;padding:6px;min-width:180px;box-shadow:0 12px 30px rgba(0,0,0,.5);z-index:90}
.hdmenu a{display:block;padding:9px 12px;border-radius:6px;color:var(--muted);font-size:13.5px;cursor:pointer}
.hdmenu a:hover{background:var(--panel2);color:var(--txt)}""", "CSS header + menu secondaire")
rep("aside{width:246px;flex:0 0 246px;", "aside{display:none;width:246px;flex:0 0 246px;", "aside masque")

# ---------- 3. HTML HEADER ----------
rep("""<div class="app">
<aside>""",
    """<header class="hd">
  <div class="brand" onclick="go('accueil')">
    <div class="mk">CA</div>
    <div class="nm">CONSTRUCTION AGENT<small>BIM · IA</small></div>
  </div>
  <nav id="navH"></nav>
  <button class="more" onclick="toggleMore(event)" aria-label="Plus">&#8943; Plus</button>
  <button class="cta" onclick="newProject()">NOUVEAU PROJET</button>
</header>
<div id="moreMenu" class="hdmenu" style="display:none">
  <a onclick="go('etapes');toggleMore()">&#128203; Etapes</a>
  <a onclick="go('gates');toggleMore()">&#128274; Validations</a>
  <a onclick="go('assistant');toggleMore()">&#128172; Assistant IA</a>
</div>
<div class="app"><aside>""", "HTML : header + menu secondaire")

# ---------- 4. RENDER : nav horizontale ----------
rep('  document.getElementById("nav").innerHTML = nav;',
    '''  document.getElementById("nav").innerHTML = nav;
  const navH = document.getElementById("navH");
  if(navH) navH.innerHTML = MENU.filter(m=>["accueil","projet","plans","3d","budget","docs"].indexOf(m[0])>=0)
    .map(([k,i,l])=>`<a class="${PAGE===k?'on':''}" onclick="go('${k}')">${i} ${k==="3d"?"BIM 3D":l}</a>`).join("");''',
    "render : nav horizontale (6 entrees)")

# ---------- 5. FONCTIONS CTA + MENU SECONDAIRE ----------
rep("function setMode(p){",
    """function toggleMore(e){
  if(e) e.stopPropagation();
  const m = document.getElementById("moreMenu");
  if(m) m.style.display = (m.style.display === "none" || !m.style.display) ? "block" : "none";
}
document.addEventListener("click", (e) => {
  const m = document.getElementById("moreMenu");
  if(m && m.style.display === "block" && !m.contains(e.target)) m.style.display = "none";
});
/* Le CTA ne simule AUCUNE creation de projet : la fonctionnalite n'existe pas.
   Il renvoie vers la vue projet existante, avec une mention explicite. */
function newProject(){
  go("projet");
  setTimeout(()=>alertBox("NOUVEAU PROJET", "Fonctionnalite non disponible.\\n\\n"+
    "La plateforme gere aujourd'hui UN SEUL projet : PRJ_1701484686 — Villa_Test_001.\\n"+
    "La creation de projet n'est pas implementee cote serveur (aucune route d'ecriture).\\n\\n"+
    "Aucun workflow de creation n'est simule."), 350);
}
function setMode(p){""", "fonctions toggleMore + newProject (sans simulation)")

assert len(s) < 120000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (delta %+d)" % (n0, len(s), len(s) - n0))
