import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/sante")({
  head: () => ({
    meta: [
      { title: "Santé système — Administration Bâtir" },
      { name: "description", content: "Section Santé système de l'espace d'administration." },
      { property: "og:title", content: "Santé système — Administration Bâtir" },
      { property: "og:description", content: "Section Santé système de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="sante" />,
});
