/**
 * Section Utilisateurs (lecture seule). La permission users.read, la suspension
 * et l'audit (autorisé comme refusé) sont décidés dans la base par admin_list_users().
 */
import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { toAdminUserRow } from "./admin-users";

export const listAdminUsers = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sb = context.supabase as any;
    const { data, error } = await sb.rpc("admin_list_users");
    if (error) throw new Error("Accès refusé.");
    // En cas de refus la base renvoie une liste vide (refus journalisé) : on le confirme en base.
    const { data: can } = await sb.rpc("has_permission", { _user_id: context.userId, _perm: "users.read" });
    if (can !== true) throw new Error("Accès refusé.");
    return ((data ?? []) as Record<string, unknown>[]).map(toAdminUserRow);
  });
