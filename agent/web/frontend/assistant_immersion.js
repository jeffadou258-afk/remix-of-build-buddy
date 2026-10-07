/* ============================================================================
   CONSTRUCTION AGENT — M3 : PREMIERE IMMERSION
   ----------------------------------------------------------------------------
   Ecran d'accueil de premiere visite : une question simple, quatre entrees.
   Chaque choix declenche un PARCOURS REEL.

   REGLES RESPECTEES :
   - aucune donnee fictive ;
   - aucune creation de projet simulee : le serveur n'expose AUCUNE route
     d'ecriture (do_GET / do_POST lecture seule) ;
   - collecte locale a la session uniquement (sessionStorage) ;
   - aucune dependance : ce fichier n'exige que des fonctions deja presentes
     dans index.html (go, ask, alertBox, ctxLoad).

   Ce fichier est volontairement ecrit en chaines simples, sans sequence
   \u{...} ni template literal imbrique : c'est ce qui avait casse la
   syntaxe lors de la premiere tentative d'integration.
   ============================================================================ */

var IMMERSION_CHOIX = [
  {
    id: "creer",
    ic: "+",
    titre: "Créer mon premier projet",
    desc: "Je vous accompagne question par question, sans termes techniques."
  },
  {
    id: "plans",
    ic: "\u25A6",
    titre: "J'ai déjà des plans",
    desc: "Consultez vos plans 2D et leur lecture."
  },
  {
    id: "comprendre",
    ic: "\u2261",
    titre: "Comprendre comment construire",
    desc: "Les étapes expliquées par le Guide de construction."
  },
  {
    id: "continuer",
    ic: "\u25B6",
    titre: "Continuer mon projet",
    desc: "Villa_Test_001 — où en est le dossier, ce qui reste à faire."
  }
];

/* Premiere visite de la session ? */
function immersionVue() {
  try {
    return !sessionStorage.getItem("ca_immersion");
  } catch (e) {
    return true; /* sessionStorage indisponible : on montre l'ecran */
  }
}

function immersionFermer() {
  try { sessionStorage.setItem("ca_immersion", "vu"); } catch (e) {}
  var el = document.getElementById("imm");
  if (el) el.style.display = "none";
}

function immersionRendu() {
  var el = document.getElementById("imm");
  if (!el) return;

  var cartes = IMMERSION_CHOIX.map(function (c) {
    return '<button class="immC" onclick="immersionGo(\'' + c.id + '\')">' +
             '<span class="immI">' + c.ic + '</span>' +
             '<b>' + c.titre + '</b>' +
             '<i>' + c.desc + '</i>' +
           '</button>';
  }).join("");

  el.innerHTML =
    '<div class="immBox">' +
      '<div class="immLb">CONSTRUCTION AGENT</div>' +
      '<h2>Que voulez-vous faire ?</h2>' +
      '<p>Vous n\'avez pas besoin de connaître les termes techniques. ' +
         'Choisissez une entrée — je vous accompagne à partir de là.</p>' +
      '<div class="immGrid">' + cartes + '</div>' +
      '<div class="immNote">Ces réponses ne sont pas enregistrées sur le serveur : ' +
         'elles restent dans votre session.</div>' +
    '</div>';
  el.style.display = "flex";
}

/* Chaque choix declenche un parcours REELLEMENT different. */
function immersionGo(id) {
  try { sessionStorage.setItem("ca_immersion", id); } catch (e) {}
  var el = document.getElementById("imm");
  if (el) el.style.display = "none";

  if (id === "plans") {
    go("plans");
    return;
  }

  if (id === "comprendre") {
    /* Parcours reel : on ouvre l'assistant ET on interroge le Guide Engine. */
    go("assistant");
    setTimeout(function () {
      if (typeof ask === "function") ask("C'est quoi une semelle ?");
    }, 800);
    return;
  }

  if (id === "continuer") {
    go("projet");
    return;
  }

  /* id === "creer" : aucun workflow de creation n'existe cote serveur.
     On ne simule RIEN : on le dit clairement, puis on ouvre le projet reel. */
  go("projet");
  setTimeout(function () {
    if (typeof alertBox === "function") {
      alertBox("CRÉER MON PREMIER PROJET",
        "La création de projet n'est pas disponible : le serveur de Construction Agent " +
        "n'expose aucune route d'écriture.\n\n" +
        "Aucune création n'est simulée.\n\n" +
        "En attendant, vous pouvez explorer le projet réel Villa_Test_001 : " +
        "données terrain, plans 2D, BIM 326 éléments, métrés, budget et validations.");
    }
  }, 350);
}
