/**
 * Vérification côté serveur §1.4 : session → compte non suspendu → permission (base) → audit.
 * Le rôle est toujours lu depuis la base via has_permission(), jamais depuis le navigateur.
 * Le client utilisé est celui de l'appelant (RLS), jamais le client privilégié.
 */
import type { SupabaseClient } from "@supabase/supabase-js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Sb = SupabaseClient<any, any, any>;

export type AuditMeta = { targetType?: string | undefined; targetId?: string | undefined; reason?: string | undefined; ip?: string | undefined; userAgent?: string | undefined; requestId?: string | undefined };

export async function isSuspended(sb: Sb, userId: string): Promise<boolean> {
  const { data } = await sb.from("account_status").select("status").eq("user_id", userId).maybeSingle();
  return (data as { status?: string } | null)?.status === "suspended";
}

/** Actions que le serveur applicatif peut journaliser ; la base refuse toute autre. */
export const LOGGABLE_ACTIONS = ["audit.list", "gates.decide", "admin.access_denied"] as const;
export type LoggableAction = (typeof LOGGABLE_ACTIONS)[number];

/**
 * Journalise via log_security_event : la base fixe elle-même permission, résultat,
 * motif et avant/après. L'appelant ne transmet que l'action et la cible.
 */
export async function audit(sb: Sb, action: LoggableAction, m: Pick<AuditMeta, "targetType" | "targetId" | "ip" | "userAgent" | "requestId"> = {}) {
  // Les échecs d'écriture ne doivent jamais transformer un refus en accès : on ignore l'erreur.
  await sb.rpc("log_security_event", {
    _action: action, _target_type: m.targetType ?? null, _target_id: m.targetId ?? null,
    _ip: m.ip ?? null, _user_agent: m.userAgent ?? null, _request_id: m.requestId ?? null,
  });
}

export class PermissionError extends Error {
  constructor(public status: 401 | 403, message: string) { super(message); }
}

export async function requirePermission(sb: Sb, userId: string, perm: string, action: LoggableAction, m: AuditMeta = {}) {
  if (!userId) throw new PermissionError(401, "Connexion requise.");
  const suspended = await isSuspended(sb, userId);
  const { data, error } = suspended ? { data: false, error: null } : await sb.rpc("has_permission", { _user_id: userId, _perm: perm });
  await audit(sb, action, m);
  if (suspended) throw new PermissionError(403, "Compte suspendu.");
  if (error || data !== true) throw new PermissionError(403, "Accès refusé.");
}

export function requestMeta(req: Request | undefined): Pick<AuditMeta, "ip" | "userAgent" | "requestId"> {
  if (!req) return {};
  return {
    ip: req.headers.get("cf-connecting-ip") ?? req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? undefined,
    userAgent: req.headers.get("user-agent") ?? undefined,
    requestId: req.headers.get("cf-ray") ?? undefined,
  };
}
