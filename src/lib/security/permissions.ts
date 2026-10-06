/**
 * Socle de sécurité Admin v1 — référence côté code.
 * La source d'autorité reste la base (tables user_roles / role_permissions,
 * fonction has_permission) : ce module ne décide jamais seul d'un accès.
 * Aucune logique métier ConstructionAgent ici.
 */
export type AppRole = "user" | "support" | "ops" | "finance" | "admin" | "auditor";

export const ROLE_LABELS: Record<AppRole, string> = {
  user: "Client",
  support: "Assistance",
  ops: "Exploitation",
  finance: "Finance",
  admin: "Admin",
  auditor: "Auditeur",
};

export type Permission =
  | "users.read" | "users.suspend" | "roles.manage"
  | "projects.read_meta" | "projects.read_content" | "projects.archive"
  | "activity.read" | "jobs.read" | "jobs.retry" | "jobs.cancel"
  | "engines.read" | "engines.toggle"
  | "gates.read" | "gates.unblock_technical"
  | "usage.read" | "costs.read" | "providers.read" | "providers.manage"
  | "errors.read" | "health.read" | "audit.read" | "security.read" | "security.manage";

export const ALL_PERMISSIONS: readonly Permission[] = [
  "users.read", "users.suspend", "roles.manage",
  "projects.read_meta", "projects.read_content", "projects.archive",
  "activity.read", "jobs.read", "jobs.retry", "jobs.cancel",
  "engines.read", "engines.toggle",
  "gates.read", "gates.unblock_technical",
  "usage.read", "costs.read", "providers.read", "providers.manage",
  "errors.read", "health.read", "audit.read", "security.read", "security.manage",
];

/** Copie exacte de la matrice §1.2 insérée dans la migration (role_permissions). */
export const ROLE_PERMISSIONS: Record<AppRole, readonly Permission[]> = {
  user: [],
  support: ["users.read", "projects.read_meta", "projects.read_content", "activity.read", "jobs.read", "jobs.retry", "gates.read", "errors.read", "health.read"],
  ops: ["projects.read_meta", "activity.read", "jobs.read", "jobs.retry", "jobs.cancel", "engines.read", "engines.toggle", "gates.read", "gates.unblock_technical", "usage.read", "providers.read", "errors.read", "health.read"],
  finance: ["users.read", "projects.read_meta", "usage.read", "costs.read", "providers.read"],
  admin: ["users.read", "users.suspend", "roles.manage", "projects.read_meta", "projects.read_content", "projects.archive", "activity.read", "jobs.read", "jobs.retry", "jobs.cancel", "engines.read", "engines.toggle", "gates.read", "gates.unblock_technical", "usage.read", "costs.read", "providers.read", "providers.manage", "errors.read", "health.read", "audit.read", "security.read", "security.manage"],
  auditor: ["activity.read", "gates.read", "audit.read", "security.read"],
};

/** Interdits §1.3 : n'existent comme permission pour AUCUN rôle, y compris admin. */
export const FORBIDDEN_FOR_ALL = [
  "gates.decide_on_behalf",
  "inputs.edit_user_provided_of_other",
  "inputs.mark_technically_validated",
  "audit.modify",
  "secrets.read",
  "users.impersonate",
] as const;

export function roleHas(roles: readonly AppRole[], perm: string): boolean {
  if ((FORBIDDEN_FOR_ALL as readonly string[]).includes(perm)) return false;
  return roles.some((r) => (ROLE_PERMISSIONS[r] as readonly string[]).includes(perm));
}

/** Décision d'un Gate métier : seul le propriétaire du projet, jamais un autre compte quel que soit son rôle. */
export function canDecideGate(callerId: string, projectOwnerId: string): boolean {
  return !!callerId && callerId === projectOwnerId;
}

export function isGateDecisionPath(sub: string): boolean {
  return /^gates\/[^/]+\/decision\/?$/.test(sub.replace(/^\/+/, ""));
}

/** Modification des données fournies par un client : seul ce client. */
export function canEditClientData(callerId: string, projectOwnerId: string): boolean {
  return !!callerId && callerId === projectOwnerId;
}
