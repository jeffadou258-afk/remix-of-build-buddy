import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/moteurs")({
  head: () => ({
    meta: [
      { title: "Moteurs — Administration Bâtir" },
      { name: "description", content: "Section Moteurs de l'espace d'administration." },
      { property: "og:title", content: "Moteurs — Administration Bâtir" },
      { property: "og:description", content: "Section Moteurs de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="moteurs" />,
});
