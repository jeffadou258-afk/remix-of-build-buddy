/**
 * Section Utilisateurs (lecture seule). La permission users.read, la suspension
 * et l'audit sont vérifiés dans la base par admin_list_users().
 */
import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { toAdminUserRow } from "./admin-users";

export const listAdminUsers = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { data, error } = await (context.supabase as any).rpc("admin_list_users");
    if (error) throw new Error("Accès refusé.");
    return ((data ?? []) as Record<string, unknown>[]).map(toAdminUserRow);
  });
