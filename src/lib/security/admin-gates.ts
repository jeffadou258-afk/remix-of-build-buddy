/**
 * Gates en lecture seule pour l'Admin : mise en forme stricte de la réponse réelle
 * de ConstructionAgent (GET /v1/projects/{id}/gates). Aucun commentaire client,
 * aucune variante choisie, aucun identifiant de décideur ne sort.
 */
export const GATE_STATUSES = ["NOT_REACHED", "OPEN", "APPROVED", "REJECTED"] as const;
export type GateStatus = (typeof GATE_STATUSES)[number] | "INCONNU";

export type AdminGateRow = {
  gate: string;
  status: GateStatus;
  opened_at: string | null;
  decision: "approve" | "reject" | null;
  decided_at: string | null;
  decided_by_owner: boolean | null;
};

export type AdminGateProject = {
  project_id: string;
  owner_id: string;
  stage: string;
  /** « ok » : Gates lues chez ConstructionAgent ; sinon NON MESURÉ avec la cause. */
  source: "ok" | "non_configure" | "injoignable" | "erreur";
  gates: AdminGateRow[];
};

const str = (v: unknown) => (typeof v === "string" ? v : null);

export function toAdminGates(body: unknown, ownerId: string): AdminGateRow[] {
  const g = (body as { gates?: unknown } | null)?.gates;
  if (!g || typeof g !== "object" || Array.isArray(g)) return [];
  return Object.entries(g as Record<string, unknown>)
    .filter(([name]) => /^[a-z_]{1,60}$/.test(name))
    .map(([name, raw]) => {
      const e = (raw ?? {}) as Record<string, unknown>;
      const st = str(e["status"]);
      const d = (e["decision"] ?? null) as Record<string, unknown> | null;
      const dec = d && (d["decision"] === "approve" || d["decision"] === "reject") ? (d["decision"] as "approve" | "reject") : null;
      return {
        gate: name,
        status: (GATE_STATUSES as readonly string[]).includes(st ?? "") ? (st as GateStatus) : "INCONNU",
        opened_at: str(e["opened_at"]),
        decision: dec,
        decided_at: d ? str(d["at"]) : null,
        decided_by_owner: d ? d["by"] === ownerId : null,
      };
    });
}
