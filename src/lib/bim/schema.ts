import { z } from "zod";

/**
 * Modèle bâtiment v1 — source unique de vérité pour la maquette 3D (navigateur)
 * et pour les futurs rendus Blender (serveur externe). Unités : mètres.
 * Plan : x vers la droite, y vers le haut du plan. Hauteurs : z.
 */
const pt = z.tuple([z.number(), z.number()]);

export const levelSchema = z.object({
  id: z.string(), name: z.string(),
  elevation: z.number().default(0), height: z.number().default(2.8),
});
export const roomSchema = z.object({
  id: z.string(), name: z.string(), levelId: z.string(),
  polygon: z.array(pt), usage: z.string().optional(), area: z.number().optional(),
});
export const wallSchema = z.object({
  id: z.string(), levelId: z.string(), start: pt, end: pt,
  thickness: z.number().default(0.2), height: z.number().optional(),
  type: z.enum(["exterieur", "interieur"]).default("interieur"),
});
export const openingSchema = z.object({
  id: z.string(), wallId: z.string(), kind: z.enum(["porte", "fenetre"]),
  offset: z.number(), width: z.number(), height: z.number(), sill: z.number().default(0),
  name: z.string().optional(),
});
export const roofSchema = z.object({
  type: z.enum(["plat", "deux_pans", "quatre_pans"]).default("plat"),
  levelId: z.string().optional(), pitch: z.number().default(25), overhang: z.number().default(0.4),
});
export const buildingModelSchema = z.object({
  version: z.literal(1).default(1),
  units: z.literal("m").default("m"),
  name: z.string().optional(),
  levels: z.array(levelSchema).min(1),
  rooms: z.array(roomSchema).default([]),
  walls: z.array(wallSchema).default([]),
  openings: z.array(openingSchema).default([]),
  roof: roofSchema.optional(),
});

export type BuildingModel = z.infer<typeof buildingModelSchema>;
export type Level = z.infer<typeof levelSchema>;
export type Room = z.infer<typeof roomSchema>;
export type Wall = z.infer<typeof wallSchema>;
export type Opening = z.infer<typeof openingSchema>;

export type ElementKind = "niveau" | "piece" | "mur" | "porte" | "fenetre" | "toiture";
export type ElementRef = { kind: ElementKind; id: string };

const BIM_BLOCK = /```bim\s*([\s\S]*?)```/g;

/** Extrait le dernier bloc ```bim valide d'un texte de l'agent. */
export function extractModel(text: string): BuildingModel | null {
  let found: BuildingModel | null = null;
  for (const m of text.matchAll(BIM_BLOCK)) {
    try {
      const r = buildingModelSchema.safeParse(JSON.parse(m[1]));
      if (r.success) found = r.data;
    } catch { /* bloc invalide ignoré */ }
  }
  return found;
}
export function stripModelBlocks(text: string) {
  return text.replace(BIM_BLOCK, "\n> 🧊 Maquette 3D mise à jour — onglet « Maquette 3D ».\n");
}

/** Charge utile destinée au futur moteur Blender (render_jobs.model_snapshot). */
export function toRenderPayload(model: BuildingModel, projectId: string) {
  return { schema: "batir.building-model", version: model.version, projectId, exportedAt: new Date().toISOString(), model };
}

export function bounds(model: BuildingModel, levelId?: string) {
  const ws = model.walls.filter((w) => !levelId || w.levelId === levelId);
  const pts = ws.flatMap((w) => [w.start, w.end]).concat(model.rooms.filter((r) => !levelId || r.levelId === levelId).flatMap((r) => r.polygon));
  if (!pts.length) return { minX: 0, minY: 0, maxX: 10, maxY: 10 };
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  return { minX: Math.min(...xs), minY: Math.min(...ys), maxX: Math.max(...xs), maxY: Math.max(...ys) };
}
