import { describe, it, expect } from "vitest";
import { toAdminUserRow, ADMIN_USER_FIELDS } from "@/lib/security/admin-users";
import { ROLE_PERMISSIONS } from "@/lib/security/permissions";
import { canSeeSection } from "@/lib/security/admin-sections";

describe("Admin — Utilisateurs (lecture seule)", () => {
  it("ne garde que les champs autorisés", () => {
    const row = toAdminUserRow({
      user_id: "u", email: "a@b.c", created_at: "2026-01-01", last_sign_in_at: null, roles: ["admin"], status: "active", project_count: 2,
      encrypted_password: "x", phone: "+225", raw_user_meta_data: { a: 1 }, confirmation_token: "t",
    });
    expect(Object.keys(row).sort()).toEqual([...ADMIN_USER_FIELDS].sort());
  });
  it("statut inconnu affiché comme actif, jamais inventé suspendu", () => {
    expect(toAdminUserRow({ user_id: "u", created_at: "x", status: "weird" }).status).toBe("active");
    expect(toAdminUserRow({ user_id: "u", created_at: "x", status: "suspended" }).status).toBe("suspended");
  });
  it("client sans rôle et finance sans users.read selon la matrice", () => {
    expect(canSeeSection(ROLE_PERMISSIONS.user, "utilisateurs")).toBe(false);
    expect(canSeeSection(ROLE_PERMISSIONS.auditor, "utilisateurs")).toBe(false);
    expect(canSeeSection(ROLE_PERMISSIONS.support, "utilisateurs")).toBe(true);
    expect(canSeeSection(ROLE_PERMISSIONS.admin, "utilisateurs")).toBe(true);
  });
});
