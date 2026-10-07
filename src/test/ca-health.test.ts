import { describe, expect, it } from "vitest";

// Health check réel de l'API ConstructionAgent (Render). Ignoré sans configuration serveur.
const base = process.env["CA_API_URL"];
const key = process.env["CA_API_KEY"];

describe.skipIf(!base || !key)("ConstructionAgent API production", () => {
  it("GET /v1/health : OK, v1, 13 moteurs, 2 Gates", async () => {
    const res = await fetch(base!.replace(/\/+$/, "") + "/v1/health", { headers: { Authorization: `Bearer ${key}` } });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe("OK");
    expect(body.api).toBe("v1");
    expect(body.engines).toHaveLength(13);
    expect(body.gates).toEqual(["design", "structural_concept"]);
    expect(JSON.stringify(body)).not.toContain(key!);
  }, 60_000);

  it("refuse un appel sans clé", async () => {
    const res = await fetch(base!.replace(/\/+$/, "") + "/v1/projects");
    expect(res.status).toBe(401);
  }, 60_000);
});
