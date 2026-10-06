import { Fragment, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
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
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: () => <AdminSection id="audit"><AuditView /></AdminSection>,
});

type Row = {
  id: string; at: string; actor_id: string | null; actor_roles: string[]; action: string; permission: string | null;
  result: string; target_type: string | null; target_id: string | null; reason: string | null; before: unknown; after: unknown;
};
type Filters = { action: string; result: string; actorId: string; from: string; to: string };
const EMPTY: Filters = { action: "", result: "", actorId: "", from: "", to: "" };
const input = "h-9 border border-border bg-background px-2 text-sm";

function AuditView() {
  const list = useServerFn(listAuditLog);
  const [draft, setDraft] = useState<Filters>(EMPTY);
  const [applied, setApplied] = useState<Filters>(EMPTY);
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState<string | null>(null);
  const q = useQuery({
    queryKey: ["admin-audit", applied, page],
    queryFn: () => list({ data: { ...applied, page } }),
    placeholderData: keepPreviousData,
  });
  const actorOk = !draft.actorId || /^[0-9a-f-]{36}$/i.test(draft.actorId);

  return (
    <div className="space-y-4">
      <form
        className="flex flex-wrap items-end gap-3 border border-border p-3"
        onSubmit={(e) => { e.preventDefault(); if (actorOk) { setApplied(draft); setPage(0); } }}
      >
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Action
          <select className={input} value={draft.action} onChange={(e) => setDraft({ ...draft, action: e.target.value })}>
            <option value="">Toutes</option>
            {(q.data?.actions ?? []).map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Résultat
          <select className={input} value={draft.result} onChange={(e) => setDraft({ ...draft, result: e.target.value })}>
            <option value="">Tous</option><option value="allowed">autorisé</option><option value="denied">refusé</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Acteur (identifiant)
          <input className={input + " w-72 font-mono"} value={draft.actorId} placeholder="uuid" onChange={(e) => setDraft({ ...draft, actorId: e.target.value.trim() })} />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Du
          <input type="date" className={input} value={draft.from} onChange={(e) => setDraft({ ...draft, from: e.target.value })} />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Au
          <input type="date" className={input} value={draft.to} onChange={(e) => setDraft({ ...draft, to: e.target.value })} />
        </label>
        <button type="submit" disabled={!actorOk} className="h-9 bg-primary px-4 text-sm text-primary-foreground disabled:opacity-50">Filtrer</button>
        <button type="button" className="h-9 border border-border px-4 text-sm" onClick={() => { setDraft(EMPTY); setApplied(EMPTY); setPage(0); }}>Réinitialiser</button>
        {!actorOk && <p className="w-full text-xs text-destructive">Identifiant d'acteur invalide.</p>}
      </form>

      {q.isLoading ? <p className="text-sm text-muted-foreground">Chargement du journal…</p>
        : q.isError ? <p className="text-sm text-destructive">Lecture du journal refusée ou impossible.</p>
        : <Table data={q.data!} page={page} setPage={setPage} open={open} setOpen={setOpen} />}
    </div>
  );
}

function Table({ data, page, setPage, open, setOpen }: {
  data: { rows: unknown[]; total: number; pageSize: number };
  page: number; setPage: (n: number) => void; open: string | null; setOpen: (id: string | null) => void;
}) {
  const rows = data.rows as Row[];
  const pages = Math.max(1, Math.ceil(data.total / data.pageSize));
  if (!rows.length) return <p className="text-sm text-muted-foreground">Aucun événement enregistré pour ces critères.</p>;
  return (
    <div className="space-y-2">
      <p className="font-mono text-xs text-muted-foreground">{data.total} événement(s) · lecture seule · journal non modifiable · cette consultation est elle-même journalisée</p>
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left font-mono text-xs uppercase text-muted-foreground">
            <tr><th className="p-2">Date (heure locale)</th><th className="p-2">Acteur</th><th className="p-2">Action</th><th className="p-2">Résultat</th><th className="p-2">Cible</th><th className="p-2">Motif</th><th className="p-2" /></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <Fragment key={r.id}>
                <tr className="border-t border-border align-top">
                  <td className="p-2 whitespace-nowrap">{new Date(r.at).toLocaleString("fr-FR")}</td>
                  <td className="p-2"><span className="font-mono text-xs" title={r.actor_id ?? ""}>{r.actor_id ? r.actor_id.slice(0, 8) : "—"}</span><br /><span className="text-xs text-muted-foreground">{r.actor_roles.join(", ") || "client"}</span></td>
                  <td className="p-2 font-mono text-xs">{r.action}</td>
                  <td className={"p-2 " + (r.result === "allowed" ? "text-primary" : "text-destructive")}>{r.result === "allowed" ? "autorisé" : "refusé"}</td>
                  <td className="p-2 font-mono text-xs">{r.target_type ? `${r.target_type}:${r.target_id ?? ""}` : "—"}</td>
                  <td className="p-2">{r.reason ?? "—"}</td>
                  <td className="p-2"><button type="button" className="text-xs underline" onClick={() => setOpen(open === r.id ? null : r.id)}>{open === r.id ? "Masquer" : "Détail"}</button></td>
                </tr>
                {open === r.id && (
                  <tr key={r.id + "-d"} className="bg-muted/30">
                    <td colSpan={7} className="p-3 font-mono text-xs">
                      <p>ID : {r.id}</p>
                      <p>Acteur : {r.actor_id ?? "—"}</p>
                      <p>Permission : {r.permission ?? "—"}</p>
                      <p>Avant : {r.before == null ? "—" : JSON.stringify(r.before)}</p>
                      <p>Après : {r.after == null ? "—" : JSON.stringify(r.after)}</p>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <button type="button" className="border border-border px-3 py-1 disabled:opacity-40" disabled={page === 0} onClick={() => setPage(page - 1)}>Précédent</button>
        <span className="font-mono text-xs">Page {page + 1} / {pages}</span>
        <button type="button" className="border border-border px-3 py-1 disabled:opacity-40" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Suivant</button>
      </div>
    </div>
  );
}
