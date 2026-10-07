#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correction finale du blanc — le viewer mesure la bbox reelle du SVG et
applique un viewBox EFFECTIF en memoire. Les fichiers SVG sur disque ne
sont JAMAIS touches.
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
    print("  OK  %-46s (1)" % label)


# ---------- 1. CSS : conteneur du SVG inline ----------
rep(".viewer.drag{cursor:grabbing}",
    """.viewer.drag{cursor:grabbing}
.viewer #svgHost{position:absolute;top:0;left:0;transform-origin:0 0;will-change:transform;transition:transform .1s}
.viewer #svgHost svg{display:block;overflow:visible}""",
    "CSS : #svgHost transformable")

# ---------- 2. fitToScreen : reference = bbox du contenu ----------
old_fit = """function fitToScreen(){
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
  _zref = ZOOM;
  const st = document.getElementById("zst");
  if(st) st.textContent = Math.round(ZOOM*100) + "%";
}"""
new_fit = """/* Dimensions de reference = celles du contenu REEL du SVG (bbox), posees par loadPlan. */
let CURW = 0, CURH = 0;
function fitToScreen(){
  const vw = document.getElementById("vw");
  if(!vw) return;
  let W = CURW, H = CURH;
  if(!W || !H){                              /* repli : aucun fit invente */
    const im = document.getElementById("img");
    W = im ? im.naturalWidth : 0; H = im ? im.naturalHeight : 0;
    if(!W || !H) return;
  }
  const cw = vw.clientWidth - PAD*2, ch = vw.clientHeight - PAD*2;
  if(cw <= 0 || ch <= 0) return;
  ZOOM = Math.min(cw / W, ch / H);           /* <= conserve le ratio */
  TX = PAD + (cw - W*ZOOM)/2;                /* centrage horizontal */
  TY = PAD + (ch - H*ZOOM)/2;                /* centrage vertical   */
  applyT();
  _zref = ZOOM;
  const st = document.getElementById("zst");
  if(st) st.textContent = Math.round(ZOOM*100) + "%";
}"""
rep(old_fit, new_fit, "JS : fitToScreen sur la bbox reelle")

# ---------- 3. applyT : cible le conteneur SVG ----------
rep('function applyT(){ const im=document.getElementById("img"); if(im) im.style.transform=`translate(${TX}px,${TY}px) scale(${ZOOM})`; }',
    """function applyT(){
  const h = document.getElementById("svgHost"), im = document.getElementById("img");
  if(h) h.style.transform = `translate(${TX}px, ${TY}px) scale(${ZOOM})`;
  else if(im) im.style.transform = `translate(${TX}px, ${TY}px) scale(${ZOOM})`;
}""", "JS : applyT -> #svgHost")

# ---------- 4. loadPlan : fetch + bbox + viewBox effectif ----------
old_load = """  ZOOM=1; TX=0; TY=0; const im = document.getElementById("img");
  if(!im) return;
  im.src = CURPLAN.url; im.style.transform = "none";
  im.onload = () => { if(im.naturalWidth){ im.setAttribute("data-vb","0 0 "+im.naturalWidth+" "+im.naturalHeight); }
                      fitToScreen(); };
  /* Si l'image est deja en cache, onload peut ne pas se declencher. */
  if(im.complete && im.naturalWidth) { im.onload(); }"""
new_load = """  const vw = document.getElementById("vw");
  if(!vw) return;
  let host = document.getElementById("svgHost");
  if(!host){ host = document.createElement("div"); host.id = "svgHost"; vw.appendChild(host); }
  const im = document.getElementById("img");
  if(im) im.style.display = "none";
  /* --- Mesure de la bbox REELLE du contenu, puis viewBox EFFECTIF en memoire.
         Les fichiers SVG sur disque ne sont jamais modifies. --- */
  const nonce = ++_loadSeq;
  fetch(CURPLAN.url).then(r => r.text()).then(txt => {
    if(nonce !== _loadSeq) return;                 /* un autre plan a ete demande entre-temps */
    host.innerHTML = txt;
    const svg = host.querySelector("svg");
    if(!svg) throw new Error("svg absent");
    svg.removeAttribute("width"); svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    let bb;
    try{ bb = svg.getBBox(); }catch(e){ bb = null; }
    let x, y, w, h2;
    if(bb && bb.width > 0 && bb.height > 0){
      const m = 8;                                 /* marge visuelle autour du dessin */
      x = bb.x - m; y = bb.y - m; w = bb.width + 2*m; h2 = bb.height + 2*m;
    }else{                                          /* repli : viewBox declare tel quel */
      const vb = (svg.getAttribute("viewBox")||"0 0 1000 1000").split(/[\\s,]+/).map(Number);
      x = vb[0]||0; y = vb[1]||0; w = vb[2]||1000; h2 = vb[3]||1000;
    }
    svg.setAttribute("viewBox", [x, y, w, h2].join(" "));   /* viewBox EFFECTIF */
    svg.setAttribute("width", w); svg.setAttribute("height", h2);
    CURW = w; CURH = h2;
    _bboxInfo = {declare: CURPLAN.vb_declare || null, effectif: [x, y, w, h2], bbox: bb ? [bb.x,bb.y,bb.width,bb.height] : null};
    ZOOM = 1; TX = 0; TY = 0;
    fitToScreen();
  }).catch(() => {                                  /* si le fetch echoue : repli sur <img> */
    if(nonce !== _loadSeq) return;
    if(host) host.innerHTML = "";
    if(im){ im.style.display = "block"; im.src = CURPLAN.url;
            im.onload = () => { CURW = im.naturalWidth; CURH = im.naturalHeight; fitToScreen(); };
            if(im.complete && im.naturalWidth) im.onload(); }
  });"""
rep(old_load, new_load, "JS : loadPlan -> fetch + bbox + viewBox effectif")

# ---------- 5. compteur de sequence (evite les courses) ----------
rep("let _zref = 1;", "let _zref = 1;\nlet _loadSeq = 0;\nlet _bboxInfo = null;", "JS : _loadSeq + _bboxInfo")

assert len(s) < 200000, "TAILLE ANORMALE %d" % len(s)
open(P, "w").write(s)
print("\n  ECRIT : %d -> %d octets (delta %+d)" % (n0, len(s), len(s) - n0))
