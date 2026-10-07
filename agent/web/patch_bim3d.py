#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHASE 2 — remplace v3D() par le viewer BIM interactif (selection, filtres, vues,
isolation, panneau, liens plan/source). Ne touche a aucune donnee du projet."""
import re

P = "/Users/mac/ConstructionAgent/web/frontend/index.html"
s = open(P).read()

start = s.index("async function v3D(){")
end = s.index("async function vBudget(){")
old = s[start:end]

NEW = r'''let BIM3D = null;   /* etat global du viewer — un seul, detruit proprement */

async function v3D(){
  const b = await api("/api/bim");
  const meta = await api("/api/bim/elements");
  const n = meta.elements ? meta.elements.length : 0;
  let h = `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center">
    <span style="font-size:12px;color:var(--muted)">Niveau :</span>
    <div class="pills" id="fNiv" style="margin:0">
      ${["Tout","Terrain","RDC","Etage","Toiture","Fondation"].map((x,i)=>
        `<button class="${i===0?'on':''}" onclick="bimFiltNiv('${x}',this)">${x}</button>`).join("")}
    </div>
    <span style="font-size:12px;color:var(--muted);margin-left:10px">Type :</span>
    <div class="pills" id="fTyp" style="margin:0">
      ${["Tout","Structure","Architecture","Exterieur"].map((x,i)=>
        `<button class="${i===0?'on':''}" onclick="bimFiltTyp('${x}',this)">${x}</button>`).join("")}
    </div>
    <span style="font-size:12px;color:var(--muted);margin-left:10px">Statut :</span>
    <div class="pills" id="fSta" style="margin:0">
      ${["Tout","VERIFIED","PROPOSED","PENDING_G3","HYPOTHESIS"].map((x,i)=>
        `<button class="${i===0?'on':''}" onclick="bimFiltSta('${x}',this)">${x}</button>`).join("")}
    </div></div>
    <div style="display:grid;grid-template-columns:1fr 330px;gap:14px" id="bimGrid">
      <div>
        <div class="vbar">
          <button onclick="bimView('reset')">⟳ Reset</button>
          <button onclick="bimView('dessus')">Vue dessus</button>
          <button onclick="bimView('rdc')">Vue RDC</button>
          <button onclick="bimView('etage')">Vue étage</button>
          <button onclick="bimView('facade')">Vue façade</button>
          <button onclick="bimView('persp')">Perspective</button>
          <button onclick="bimZoom(1)">🔍+</button><button onclick="bimZoom(-1)">🔍−</button>
        </div>
        <div id="gl" style="height:560px;background:#0a0d10;border:1px solid var(--line);border-radius:10px;position:relative">
          <div id="bimLoad" style="position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:13px">Chargement du modèle…</div>
        </div>
        <div class="note"><b>Cliquez sur un élément</b> pour ouvrir sa fiche. <span id="bimCount"></span>
        · GLB réel <span class="mono">${b.glb?'('+(b.glb_octets/1024).toFixed(0)+' Ko)':'NON EXPORTÉ'}</span>
        · BLEND <span class="mono">${(b.octets/1024).toFixed(0)} Ko</span> ${badge("VERIFIED")}</div>
      </div>
      <div id="bimPanel"><div class="card"><h3>Fiche élément</h3>
        <div style="font-size:13px;color:var(--muted)">Aucun élément sélectionné.<br><br>
        ${n} éléments BIM disponibles.<br><br>
        ${PRO?'<span class="mono" style="font-size:11.5px">source : 3D/bim_elements.json<br>extrait de BIM_FINAL_A3.blend</span>':''}
        </div></div></div>
    </div>`;
  setTimeout(()=>bimStart(b, meta), 80);
  return h;
}

/* ================= INITIALISATION DU VIEWER ================= */
async function bimStart(b, meta){
  const el = document.getElementById("gl");
  if(!el) return;
  if(!b.glb){ el.innerHTML = '<div style="padding:24px;color:var(--muted);font-size:13px">'+
    '<b>Vue 3D indisponible</b> — GLB non exporté.<br>Le fichier BLEND original est intact et vérifié.</div>';
    return; }
  try{
    const T = await import("https://unpkg.com/three@0.160.0/build/three.module.js");
    const {OrbitControls} = await import("https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js");
    const {GLTFLoader} = await import("https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js");
    bimDispose();
    const scene = new T.Scene(); scene.background = new T.Color(0x0a0d10);
    const cam = new T.PerspectiveCamera(46, el.clientWidth/el.clientHeight, 0.1, 800);
    const ren = new T.WebGLRenderer({antialias:true}); ren.setPixelRatio(Math.min(2,devicePixelRatio));
    ren.setSize(el.clientWidth, el.clientHeight); el.appendChild(ren.domElement);
    scene.add(new T.HemisphereLight(0xe8eef4, 0x2a3038, 1.6));
    const dl = new T.DirectionalLight(0xffffff, 2.0); dl.position.set(30,-20,45); scene.add(dl);
    const dl2 = new T.DirectionalLight(0xffffff, 0.7); dl2.position.set(-25,25,20); scene.add(dl2);
    const ctl = new OrbitControls(cam, ren.domElement); ctl.enableDamping = true;
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(b.glb_url);
    scene.add(gltf.scene);
    /* index : nom de mesh normalise -> element BIM */
    const byNom = {}; (meta.elements||[]).forEach(e => { byNom[e.id] = e; });
    const meshes = [];
    gltf.scene.traverse(o => { if(o.isMesh || o.isObject3D){
      o.traverse && o.traverse(x=>{ if(x.isMesh) meshes.push(x); });
      if(o.isMesh) meshes.push(o);
    }});
    const uniq = [...new Set(meshes)];
    uniq.forEach(m => { m.userData.eid = bimMatch(m.name, byNom);
      m.userData.baseColor = m.material && m.material.color ? m.material.color.clone() : null; });
    BIM3D = {T, scene, cam, ren, ctl, meshes: uniq, byNom, meta, el, selected:null, hidden:[], sel:new T.Object3D()};
    /* contour de selection */
    BIM3D.selBox = new T.BoxHelper(BIM3D.sel, 0xc8a45c); BIM3D.selBox.visible=false; scene.add(BIM3D.selBox);
    const box = new T.Box3().setFromObject(gltf.scene); const ct = box.getCenter(new T.Vector3());
    BIM3D.center = ct; BIM3D.size = box.getSize(new T.Vector3());
    bimView("reset");
    const ld = document.getElementById("bimLoad"); if(ld) ld.remove();
    /* clic = selection */
    const rc = new T.Raycaster(); const ptr = new T.Vector2();
    let downX=0, downY=0;
    ren.domElement.addEventListener("pointerdown", e => { downX=e.clientX; downY=e.clientY; });
    ren.domElement.addEventListener("pointerup", e => {
      if(Math.abs(e.clientX-downX) > 5 || Math.abs(e.clientY-downY) > 5) return;  /* c'etait un drag */
      const r = ren.domElement.getBoundingClientRect();
      ptr.x = ((e.clientX-r.left)/r.width)*2-1; ptr.y = -((e.clientY-r.top)/r.height)*2+1;
      rc.setFromCamera(ptr, cam);
      const vis = uniq.filter(m => m.visible);
      const hits = rc.intersectObjects(vis, false);
      if(hits.length){ bimSelect(hits[0].object); }
    });
    const cnt = document.getElementById("bimCount");
    if(cnt) cnt.textContent = uniq.length+" objets rendus · "+(meta.elements||[]).length+" éléments indexés";
    (function loop(){ if(!BIM3D || BIM3D.ren !== ren) return; requestAnimationFrame(loop); ctl.update();
      BIM3D.selBox.visible = !!BIM3D.selected; if(BIM3D.selected) BIM3D.selBox.setFromObject(BIM3D.selected);
      ren.render(scene, cam); })();
    BIM3D.onResize = () => { if(!BIM3D) return; cam.aspect = el.clientWidth/el.clientHeight;
      cam.updateProjectionMatrix(); ren.setSize(el.clientWidth, el.clientHeight); };
    addEventListener("resize", BIM3D.onResize);
  } catch(err){
    const ld = document.getElementById("bimLoad");
    if(ld) ld.innerHTML = '<div style="padding:24px;color:var(--muted);font-size:13px;text-align:center">'+
      '<b>Viewer 3D non chargé</b><br>'+String(err.message||err).slice(0,120)+
      '<br><br>Three.js est chargé depuis <span class="mono">unpkg.com</span> (CDN) — '+
      'ce message apparaît si l\'accès réseau est indisponible.<br>'+
      'Le GLB réel reste présent : vérifiez <span class="mono">/api/bim</span>.</div>';
  }
}

/* rapproche un nom de mesh GLB d'un id d'element BIM */
function bimMatch(nom, byNom){
  if(!nom) return null;
  if(byNom[nom]) return nom;
  const base = nom.replace(/[._-](mesh|obj|001|\d{3,})$/i,"").split(".")[0];
  if(byNom[base]) return base;
  for(const id in byNom){ if(nom.startsWith(id)) return id; }
  return null;
}

function bimDispose(){
  if(!BIM3D) return;
  try{
    if(BIM3D.onResize) removeEventListener("resize", BIM3D.onResize);
    BIM3D.meshes.forEach(m=>{ if(m.geometry) m.geometry.dispose();
      if(m.material){ (Array.isArray(m.material)?m.material:[m.material]).forEach(x=>x.dispose()); } });
    BIM3D.ren.dispose(); BIM3D.ctl.dispose();
    if(BIM3D.el && BIM3D.ren.domElement && BIM3D.ren.domElement.parentNode)
      BIM3D.ren.domElement.parentNode.removeChild(BIM3D.ren.domElement);
  }catch(e){}
  BIM3D = null;
}

/* ================= SELECTION + PANNEAU ================= */
function bimSelect(mesh){
  const eid = mesh.userData.eid;
  BIM3D.selected = mesh;
  const e = eid ? BIM3D.byNom[eid] : null;
  const p = document.getElementById("bimPanel");
  if(!e){
    p.innerHTML = `<div class="card"><h3>Fiche élément</h3>
      <div class="notice" style="color:var(--warn);font-size:13px">Objet <span class="mono">${mesh.name}</span> rendu dans la 3D
      mais <b>sans métadonnée BIM</b> correspondante.</div>
      <div class="kv" style="margin-top:10px"><span>Nom mesh GLB</span><b class="mono">${mesh.name}</b></div>
      <div class="kv"><span>Métadonnée</span><b>UNKNOWN</b></div>
      <div class="note">Aucune donnée inventée : cet objet n'est pas indexé dans 3D/bim_elements.json.</div></div>`;
    return;
  }
  const d = e.dimensions_m, v = e.volume_m3;
  const GLOS = {Poteau:"poteau", Poutre:"poutre", Dalle:"dalle", Semelle:"semelle", Longrine:"longrine",
                Mur:"mur", Cloison:"cloison", Fondation:"fondation", Escalier:"escalier"};
  const gk = GLOS[e.type];
  let peda = "";
  if(!PRO && gk){
    const def = GLOSSAIRE_UI[gk];
    if(def) peda = `<div class="note" style="border-color:var(--accent2)">
      <b>À quoi ça sert ?</b><br>${def}<br><br><b>Dans ce projet :</b></div>`;
    else peda = `<div class="note" style="border-color:var(--unk)"><b>Explication non disponible</b>
      pour ce type d'élément (aucune définition au glossaire du moteur).</div>`;
  }
  const qte = bimQte(e);
  p.innerHTML = `<div class="card" style="border-color:${eid&&BIM3D.selected?'var(--accent)':'var(--line)'}">
    ${peda}
    <h3 style="margin-top:10px">ÉLÉMENT BIM</h3>
    <div class="kv"><span>Nom</span><b class="mono" style="font-size:12px">${e.id}</b></div>
    <div class="kv"><span>Type</span><b>${e.type}</b></div>
    <div class="kv"><span>Niveau</span><b>${e.niveau}</b></div>
    <div class="kv"><span>Dimensions</span><b class="mono">${d[0]} × ${d[1]} × ${d[2]} m</b></div>
    <div class="kv"><span>Volume</span><b class="mono">${v} m³</b></div>
    <div class="kv"><span>Z (base→haut)</span><b class="mono">${e.z_base} → ${e.z_haut} m</b></div>
    <div class="kv"><span>Matériau</span><b>${e.materiau||"UNKNOWN"}</b></div>
    <div class="kv"><span>Statut</span><b>${badge(e.statut)}</b></div>
    <div class="kv"><span>Source</span><b class="mono" style="font-size:11px">${e.source}</b></div>
    ${PRO?`<div class="kv"><span>SHA-256 BIM</span><b class="mono" style="font-size:10.5px">${(e.sha256_source||"").slice(0,32)}…</b></div>`:""}
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px">
      <button class="btn" onclick="bimIsolate()">Isoler</button>
      <button class="btn" onclick="bimShowAll()">Tout afficher</button>
      <button class="btn" onclick="bimFocus()">Centrer</button>
    </div>
    <div style="margin-top:12px;border-top:1px solid var(--line);padding-top:10px">
      <div class="kv"><span>Quantité (métré)</span><b>${qte?qte.n+" "+qte.u:'UNKNOWN'}</b></div>
      ${qte?`<div class="kv"><span>Source métré</span><b class="mono" style="font-size:11px">${qte.src}</b></div>`:""}
      <div class="kv"><span>Correspondance budget</span><b>${bimBudget(e)}</b></div>
      <div class="kv"><span>Correspondance 2D</span><b>${e.correspondance_2D?
        `<button class="btn" style="padding:4px 9px" onclick="bimPlan('${e.correspondance_2D}')">Voir sur le plan</button>`:"UNKNOWN"}</b></div>
      <div class="kv"><span>Voir la source</span><b><button class="btn" style="padding:4px 9px" onclick="bimSrc()">Document BIM</button></b></div>
    </div></div>`;
}
const GLOSSAIRE_UI = {
  poteau:"Un élément vertical qui reprend les charges et les transmet aux fondations. C'est une jambe de la maison.",
  poutre:"Un élément horizontal qui reprend le plancher et le porte aux poteaux. C'est le bras qui relie les jambes.",
  dalle:"La surface horizontale en béton qui forme le plancher. C'est ce sur quoi on marche à l'étage.",
  semelle:"Un bloc de béton enterré sous chaque poteau, qui répartit la charge sur le sol.",
  longrine:"Une poutre enterrée qui relie les semelles entre elles, pour qu'elles ne bougent pas séparément.",
  mur:"La paroi extérieure de la maison : elle isole, protège et porte.",
  cloison:"Une paroi intérieure légère qui sépare deux pièces.",
  fondation:"La partie sous la maison qui transmet son poids au sol. Imaginez le pied de la maison.",
  escalier:"L'ouvrage qui permet de monter d'un niveau à l'autre."};
function bimQte(e){
  const M = {"Poteau":{n:32,u:"m³ (total)",v:9.216,src:"metre/metre_final_v2.json"},
             "Poutre":{n:16,u:"m³ (total)",v:13.856,src:"metre/metre_final_v2.json"},
             "Dalle":{n:3,u:"m³ (total)",v:31.992,src:"metre/metre_final_v2.json"},
             "Semelle":{n:16,u:"m³ (total)",v:5.760,src:"metre/metre_final_v2.json"},
             "Longrine":{n:8,u:"m³ (total)",v:4.920,src:"metre/metre_final_v2.json"}};
  const x = M[e.type]; if(!x) return null;
  return {n:x.n+" éléments · "+x.v, u:x.u, src:x.src};
}
function bimBudget(e){
  const b = {"Poteau":"PENDING_G3","Poutre":"PENDING_G3","Dalle":"PENDING_G3","Semelle":"PENDING_G3",
             "Longrine":"PENDING_G3","Mur":"NON DISPONIBLE","Cloison":"NON DISPONIBLE","Fenetre":"NON DISPONIBLE"};
  return b[e.type] || "NON DISPONIBLE";
}
function bimPlan(url){ go("plans"); setTimeout(()=>{ const i = PLANS.findIndex(p=>p.nom.includes(url.split("/").pop().replace(".svg","")));
  if(i>=0) loadPlan(i, document.querySelectorAll("#pills button")[i]); }, 400); }
function bimSrc(){ alertBox("SOURCE DOCUMENTAIRE", `Élément rendu depuis : 3D/BIM_FINAL_A3.blend\n`+
  `Métadonnées : 3D/bim_elements.json\nDocumentation : docs/D02_synthese_BIM.md\n`+
  `Métré : metre/metre_final_v2.json\nPlans 2D : plans/P02_plan_RDC.svg (RDC) · plans/P03_plan_etage.svg (Étage)\n\n`+
  `Aucune source n'est inventée : seuls ces fichiers réels existent.`); }

/* ================= FILTRES ================= */
function bimSetFilt(id,val,btn){
  document.querySelectorAll("#"+id+" button").forEach(b=>b.className="");
  if(btn) btn.className="on";
  if(id==="fNiv") BIM3D.fNiv=val; if(id==="fTyp") BIM3D.fTyp=val; if(id==="fSta") BIM3D.fSta=val;
  bimApply();
}
function bimFiltNiv(v,b){ bimSetFilt("fNiv",v,b); }
function bimFiltTyp(v,b){ bimSetFilt("fTyp",v,b); }
function bimFiltSta(v,b){ bimSetFilt("fSta",v,b); }
function bimApply(){
  if(!BIM3D) return;
  const groupe = {Poteau:"Structure",Poutre:"Structure",Dalle:"Structure",Semelle:"Structure",
    Longrine:"Structure",Poutre2:"Structure",Mur:"Architecture",Cloison:"Architecture",Fenetre:"Architecture",
    Meuble:"Architecture",Etancheite:"Architecture",Acrotere:"Architecture",Garde:"Exterieur",
    Terrasse:"Exterieur",Garage:"Exterieur",Terrain:"Exterieur",Dallage:"Exterieur",Marche:"Structure"};
  let vis = 0;
  BIM3D.meshes.forEach(m=>{
    const e = m.userData.eid ? BIM3D.byNom[m.userData.eid] : null;
    let ok = true;
    if(BIM3D.fNiv && BIM3D.fNiv!=="Tout") ok = ok && e && (e.niveau===BIM3D.fNiv ||
      (BIM3D.fNiv==="Toiture" && e.niveau==="Toiture") || (BIM3D.fNiv==="Etage" && e.niveau==="Etage"));
    if(ok && BIM3D.fTyp && BIM3D.fTyp!=="Tout") ok = ok && e && groupe[e.type]===BIM3D.fTyp;
    if(ok && BIM3D.fSta && BIM3D.fSta!=="Tout") ok = ok && e && e.statut===BIM3D.fSta;
    if(ok && BIM3D.hidden.indexOf(m.userData.eid)>=0) ok = false;
    m.visible = ok; if(ok) vis++;
  });
  const c = document.getElementById("bimCount");
  if(c) c.textContent = vis+" / "+BIM3D.meshes.length+" objets affichés";
}
function bimIsolate(){
  if(!BIM3D || !BIM3D.selected) return;
  const keep = BIM3D.selected.userData.eid;
  BIM3D.meshes.forEach(m=>{ m.visible = (m.userData.eid===keep); });
  const c = document.getElementById("bimCount"); if(c) c.textContent = "1 objet isolé ("+keep+")";
}
function bimShowAll(){
  if(!BIM3D) return;
  BIM3D.hidden = [];
  BIM3D.fNiv="Tout"; BIM3D.fTyp="Tout"; BIM3D.fSta="Tout";
  document.querySelectorAll("#fNiv button,#fTyp button,#fSta button").forEach((b,i)=>b.className = b.textContent==="Tout"?"on":"");
  BIM3D.meshes.forEach(m=>m.visible=true);
  bimApply();
}
function bimFocus(){
  if(!BIM3D || !BIM3D.selected) return;
  const T = BIM3D.T; const box = new T.Box3().setFromObject(BIM3D.selected);
  const ct = box.getCenter(new T.Vector3()); const s = box.getSize(new T.Vector3()).length();
  BIM3D.ctl.target.copy(ct); BIM3D.cam.position.set(ct.x+s*1.6, ct.y-s*1.6, ct.z+s*1.2);
  BIM3D.cam.lookAt(ct); BIM3D.ctl.update();
}
function bimZoom(dir){
  if(!BIM3D) return; const d = new BIM3D.T.Vector3();
  BIM3D.cam.getWorldDirection(d); BIM3D.cam.position.addScaledVector(d, dir*2.5); BIM3D.ctl.update();
}
function bimView(kind){
  if(!BIM3D) return;
  const {cam, ctl, center:c, size:s} = BIM3D;
  const L = Math.max(s.x, s.y, s.z);
  if(kind==="reset"||kind==="persp"){ cam.position.set(c.x+L*0.85, c.y-L*0.85, c.z+L*0.7); }
  else if(kind==="dessus"){ cam.position.set(c.x, c.y, c.z+L*1.5); }
  else if(kind==="facade"){ cam.position.set(c.x, c.y-L*1.6, c.z+L*0.12); }
  else if(kind==="rdc"){ cam.position.set(c.x+L*0.5, c.y-L*0.5, 2.2); }
  else if(kind==="etage"){ cam.position.set(c.x+L*0.5, c.y-L*0.5, 5.4); }
  ctl.target.copy(c); cam.lookAt(c); ctl.update();
}

'''

s = s[:start] + NEW + s[end:]

# --- destruction propre du viewer quand on quitte la page 3D ---
s = s.replace('''  const F = {accueil:vAccueil, projet:vProjet, etapes:vEtapes, plans:vPlans, "3d":v3D, budget:vBudget,
    docs:vDocs, assistant:vAssistant, gates:vGates};''',
'''  if(PAGE !== "3d" && typeof BIM3D !== "undefined" && BIM3D) bimDispose();   /* liberation memoire */
  const F = {accueil:vAccueil, projet:vProjet, etapes:vEtapes, plans:vPlans, "3d":v3D, budget:vBudget,
    docs:vDocs, assistant:vAssistant, gates:vGates};''')

# --- responsive : panneau BIM en carte sous la 3D sur mobile ---
s = s.replace('''  table{font-size:12.5px}th,td{padding:8px 6px}
  .msg{max-width:94%}''',
'''  table{font-size:12.5px}th,td{padding:8px 6px}
  .msg{max-width:94%}
  #bimGrid{grid-template-columns:1fr!important}
  #gl{height:340px!important}''')

open(P, "w").write(s)
print("v3D() remplace : %d -> %d caracteres (delta %+d)" % (len(old), len(NEW), len(NEW)-len(old)))
print("fonctions ajoutees : bimStart, bimSelect, bimDispose, bimApply, bimIsolate, bimShowAll, bimFocus, bimView, bimZoom, bimPlan, bimSrc, bimMatch")
