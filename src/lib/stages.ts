export const STAGES = [
  { key: "decouverte", label: "Découverte" },
  { key: "programme", label: "Programme" },
  { key: "conception", label: "Conception" },
  { key: "plans", label: "Plans" },
  { key: "documentation", label: "Documentation" },
  { key: "livre", label: "Livré" },
] as const;

export type StageKey = (typeof STAGES)[number]["key"];
