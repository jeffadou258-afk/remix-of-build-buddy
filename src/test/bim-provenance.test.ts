import { describe, expect, it } from "vitest";
import { extractModel } from "@/lib/bim/schema";

const block = (o: unknown) => "```bim\n" + JSON.stringify(o) + "\n```";

describe("maquette : aucune donnée présentée comme validée", () => {
  it("un élément sans statut est une hypothèse", () => {
    const m = extractModel(block({ levels: [{ id: "rdc", name: "RDC", elevation: 0, height: 3 }] }))!;
    expect(m.levels[0]!.status).toBe("hypothese");
  });
  it("le modèle extrait n'est jamais validé, même si l'agent l'affirme", () => {
    const m = extractModel(block({ validated: true, levels: [{ id: "rdc", name: "RDC" }] }))!;
    expect(m.validated).toBe(false);
  });
  it("signale les valeurs complétées par défaut", () => {
    const m = extractModel(block({ levels: [{ id: "rdc", name: "RDC" }], walls: [{ id: "m1", levelId: "rdc", start: [0, 0], end: [5, 0] }] }))!;
    expect(m.defaultsApplied).toEqual(["niveau:rdc.elevation", "niveau:rdc.height", "mur:m1.thickness", "mur:m1.type"]);
  });
});
