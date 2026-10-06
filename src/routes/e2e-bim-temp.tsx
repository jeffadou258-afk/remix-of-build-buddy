import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ModelPanel } from "@/components/bim/ModelPanel";
import { buildingModelSchema, type BuildingModel } from "@/lib/bim/schema";
export const Route = createFileRoute("/e2e-bim-temp")({ component: P });
function P() {
  const [m, setM] = useState<BuildingModel | null>(null);
  useEffect(() => { fetch("/__e2e/m.json").then((r) => r.json()).then((d) => setM(buildingModelSchema.parse(d.model))); }, []);
  return <div className="p-4">{m ? <ModelPanel projectId="test" model={m} /> : "…"}</div>;
}
