import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { AdminSection } from "@/components/admin/AdminSection";
import { listAdminGates } from "@/lib/security/admin-gates.functions";
import type { AdminGateProject } from "@/lib/security/admin-gates";

export const Route = createFileRoute("/_authenticated/admin/gates")({
  head: () => ({
    meta: [
      { title: "Gates — Administration Bâtir" },
      { name: "description", content: "État des Gates des projets, en lecture seule." },
      { property: "og:title", content: "Gates — Administration Bâtir" },
      { property: "og:description", content: "État des Gates des projets, en lecture seule." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="gates"><GatesView /></AdminSection>,
});

const STATUS: Record<string, string> = { NOT_REACHED: "non atteinte", OPEN: "en attente du client", APPROVED: "approuvée", REJECTED: "refusée", INCONNU: "inconnu" };
const SOURCE: Record<AdminGateProject["source"], string> = {
  ok: "", non_configure: "NON MESURÉ — ConstructionAgent non configuré", injoignable: "NON MESURÉ — ConstructionAgent injoignable", erreur: "NON MESURÉ — réponse ConstructionAgent invalide",
};
const fmt = (d: string | null) => (d ? new Date(d).toLocaleString("fr-FR") : "—");

function GatesView() {
  const list = useServerFn(listAdminGates);
  const q = useQuery({ queryKey: ["admin-gates"], queryFn: () => list() });
  if (q.isLoading) return <p className="text-sm text-muted-foreground">Chargement des Gates…</p>;
  if (q.isError) return <p className="text-sm text-destructive">Lecture des Gates refusée ou impossible.</p>;
  const projects = q.data ?? [];
  return (
    <div className="space-y-4">
      <p className="border border-border p-3 text-sm text-muted-foreground">
        Lecture seule. Les décisions de Gates appartiennent uniquement au client propriétaire du projet ; l'administration ne peut ni approuver ni refuser. Consultation inscrite au journal d'audit.
      </p>
      {!projects.length ? (
        <p className="text-sm text-muted-foreground">Aucun projet relié à ConstructionAgent : aucune Gate existante.</p>
      ) : projects.map((p) => (
        <section key={p.project_id} className="border border-border">
          <header className="flex flex-wrap gap-4 bg-muted/50 p-2 font-mono text-xs">
            <span title={p.project_id}>Projet {p.project_id.slice(0, 8)}</span>
            <span title={p.owner_id}>Propriétaire {p.owner_id.slice(0, 8)}</span>
            <span>Étape {p.stage}</span>
          </header>
          {p.source !== "ok" ? (
            <p className="p-3 font-mono text-xs uppercase text-muted-foreground">{SOURCE[p.source]}</p>
          ) : !p.gates.length ? (
            <p className="p-3 text-sm text-muted-foreground">Aucune Gate renvoyée par ConstructionAgent.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left font-mono text-xs uppercase text-muted-foreground">
                <tr><th className="p-2">Gate</th><th className="p-2">État</th><th className="p-2">Ouverte le</th><th className="p-2">Décision</th><th className="p-2">Décidée le</th><th className="p-2">Par le propriétaire</th></tr>
              </thead>
              <tbody>
                {p.gates.map((g) => (
                  <tr key={g.gate} className="border-t border-border">
                    <td className="p-2 font-mono text-xs">{g.gate}</td>
                    <td className="p-2">{STATUS[g.status]}</td>
                    <td className="p-2 whitespace-nowrap">{fmt(g.opened_at)}</td>
                    <td className="p-2">{g.decision === "approve" ? "approuvée" : g.decision === "reject" ? "refusée" : "—"}</td>
                    <td className="p-2 whitespace-nowrap">{fmt(g.decided_at)}</td>
                    <td className="p-2">{g.decided_by_owner === null ? "—" : g.decided_by_owner ? "oui" : "non"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ))}
    </div>
  );
}
