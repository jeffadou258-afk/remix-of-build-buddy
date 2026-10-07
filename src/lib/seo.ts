/**
 * Construction des balises SEO et des données structurées (JSON-LD).
 *
 * - SEO  : titre, description, canonical, Open Graph, Twitter, robots.
 * - AEO  : FAQPage + HowTo, pour être cité comme réponse directe.
 * - GEO  : entités explicites (Organization, Service, Place, WebSite).
 * - LLMO : mêmes faits, en clair et structurés, réutilisés par /llms.txt.
 */
import { SITE, absoluteUrl } from "./site";

type Meta = Record<string, string>;
type Link = { rel: string; href: string; [k: string]: string };
type Script = { type: string; children: string };

export type PageHead = {
  meta: Meta[];
  links: Link[];
  scripts?: Script[];
};

/** Balises communes à toutes les pages publiques. */
export function pageHead(opts: {
  title: string;
  description: string;
  /** Chemin canonique, ex. "/tarifs". */
  path: string;
  /** Image de partage (chemin absolu du site). */
  image?: string;
  imageAlt?: string;
  /** Pages privées (connexion, espace projet) : ne pas indexer. */
  noindex?: boolean;
  /** Données structurées supplémentaires. */
  jsonLd?: unknown[];
}): PageHead {
  const url = absoluteUrl(opts.path);
  const image = absoluteUrl(opts.image ?? SITE.ogImage);
  const imageAlt = opts.imageAlt ?? SITE.ogImageAlt;

  const meta: Meta[] = [
    { title: opts.title },
    { name: "description", content: opts.description },

    // Canonical + robots
    ...(opts.noindex
      ? [{ name: "robots", content: "noindex, nofollow" }]
      : [{ name: "robots", content: "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" }]),

    // Localisation (GEO)
    { name: "geo.region", content: SITE.areaServed.country },
    { name: "geo.placename", content: SITE.areaServed.city },
    { name: "content-language", content: SITE.lang },

    // Open Graph
    { property: "og:type", content: "website" },
    { property: "og:site_name", content: SITE.name },
    { property: "og:locale", content: SITE.locale },
    { property: "og:title", content: opts.title },
    { property: "og:description", content: opts.description },
    { property: "og:url", content: url },
    { property: "og:image", content: image },
    { property: "og:image:alt", content: imageAlt },
    { property: "og:image:width", content: "1200" },
    { property: "og:image:height", content: "630" },

    // Twitter / X
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: opts.title },
    { name: "twitter:description", content: opts.description },
    { name: "twitter:image", content: image },
    { name: "twitter:image:alt", content: imageAlt },
  ];

  const links: Link[] = [{ rel: "canonical", href: url }];

  const scripts: Script[] = [
    jsonLd(websiteNode()),
    jsonLd(organizationNode()),
    ...(opts.jsonLd ?? []).map(jsonLd),
  ];

  return { meta, links, scripts };
}

function jsonLd(data: unknown): Script {
  return { type: "application/ld+json", children: JSON.stringify(data) };
}

// ---------------------------------------------------------------- entités (GEO)

export function organizationNode() {
  return {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "@id": absoluteUrl("/#organization"),
    name: SITE.name,
    legalName: SITE.legalName,
    url: SITE.url,
    description: SITE.description,
    slogan: SITE.tagline,
    image: absoluteUrl(SITE.ogImage),
    logo: absoluteUrl("/favicon.ico"),
    areaServed: {
      "@type": "Country",
      name: SITE.areaServed.countryName,
    },
    address: {
      "@type": "PostalAddress",
      addressLocality: SITE.areaServed.city,
      addressCountry: SITE.areaServed.country,
    },
    ...(SITE.contact.email ? { email: SITE.contact.email } : {}),
    ...(SITE.contact.telephone ? { telephone: SITE.contact.telephone } : {}),
    ...(SITE.sameAs.length ? { sameAs: [...SITE.sameAs] } : {}),
    knowsAbout: [
      "conception architecturale",
      "programmation architecturale",
      "maquette 3D et BIM",
      "plans de construction",
      "documentation technique",
    ],
    serviceType: "Conception architecturale assistée par intelligence artificielle",
  };
}

export function websiteNode() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": absoluteUrl("/#website"),
    url: SITE.url,
    name: SITE.name,
    description: SITE.description,
    inLanguage: SITE.lang,
    publisher: { "@id": absoluteUrl("/#organization") },
  };
}

/** Catalogue de services (une entrée par étape livrée). */
export function serviceNode(input: {
  name: string;
  description: string;
  path: string;
  offer?: { name: string; price: string; currency: string; description?: string };
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    name: input.name,
    description: input.description,
    serviceType: input.name,
    provider: { "@id": absoluteUrl("/#organization") },
    areaServed: { "@type": "Country", name: SITE.areaServed.countryName },
    url: absoluteUrl(input.path),
    ...(input.offer
      ? {
          offers: {
            "@type": "Offer",
            name: input.offer.name,
            price: input.offer.price,
            priceCurrency: input.offer.currency,
            ...(input.offer.description ? { description: input.offer.description } : {}),
          },
        }
      : {}),
  };
}

/** FAQPage — cœur de l'AEO (réponses directes citables). */
export function faqNode(items: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((i) => ({
      "@type": "Question",
      name: i.question,
      acceptedAnswer: { "@type": "Answer", text: i.answer },
    })),
  };
}

/** HowTo — les étapes du parcours, exploitables par les moteurs de réponse. */
export function howToNode(input: { name: string; description: string; steps: { name: string; text: string }[] }) {
  return {
    "@context": "https://schema.org",
    "@type": "HowTo",
    name: input.name,
    description: input.description,
    totalTime: "PT20M",
    tool: [{ "@type": "HowToTool", name: SITE.name }],
    step: input.steps.map((s, i) => ({
      "@type": "HowToStep",
      position: i + 1,
      name: s.name,
      text: s.text,
      url: absoluteUrl("/#" + s.name.toLowerCase()),
    })),
  };
}

export function breadcrumbNode(items: { name: string; path: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: it.name,
      item: absoluteUrl(it.path),
    })),
  };
}
