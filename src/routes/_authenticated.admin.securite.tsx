import { createFileRoute } from "@tanstack/react-router";
import { AdminSection } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin/securite")({
  head: () => ({
    meta: [
      { title: "Sécurité — Administration Bâtir" },
      { name: "description", content: "Section Sécurité de l'espace d'administration." },
      { property: "og:title", content: "Sécurité — Administration Bâtir" },
      { property: "og:description", content: "Section Sécurité de l'espace d'administration." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="securite" />,
});
