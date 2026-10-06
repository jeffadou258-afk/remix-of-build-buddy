/**
 * Forme publique d'une ligne « Utilisateurs » de l'Admin (lecture seule).
 * Liste blanche stricte : tout autre champ renvoyé par la base est ignoré.
 */
export const ADMIN_USER_FIELDS = ["user_id", "email", "created_at", "last_sign_in_at", "roles", "status", "project_count"] as const;

export type AdminUserRow = {
  user_id: string;
  email: string | null;
  created_at: string;
  last_sign_in_at: string | null;
  roles: string[];
  status: "active" | "suspended";
  project_count: number;
};

export function toAdminUserRow(r: Record<string, unknown>): AdminUserRow {
  return {
    user_id: String(r.user_id),
    email: typeof r.email === "string" ? r.email : null,
    created_at: String(r.created_at),
    last_sign_in_at: typeof r.last_sign_in_at === "string" ? r.last_sign_in_at : null,
    roles: Array.isArray(r.roles) ? r.roles.map(String) : [],
    status: r.status === "suspended" ? "suspended" : "active",
    project_count: Number(r.project_count ?? 0),
  };
}
