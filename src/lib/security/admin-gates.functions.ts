/**
 * Section Gates (lecture seule). gates.read, suspension et audit sont décidés en base
 * (admin_list_gate_projects). Les Gates viennent uniquement de l'API ConstructionAgent réelle,
 * en GET, au nom du propriétaire du projet. Aucune décision n'est possible ici.
 */
import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { toAdminGates, type AdminGateProject } from "./admin-gates";
import { redactBody } from "./redact.server";

const CA_ID = /^P_[0-9a-f]{32}$/;
const OWNER = /^[0-9a-f-]{36}$/i;

export const listAdminGates = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sb = context.supabase as any;
    const { data, error } = await sb.rpc("admin_list_gate_projects");
    if (error) throw new Error("Accès refusé.");
    const { data: can } = await sb.rpc("has_permission", { _user_id: context.userId, _perm: "gates.read" });
    if (can !== true) throw new Error("Accès refusé.");

    const base = process.env["CA_API_URL"];
    const key = process.env["CA_API_KEY"];
    const rows = (data ?? []) as { project_id: string; owner_id: string; stage: string; ca_project_id: string }[];

    const out: AdminGateProject[] = await Promise.all(rows.map(async (p) => {
      const meta = { project_id: p.project_id, owner_id: p.owner_id, stage: p.stage };
      if (!base || !key) return { ...meta, source: "non_configure" as const, gates: [] };
      if (!CA_ID.test(p.ca_project_id) || !OWNER.test(p.owner_id)) return { ...meta, source: "erreur" as const, gates: [] };
      try {
        const res = await fetch(`${base.replace(/\/+$/, "")}/v1/projects/${p.ca_project_id}/gates`, {
          method: "GET",
          headers: { Authorization: `Bearer ${key}`, "X-Owner-Id": p.owner_id },
          signal: AbortSignal.timeout(10_000),
        });
        if (!res.ok) return { ...meta, source: "erreur" as const, gates: [] };
        const body = JSON.parse(redactBody(await res.text()));
        return { ...meta, source: "ok" as const, gates: toAdminGates(body, p.owner_id) };
      } catch {
        return { ...meta, source: "injoignable" as const, gates: [] };
      }
    }));
    return out;
  });
