/**
 * /sitemap.xml — généré côté serveur.
 *
 * L'origine est lue sur la requête : le sitemap reste donc correct quel que soit
 * le domaine (preview Vercel, domaine de production), sans reconfiguration.
 */
import { createFileRoute } from "@tanstack/react-router";
import { SITE } from "@/lib/site";

/** Uniquement les pages publiques indexables. */
const PAGES = [
  { path: "/", changefreq: "weekly", priority: "1.0" },
  { path: "/tarifs", changefreq: "monthly", priority: "0.8" },
] as const;

/** Date de dernière modification du contenu (à mettre à jour lors d'un changement notable). */
const LASTMOD = "2026-10-07";

function escapeXml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export const Route = createFileRoute("/sitemap.xml")({
  server: {
    handlers: {
      GET: ({ request }) => {
        let origin = SITE.url;
        try {
          const u = new URL(request.url);
          if (u.origin && u.origin !== "null") origin = u.origin;
        } catch {
          /* on garde l'origine par défaut */
        }

        const urls = PAGES.map(
          (p) =>
            `  <url>\n` +
            `    <loc>${escapeXml(origin + p.path)}</loc>\n` +
            `    <lastmod>${LASTMOD}</lastmod>\n` +
            `    <changefreq>${p.changefreq}</changefreq>\n` +
            `    <priority>${p.priority}</priority>\n` +
            `  </url>`,
        ).join("\n");

        const xml =
          `<?xml version="1.0" encoding="UTF-8"?>\n` +
          `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
          `${urls}\n` +
          `</urlset>\n`;

        return new Response(xml, {
          status: 200,
          headers: {
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=3600",
          },
        });
      },
    },
  },
});
