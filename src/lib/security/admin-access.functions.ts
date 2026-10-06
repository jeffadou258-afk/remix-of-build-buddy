/**
 * Contrôle d'accès serveur de l'espace /admin.
 * Session (requireSupabaseAuth) → suspension → has_permission() en base pour chaque permission.
 * Aucune donnée métier, aucun client privilégié.
 */
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { getRequest } from "@tanstack/react-start/server";
import { isSuspended, audit, requestMeta } from "./guard.server";
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
  return { suspended: false, permissions: results.filter((p): p is NonNullable<typeof p> => p !== null) as string[] };
}

export const getAdminAccess = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ enter: z.boolean().optional() }).optional().parse(d))
  .handler(async ({ data, context }) => {
    const r = await effectivePermissions(context);
    const allowed = !r.suspended && r.permissions.length > 0;
    // Refus journalisé uniquement à l'entrée réelle dans /admin (pas pour l'affichage du lien d'en-tête).
    if (!allowed && data?.enter) await logDenied(context, "dashboard");
    return { ...r, allowed };
  });

async function logDenied(context: Ctx, section: AdminSectionId) {
  let meta = {};
  try { meta = requestMeta(getRequest()); } catch { /* pas de requête */ }
  await audit(context.supabase, "admin.access_denied", { targetType: "admin_section", targetId: section, ...meta });
}

export const requireAdminSection = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ section: SECTION }).parse(d))
  .handler(async ({ data, context }) => {
    const r = await effectivePermissions(context);
    const ok = !r.suspended && canSeeSection(r.permissions, data.section as AdminSectionId);
    if (!ok) await logDenied(context, data.section as AdminSectionId);
    return { allowed: ok, suspended: r.suspended };
  });
