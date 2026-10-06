import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/projets")({
  head: () => ({
    meta: [
      { title: "Projets — Administration Bâtir" },
      { name: "description", content: "Section Projets de l'espace d'administration." },
      { property: "og:title", content: "Projets — Administration Bâtir" },
      { property: "og:description", content: "Section Projets de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="projets" />,
});
