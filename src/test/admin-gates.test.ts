import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { toAdminGates } from "@/lib/security/admin-gates";
import { canSeeSection } from "@/lib/security/admin-sections";
import { ROLE_PERMISSIONS } from "@/lib/security/permissions";

const OWNER = "11111111-1111-1111-1111-111111111111";
// Forme réelle de pipeline.py (initial_gates / decide)
const body = {
  gates: {
    programming: { status: "APPROVED", opened_at: "2026-10-06T10:00:00Z", decision: { decision: "approve", by: OWNER, at: "2026-10-06T11:00:00Z", comment: "COMMENTAIRE_PRIVE", variant_id: "V2" } },
    design: { status: "OPEN", opened_at: "2026-10-06T12:00:00Z", decision: null },
    plans: { status: "NOT_REACHED", opened_at: null, decision: null },
  },
};

describe("Admin — Gates (lecture seule)", () => {
  it("garde l'état, les dates et la décision, sans commentaire ni variante ni décideur", () => {
    const rows = toAdminGates(body, OWNER);
    expect(rows.map((r) => r.status)).toEqual(["APPROVED", "OPEN", "NOT_REACHED"]);
    expect(rows[0]).toEqual({ gate: "programming", status: "APPROVED", opened_at: "2026-10-06T10:00:00Z", decision: "approve", decided_at: "2026-10-06T11:00:00Z", decided_by_owner: true });
    expect(JSON.stringify(rows)).not.toMatch(/COMMENTAIRE_PRIVE|V2|1111/);
  });
  it("statut inattendu affiché INCONNU, réponse vide = aucune Gate inventée", () => {
    expect(toAdminGates({ gates: { x: { status: "WEIRD" } } }, OWNER)[0]!.status).toBe("INCONNU");
    expect(toAdminGates({}, OWNER)).toEqual([]);
    expect(toAdminGates(null, OWNER)).toEqual([]);
  });
  it("gates.read requis ; client refusé", () => {
    expect(canSeeSection(ROLE_PERMISSIONS.user, "gates")).toBe(false);
    expect(canSeeSection(["gates.read"], "gates")).toBe(true);
  });
  it("le module Admin Gates n'appelle jamais une décision ni une méthode d'écriture", () => {
    const src = readFileSync("src/lib/security/admin-gates.functions.ts", "utf8") + readFileSync("src/routes/_authenticated.admin.gates.tsx", "utf8");
    expect(src).not.toMatch(/\/decision|method:\s*"(POST|PATCH|PUT|DELETE)"|Approuver|Refuser/);
  });
});
