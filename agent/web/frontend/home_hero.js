/* ============================================================================
   CONSTRUCTION AGENT — B2 : HERO EN DEUX ZONES
   ----------------------------------------------------------------------------
   OBJECTIF : mise en page GAUCHE = message + CTA, DROITE = rendu reel du projet.

   MOTEUR NON TOUCHE. heroInit(), heroApply() et heroGo() ne sont ni redefinis
   ni modifies. Aucune rotation, aucun dot, aucune URL n'est touchee.

   POURQUOI DU CSS ET PAS DES <img> :
     heroApply() fait  el.className = "sl" + (i === _heroI ? " on" : "");
     -> il ECRAit les classes des slides a chaque changement. On ne touche donc
        pas aux slides : on ajoute une classe sur .hero et on repositionne les
        slides en CSS. Le moteur continue de poser ses fonds d'image exactement
        comme avant, mais dans la moitie droite.

   Aucune image creee, aucun base64, aucune valeur projet en dur.
   ============================================================================ */

var CA = (typeof CA !== "undefined" && CA) ? CA : {};

/* ---------------------------------------------------------------------------
   1. FEUILLE DE STYLE — injectee une seule fois, marquee pour verification
   --------------------------------------------------------------------------- */
CA.heroStyle = function () {
  if (document.getElementById("ca-hero-b2")) return false;
  var st = document.createElement("style");
  st.id = "ca-hero-b2";
  st.textContent = [
    /* --- .hero passe en deux zones : le texte occupe la gauche --- */
    ".hero.hero-split{min-height:clamp(480px,72vh,760px);display:block;",
    "  border-radius:0 0 18px 18px;border-bottom:1px solid var(--line)}",
    ".hero.hero-split .in{max-width:52%;padding:0 40px 76px 0}",
    /* --- les slides sont confines a la moitie droite + fondu vers la gauche --- */
    ".hero.hero-split .sl{left:52%;right:0;top:0;bottom:0;",
    "  border-radius:14px 0 0 14px;",
    "  -webkit-mask-image:linear-gradient(90deg,transparent 0,rgba(0,0,0,.55) 14%,#000 34%);",
    "          mask-image:linear-gradient(90deg,transparent 0,rgba(0,0,0,.55) 14%,#000 34%)}",
    /* --- overlay : assombrit la gauche pour la lisibilite du titre --- */
    ".hero.hero-split .ov{background:linear-gradient(90deg,",
    "  rgba(11,18,32,.985) 0%,rgba(11,18,32,.97) 44%,rgba(11,18,32,.42) 62%,",
    "  rgba(11,18,32,.10) 84%,rgba(11,18,32,0) 100%)}",
    /* --- badge BIM dynamique, coin du rendu --- */
    ".ca-heroBadge{position:absolute;right:26px;bottom:26px;z-index:6;",
    "  display:flex;align-items:center;gap:10px;padding:11px 15px;",
    "  background:rgba(11,18,32,.62);border:1px solid var(--line);border-radius:11px;",
    "  backdrop-filter:blur(9px);-webkit-backdrop-filter:blur(9px)}",
    ".ca-heroBadge .ic{width:26px;height:26px;border-radius:7px;flex:0 0 26px;",
    "  background:linear-gradient(135deg,var(--accent),#b2460f);",
    "  display:grid;place-items:center;font-size:13px}",
    ".ca-heroBadge b{display:block;color:var(--txt);font-size:12.5px;font-weight:700;line-height:1.15}",
    ".ca-heroBadge span{display:block;color:var(--muted);font-size:11px;margin-top:2px}",
    /* --- tablette : la composition glisse vers le vertical --- */
    "@media (max-width:1020px){",
    "  .hero.hero-split .in{max-width:60%;padding-right:24px}",
    "  .hero.hero-split .sl{left:46%}}",
    /* --- mobile : rendu AU-DESSUS, texte en dessous. Jamais une grille comprimee --- */
    "@media (max-width:900px){",
    "  .hero.hero-split{min-height:0;display:block}",
    "  .hero.hero-split .sl{left:0;right:0;top:0;bottom:52%;border-radius:0;",
    "    -webkit-mask-image:linear-gradient(180deg,#000 0,#000 66%,transparent 100%);",
    "            mask-image:linear-gradient(180deg,#000 0,#000 66%,transparent 100%)}",
    "  .hero.hero-split .ov{background:linear-gradient(180deg,",
    "    rgba(11,18,32,.30) 0%,rgba(11,18,32,.72) 42%,rgba(11,18,32,.97) 62%,var(--bg) 100%)}",
    "  .hero.hero-split .in{max-width:100%;padding:44vh 18px 30px}",
    "  .ca-heroBadge{right:14px;bottom:calc(52% + 14px)}}",
    /* --- accessibilite : animations desactivees, le hero reste complet --- */
    "@media (prefers-reduced-motion:reduce){",
    "  .hero.hero-split .sl{transition:none}}"
  ].join("\n");
  (document.head || document.documentElement).appendChild(st);
  return true;
};

/* ---------------------------------------------------------------------------
   2. BADGE BIM — valeur DYNAMIQUE, jamais ecrite en dur
   --------------------------------------------------------------------------- */
CA.heroBadge = function () {
  var h = document.getElementById("hero");
  if (!h) return false;
  var old = document.getElementById("ca-heroBadge");
  if (old) old.parentNode.removeChild(old);

  var el = document.createElement("div");
  el.id = "ca-heroBadge";
  el.className = "ca-heroBadge";
  el.setAttribute("role", "status");
  el.innerHTML =
    '<span class="ic">&#129513;</span><div><b>BIM 3D</b><span>' +
    CA.esc(CA.badgeTexte()) + '</span></div>';
  h.appendChild(el);
  return true;
};

/* Texte du badge : uniquement a partir du contexte reel.
   Si le contexte est absent, on affiche UNKNOWN plutot qu'un chiffre invente. */
CA.badgeTexte = function () {
  var c = CA.context();
  if (!c) return "UNKNOWN";
  var n = CA.at(c, "bim.total", null);
  if (n === null) return "UNKNOWN";
  return CA.num(n) + " \u00e9l\u00e9ments";
};

/* ---------------------------------------------------------------------------
   3. APPLICATION — une seule fois, apres que le hero soit dans le DOM
   --------------------------------------------------------------------------- */
CA.heroApplyLayout = function () {
  var h = document.getElementById("hero");
  if (!h) return false;
  CA.heroStyle();
  h.classList.add("hero-split");
  CA.heroBadge();
  return true;
};

/* Point d'entree appele par l'accueil. Ne touche a AUCUNE fonction existante. */
CA.heroBoot = function () {
  return CA.hydrate().then(function (c) {
    CA.heroApplyLayout();           /* le badge se remplit avec CA.context() */
    if (typeof console !== "undefined" && console.log) {
      console.log("[CA] B2 hero deux zones — contexte " + (c ? "charge" : "indisponible") +
                  " · badge : " + CA.badgeTexte());
    }
    return true;
  });
};

if (typeof window !== "undefined") {
  window.CA = CA;
}
