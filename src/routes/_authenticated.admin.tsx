import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { getAdminAccess } from "@/lib/security/admin-access.functions";
import { visibleSections } from "@/lib/security/admin-sections";
import { AdminDenied } from "@/components/admin/AdminSection";

export const Route = createFileRoute("/_authenticated/admin")({
  head: () => ({
    meta: [
      { title: "Administration — Bâtir" },
      { name: "description", content: "Espace d'administration réservé, accès contrôlé côté serveur." },
      { property: "og:title", content: "Administration — Bâtir" },
      { property: "og:description", content: "Espace d'administration réservé." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: AdminLayout,
});

function AdminLayout() {
  const fetchAccess = useServerFn(getAdminAccess);
  const q = useQuery({ queryKey: ["admin-access"], queryFn: () => fetchAccess() });

  if (q.isLoading) return <p className="p-10 text-center text-muted-foreground">Vérification des droits…</p>;
  if (q.isError || !q.data?.allowed) {
    return (
      <div className="mx-auto max-w-xl p-10">
        <AdminDenied message={q.data?.suspended ? "Compte suspendu." : "Cet espace est réservé aux comptes disposant d'un rôle d'administration."} />
      </div>
    );
  }

  const sections = visibleSections(q.data.permissions);
  return (
    <div className="mx-auto flex max-w-6xl gap-8 px-5 py-8">
      <aside className="w-52 shrink-0">
        <p className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">Administration</p>
        <nav className="flex flex-col">
          {sections.map((s) => (
            <Link
              key={s.id}
              to={s.path}
              activeOptions={{ exact: true }}
              className="border-l-2 border-transparent px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
              activeProps={{ className: "border-primary text-foreground font-medium" }}
            >
              {s.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 flex-1"><Outlet /></main>
    </div>
  );
}
