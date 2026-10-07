/**
 * Source unique de vérité pour l'identité du site.
 * Sert au SEO (balises), à l'AEO (réponses), au GEO (entités) et au LLMO (llms.txt).
 *
 * L'URL publique est configurable par variable d'environnement : elle doit être
 * renseignée sur Vercel (VITE_SITE_URL) une fois le domaine connu.
 */

const RAW_URL = (import.meta.env["VITE_SITE_URL"] as string | undefined) ?? "";

export const SITE = {
  /** URL publique canonique, sans slash final. */
  url: (RAW_URL || "https://constructionagent.vercel.app").replace(/\/+$/, ""),

  name: "ConstructionAgent",
  /** Nom affiché dans les titres. */
  shortName: "ConstructionAgent",
  legalName: "ConstructionAgent",

  /** Phrase de positionnement, réutilisée partout. */
  tagline: "De l'idée à la construction.",

  description:
    "Agent d'intelligence artificielle qui transforme une description de projet en programme, conception, maquette 3D, plans et documents, avec validation humaine à chaque étape.",

  /** Marché principal (GEO / SEO local). */
  areaServed: {
    country: "CI",
    countryName: "Côte d'Ivoire",
    city: "Abidjan",
    regions: ["Abidjan", "Côte d'Ivoire", "Afrique de l'Ouest"],
  },

  locale: "fr_FR",
  lang: "fr",

  /** Coordonnées — à compléter par le propriétaire. */
  contact: {
    email: "contact@constructionagent.app",
    telephone: null as string | null,
  },

  /** Image de partage social (1200×630), générée dans public/og/. */
  ogImage: "/og/constructionagent.png",
  ogImageAlt:
    "Rendu 3D d'une villa contemporaine produit par ConstructionAgent",

  themeColor: "#12100E",

  /** Profils officiels (sameAs pour le JSON-LD) — à compléter. */
  sameAs: [] as string[],
} as const;

/** URL absolue à partir d'un chemin. */
export function absoluteUrl(path = "/"): string {
  return SITE.url + (path.startsWith("/") ? path : "/" + path);
}
