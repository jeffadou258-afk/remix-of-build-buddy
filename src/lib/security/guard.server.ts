/**
 * Vérification côté serveur §1.4 : session → compte non suspendu → permission (base) → audit.
 * Le rôle est toujours lu depuis la base via has_permission(), jamais depuis le navigateur.
 * Le client utilisé est celui de l'appelant (RLS), jamais le client privilégié.
 */
import type { SupabaseClient } from "@supabase/supabase-js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Sb = SupabaseClient<any, any, any>;

export type AuditMeta = { targetType?: string; targetId?: string; reason?: string; ip?: string; userAgent?: string; requestId?: string };

export async function isSuspended(sb: Sb, userId: string): Promise<boolean> {
  const { data } = await sb.from("account_status").select("status").eq("user_id", userId).maybeSingle();
  return (data as { status?: string } | null)?.status === "suspended";
}

export async function audit(sb: Sb, action: string, permission: string | null, result: "allowed" | "denied" | "error", m: AuditMeta = {}) {
  await sb.rpc("log_admin_action", {
    _action: action, _permission: permission, _target_type: m.targetType ?? null, _target_id: m.targetId ?? null,
    _reason: m.reason ?? null, _result: result, _ip: m.ip ?? null, _user_agent: m.userAgent ?? null, _request_id: m.requestId ?? null,
  });
}

export class PermissionError extends Error {
  constructor(public status: 401 | 403, message: string) { super(message); }
}

export async function requirePermission(sb: Sb, userId: string, perm: string, action: string, m: AuditMeta = {}) {
  if (!userId) throw new PermissionError(401, "Connexion requise.");
  if (await isSuspended(sb, userId)) {
    await audit(sb, action, perm, "denied", { ...m, reason: "compte suspendu" });
    throw new PermissionError(403, "Compte suspendu.");
  }
  const { data, error } = await sb.rpc("has_permission", { _user_id: userId, _perm: perm });
  if (error || data !== true) {
    await audit(sb, action, perm, "denied", m);
    throw new PermissionError(403, "Accès refusé.");
  }
  await audit(sb, action, perm, "allowed", m);
}

export function requestMeta(req: Request | undefined): Pick<AuditMeta, "ip" | "userAgent" | "requestId"> {
  if (!req) return {};
  return {
    ip: req.headers.get("cf-connecting-ip") ?? req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? undefined,
    userAgent: req.headers.get("user-agent") ?? undefined,
    requestId: req.headers.get("cf-ray") ?? undefined,
  };
}
