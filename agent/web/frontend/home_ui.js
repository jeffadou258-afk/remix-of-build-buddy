/* ============================================================================
   CONSTRUCTION AGENT — B1 : FONDATION UI PREMIUM
   ----------------------------------------------------------------------------
   Ce fichier ne contient AUCUNE donnee projet et AUCUNE requete reseau propre.

   PRINCIPES (mission UI Premium, §21 et §22) :
     - une seule source de donnees : ctxLoad() existant, qui met deja en cache
       /api/assistant/context. On ne cree PAS de deuxieme logique concurrente ;
     - le frontend n'invente jamais : nom, localisation, chambres, surfaces,
       nombre d'elements BIM, budget, progression, statuts viennent du contexte ;
     - aucune valeur par defaut inventee : un champ absent donne "UNKNOWN" ;
     - B1 ne construit AUCUNE des 12 sections : il prepare la fondation.

   PROTECTIONS : ce fichier ne definit rien qui puisse ecraser une fonction
   existante (heroInit, heroApply, immersionGo, bim*, loadPlan, fitToScreen...).
   Tout est range sous le namespace CA.

   Ecrit en chaines simples, sans sequence \u{...} ni template literal imbrique :
   c'est exactement ce qui avait casse la syntaxe lors de la 1re tentative M3.
   ============================================================================ */

var CA = (typeof CA !== "undefined" && CA) ? CA : {};

/* ---------------------------------------------------------------------------
   1. CONTEXTE PROJET — reutilise ctxLoad(), sans dupliquer la requete
   --------------------------------------------------------------------------- */
CA._ctxPromise = null;

/* loadProjectContext() : point d'entree unique des donnees projet.
   Si ctxLoad() existe (defini par index.html), on l'utilise : il gere deja
   le cache. Sinon on appelle /api/assistant/context une seule fois et on
   memorise la promesse, pour ne jamais lancer deux requetes identiques. */
CA.loadProjectContext = function () {
  if (typeof ctxLoad === "function") {
    return Promise.resolve(ctxLoad());
  }
  if (!CA._ctxPromise) {
    if (typeof api !== "function") return Promise.resolve(null);
    CA._ctxPromise = Promise.resolve(api("/api/assistant/context"))
      .catch(function () { return null; });
  }
  return CA._ctxPromise;
};

/* Acces sur a un chemin imbrique : CA.at(ctx, "program.chambres", "UNKNOWN").
   Jamais de 0 ni de undefined a l'ecran : un champ absent devient UNKNOWN. */
CA.at = function (obj, path, def) {
  var cur = obj;
  var parts = String(path || "").split(".");
  for (var i = 0; i < parts.length; i++) {
    if (cur === null || cur === undefined) return (def === undefined ? "UNKNOWN" : def);
    cur = cur[parts[i]];
  }
  if (cur === null || cur === undefined || cur === "") return (def === undefined ? "UNKNOWN" : def);
  return cur;
};

/* Separateur de milliers a la francaise. Aucune valeur en dur. */
CA.num = function (n) {
  if (n === null || n === undefined || n === "") return "UNKNOWN";
  if (typeof n !== "number") {
    var t = parseInt(String(n).replace(/\s/g, ""), 10);
    if (isNaN(t)) return String(n);
    n = t;
  }
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
};

/* ---------------------------------------------------------------------------
   2. PETIT CACHE LOCAL DU CONTEXTE (evite de re-demander le contexte a chaque
      section lors du rendu de l'accueil)
   --------------------------------------------------------------------------- */
CA._ctx = null;

CA.context = function () {
  return CA._ctx;
};

CA.hydrate = function () {
  return CA.loadProjectContext().then(function (c) {
    CA._ctx = c || null;
    return CA._ctx;
  });
};

/* ---------------------------------------------------------------------------
   3. OUTILS DE RENDU — sans dependance a une section particuliere
   --------------------------------------------------------------------------- */
CA.esc = function (s) {
  return String(s === null || s === undefined ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
};

/* Point de montage : remplace le contenu d'un element s'il existe.
   Ne cree rien si la cible est absente (aucune erreur si la section n'est
   pas encore branchee). */
CA.mount = function (id, html) {
  var el = document.getElementById(id);
  if (!el) return false;
  el.innerHTML = html;
  return true;
};

/* ---------------------------------------------------------------------------
   4. REGISTRE DES SECTIONS — PREPARE EN B1, CONSTRUIT EN B2..B8
      Chaque entree est un emplacement reserve. En B1 elles renvoient une
      chaine vide : la fondation est posee, les sections ne sont PAS baties.
   --------------------------------------------------------------------------- */
CA.SECTION_IDS = {
  hero: "homeHero",
  parcours: "homeParcours",
  assistant: "homeAssistant",
  projet: "homeProjet",
  bim: "homeBim",
  plans: "homePlans",
  guide: "homeGuide",
  budget: "homeBudget",
  gates: "homeGates",
  cta: "homeCta",
  footer: "homeFooter"
};

CA.sections = {};

/* B2 */ CA.sections.hero      = function () { return ""; };
/* B3 */ CA.sections.parcours   = function () { return ""; };
/* B4 */ CA.sections.assistant  = function () { return ""; };
/* B5 */ CA.sections.projet     = function () { return ""; };
/* B5 */ CA.sections.bim        = function () { return ""; };
/* B5 */ CA.sections.plans      = function () { return ""; };
/* B5 */ CA.sections.guide      = function () { return ""; };
/* B5 */ CA.sections.budget     = function () { return ""; };
/* B6 */ CA.sections.gates      = function () { return ""; };
/* B6 */ CA.sections.cta        = function () { return ""; };
/* B6 */ CA.sections.footer     = function () { return ""; };

/* Etat de la fondation — utile pour verifier B1 dans le navigateur. */
CA.status = function () {
  return {
    fondation: "B1",
    ctxLoad_disponible: (typeof ctxLoad === "function"),
    api_disponible: (typeof api === "function"),
    namespace: (typeof CA === "object"),
    contexte_charge: !!CA._ctx,
    sections_preparees: Object.keys(CA.sections).length,
    sections_construites: 0
  };
};

/* ---------------------------------------------------------------------------
   5. PARCOURS M3 — on APPELLE l'existant, on ne le reimplemente pas.
      (M3 est VERIFIED : immersionGo() doit rester la seule logique.)
   --------------------------------------------------------------------------- */
CA.parcoursLancer = function (id) {
  if (typeof immersionGo === "function") { immersionGo(id); return true; }
  return false;
};

/* ---------------------------------------------------------------------------
   6. NAVIGATION — delegue a go() existant. Aucun duplicata.
   --------------------------------------------------------------------------- */
CA.aller = function (page) {
  if (typeof go === "function") { go(page); return true; }
  return false;
};

/* ---------------------------------------------------------------------------
   7. AMORCAGE — hydrate le contexte et signale l'etat.
      Ne monte AUCUNE section (B1). Ne touche a aucune fonction existante.
   --------------------------------------------------------------------------- */
CA.boot = function () {
  return CA.hydrate().then(function (ctx) {
    if (typeof console !== "undefined" && console.log) {
      console.log("[CA] B1 fondation prete — contexte " + (ctx ? "charge" : "indisponible") +
                  " · sections preparees : " + Object.keys(CA.sections).length);
    }
    return ctx;
  });
};

if (typeof window !== "undefined") {
  window.CA = CA;
}
