import { Fragment, lazy, Suspense, useState } from "react";
import { ClientOnly } from "@tanstack/react-router";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { provenanceSummary, toRenderPayload, type BuildingModel, type DataStatus, type ElementRef } from "@/lib/bim/schema";

const ST: Record<DataStatus, string> = { fourni: "FOURNI", deduit: "DÉDUIT", hypothese: "HYPOTHÈSE", inconnu: "INCONNU" };

const BuildingViewer = lazy(() => import("./BuildingViewer"));

function describe(model: BuildingModel, sel: ElementRef): [string, [string, string][]] {
  const lvl = (id: string) => model.levels.find((l) => l.id === id)?.name ?? id;
  if (sel.kind === "piece") {
    const r = model.rooms.find((x) => x.id === sel.id)!;
    return [`Pièce · ${r.name}`, [["ID", r.id], ["Niveau", lvl(r.levelId)], ["Usage", r.usage ?? "inconnu"], ["Surface", r.area ? `${r.area} m²` : "inconnue"], ["Statut", ST[r.status]]]];
  }
  if (sel.kind === "mur") {
    const w = model.walls.find((x) => x.id === sel.id)!;
    const len = Math.hypot(w.end[0] - w.start[0], w.end[1] - w.start[1]);
    return [`Mur ${w.type}`, [["ID", w.id], ["Niveau", lvl(w.levelId)], ["Longueur", `${len.toFixed(2)} m`], ["Épaisseur", `${w.thickness} m${model.defaultsApplied.includes(`mur:${w.id}.thickness`) ? " (valeur par défaut)" : ""}`], ["Statut", ST[w.status]]]];
  }
  if (sel.kind === "porte" || sel.kind === "fenetre") {
    const o = model.openings.find((x) => x.id === sel.id)!;
    return [`${o.kind === "porte" ? "Porte" : "Fenêtre"}${o.name ? ` · ${o.name}` : ""}`, [["ID", o.id], ["Mur", o.wallId], ["Dimensions", `${o.width} × ${o.height} m`], ["Allège", `${o.sill} m`], ["Statut", ST[o.status]]]];
  }
  const r = model.roof!;
  return ["Toiture", [["Type", r.type.replace("_", " ")], ["Pente", `${r.pitch}°`], ["Débord", `${r.overhang} m`], ["Statut", ST[r.status]]]];
}

export function ModelPanel({ projectId, model }: { projectId: string; model: BuildingModel | null }) {
  const [selected, setSelected] = useState<ElementRef | null>(null);
  const [hidden, setHidden] = useState<string[]>([]);
  const [roof, setRoof] = useState(true);

  if (!model) return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-3 border border-border bg-card p-10 text-center">
      <p className="label-mono text-muted-foreground">Maquette 3D</p>
      <p className="max-w-md text-sm text-muted-foreground">La maquette apparaîtra dès que l'agent aura produit les plans (étape « Plans »). Vous pouvez aussi lui demander : « Génère la maquette 3D ».</p>
    </div>
  );

  function exportJson() {
    const blob = new Blob([JSON.stringify(toRenderPayload(model!, projectId), null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `maquette-${projectId}.json`; a.click();
  }
  async function requestRender() {
    const { data: u } = await supabase.auth.getUser();
    if (!u.user) return;
    const { error } = await supabase.from("render_jobs").insert({ project_id: projectId, user_id: u.user.id, model_snapshot: toRenderPayload(model!, projectId) as never });
    if (error) toast.error("Demande impossible"); else toast.success("Demande enregistrée — les rendus photoréalistes seront disponibles prochainement.");
  }

  const info = selected ? describe(model, selected) : null;
  const prov = provenanceSummary(model);
  return (
    <div className="flex flex-col border border-border bg-card">
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <span className="label-mono text-muted-foreground mr-1">Niveaux</span>
        {model.levels.map((l) => {
          const on = !hidden.includes(l.id);
          return <Button key={l.id} size="sm" variant={on ? "default" : "outline"} onClick={() => setHidden(on ? [...hidden, l.id] : hidden.filter((h) => h !== l.id))}>{l.name}</Button>;
        })}
        {model.roof && <Button size="sm" variant={roof ? "default" : "outline"} onClick={() => setRoof(!roof)}>Toiture</Button>}
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="outline" onClick={exportJson}>Exporter (JSON)</Button>
          <Button size="sm" variant="outline" onClick={requestRender}>Demander un rendu réaliste</Button>
        </div>
      </div>
      <div className="border-b border-border p-3 text-xs">
        <p><span className="font-semibold">{prov.validated ? "Maquette validée" : "Maquette conceptuelle NON VALIDÉE"}</span>
          {" · "}Fourni {prov.counts.fourni} · Déduit {prov.counts.deduit} · Hypothèse {prov.counts.hypothese} · Inconnu {prov.counts.inconnu}</p>
        {prov.unknowns.length > 0 && <p className="mt-1 text-muted-foreground">Inconnu : {prov.unknowns.map((u) => u.reason ? `${u.field} (${u.reason})` : u.field).join(" ; ")}</p>}
        {prov.defaultsApplied.length > 0 && <p className="mt-1 text-muted-foreground">Valeurs par défaut affichées (non fournies) : {prov.defaultsApplied.length} champ(s)</p>}
      </div>
      <div className="relative h-[65vh]">
        <ClientOnly fallback={<p className="p-10 text-center text-muted-foreground">Chargement de la 3D…</p>}>
          <Suspense fallback={<p className="p-10 text-center text-muted-foreground">Chargement de la 3D…</p>}>
            <BuildingViewer model={model} hiddenLevels={hidden} selected={selected} onSelect={setSelected} showRoof={roof} />
          </Suspense>
        </ClientOnly>
        <div className="pointer-events-none absolute left-3 top-3 max-w-xs border border-border bg-card/90 p-3 text-xs backdrop-blur">
          {info ? (<>
            <p className="font-semibold">{info[0]}</p>
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">{info[1].map(([k, v]) => <Fragment key={k}><dt className="text-muted-foreground">{k}</dt><dd>{v}</dd></Fragment>)}</dl>
          </>) : <p className="text-muted-foreground">Cliquez sur un élément pour l'identifier · glisser pour tourner · molette pour zoomer</p>}
        </div>
        <p className="absolute bottom-2 right-3 label-mono text-muted-foreground">{model.rooms.length} pièces · {model.walls.length} murs · {model.openings.length} ouvertures</p>
      </div>
    </div>
  );
}
