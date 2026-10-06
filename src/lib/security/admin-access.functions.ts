/**
 * Contrôle d'accès serveur de l'espace /admin.
 * Session (requireSupabaseAuth) → suspension → has_permission() en base pour chaque permission.
 * Aucune donnée métier, aucun client privilégié.
 */
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { isSuspended } from "./guard.server";
import { ALL_PERMISSIONS } from "./permissions";
import { canSeeSection, type AdminSectionId } from "./admin-sections";

const SECTION = z.enum(["dashboard", "utilisateurs", "projets", "gates", "moteurs", "usage", "audit", "sante", "securite"]);

type Ctx = { supabase: Parameters<typeof isSuspended>[0]; userId: string };

async function effectivePermissions({ supabase, userId }: Ctx): Promise<{ suspended: boolean; permissions: string[] }> {
  if (await isSuspended(supabase, userId)) return { suspended: true, permissions: [] };
  const results = await Promise.all(
    ALL_PERMISSIONS.map(async (p) => {
      const { data, error } = await supabase.rpc("has_permission", { _user_id: userId, _perm: p });
      return !error && data === true ? p : null;
    }),
  );
  return { suspended: false, permissions: results.filter((p): p is string => p !== null) };
}

export const getAdminAccess = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const r = await effectivePermissions(context);
    return { ...r, allowed: !r.suspended && r.permissions.length > 0 };
  });

export const requireAdminSection = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ section: SECTION }).parse(d))
  .handler(async ({ data, context }) => {
    const r = await effectivePermissions(context);
    const ok = !r.suspended && canSeeSection(r.permissions, data.section as AdminSectionId);
    return { allowed: ok, suspended: r.suspended };
  });
