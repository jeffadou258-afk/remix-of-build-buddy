import { describe, it, expect } from "vitest";
import { AUDIT_COLUMNS, cleanAuditFilter, endOfDay } from "@/lib/security/admin-audit";

describe("Admin — Audit (lecture seule)", () => {
  it("n'envoie jamais IP ni user-agent à l'interface", () => {
    expect(AUDIT_COLUMNS).not.toContain("ip");
    expect(AUDIT_COLUMNS).not.toContain("user_agent");
    expect(AUDIT_COLUMNS).not.toContain("request_id");
  });
  it("affiche date, acteur, action, résultat, cible et motif", () => {
    for (const c of ["at", "actor_id", "action", "result", "target_type", "target_id", "reason"]) expect(AUDIT_COLUMNS).toContain(c);
  });
  it("filtres vides ignorés, page 0 par défaut", () => {
    expect(cleanAuditFilter({ action: "", result: "", actorId: "" })).toEqual({ page: 0 });
  });
  it("rejette un résultat, un acteur ou une action hors format", () => {
    expect(() => cleanAuditFilter({ result: "ok" })).toThrow();
    expect(() => cleanAuditFilter({ actorId: "abc" })).toThrow();
    expect(() => cleanAuditFilter({ action: "x'; drop" })).toThrow();
  });
  it("la date de fin inclut toute la journée", () => {
    expect(endOfDay("2026-10-06")).toBe("2026-10-06T23:59:59.999Z");
  });
});
