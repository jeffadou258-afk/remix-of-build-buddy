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

const ROLE = z.enum(["user", "support", "ops", "finance", "admin", "auditor"]);
const reason = z.string().trim().min(10, "Motif de 10 caractères minimum").max(1000);

type RpcResult = { ok: boolean; error?: string; [k: string]: unknown };

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
  .inputValidator((d) => z.object({ limit: z.number().int().min(1).max(500).default(100) }).parse(d ?? {}))
  .handler(async ({ data, context }) => {
    await requirePermission(context.supabase, context.userId, "audit.read", "audit.list", requestMeta(getRequest()));
    const { data: rows, error } = await context.supabase
      .from("admin_audit_log").select("*").order("at", { ascending: false }).limit(data.limit);
    if (error) throw new Error("Lecture du journal impossible.");
    return redactSecrets(rows ?? [], serverSecretValues());
  });
