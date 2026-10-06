/**
 * Section Projets (lecture seule, métadonnées). Permission projects.read_meta,
 * suspension et audit décidés dans la base par admin_list_projects().
 */
import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { toAdminProjectRow } from "./admin-projects";

export const listAdminProjects = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sb = context.supabase as any;
    const { data, error } = await sb.rpc("admin_list_projects");
    if (error) throw new Error("Accès refusé.");
    const { data: can } = await sb.rpc("has_permission", { _user_id: context.userId, _perm: "projects.read_meta" });
    if (can !== true) throw new Error("Accès refusé.");
    return ((data ?? []) as Record<string, unknown>[]).map(toAdminProjectRow);
  });
