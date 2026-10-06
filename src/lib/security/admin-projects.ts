/**
 * Forme d'une ligne « Projets » de l'Admin : métadonnées uniquement (liste blanche).
 * Aucun titre, message, information, maquette ou document client.
 */
export const ADMIN_PROJECT_FIELDS = ["project_id", "owner_id", "client_type", "stage", "created_at", "updated_at", "ca_linked"] as const;

/** Indicateurs sans source réelle branchée : toujours affichés « NON MESURÉ », jamais 0. */
export const NOT_MEASURED_PROJECT_METRICS = ["runs", "cout"] as const;

export type AdminProjectRow = {
  project_id: string;
  owner_id: string;
  client_type: string;
  stage: string;
  created_at: string;
  updated_at: string;
  ca_linked: boolean;
};

export function toAdminProjectRow(r: Record<string, unknown>): AdminProjectRow {
  return {
    project_id: String(r["project_id"]),
    owner_id: String(r["owner_id"]),
    client_type: String(r["client_type"] ?? ""),
    stage: String(r["stage"] ?? ""),
    created_at: String(r["created_at"]),
    updated_at: String(r["updated_at"]),
    ca_linked: r["ca_linked"] === true,
  };
}
