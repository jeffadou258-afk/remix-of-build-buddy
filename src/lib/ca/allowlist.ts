/**
 * Adresses de l'API ConstructionAgent /v1 que le relais laisse passer.
 * Uniquement des endpoints réellement présents dans web/api/server.py.
 * Aucune logique métier ici : seulement un filtre.
 */
export type CaMethod = "GET" | "POST" | "PATCH";

const ALLOWED: ReadonlyArray<readonly [CaMethod, string]> = [
  ["GET", ""],          // GET /v1/projects/{id} : projet, état, gates
  ["GET", "state"],
  ["GET", "messages"],
  ["POST", "messages"], // message + extraction réelle
  ["GET", "inputs"],
  ["PATCH", "inputs"],  // corrections via engine.edit()
  ["POST", "rooms"],
  ["GET", "unknowns"],
  ["POST", "runs"],     // exécution réelle des moteurs
  ["GET", "gates"],
];

/** `sub` = partie après /v1/projects/{id}/ (sans slash). */
export function isAllowed(method: string, sub: string): boolean {
  const s = sub.replace(/^\/+|\/+$/g, "");
  if (s.includes("..") || s.includes("?")) return false;
  return ALLOWED.some(([m, p]) => m === method && p === s);
}

export function upstreamPath(caProjectId: string, sub: string): string {
  if (!/^P_[0-9a-f]{32}$/.test(caProjectId)) throw new Error("identifiant ConstructionAgent invalide");
  const s = sub.replace(/^\/+|\/+$/g, "");
  return `/v1/projects/${caProjectId}${s ? "/" + s : ""}`;
}
