import { z } from "zod";

/**
 * Modèle bâtiment v1 — source unique de vérité pour la maquette 3D (navigateur)
 * et pour les futurs rendus Blender (serveur externe). Unités : mètres.
 * Plan : x vers la droite, y vers le haut du plan. Hauteurs : z.
 */
const pt = z.tuple([z.number(), z.number()]);

/** Statut de la donnée (doctrine PREUVE > AFFIRMATION). Absent = non prouvé → hypothèse. */
export const dataStatus = z.enum(["fourni", "deduit", "hypothese", "inconnu"]);
export type DataStatus = z.infer<typeof dataStatus>;
const status = dataStatus.default("hypothese");

export const levelSchema = z.object({
  id: z.string(), name: z.string(),
  elevation: z.number().default(0), height: z.number().default(2.8), status,
});
export const roomSchema = z.object({
  id: z.string(), name: z.string(), levelId: z.string(),
  polygon: z.array(pt), usage: z.string().optional(), area: z.number().optional(), status,
});
export const wallSchema = z.object({
  id: z.string(), levelId: z.string(), start: pt, end: pt,
  thickness: z.number().default(0.2), height: z.number().optional(),
  type: z.enum(["exterieur", "interieur"]).default("interieur"), status,
});
export const openingSchema = z.object({
  id: z.string(), wallId: z.string(), kind: z.enum(["porte", "fenetre"]),
  offset: z.number(), width: z.number(), height: z.number(), sill: z.number().default(0),
  name: z.string().optional(), status,
});
export const roofSchema = z.object({
  type: z.enum(["plat", "deux_pans", "quatre_pans"]).default("plat"),
  levelId: z.string().optional(), pitch: z.number().default(25), overhang: z.number().default(0.4), status,
});
export const unknownSchema = z.object({ field: z.string(), reason: z.string().optional() });
export const buildingModelSchema = z.object({
  version: z.literal(1).default(1),
  units: z.literal("m").default("m"),
  name: z.string().optional(),
  levels: z.array(levelSchema).min(1),
  rooms: z.array(roomSchema).default([]),
  walls: z.array(wallSchema).default([]),
  openings: z.array(openingSchema).default([]),
  roof: roofSchema.optional(),
  /** Informations nécessaires à la géométrie mais inconnues (déclarées par l'agent). */
  unknowns: z.array(unknownSchema).default([]),
  /** Valeurs complétées par l'application faute de donnée (jamais validées). */
  defaultsApplied: z.array(z.string()).default([]),
  validated: z.boolean().default(false),
});

export type BuildingModel = z.infer<typeof buildingModelSchema>;
export type Level = z.infer<typeof levelSchema>;
export type Room = z.infer<typeof roomSchema>;
export type Wall = z.infer<typeof wallSchema>;
export type Opening = z.infer<typeof openingSchema>;

export type ElementKind = "niveau" | "piece" | "mur" | "porte" | "fenetre" | "toiture";
export type ElementRef = { kind: ElementKind; id: string };

const BIM_BLOCK = /```bim\s*([\s\S]*?)```/g;

/** Liste les champs géométriques absents du JSON brut, que le schéma remplit par défaut. */
export function detectDefaults(raw: unknown): string[] {
  const out: string[] = [];
  const r = (raw ?? {}) as { levels?: unknown; walls?: unknown; openings?: unknown; roof?: unknown };
  const check = (arr: unknown, kind: string, fields: string[]) => {
    if (!Array.isArray(arr)) return;
    for (const el of arr as Record<string, unknown>[]) for (const f of fields) if (el?.[f] === undefined) out.push(`${kind}:${String(el?.["id"] ?? "?")}.${f}`);
  };
  check(r.levels, "niveau", ["elevation", "height"]);
  check(r.walls, "mur", ["thickness", "type"]);
  check(r.openings, "ouverture", ["sill"]);
  if (r.roof && typeof r.roof === "object") check([{ id: "toiture", ...(r.roof as object) }], "toiture", ["type", "pitch", "overhang"]);
  return out;
}

/** Extrait le dernier bloc ```bim valide d'un texte de l'agent. Le modèle extrait n'est jamais "validé". */
export function extractModel(text: string): BuildingModel | null {
  let found: BuildingModel | null = null;
  for (const m of text.matchAll(BIM_BLOCK)) {
    try {
      const raw = JSON.parse(m[1] ?? "");
      const r = buildingModelSchema.safeParse(raw);
      if (r.success) found = { ...r.data, defaultsApplied: detectDefaults(raw), validated: false };
    } catch { /* bloc invalide ignoré */ }
  }
  return found;
}

export function provenanceSummary(model: BuildingModel) {
  const all = [...model.levels, ...model.rooms, ...model.walls, ...model.openings, ...(model.roof ? [model.roof] : [])];
  const counts: Record<DataStatus, number> = { fourni: 0, deduit: 0, hypothese: 0, inconnu: 0 };
  for (const e of all) counts[e.status]++;
  return { counts, unknowns: model.unknowns, defaultsApplied: model.defaultsApplied, validated: model.validated };
}

export function stripModelBlocks(text: string) {
  return text.replace(BIM_BLOCK, "\n> 🧊 Maquette 3D mise à jour — onglet « Maquette 3D ».\n");
}

/** Charge utile destinée au futur moteur Blender (render_jobs.model_snapshot). */
export function toRenderPayload(model: BuildingModel, projectId: string) {
  return {
    schema: "batir.building-model", version: model.version, projectId, exportedAt: new Date().toISOString(),
    conventions: { units: "m", axes: "plan x→droite, y→haut ; hauteur z (Blender Z-up)", openingOffset: "distance depuis wall.start le long du mur", roofPitch: "degrés" },
    provenance: provenanceSummary(model),
    model,
  };
}

export function bounds(model: BuildingModel, levelId?: string) {
  const ws = model.walls.filter((w) => !levelId || w.levelId === levelId);
  const pts = ws.flatMap((w) => [w.start, w.end]).concat(model.rooms.filter((r) => !levelId || r.levelId === levelId).flatMap((r) => r.polygon));
  if (!pts.length) return { minX: 0, minY: 0, maxX: 10, maxY: 10 };
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  return { minX: Math.min(...xs), minY: Math.min(...ys), maxX: Math.max(...xs), maxY: Math.max(...ys) };
}
