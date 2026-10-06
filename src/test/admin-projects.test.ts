import { describe, it, expect } from "vitest";
import { toAdminProjectRow, ADMIN_PROJECT_FIELDS } from "@/lib/security/admin-projects";
import { ROLE_PERMISSIONS } from "@/lib/security/permissions";
import { canSeeSection } from "@/lib/security/admin-sections";

describe("Admin — Projets (métadonnées, lecture seule)", () => {
  it("ne garde jamais le contenu client", () => {
    const row = toAdminProjectRow({
      project_id: "p", owner_id: "u", client_type: "particulier", stage: "programme", created_at: "a", updated_at: "b", ca_linked: true,
      title: "Villa", messages: [{ role: "user", content: "secret" }], inputs: { x: 1 }, building_model: {}, ca_project_id: "ca_1",
    });
    expect(Object.keys(row).sort()).toEqual([...ADMIN_PROJECT_FIELDS].sort());
    expect(JSON.stringify(row)).not.toMatch(/Villa|secret|ca_1/);
  });
  it("liaison ConstructionAgent jamais supposée", () => {
    expect(toAdminProjectRow({ project_id: "p", owner_id: "u" }).ca_linked).toBe(false);
  });
  it("seul projects.read_meta ouvre la section ; client et finance refusés", () => {
    expect(canSeeSection(ROLE_PERMISSIONS.user, "projets")).toBe(false);
    expect(canSeeSection(["projects.read_content"], "projets")).toBe(false);
    expect(canSeeSection(["projects.read_meta"], "projets")).toBe(true);
    expect(canSeeSection(ROLE_PERMISSIONS.admin, "projets")).toBe(true);
  });
});
