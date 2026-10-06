import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { AdminSection } from "@/components/admin/AdminSection";
import { listAdminProjects } from "@/lib/security/admin-projects.functions";

export const Route = createFileRoute("/_authenticated/admin/projets")({
  head: () => ({
    meta: [
      { title: "Projets — Administration Bâtir" },
      { name: "description", content: "Métadonnées des projets, en lecture seule, sans contenu client." },
      { property: "og:title", content: "Projets — Administration Bâtir" },
      { property: "og:description", content: "Métadonnées des projets, en lecture seule." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="projets"><ProjectsTable /></AdminSection>,
});

const fmt = (d: string) => new Date(d).toLocaleString("fr-FR");
const short = (id: string) => id.slice(0, 8);
const NM = () => <span className="font-mono text-xs uppercase text-muted-foreground">Non mesuré</span>;

function ProjectsTable() {
  const list = useServerFn(listAdminProjects);
  const q = useQuery({ queryKey: ["admin-projects"], queryFn: () => list() });
  if (q.isLoading) return <p className="text-sm text-muted-foreground">Chargement des projets…</p>;
  if (q.isError) return <p className="text-sm text-destructive">Lecture des projets refusée ou impossible.</p>;
  const rows = q.data ?? [];
  if (!rows.length) return <p className="text-sm text-muted-foreground">Aucun projet.</p>;
  return (
    <div className="space-y-2">
      <p className="font-mono text-xs text-muted-foreground">{rows.length} projet(s) · métadonnées uniquement · lecture seule · consultation inscrite au journal d'audit</p>
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left font-mono text-xs uppercase text-muted-foreground">
            <tr><th className="p-2">Projet</th><th className="p-2">Propriétaire</th><th className="p-2">Type</th><th className="p-2">Étape</th><th className="p-2">ConstructionAgent</th><th className="p-2">Runs</th><th className="p-2">Coût</th><th className="p-2">Créé</th><th className="p-2">Modifié</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.project_id} className="border-t border-border">
                <td className="p-2 font-mono text-xs" title={r.project_id}>{short(r.project_id)}</td>
                <td className="p-2 font-mono text-xs" title={r.owner_id}>{short(r.owner_id)}</td>
                <td className="p-2">{r.client_type}</td>
                <td className="p-2">{r.stage}</td>
                <td className="p-2">{r.ca_linked ? "relié" : "non relié"}</td>
                <td className="p-2"><NM /></td>
                <td className="p-2"><NM /></td>
                <td className="p-2 whitespace-nowrap">{fmt(r.created_at)}</td>
                <td className="p-2 whitespace-nowrap">{fmt(r.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
