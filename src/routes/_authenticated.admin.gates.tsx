import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/gates")({
  head: () => ({
    meta: [
      { title: "Gates — Administration Bâtir" },
      { name: "description", content: "Section Gates de l'espace d'administration." },
      { property: "og:title", content: "Gates — Administration Bâtir" },
      { property: "og:description", content: "Section Gates de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="gates" />,
});
