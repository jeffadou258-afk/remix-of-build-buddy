import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { AdminSection } from "@/components/admin/AdminSection";
import { listAuditLog } from "@/lib/security/admin.functions";

export const Route = createFileRoute("/_authenticated/admin/audit")({
  head: () => ({
    meta: [
      { title: "Audit — Administration Bâtir" },
      { name: "description", content: "Journal d'audit immuable, lecture seule." },
      { property: "og:title", content: "Audit — Administration Bâtir" },
      { property: "og:description", content: "Journal d'audit immuable, lecture seule." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="audit"><AuditTable /></AdminSection>,
});

type Row = { id: string; at: string; action: string; result: string; actor_roles: string[]; target_type: string | null; target_id: string | null; reason: string | null };

function AuditTable() {
  const list = useServerFn(listAuditLog);
  const q = useQuery({ queryKey: ["admin-audit"], queryFn: () => list({ data: { limit: 100 } }) });
  if (q.isLoading) return <p className="text-sm text-muted-foreground">Chargement du journal…</p>;
  if (q.isError) return <p className="text-sm text-destructive">Lecture du journal refusée ou impossible.</p>;
  const rows = (q.data ?? []) as Row[];
  if (!rows.length) return <p className="text-sm text-muted-foreground">Journal vide.</p>;
  return (
    <div className="overflow-x-auto border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left font-mono text-xs uppercase text-muted-foreground">
          <tr><th className="p-2">Date</th><th className="p-2">Action</th><th className="p-2">Résultat</th><th className="p-2">Rôles</th><th className="p-2">Cible</th><th className="p-2">Motif</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-border">
              <td className="p-2 whitespace-nowrap">{new Date(r.at).toLocaleString("fr-FR")}</td>
              <td className="p-2 font-mono">{r.action}</td>
              <td className={"p-2 " + (r.result === "allowed" ? "text-primary" : "text-destructive")}>{r.result === "allowed" ? "autorisé" : "refusé"}</td>
              <td className="p-2">{r.actor_roles.join(", ") || "—"}</td>
              <td className="p-2 font-mono text-xs">{r.target_type ? `${r.target_type}:${r.target_id ?? ""}` : "—"}</td>
              <td className="p-2">{r.reason ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
