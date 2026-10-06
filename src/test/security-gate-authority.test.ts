import { describe, expect, it } from "vitest";
import { canDecideGate, canEditClientData, isGateDecisionPath } from "@/lib/security/permissions";
import { isAllowed } from "@/lib/ca/allowlist";

const OWNER = "11111111-1111-1111-1111-111111111111";
const ADMIN = "22222222-2222-2222-2222-222222222222";

describe("autorité sur les Gates et les données client", () => {
  it("seul le propriétaire décide d'un Gate", () => {
    expect(canDecideGate(OWNER, OWNER)).toBe(true);
    expect(canDecideGate(ADMIN, OWNER)).toBe(false);
    expect(canDecideGate("", OWNER)).toBe(false);
  });
  it("reconnaît les adresses de décision de Gate", () => {
    expect(isGateDecisionPath("gates/G1/decision")).toBe(true);
    expect(isGateDecisionPath("gates")).toBe(false);
  });
  it("la décision de Gate reste fermée dans le relais en v1", () => {
    expect(isAllowed("POST", "gates/G1/decision")).toBe(false);
  });
  it("un autre compte ne modifie pas les données fournies par un client", () => {
    expect(canEditClientData(ADMIN, OWNER)).toBe(false);
    expect(canEditClientData(OWNER, OWNER)).toBe(true);
  });
});
