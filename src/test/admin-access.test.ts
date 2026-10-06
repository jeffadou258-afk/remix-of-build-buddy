import { describe, it, expect } from "vitest";
import { ADMIN_SECTIONS, visibleSections, canSeeSection } from "@/lib/security/admin-sections";
import { ROLE_PERMISSIONS, FORBIDDEN_FOR_ALL, ALL_PERMISSIONS } from "@/lib/security/permissions";

const ids = (perms: readonly string[]) => visibleSections(perms).map((s) => s.id);

describe("espace /admin — sections par rôle", () => {
  it("client sans rôle : aucune section", () => {
    expect(ids(ROLE_PERMISSIONS.user)).toEqual([]);
  });
  it("auditeur : Dashboard, Gates, Audit, Sécurité uniquement", () => {
    expect(ids(ROLE_PERMISSIONS.auditor)).toEqual(["dashboard", "gates", "audit", "securite"]);
  });
  it("finance : pas d'accès Audit ni Sécurité", () => {
    expect(canSeeSection(ROLE_PERMISSIONS.finance, "audit")).toBe(false);
    expect(canSeeSection(ROLE_PERMISSIONS.finance, "securite")).toBe(false);
    expect(canSeeSection(ROLE_PERMISSIONS.finance, "usage")).toBe(true);
  });
  it("admin : les 9 sections", () => {
    expect(ids(ROLE_PERMISSIONS.admin)).toHaveLength(9);
  });
  it("admin possède les 23 permissions", () => {
    expect(ALL_PERMISSIONS).toHaveLength(23);
    expect([...ROLE_PERMISSIONS.admin].sort()).toEqual([...ALL_PERMISSIONS].sort());
  });
  it("aucune section n'exige ou n'ouvre une permission interdite", () => {
    for (const s of ADMIN_SECTIONS) for (const p of s.anyOf) expect((FORBIDDEN_FOR_ALL as readonly string[]).includes(p)).toBe(false);
    expect(ids([...FORBIDDEN_FOR_ALL])).toEqual([]);
  });
  it("Projets n'exige que les métadonnées, pas le contenu client", () => {
    expect(ADMIN_SECTIONS.find((s) => s.id === "projets")!.anyOf).toEqual(["projects.read_meta"]);
  });
});
