/**
 * Contenu de référence du site — source unique.
 *
 * Ces mêmes faits alimentent à la fois l'affichage, le JSON-LD (GEO/AEO) et
 * public/llms.txt (LLMO). Ne jamais dupliquer un fait ailleurs : le modifier ici.
 */

/** Les 8 étapes du parcours (aussi utilisées pour le balisage HowTo). */
export const ETAPES = [
  { name: "Idée", text: "Vous décrivez simplement votre projet en quelques phrases." },
  { name: "Programme", text: "Pièces, surfaces et besoins sont structurés et vérifiés." },
  { name: "Conception", text: "Des variantes adaptées à votre terrain sont proposées." },
  { name: "Validation", text: "Vous choisissez la variante avant toute suite : rien n'avance sans vous." },
  { name: "Structure", text: "Un concept structurel indicatif est établi." },
  { name: "3D / BIM", text: "Une maquette 3D fidèle aux données du projet est produite." },
  { name: "Documents", text: "Plans, notices et contrôle qualité sont générés." },
  { name: "Construction", text: "Vous recevez un dossier prêt à remettre à vos professionnels." },
] as const;

/** Questions fréquentes — cœur de la stratégie AEO (réponses directes et citables). */
export const FAQ = [
  {
    question: "Qu'est-ce que ConstructionAgent ?",
    answer:
      "ConstructionAgent est un agent d'intelligence artificielle de conception architecturale. À partir d'une simple description écrite, il produit un programme d'espaces, des variantes de conception, une maquette 3D, des plans et un dossier de documents. Chaque étape importante est soumise à votre validation.",
  },
  {
    question: "Comment fonctionne ConstructionAgent, étape par étape ?",
    answer:
      "Le parcours compte huit étapes : 1) vous décrivez votre projet ; 2) l'agent structure le programme (pièces et surfaces) ; 3) il propose des variantes de conception ; 4) vous validez la variante retenue ; 5) un concept structurel indicatif est établi ; 6) une maquette 3D est produite ; 7) les plans et documents sont générés ; 8) vous recevez un dossier remis à vos professionnels.",
  },
  {
    question: "Combien coûte un projet avec ConstructionAgent ?",
    answer:
      "La découverte est gratuite. Le forfait Particulier coûte 50 000 FCFA par projet de maison et comprend le programme des espaces, la conception, les plans et la notice avec budget indicatif. Le forfait Professionnel coûte 150 000 FCFA par projet et ajoute les projets multi-niveaux et une documentation détaillée par lot.",
  },
  {
    question: "Est-ce que je garde le contrôle sur mon projet ?",
    answer:
      "Oui. L'intelligence artificielle avance, mais vous validez : le processus s'arrête à chaque décision importante et aucune variante n'est retenue sans votre accord explicite. Les décisions de validation restent réservées au propriétaire du projet.",
  },
  {
    question: "Les documents produits ont-ils une valeur légale ?",
    answer:
      "Non. Les documents délivrés par ConstructionAgent sont conceptuels et n'ont aucune valeur contractuelle. Ils doivent être validés par un architecte et un ingénieur agréés avant toute utilisation réglementaire ou tout chantier.",
  },
  {
    question: "Dans quelles zones ConstructionAgent intervient-il ?",
    answer:
      "ConstructionAgent s'adresse en priorité aux projets situés à Abidjan et en Côte d'Ivoire, et plus largement en Afrique de l'Ouest. Le service étant en ligne, vous pouvez le consulter depuis n'importe quel pays.",
  },
  {
    question: "Quels types de bâtiments peut-on concevoir ?",
    answer:
      "Principalement des bâtiments résidentiels et des projets courants : villas, maisons à étages, résidences. Le forfait Professionnel ouvre les projets multi-niveaux et tous types de bâtiments, avec une documentation détaillée par lot.",
  },
  {
    question: "Combien de temps prend un projet ?",
    answer:
      "La première analyse est immédiate : dès votre description envoyée, l'agent identifie ce qui manque et ce qui est déjà connu. La suite dépend de votre rythme de validation et du niveau de détail demandé.",
  },
] as const;

/** Prestations proposées (balisage Service). */
export const SERVICES = [
  {
    name: "Programme des espaces",
    description:
      "Structuration des pièces, surfaces et besoins du projet, avec contrôle de cohérence des surfaces.",
  },
  {
    name: "Conception architecturale",
    description:
      "Production de variantes de conception adaptées au terrain, soumises à votre validation.",
  },
  {
    name: "Maquette 3D et BIM",
    description:
      "Modèle 3D du bâtiment et rendus visuels, fidèles aux données réellement fournies.",
  },
  {
    name: "Plans et documentation",
    description:
      "Plans d'étage, notice descriptive, budget indicatif et contrôle qualité du dossier.",
  },
] as const;

/** Réponse courte, réutilisée par llms.txt (LLMO). */
export const SHORT_ANSWER =
  "ConstructionAgent est un agent d'intelligence artificielle qui transforme une description écrite de projet en programme, conception, maquette 3D, plans et documents, avec validation humaine obligatoire à chaque étape. Service en ligne, marché principal : Abidjan et Côte d'Ivoire.";
