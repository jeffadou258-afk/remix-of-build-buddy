import { describe, expect, it } from "vitest";
import { FORBIDDEN_FOR_ALL, ROLE_PERMISSIONS, roleHas, type AppRole } from "@/lib/security/permissions";

const ALL: AppRole[] = ["user", "support", "ops", "finance", "admin", "auditor"];

describe("matrice des permissions §1.2", () => {
  it("un client n'a aucune permission Admin", () => {
    expect(ROLE_PERMISSIONS.user).toEqual([]);
  });
  it("finance et exploitation n'ont pas accès au contenu des projets", () => {
    expect(roleHas(["finance"], "projects.read_content")).toBe(false);
    expect(roleHas(["ops"], "projects.read_content")).toBe(false);
  });
  it("assistance et admin peuvent demander un accès audité au contenu", () => {
    expect(roleHas(["support"], "projects.read_content")).toBe(true);
    expect(roleHas(["admin"], "projects.read_content")).toBe(true);
  });
  it("l'auditeur est en lecture seule", () => {
    for (const p of ROLE_PERMISSIONS.auditor) expect(p.endsWith(".read")).toBe(true);
  });
  it("seul admin gère les rôles", () => {
    expect(ALL.filter((r) => roleHas([r], "roles.manage"))).toEqual(["admin"]);
  });
});

describe("interdits §1.3 pour tous, y compris admin", () => {
  it.each(FORBIDDEN_FOR_ALL)("%s refusé à tous les rôles cumulés", (perm) => {
    expect(roleHas(ALL, perm)).toBe(false);
  });
});
