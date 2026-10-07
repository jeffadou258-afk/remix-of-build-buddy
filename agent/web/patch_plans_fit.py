#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLANS 2D — correction FIT TO SCREEN.
scale = min(cw/W, ch/H) + centrage + marge 30 px.
Aucune largeur fixe. overflow:hidden + transform scale/translate.
"""
import re

P = "/Users/mac/ConstructionAgent/web/frontend/index.html"
s = open(P).read()
n0 = len(s)


def rep(old, new, label, count=0):
    global s
    c = s.count(old)
    if c != 1:
        raise SystemExit("STOP - ancre '%s' : %d occurrence(s), attendu 1" % (label, c))
    s = s.replace(old, new)
    print("  OK  %-40s (1)" % label)


# ---------- 1. CSS : zone de visualisation ----------
m = re.search(r"\.viewer\{[^}]*\}", s)
if not m:
    raise SystemExit("STOP - bloc .viewer introuvable")
print("  AVANT : %s" % m.group(0))
# On PRESERVE le bloc existant : on injecte seulement les proprietes necessaires.
rep(".viewer{",
    ".viewer{position:relative;overflow:hidden;height:clamp(340px,62vh,760px);"
    "width:100%;max-width:100%;",
    "CSS .viewer -> overflow:hidden + hauteur responsive")

rep(".viewer img{display:block;transform-origin:0 0;transition:transform .1s;max-width:none}",
    ".viewer img{display:block;position:absolute;top:0;left:0;transform-origin:0 0;"
    "transition:transform .1s;max-width:none;user-select:none;will-change:transform}",
    "CSS .viewer img -> position absolute")

# ---------- 2. JS : fitToScreen ----------
rep("function applyT(){",
    """/* ===== FIT TO SCREEN (correction plans 2D) =====
   scale = min(cw/W, ch/H) puis centrage par translateX/translateY.
   Marge visuelle de 30 px. Ne deforme jamais : un seul facteur d'echelle. */
const PAD = 30;
function fitToScreen(){
  const vw = document.getElementById("vw"), im = document.getElementById("img");
  if(!vw || !im) return;
  /* Un SVG sans width/height peut avoir naturalWidth = 0 : on lit alors le viewBox. */
  let W = im.naturalWidth, H = im.naturalHeight;
  if(!W || !H){
    const vb = im.getAttribute("data-vb");
    if(vb){ const t = vb.split(/[\\s,]+/).map(Number); if(t.length===4 && t[2]>0 && t[3]>0){ W=t[2]; H=t[3]; } }
  }
  if(!W || !H) return;                       /* rien a ajuster : aucun fit invente */
  const cw = vw.clientWidth - PAD*2, ch = vw.clientHeight - PAD*2;
  if(cw <= 0 || ch <= 0) return;
  ZOOM = Math.min(cw / W, ch / H);           /* <= conserve le ratio */
  TX = PAD + (cw - W*ZOOM)/2;                /* centrage horizontal */
  TY = PAD + (ch - H*ZOOM)/2;                /* centrage vertical   */
  applyT();
  const st = document.getElementById("zst");
  if(st) st.textContent = Math.round(ZOOM*100) + "%";
}
function applyT(){""", "JS : fitToScreen()")

# ---------- 3. loadPlan -> FIT ----------
rep('  im.src = CURPLAN.url; im.style.transform = "none"; im.onload = ()=>applyT();',
    '''  im.src = CURPLAN.url; im.style.transform = "none";
  im.onload = () => { if(im.naturalWidth){ im.setAttribute("data-vb","0 0 "+im.naturalWidth+" "+im.naturalHeight); }
                      fitToScreen(); };
  /* Si l'image est deja en cache, onload peut ne pas se declencher. */
  if(im.complete && im.naturalWidth) { im.onload(); }''',
    "JS : loadPlan -> fitToScreen a chaque plan")

# ---------- 4. reset = fit ----------
rep("function setZoom(d, reset){ if(reset){ ZOOM=1;TX=0;TY=0; } else ZOOM=Math.min(6,Math.max(0.25,ZOOM+d)); applyT(); }",
    """function setZoom(d, reset){
  if(reset){ fitToScreen(); return; }             /* Reinitialiser == FIT exact */
  const vw = document.getElementById("vw"), im = document.getElementById("img");
  if(!vw || !im || !im.naturalWidth){ applyT(); return; }
  const z0 = ZOOM, z1 = Math.min(12, Math.max(0.05, ZOOM + d));
  /* zoom centre sur le milieu de la zone : le point sous le curseur reste stable */
  const cx = (vw.clientWidth/2 - TX)/z0, cy = (vw.clientHeight/2 - TY)/z0;
  ZOOM = z1; TX = vw.clientWidth/2 - cx*z1; TY = vw.clientHeight/2 - cy*z1;
  applyT();
  const st = document.getElementById("zst");
  if(st) st.textContent = Math.round(ZOOM*100) + "%";
}""", "JS : setZoom + reset->fit")

# ---------- 5. pan par translate + tactile + resize ----------
rep('  const vw = document.getElementById("vw"); vw.scrollTop=0; vw.scrollLeft=0;',
    '  const vw = document.getElementById("vw");',
    "JS : suppression scrollTop/Left")

rep('''  if(!vw._bound){ vw._bound=1; let dg=0,sx=0,sy=0;
    vw.addEventListener("mousedown",e=>{dg=1;sx=e.clientX-vw.scrollLeft;sy=e.clientY-vw.scrollTop;vw.classList.add("drag")});
    window.addEventListener("mouseup",()=>{dg=0;vw.classList.remove("drag")});
    vw.addEventListener("mousemove",e=>{ if(!dg)return; vw.scrollLeft=sx-e.clientX; vw.scrollTop=sy-e.clientY; });
    vw.addEventListener("wheel",e=>{ if(!e.ctrlKey&&!e.metaKey)return; e.preventDefault(); setZoom(e.deltaY<0?0.12:-0.12); },{passive:false});
  }''',
    '''  if(!vw._bound){
    vw._bound = 1;
    let dg = 0, lx = 0, ly = 0;                          /* pan souris */
    vw.addEventListener("mousedown", e => { dg=1; lx=e.clientX; ly=e.clientY; vw.classList.add("drag"); e.preventDefault(); });
    window.addEventListener("mouseup", () => { dg=0; vw.classList.remove("drag"); });
    window.addEventListener("mousemove", e => { if(!dg) return;
      TX += e.clientX - lx; TY += e.clientY - ly; lx = e.clientX; ly = e.clientY; applyT(); });
    vw.addEventListener("wheel", e => {                    /* zoom molette, sans modificateur */
      e.preventDefault();
      const r = vw.getBoundingClientRect(), im = document.getElementById("img");
      if(!im) return;
      const z0 = ZOOM, z1 = Math.min(12, Math.max(0.05, ZOOM + (e.deltaY<0 ? 0.12 : -0.12)));
      const cx = (e.clientX-r.left - TX)/z0, cy = (e.clientY-r.top - TY)/z0;
      ZOOM = z1; TX = (e.clientX-r.left) - cx*z1; TY = (e.clientY-r.top) - cy*z1; applyT();
      const st = document.getElementById("zst"); if(st) st.textContent = Math.round(ZOOM*100)+"%";
    }, {passive:false});
    /* Tactile : 1 doigt = pan, 2 doigts = zoom */
    let t0x = 0, t0y = 0, td = 0, tz = 1;
    const dist = t => Math.hypot(t[0].clientX-t[1].clientX, t[0].clientY-t[1].clientY);
    vw.addEventListener("touchstart", e => {
      if(e.touches.length === 2){ td = dist(e.touches); tz = ZOOM; }
      else if(e.touches.length === 1){ t0x = e.touches[0].clientX; t0y = e.touches[0].clientY; }
    }, {passive:true});
    vw.addEventListener("touchmove", e => {
      if(e.touches.length === 2 && td > 0){                        /* pinch */
        e.preventDefault();
        const r = vw.getBoundingClientRect();
        const z1 = Math.min(12, Math.max(0.05, tz * (dist(e.touches)/td)));
        const cx = (r.width/2 - TX)/ZOOM, cy = (r.height/2 - TY)/ZOOM;
        ZOOM = z1; TX = r.width/2 - cx*z1; TY = r.height/2 - cy*z1; applyT();
      } else if(e.touches.length === 1){                           /* pan */
        TX += e.touches[0].clientX - t0x; TY += e.touches[0].clientY - t0y;
        t0x = e.touches[0].clientX; t0y = e.touches[0].clientY; applyT();
      }
    }, {passive:false});
    /* Le FIT est recalcule quand la fenetre change de taille */
    window.addEventListener("resize", () => { if(document.getElementById("vw")) fitToScreen(); });
  }''', "JS : pan translate + tactile + resize")

# z0ratio : facteur interne pour le pinch (evite un etat global supplementaire)
rep("function fitToScreen(){",
    "let _zref = 1;\nfunction z0ratio(){ return _zref; }\nfunction fitToScreen(){",
    "JS : helper z0ratio")

# ---------- 6. barre d'outils : indicateur de zoom + FIT ----------
rep('<button onclick="setZoom(0,1)">⟳ Réinitialiser</button>',
    '<button onclick="fitToScreen()">&#8635; Ajuster</button>'
    '<button onclick="setZoom(0,1)">&#9634; 100 %</button>'
    '<span id="zst" class="mono" style="padding:6px 10px;font-size:12px;color:var(--muted)">100%</span>',
    "HTML : bouton Ajuster + indicateur de zoom")

# _zref doit suivre ZOOM apres chaque fit (pour le pinch)
rep("  const st = document.getElementById(\"zst\");\n  if(st) st.textContent = Math.round(ZOOM*100) + \"%\";\n}\nfunction applyT(){",
    "  _zref = ZOOM;\n  const st = document.getElementById(\"zst\");\n  if(st) st.textContent = Math.round(ZOOM*100) + \"%\";\n}\nfunction applyT(){",
    "JS : _zref = ZOOM apres fit")

assert len(s) < 200000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (delta %+d)" % (n0, len(s), len(s) - n0))
