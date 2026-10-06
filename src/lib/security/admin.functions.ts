/**
 * Fonctions serveur sensibles (sans interface en v1).
 * Toutes : session (requireSupabaseAuth) → permission en base → audit → action, sous RLS de l'appelant.
 */
import { createServerFn } from "@tanstack/react-start";
import { getRequest } from "@tanstack/react-start/server";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { requirePermission, requestMeta, isSuspended } from "./guard.server";
import { redactSecrets, serverSecretValues } from "./redact.server";
import { AUDIT_SELECT, AUDIT_PAGE_SIZE, cleanAuditFilter, endOfDay } from "./admin-audit";

const ROLE = z.enum(["user", "support", "ops", "finance", "admin", "auditor"]);
const reason = z.string().trim().min(10, "Motif de 10 caractères minimum").max(1000);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RpcResult = { ok: boolean; error?: string } & Record<string, any>;

function unwrap(r: { data: unknown; error: { message: string } | null }): RpcResult {
  if (r.error) throw new Error("Opération refusée.");
  const d = r.data as RpcResult;
  if (!d?.ok) throw new Error(d?.error === "forbidden" ? "Accès refusé." : (d?.error ?? "Opération refusée."));
  return redactSecrets(d, serverSecretValues());
}

async function notSuspended(sb: Parameters<typeof isSuspended>[0], uid: string) {
  if (await isSuspended(sb, uid)) throw new Error("Compte suspendu.");
}

export const requestProjectContentAccess = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ projectId: z.string().uuid(), reason }).parse(d))
  .handler(async ({ data, context }) => {
    await notSuspended(context.supabase, context.userId);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return unwrap(await (context.supabase as any).rpc("request_project_access", { _project_id: data.projectId, _reason: data.reason }));
  });

export const readProjectContentAudited = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ projectId: z.string().uuid() }).parse(d))
  .handler(async ({ data, context }) => {
    await notSuspended(context.supabase, context.userId);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return unwrap(await (context.supabase as any).rpc("read_project_content", { _project_id: data.projectId }));
  });

export const grantRole = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ userId: z.string().uuid(), role: ROLE, reason }).parse(d))
  .handler(async ({ data, context }) => {
    await notSuspended(context.supabase, context.userId);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return unwrap(await (context.supabase as any).rpc("grant_role", { _target: data.userId, _role: data.role, _reason: data.reason }));
  });

export const revokeRole = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ userId: z.string().uuid(), role: ROLE, reason }).parse(d))
  .handler(async ({ data, context }) => {
    await notSuspended(context.supabase, context.userId);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return unwrap(await (context.supabase as any).rpc("revoke_role", { _target: data.userId, _role: data.role, _reason: data.reason }));
  });

export const listAuditLog = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => cleanAuditFilter((d ?? {}) as Record<string, unknown>))
  .handler(async ({ data, context }) => {
    // Permission vérifiée en base + consultation journalisée (refus compris) ; puis lecture sous RLS (audit.read).
    await requirePermission(context.supabase, context.userId, "audit.read", "audit.list", requestMeta(getRequest()));
    let q = context.supabase.from("admin_audit_log").select(AUDIT_SELECT, { count: "exact" });
    if (data.action) q = q.eq("action", data.action);
    if (data.result) q = q.eq("result", data.result);
    if (data.actorId) q = q.eq("actor_id", data.actorId);
    if (data.from) q = q.gte("at", `${data.from}T00:00:00Z`);
    if (data.to) q = q.lte("at", endOfDay(data.to));
    const start = data.page * AUDIT_PAGE_SIZE;
    const { data: rows, error, count } = await q.order("at", { ascending: false }).range(start, start + AUDIT_PAGE_SIZE - 1);
    if (error) throw new Error("Lecture du journal impossible.");
    // Actions réellement présentes dans le journal (pour le filtre).
    const { data: acts } = await context.supabase.from("admin_audit_log").select("action").limit(5000);
    const actions = [...new Set(((acts ?? []) as { action: string }[]).map((a) => a.action))].sort();
    return redactSecrets({ rows: rows ?? [], total: count ?? 0, page: data.page, pageSize: AUDIT_PAGE_SIZE, actions }, serverSecretValues());
  });
