import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { AdminSection } from "@/components/admin/AdminSection";
import { listAdminUsers } from "@/lib/security/admin-users.functions";

export const Route = createFileRoute("/_authenticated/admin/utilisateurs")({
  head: () => ({
    meta: [
      { title: "Utilisateurs — Administration Bâtir" },
      { name: "description", content: "Comptes, rôles et statuts, en lecture seule." },
      { property: "og:title", content: "Utilisateurs — Administration Bâtir" },
      { property: "og:description", content: "Comptes, rôles et statuts, en lecture seule." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="utilisateurs"><UsersTable /></AdminSection>,
});

const fmt = (d: string | null) => (d ? new Date(d).toLocaleString("fr-FR") : "Jamais");

function UsersTable() {
  const list = useServerFn(listAdminUsers);
  const q = useQuery({ queryKey: ["admin-users"], queryFn: () => list() });
  if (q.isLoading) return <p className="text-sm text-muted-foreground">Chargement des comptes…</p>;
  if (q.isError) return <p className="text-sm text-destructive">Lecture des comptes refusée ou impossible.</p>;
  const rows = q.data ?? [];
  if (!rows.length) return <p className="text-sm text-muted-foreground">Aucun compte.</p>;
  return (
    <div className="space-y-2">
      <p className="font-mono text-xs text-muted-foreground">{rows.length} compte(s) · lecture seule · consultation inscrite au journal d'audit</p>
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left font-mono text-xs uppercase text-muted-foreground">
            <tr><th className="p-2">E-mail</th><th className="p-2">Rôles</th><th className="p-2">Statut</th><th className="p-2">Projets</th><th className="p-2">Créé le</th><th className="p-2">Dernière connexion</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.user_id} className="border-t border-border">
                <td className="p-2">{r.email ?? "—"}</td>
                <td className="p-2 font-mono text-xs">{r.roles.length ? r.roles.join(", ") : "client"}</td>
                <td className={"p-2 " + (r.status === "suspended" ? "text-destructive" : "")}>{r.status === "suspended" ? "suspendu" : "actif"}</td>
                <td className="p-2">{r.project_count}</td>
                <td className="p-2 whitespace-nowrap">{fmt(r.created_at)}</td>
                <td className="p-2 whitespace-nowrap">{fmt(r.last_sign_in_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
