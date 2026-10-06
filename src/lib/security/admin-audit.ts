/**
 * Consultation du journal d'audit (lecture seule) : colonnes affichées et filtres.
 * IP et user-agent ne sont jamais renvoyés à l'interface.
 */
import { z } from "zod";

export const AUDIT_COLUMNS = ["id", "at", "actor_id", "actor_roles", "action", "permission", "result", "target_type", "target_id", "reason", "before", "after"] as const;
export const AUDIT_SELECT = AUDIT_COLUMNS.join(",");
export const AUDIT_PAGE_SIZE = 50;

export const auditFilterSchema = z.object({
  action: z.string().trim().regex(/^[a-z_.]{1,100}$/).optional(),
  result: z.enum(["allowed", "denied"]).optional(),
  actorId: z.string().uuid().optional(),
  from: z.string().date().optional(),
  to: z.string().date().optional(),
  page: z.number().int().min(0).max(1000).default(0),
});
export type AuditFilter = z.infer<typeof auditFilterSchema>;

/** Supprime les filtres vides venant du formulaire avant validation. */
export function cleanAuditFilter(raw: Record<string, unknown>): AuditFilter {
  const o: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(raw)) if (v !== "" && v !== undefined && v !== null) o[k] = v;
  return auditFilterSchema.parse(o);
}

/** Borne de fin inclusive : jusqu'à la fin de la journée choisie (UTC). */
export function endOfDay(d: string): string {
  return `${d}T23:59:59.999Z`;
}
