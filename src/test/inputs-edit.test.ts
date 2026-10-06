import { describe, expect, it } from "vitest";
import { applyEdit, emptyInputs, inputsSchema } from "@/lib/extraction/inputs";

describe("formulaire de correction (contrat edit())", () => {
  it("une saisie produit USER_PROVIDED mais jamais validée techniquement", () => {
    const d = applyEdit(emptyInputs("P1"), { bedrooms: 4 }, "u1");
    expect(d.fields["bedrooms"]!.status).toBe("USER_PROVIDED");
    expect(d.fields["bedrooms"]!.technically_validated).toBe(false);
  });
  it("une modification garde l'ancienne valeur dans l'historique", () => {
    let d = applyEdit(emptyInputs("P1"), { plot_area_m2: 36 }, "u1");
    d = applyEdit(d, { plot_area_m2: 42 }, "u1");
    expect(d.fields["plot_area_m2"]!.value).toBe(42);
    expect(d.history.at(-1)?.previous.value).toBe(36);
  });
  it("une valeur effacée redevient UNKNOWN", () => {
    let d = applyEdit(emptyInputs("P1"), { plot_area_m2: 42 }, "u1");
    d = applyEdit(d, { plot_area_m2: null }, "u1");
    expect(d.fields["plot_area_m2"]!.status).toBe("UNKNOWN");
    expect(d.history.at(-1)?.previous.value).toBe(42);
  });
  it("le budget client ne devient jamais une estimation", () => {
    const d = applyEdit(emptyInputs("P1"), { budget_declared: { amount: 50_000_000, currency: "XOF" } }, "u1");
    expect(d.budget.estimate.status).toBe("NOT_EXECUTED");
    expect(d.budget.estimate.value).toBeNull();
  });
  it("les hypothèses ne sont jamais converties en données fournies", () => {
    const base = { ...emptyInputs("P1"), hypotheses: [{ field: "bathrooms", value: 3, status: "HYPOTHESIS" as const }] };
    const d = applyEdit(base, { bedrooms: 4 }, "u1");
    expect(d.fields["bathrooms"]!.status).toBe("UNKNOWN");
    expect(d.hypotheses).toHaveLength(1);
  });
  it("un projet vide n'a aucune valeur par défaut", () => {
    const d = emptyInputs("P1");
    expect(Object.values(d.fields).every((f) => f.value === null && f.status === "UNKNOWN")).toBe(true);
    expect(inputsSchema.safeParse(d).success).toBe(true);
  });
  it("refuse un fichier marqué validé techniquement", () => {
    const d = emptyInputs("P1") as any;
    d.fields.bedrooms = { value: 4, status: "USER_PROVIDED", source: { origin: "x" }, technically_validated: true };
    expect(inputsSchema.safeParse(d).success).toBe(false);
  });
});
