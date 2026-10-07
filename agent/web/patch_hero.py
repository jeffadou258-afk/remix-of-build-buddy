#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HERO CAROUSEL — page d accueil.
Utilise les 2 RENDUS REELS du projet (renders/R01, R07) servis par /files/renders/.
Aucune image de maquette, aucun texte marketing incruste, aucune donnee inventee.
Ajoute le hero AU-DESSUS du contenu existant : les cartes DOSSIER/CHANTIER restent.
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
    print("  OK  %-42s (1)" % label)


# ---------- 1. CSS du hero ----------
rep(".app{display:flex;min-height:100vh}",
    """.app{display:flex;min-height:100vh}
/* ===== HERO PLEIN ECRAN + CAROUSEL (2 rendus REELS du projet) ===== */
.hero{position:relative;width:100%;min-height:clamp(430px,72vh,780px);
  display:flex;align-items:flex-end;overflow:hidden;background:#070d18;
  border-bottom:1px solid var(--line)}
.hero .sl{position:absolute;inset:0;background-size:cover;background-position:center;
  opacity:0;transition:opacity 2.6s ease-in-out,transform 12s linear;
  transform:scale(1.06)}
.hero .sl.on{opacity:1;transform:scale(1)}
.hero .ov{position:absolute;inset:0;
  background:linear-gradient(90deg,rgba(4,9,18,.94) 0%,rgba(4,9,18,.80) 42%,
             rgba(4,9,18,.42) 72%,rgba(4,9,18,.20) 100%)}
.hero .in{position:relative;z-index:3;padding:clamp(28px,5vw,64px);max-width:760px}
.hero .lb{font-size:11px;letter-spacing:3.2px;font-weight:700;color:var(--accent);
  margin-bottom:16px;text-transform:uppercase}
.hero h1{font-size:clamp(32px,5.6vw,62px);line-height:1.04;font-weight:800;
  color:#fff;letter-spacing:-1.6px;margin:0 0 16px}
.hero h1 em{color:var(--accent);font-style:normal}
.hero p{font-size:clamp(14px,1.5vw,17.5px);color:#c4d2e4;line-height:1.6;
  max-width:520px;margin:0 0 26px}
.hero .acts{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.hero .b1{background:var(--accent);color:#fff;border:0;padding:14px 24px;border-radius:9px;
  font-weight:700;font-size:14.5px;cursor:pointer;font-family:inherit;
  display:inline-flex;align-items:center;gap:9px;transition:.15s}
.hero .b1:hover{background:#ff8347;transform:translateY(-1px)}
.hero .b2{background:rgba(255,255,255,.07);color:#fff;border:1px solid rgba(255,255,255,.28);
  padding:13px 22px;border-radius:9px;font-weight:600;font-size:14.5px;cursor:pointer;
  font-family:inherit;display:inline-flex;align-items:center;gap:9px;backdrop-filter:blur(6px)}
.hero .b2:hover{background:rgba(255,255,255,.14);border-color:#fff}
.hero .dots{position:absolute;bottom:16px;right:22px;z-index:4;display:flex;gap:7px}
.hero .dots i{width:26px;height:3px;border-radius:2px;background:rgba(255,255,255,.28);
  cursor:pointer;transition:.3s}
.hero .dots i.on{background:var(--accent);width:40px}
.hero .cap{position:absolute;bottom:16px;left:clamp(28px,5vw,64px);z-index:4;
  font-size:11px;color:rgba(255,255,255,.5);letter-spacing:.4px}
.hcaps{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border-top:1px solid var(--line)}
.hcaps > div{background:var(--panel);padding:18px 20px;display:flex;gap:11px;align-items:flex-start}
.hcaps b{display:block;font-size:13px;color:var(--txt);font-weight:700;letter-spacing:.2px}
.hcaps span{display:block;font-size:11.5px;color:var(--muted);margin-top:2px}
.hcaps .ic{font-size:17px;line-height:1;flex:0 0 auto}
@media(max-width:900px){
  .hero{min-height:520px}
  .hcaps{grid-template-columns:1fr 1fr}
  .hero .cap{display:none}
}""", "CSS hero + bandeau capacites")

# ---------- 2. HTML du hero, au debut de la page d accueil ----------
rep('  let h = `<div class="prog">',
    '''  let h = `<section class="hero" id="hero">
    <div class="sl on" id="sl0"></div><div class="sl" id="sl1"></div>
    <div class="ov"></div>
    <div class="in">
      <div class="lb">CONSTRUCTION AGENT</div>
      <h1>Votre projet<br>de construction.<br><em>Compris et visualise.</em></h1>
      <p>Un assistant intelligent pour comprendre votre maison, explorer vos plans,
      visualiser votre BIM et suivre chaque etape — du plan au dossier de construction.</p>
      <div class="acts">
        <button class="b1" onclick="heroStart()">COMMENCER MON PROJET &#8594;</button>
        <button class="b2" onclick="heroVisit()">&#9658; VOIR LA VISITE 3D</button>
      </div>
    </div>
    <div class="dots" id="hdots"><i class="on" onclick="heroGo(0)"></i><i onclick="heroGo(1)"></i></div>
    <div class="cap" id="hcap"></div>
  </section>
  <div class="hcaps">
    <div><span class="ic">&#128208;</span><div><b>PLANS 2D</b><span>Clairs et detailles</span></div></div>
    <div><span class="ic">&#129513;</span><div><b>BIM 3D</b><span>Interactif, 326 elements</span></div></div>
    <div><span class="ic">&#128200;</span><div><b>BUDGET</b><span>Estimation de travail</span></div></div>
    <div><span class="ic">&#128218;</span><div><b>GUIDE</b><span>Etape par etape</span></div></div>
  </div>
  <div class="pagehead">''', "HTML hero + bandeau, au-dessus du contenu existant")

# ---------- 3. JS du carousel ----------
rep("function toggleMore(e){",
    """/* ===== HERO CAROUSEL — 2 RENDUS REELS du projet (aucune maquette) =====
   Les images viennent de /api/renders ; si l API ne repond pas, le hero reste
   affiche avec son degrade sombre et AUCUNE image inventee. */
const HERO = [
  {fichier:"R01_vue_principale.png", legende:"Rendu du projet - vue principale"},
  {fichier:"R07_salon.png",          legende:"Rendu du projet - salon"}
];
let _heroI = 0, _heroT = null;
function heroApply(){
  HERO.forEach((h, i) => {
    const el = document.getElementById("sl" + i);
    if(!el) return;
    if(!el.dataset.url) return;                       /* pas d image reelle : rien a afficher */
    el.style.backgroundImage = "url('" + el.dataset.url + "')";
    el.className = "sl" + (i === _heroI ? " on" : "");
  });
  const c = document.getElementById("hcap");
  if(c && HERO[_heroI]) c.textContent = HERO[_heroI].legende;
  document.querySelectorAll("#hdots i").forEach((d, i) =>
    d.className = (i === _heroI ? "on" : ""));
}
function heroGo(i){ _heroI = i % HERO.length; heroApply(); }
function heroStart(){ go("projet"); }
function heroVisit(){ go("3d"); }
async function heroInit(){
  try{
    const r = await api("/api/renders");
    const liste = (r && r.rendus) || [];
    HERO.forEach((h, i) => {
      const el = document.getElementById("sl" + i);
      if(!el) return;
      const m = liste.find(x => (x.nom || x.fichier || "").indexOf(h.fichier) >= 0);
      if(m && (m.url || m.fichier)) el.dataset.url = m.url || ("/files/renders/" + h.fichier);
    });
  }catch(e){ /* API indisponible : hero sans image, aucun substitut invente */ }
  heroApply();
  if(_heroT) clearInterval(_heroT);
  _heroT = setInterval(() => heroGo((_heroI + 1) % HERO.length), 7000);   /* defilement auto */
}
function toggleMore(e){""", "JS carousel hero")

# ---------- 4. lancer le carousel a l affichage de l accueil ----------
rep('  const navH = document.getElementById("navH");',
    '  const navH = document.getElementById("navH");\n  if(document.getElementById("hero")) heroInit();',
    "JS : heroInit au rendu de l accueil")

assert len(s) < 200000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (%+d)" % (n0, len(s), len(s) - n0))
