import { describe, expect, it } from "vitest";
import { isAllowed, upstreamPath } from "@/lib/ca/allowlist";

describe("relais ConstructionAgent — liste blanche /v1", () => {
  it("laisse passer le parcours vertical", () => {
    for (const [m, s] of [["GET", ""], ["POST", "messages"], ["GET", "inputs"], ["PATCH", "inputs"], ["POST", "rooms"], ["POST", "runs"], ["GET", "gates"], ["GET", "state"]]) {
      expect(isAllowed(m!, s!)).toBe(true);
    }
  });
  it("refuse les adresses non branchées ou inexistantes", () => {
    expect(isAllowed("POST", "gates/design/decision")).toBe(false); // décisions pas encore branchées
    expect(isAllowed("GET", "memory")).toBe(false);
    expect(isAllowed("DELETE", "")).toBe(false);
    expect(isAllowed("GET", "../projects")).toBe(false);
    expect(isAllowed("GET", "admin")).toBe(false);
  });
  it("refuse un identifiant ConstructionAgent mal formé", () => {
    expect(() => upstreamPath("../x", "state")).toThrow();
    expect(upstreamPath("P_" + "a".repeat(32), "runs")).toBe(`/v1/projects/P_${"a".repeat(32)}/runs`);
  });
});
