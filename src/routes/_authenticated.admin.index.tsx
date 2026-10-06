import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/")({
  head: () => ({
    meta: [
      { title: "Dashboard — Administration Bâtir" },
      { name: "description", content: "Section Dashboard de l'espace d'administration." },
      { property: "og:title", content: "Dashboard — Administration Bâtir" },
      { property: "og:description", content: "Section Dashboard de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="dashboard" />,
});
