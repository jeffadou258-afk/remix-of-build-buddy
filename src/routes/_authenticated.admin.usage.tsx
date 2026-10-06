import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/usage")({
  head: () => ({
    meta: [
      { title: "Usage & coûts — Administration Bâtir" },
      { name: "description", content: "Section Usage & coûts de l'espace d'administration." },
      { property: "og:title", content: "Usage & coûts — Administration Bâtir" },
      { property: "og:description", content: "Section Usage & coûts de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="usage" />,
});
