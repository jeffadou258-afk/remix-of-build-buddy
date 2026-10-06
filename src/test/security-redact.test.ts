import { describe, expect, it } from "vitest";
import { MASK, redactSecrets, redactText } from "@/lib/security/redact.server";

describe("aucun secret dans une réponse", () => {
  it("masque les champs nommés clé / secret / jeton", () => {
    const out = redactSecrets({ api_key: "abc", nested: { CA_API_KEY: "x", password: "p" }, title: "Villa" });
    expect(out).toEqual({ api_key: MASK, nested: { CA_API_KEY: MASK, password: MASK }, title: "Villa" });
  });
  it("masque les valeurs ayant la forme d'un secret", () => {
    const s = redactText("k=sb_secret_ABC123 h=Bearer abc.def.ghi j=eyJhbGc.eyJzdWI.sig");
    expect(s).not.toMatch(/sb_secret_|Bearer abc|eyJhbGc/);
  });
  it("masque la valeur exacte d'un secret serveur où qu'elle apparaisse", () => {
    const out = redactSecrets({ log: ["erreur avec ma-cle-tres-secrete-123"] }, ["ma-cle-tres-secrete-123"]);
    expect(JSON.stringify(out)).not.toContain("ma-cle-tres-secrete-123");
  });
  it("ne touche pas aux données du projet", () => {
    expect(redactSecrets({ rooms: [{ name: "Salon", area_m2: 42 }] })).toEqual({ rooms: [{ name: "Salon", area_m2: 42 }] });
  });
});
