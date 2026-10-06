/**
 * Sections de l'espace /admin et permission requise.
 * Sert à l'affichage et aux tests ; l'accès est toujours décidé côté serveur
 * (admin-access.functions.ts → has_permission en base).
 */
import { ALL_PERMISSIONS, FORBIDDEN_FOR_ALL, type Permission } from "./permissions";

export type AdminSectionId =
  | "dashboard" | "utilisateurs" | "projets" | "gates" | "moteurs"
  | "usage" | "audit" | "sante" | "securite";

export type AdminSectionDef = {
  id: AdminSectionId;
  label: string;
  path: string;
  /** Au moins une de ces permissions est requise. */
  anyOf: readonly Permission[];
  description: string;
};

export const ADMIN_SECTIONS: readonly AdminSectionDef[] = [
  { id: "dashboard", label: "Dashboard", path: "/admin", anyOf: ALL_PERMISSIONS, description: "Vue d'ensemble de l'espace d'administration." },
  { id: "utilisateurs", label: "Utilisateurs", path: "/admin/utilisateurs", anyOf: ["users.read"], description: "Comptes, rôles et statuts." },
  { id: "projets", label: "Projets", path: "/admin/projets", anyOf: ["projects.read_meta"], description: "Métadonnées des projets uniquement. Aucun contenu client sans accès motivé et audité." },
  { id: "gates", label: "Gates", path: "/admin/gates", anyOf: ["gates.read"], description: "Lecture seule. Les décisions de Gates appartiennent au client propriétaire." },
  { id: "moteurs", label: "Moteurs", path: "/admin/moteurs", anyOf: ["engines.read"], description: "État des 13 moteurs ConstructionAgent." },
  { id: "usage", label: "Usage & coûts", path: "/admin/usage", anyOf: ["usage.read", "costs.read"], description: "Consommation, coûts et providers IA." },
  { id: "audit", label: "Audit", path: "/admin/audit", anyOf: ["audit.read"], description: "Journal d'audit immuable (lecture seule)." },
  { id: "sante", label: "Santé système", path: "/admin/sante", anyOf: ["health.read"], description: "Disponibilité des services et erreurs." },
  { id: "securite", label: "Sécurité", path: "/admin/securite", anyOf: ["security.read"], description: "Événements et réglages de sécurité." },
];

export function sectionById(id: AdminSectionId): AdminSectionDef {
  return ADMIN_SECTIONS.find((s) => s.id === id)!;
}

export function canSeeSection(perms: readonly string[], id: AdminSectionId): boolean {
  const s = sectionById(id);
  return s.anyOf.some((p) => perms.includes(p) && !(FORBIDDEN_FOR_ALL as readonly string[]).includes(p));
}

export function visibleSections(perms: readonly string[]): AdminSectionDef[] {
  return ADMIN_SECTIONS.filter((s) => canSeeSection(perms, s.id));
}
