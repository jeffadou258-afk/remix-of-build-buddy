import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/utilisateurs")({
  head: () => ({
    meta: [
      { title: "Utilisateurs — Administration Bâtir" },
      { name: "description", content: "Section Utilisateurs de l'espace d'administration." },
      { property: "og:title", content: "Utilisateurs — Administration Bâtir" },
      { property: "og:description", content: "Section Utilisateurs de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="utilisateurs" />,
});
