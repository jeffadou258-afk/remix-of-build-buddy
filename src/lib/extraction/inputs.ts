/**
 * Contrat de données du module d'extraction ConstructionAgent
 * (engines/extraction/engine.py, schéma "construction-agent.inputs" v1).
 * Ce fichier ne fait AUCUNE extraction : il lit/écrit ce format et reproduit
 * à l'identique la sémantique de edit() (USER_PROVIDED, technically_validated=false,
 * historique, valeur vidée => UNKNOWN). Aucune valeur par défaut.
 */
import { z } from "zod";

export const FIELDS = [
  "building_type", "levels_label", "levels_count", "bedrooms", "bathrooms", "plot_area_m2",
  "plot_dimensions_m", "location_city", "garage", "pool", "occupants", "style",
] as const;
export type FieldKey = (typeof FIELDS)[number];

export const FIELD_META: Record<FieldKey, { label: string; kind: "text" | "int" | "number" | "bool" | "dims"; unit?: string }> = {
  building_type: { label: "Type de bâtiment", kind: "text" },
  levels_label: { label: "Niveaux (libellé)", kind: "text" },
  levels_count: { label: "Nombre de niveaux", kind: "int" },
  bedrooms: { label: "Nombre de chambres", kind: "int" },
  bathrooms: { label: "Salles de bain", kind: "int" },
  plot_area_m2: { label: "Surface du terrain", kind: "number", unit: "m²" },
  plot_dimensions_m: { label: "Dimensions du terrain", kind: "dims", unit: "m" },
  location_city: { label: "Ville", kind: "text" },
  garage: { label: "Garage", kind: "bool" },
  pool: { label: "Piscine", kind: "bool" },
  occupants: { label: "Occupants", kind: "int" },
  style: { label: "Style", kind: "text" },
};

const sourceSchema = z.object({
  origin: z.string(), message_id: z.string().nullable().optional(), excerpt: z.string().nullable().optional(),
  at: z.string().optional(), user_id: z.string().nullable().optional(),
}).passthrough();

export const entrySchema = z.object({
  value: z.unknown().nullable(),
  status: z.enum(["USER_PROVIDED", "UNKNOWN"]),
  source: sourceSchema.nullable(),
  technically_validated: z.literal(false),
}).passthrough();
export type Entry = z.infer<typeof entrySchema>;

export const inputsSchema = z.object({
  schema: z.literal("construction-agent.inputs"),
  version: z.literal(1),
  project_id: z.string(),
  updated_at: z.string(),
  notice: z.string().optional(),
  fields: z.record(z.string(), entrySchema),
  rooms: z.array(z.object({ name: z.string(), surface_m2: entrySchema }).passthrough()),
  budget: z.object({
    declared: entrySchema,
    estimate: z.object({ status: z.string(), value: z.unknown().nullable(), reason: z.string().optional() }).passthrough(),
  }),
  quantities: z.object({ status: z.string(), items: z.array(z.unknown()), reason: z.string().optional() }).passthrough(),
  hypotheses: z.array(z.object({ field: z.string(), value: z.unknown(), status: z.literal("HYPOTHESIS"), reason: z.string().optional(), author: z.string().optional(), at: z.string().optional() }).passthrough()),
  history: z.array(z.object({ field: z.string(), previous: entrySchema, replaced_at: z.string() }).passthrough()),
}).passthrough();
export type Inputs = z.infer<typeof inputsSchema>;

const now = () => new Date().toISOString().slice(0, 19);
const unknown = (): Entry => ({ value: null, status: "UNKNOWN", source: null, technically_validated: false });
const given = (value: unknown, userId: string | null): Entry => ({
  value, status: "USER_PROVIDED", technically_validated: false,
  source: { origin: "formulaire", message_id: null, excerpt: null, at: now(), user_id: userId },
});

/** Équivalent de empty_inputs() : tout UNKNOWN, estimation NOT_EXECUTED, quantités UNKNOWN. */
export function emptyInputs(projectId: string): Inputs {
  return {
    schema: "construction-agent.inputs", version: 1, project_id: projectId, updated_at: now(),
    notice: "USER_PROVIDED = declare par le client, non valide techniquement. UNKNOWN = non fourni.",
    fields: Object.fromEntries(FIELDS.map((k) => [k, unknown()])),
    rooms: [],
    budget: { declared: unknown(), estimate: { status: "NOT_EXECUTED", value: null, reason: "aucun moteur reel de chiffrage" } },
    quantities: { status: "UNKNOWN", items: [], reason: "aucun moteur de quantification dynamique" },
    hypotheses: [], history: [],
  };
}

const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** Équivalent de edit() : value=null remet à UNKNOWN ; l'ancienne valeur va dans history. */
export function applyEdit(d: Inputs, changes: Partial<Record<FieldKey | "budget_declared", unknown>>, userId: string | null): Inputs {
  const next: Inputs = structuredClone(d);
  for (const [k, v] of Object.entries(changes)) {
    const entry = v === null || v === undefined ? unknown() : given(v, userId);
    if (k === "budget_declared") {
      const old = next.budget.declared;
      if (old.status !== "UNKNOWN" && !same(old.value, entry.value)) next.history.push({ field: "budget.declared", previous: old, replaced_at: now() });
      next.budget.declared = entry;
      continue;
    }
    if (!(FIELDS as readonly string[]).includes(k)) throw new Error(`champ inconnu: ${k}`);
    const old = next.fields[k];
    if (old && old.status !== "UNKNOWN" && !same(old.value, entry.value)) next.history.push({ field: k, previous: old, replaced_at: now() });
    next.fields[k] = entry;
  }
  next.updated_at = now();
  return next;
}

export function formatValue(key: string, v: unknown): string {
  if (v === null || v === undefined) return "UNKNOWN";
  const meta = FIELD_META[key as FieldKey];
  if (typeof v === "boolean") return v ? "Oui" : "Non";
  if (Array.isArray(v)) return `${v.join(" × ")}${meta?.unit ? " " + meta.unit : ""}`;
  if (typeof v === "object" && v && "amount" in v) {
    const b = v as { amount: number; currency?: string | null };
    return `${b.amount.toLocaleString("fr-FR")} ${b.currency ?? ""}`.trim();
  }
  return `${v}${meta?.unit ? " " + meta.unit : ""}`;
}
