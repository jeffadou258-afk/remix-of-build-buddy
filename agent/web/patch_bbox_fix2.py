#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECTION FINALE DU BLANC — viewer 2D.
Fit sur la BBOX REELLE du contenu (union des elements visibles), pas sur le viewBox declare.
Les 16 SVG ne sont PAS modifies : lecture seule via fetch() + DOM.
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
    print("  OK  %-44s (1)" % label)


# ---------- 1. bbox reelle : mesure + cache ----------
rep("function applyT(){",
    """/* ===== BBOX REELLE DU CONTENU (correction finale du blanc) =====
   Certains SVG declarent un viewBox plus petit que leur dessin (clipping) et le
   getBBox() racine est fausse par des elements parasites. On mesure l'union des
   bbox des ELEMENTS VISIBLES et on l'utilise comme cadre effectif du viewer.
   Les fichiers SVG ne sont JAMAIS modifies : lecture seule via fetch(). */
const BB_CACHE = {};
const BALISES_IGNOREES = ["defs","style","title","desc","metadata","clippath","mask",
  "marker","pattern","filter","lineargradient","radialgradient","symbol","script"];

async function mesurerBBox(url){
  if(BB_CACHE[url]) return BB_CACHE[url];
  let r;
  try{ r = await fetch(url); }catch(e){ return null; }
  if(!r.ok) return null;
  const txt = await r.text();
  const host = document.createElement("div");
  host.style.cssText = "position:absolute;left:-99999px;top:0;width:0;height:0;overflow:hidden";
  host.innerHTML = txt;
  document.body.appendChild(host);
  const svg = host.querySelector("svg");
  let out = null;
  if(svg){
    let X0=1e9, Y0=1e9, X1=-1e9, Y1=-1e9, n=0;
    svg.querySelectorAll("*").forEach(el => {
      const tag = el.tagName.toLowerCase();
      if(BALISES_IGNOREES.indexOf(tag) >= 0) return;
      const cs = getComputedStyle(el);
      if(cs.display==="none" || cs.visibility==="hidden" || parseFloat(cs.opacity)===0) return;
      let b;
      try{ b = el.getBBox(); }catch(e){ return; }
      if(!isFinite(b.width) || !isFinite(b.height)) return;
      if(b.width <= 0 && b.height <= 0) return;
      let x0=b.x, y0=b.y, x1=b.x+b.width, y1=b.y+b.height;
      const M = el.getCTM ? el.getCTM() : null;
      if(M){                                   /* applique le transform local */
        const d = (M.a*M.d - M.b*M.c) || 1;
        const pts = [[x0,y0],[x1,y0],[x0,y1],[x1,y1]].map(([x,y]) => [
          ( M.d*(x-M.e) - M.c*(y-M.f)) / d,
          (-M.b*(x-M.e) + M.a*(y-M.f)) / d ]);
        x0 = Math.min.apply(null,pts.map(p=>p[0])); x1 = Math.max.apply(null,pts.map(p=>p[0]));
        y0 = Math.min.apply(null,pts.map(p=>p[1])); y1 = Math.max.apply(null,pts.map(p=>p[1]));
      }
      X0=Math.min(X0,x0); Y0=Math.min(Y0,y0);
      X1=Math.max(X1,x1); Y1=Math.max(Y1,y1); n++;
    });
    if(n){
      const m = 2;                            /* marge : ne pas rogner les traits */
      out = {x:X0-m, y:Y0-m, w:(X1-X0)+2*m, h:(Y1-Y0)+2*m, n:n,
             vb:svg.getAttribute("viewBox")};
    }
  }
  host.remove();
  if(out) BB_CACHE[url] = out;
  return out;
}

function applyT(){""", "JS : mesurerBBox() + cache")

# ---------- 2. fitToScreen sur la bbox ----------
rep("""  if(!W || !H) return;                       /* rien a ajuster : aucun fit invente */
  const cw = vw.clientWidth - PAD*2, ch = vw.clientHeight - PAD*2;
  if(cw <= 0 || ch <= 0) return;
  ZOOM = Math.min(cw / W, ch / H);           /* <= conserve le ratio */
  TX = PAD + (cw - W*ZOOM)/2;                /* centrage horizontal */
  TY = PAD + (ch - H*ZOOM)/2;                /* centrage vertical   */
  applyT();""",
"""  if(!W || !H) return;                       /* rien a ajuster : aucun fit invente */
  const cw = vw.clientWidth - PAD*2, ch = vw.clientHeight - PAD*2;
  if(cw <= 0 || ch <= 0) return;
  /* Cadre effectif = bbox reelle du contenu si connue, sinon tout le canevas.
     bx/by peuvent etre NEGATIFS : la formule le gere nativement. */
  const bb = BB_CACHE[CURPLAN && CURPLAN.url];
  const bx = bb ? bb.x : 0, by = bb ? bb.y : 0;
  const bw = bb ? bb.w : W,  bh = bb ? bb.h : H;
  ZOOM = Math.min(cw / bw, ch / bh);         /* <= conserve le ratio */
  TX = PAD + (cw - bw*ZOOM)/2 - bx*ZOOM;     /* centrage du CONTENU, pas du canevas */
  TY = PAD + (ch - bh*ZOOM)/2 - by*ZOOM;
  applyT();""", "JS : fitToScreen sur la bbox reelle")

# ---------- 3. loadPlan : mesurer AVANT de fit ----------
rep('''  im.src = CURPLAN.url; im.style.transform = "none";
  im.onload = () => { if(im.naturalWidth){ im.setAttribute("data-vb","0 0 "+im.naturalWidth+" "+im.naturalHeight); }
                      fitToScreen(); };
  /* Si l'image est deja en cache, onload peut ne pas se declencher. */
  if(im.complete && im.naturalWidth) { im.onload(); }''',
'''  im.src = CURPLAN.url; im.style.transform = "none";
  /* Ordre impose : charger le SVG -> mesurer la bbox -> calculer le scale -> centrer. */
  const urlPlan = CURPLAN.url;
  const apresMesure = () => {
    if(CURPLAN && CURPLAN.url !== urlPlan) return;   /* plan deja change entre-temps */
    fitToScreen();
  };
  im.onload = () => {
    if(im.naturalWidth){ im.setAttribute("data-vb","0 0 "+im.naturalWidth+" "+im.naturalHeight); }
    if(BB_CACHE[urlPlan]) apresMesure();
    else mesurerBBox(urlPlan).then(apresMesure).catch(apresMesure);
  };
  /* Si l'image est deja en cache, onload peut ne pas se declencher. */
  if(im.complete && im.naturalWidth) { im.onload(); }''',
    "JS : loadPlan mesure la bbox avant le fit")

# ---------- 4. diagnostic a l'ecran ----------
rep('  const st = document.getElementById("zst");\n  if(st) st.textContent = Math.round(ZOOM*100) + "%";\n}\nfunction applyT(){',
    '''  const st = document.getElementById("zst");
  if(st) st.textContent = Math.round(ZOOM*100) + "%";
  const bi = document.getElementById("binfo");
  if(bi){
    const b2 = BB_CACHE[CURPLAN && CURPLAN.url];
    bi.textContent = b2 ? ("bbox " + Math.round(b2.w) + "x" + Math.round(b2.h) +
      " @ " + Math.round(b2.x) + "," + Math.round(b2.y) + " · " + b2.n + " elts")
      : "bbox : canevas complet";
  }
}
function applyT(){''', "JS : indicateur bbox")

rep('<span id="zst" class="mono" style="padding:6px 10px;font-size:12px;color:var(--muted)">100%</span>',
    '<span id="zst" class="mono" style="padding:6px 10px;font-size:12px;color:var(--muted)">100%</span>'
    '<span id="binfo" class="mono" style="padding:6px 10px;font-size:11.5px;color:var(--muted);opacity:.8"></span>',
    "HTML : indicateur bbox")

assert len(s) < 200000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (delta %+d)" % (n0, len(s), len(s) - n0))
