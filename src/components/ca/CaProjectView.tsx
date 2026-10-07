/**
 * Vue d'un projet relié à ConstructionAgent : tout vient de l'API /v1 via le relais.
 * Aucune règle métier ici — on affiche ce que renvoient les moteurs réels.
 */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { InputsPanel } from "@/components/extraction/InputsPanel";
import { ModelPanel } from "@/components/bim/ModelPanel";
import { ca, CaError, type CaGate, type CaMessage, type CaRun, type CaState } from "@/lib/ca/client";
import { GateDecisionCard } from "@/components/ca/GateDecisionCard";
import { FIELD_META, inputsSchema, type FieldKey, type Inputs } from "@/lib/extraction/inputs";
import type { BuildingModel } from "@/lib/bim/schema";

type Extraction = { status: string; user_provided: string[]; unknown: string[]; rooms_with_surface: number };
const label = (k: string) => (k === "budget.declared" ? "Budget annoncé" : FIELD_META[k as FieldKey]?.label ?? k);

export function CaProjectView({ id, title, model }: { id: string; title: string; model: BuildingModel | null }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"chat" | "infos" | "run" | "3d">("chat");
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [extractions, setExtractions] = useState<Record<string, Extraction>>({});
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<CaRun | null>(null);
  const [runBlock, setRunBlock] = useState<string | null>(null);

  const overview = useQuery({ queryKey: ["ca", id, "overview"], queryFn: () => ca<{ state: CaState; gates: Record<string, CaGate> }>(id, "GET"), retry: false });
  const messages = useQuery({ queryKey: ["ca", id, "messages"], queryFn: () => ca<{ messages: CaMessage[] }>(id, "GET", "messages"), retry: false });
  const inputs = useQuery({ queryKey: ["ca", id, "inputs"], queryFn: async () => inputsSchema.parse((await ca<{ inputs: unknown }>(id, "GET", "inputs")).inputs), retry: false });

  const offline = [overview.error, messages.error, inputs.error].find((e) => e instanceof CaError && (e.status === 502 || e.status === 503)) as CaError | undefined;
  const refresh = () => qc.invalidateQueries({ queryKey: ["ca", id] });

  async function send(e?: React.FormEvent) {
    e?.preventDefault();
    const t = text.trim();
    if (!t || sending) return;
    setSending(true);
    try {
      const r = await ca<{ message_id: string; extraction: Extraction }>(id, "POST", "messages", { text: t.slice(0, 5000) });
      setExtractions((x) => ({ ...x, [r.message_id]: r.extraction }));
      setText("");
      await refresh();
    } catch (err) { toast.error((err as Error).message); } finally { setSending(false); }
  }

  async function run() {
    setRunning(true); setRunBlock(null);
    try {
      const r = await ca<{ run: CaRun }>(id, "POST", "runs");
      setLastRun(r.run);
    } catch (err) {
      if (err instanceof CaError && err.status === 409) setRunBlock(err.message); else toast.error((err as Error).message);
    } finally { setRunning(false); await refresh(); }
  }

  const remote = {
    patch: async (changes: Record<string, unknown>) => { const r = await ca<{ inputs: unknown }>(id, "PATCH", "inputs", { changes }); await refresh(); return inputsSchema.parse(r.inputs) as Inputs; },
    addRoom: async (room: { name: string; surface_m2: number; level: string }) => { await ca(id, "POST", "rooms", room); await refresh(); return inputsSchema.parse((await ca<{ inputs: unknown }>(id, "GET", "inputs")).inputs) as Inputs; },
  };

  const state = overview.data?.state;
  const gates = overview.data?.gates ?? {};
  const openGates = Object.entries(gates).filter(([, g]) => g.status === "OPEN");

  return (
    <div className="mx-auto max-w-6xl px-5 py-8">
      <p className="label-mono text-muted-foreground">Projet</p>
      <h1 className="mt-1 text-2xl font-bold">{title}</h1>

      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border border-border bg-card p-4 text-sm">
        <span className={`font-mono text-xs uppercase tracking-wider ${offline ? "text-destructive" : "text-primary"}`}>
          {offline ? "● Backend ConstructionAgent injoignable" : "● Connecté à ConstructionAgent"}
        </span>
        {state && <span>État : <strong className="font-mono">{state.status}</strong></span>}
        {state && <span>Moteurs terminés : {state.completed.length}</span>}
        {openGates.map(([g]) => <span key={g} className="font-mono text-xs uppercase text-amber-500">Validation humaine requise · {g}</span>)}
      </div>
      {offline && <p className="mt-3 text-sm text-destructive">{offline.message} Aucune réponse n'est produite à sa place.</p>}

      <div className="my-4 flex flex-wrap gap-2">
        {([["chat", "Conversation"], ["infos", "Informations"], ["run", "Exécution"], ["3d", "Maquette 3D"]] as const).map(([k, l]) => (
          <Button key={k} size="sm" variant={tab === k ? "default" : "outline"} onClick={() => setTab(k)}>{l}</Button>
        ))}
      </div>

      {tab === "chat" && (
        <section className="flex min-h-[60vh] flex-col border border-border bg-card">
          <div className="flex-1 space-y-5 overflow-y-auto p-6">
            {messages.data?.messages.length === 0 && <p className="text-sm text-muted-foreground">Décrivez votre projet. ConstructionAgent n'enregistre que ce que vous écrivez explicitement ; le reste reste inconnu.</p>}
            {messages.data?.messages.map((m) => (
              <div key={m.id} className="space-y-2">
                <div className="flex justify-end"><div className="max-w-[80%] bg-ink px-4 py-3 text-ink-foreground">{m.text}</div></div>
                {extractions[m.id] && <ExtractionCard x={extractions[m.id]!} />}
              </div>
            ))}
          </div>
          <form onSubmit={send} className="flex gap-3 border-t border-border p-4">
            <Textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Ex : Je veux construire une villa R+1 de 4 chambres sur un terrain de 600 m²." rows={2} maxLength={5000}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
            <Button type="submit" disabled={sending || !!offline}>{sending ? "Envoi…" : "Envoyer"}</Button>
          </form>
        </section>
      )}

      {tab === "infos" && (inputs.data ? <InputsPanel key={inputs.data.updated_at} projectId={id} initial={inputs.data} remote={remote} /> : <p className="text-sm text-muted-foreground">{inputs.isLoading ? "Chargement…" : "Informations indisponibles."}</p>)}

      {tab === "run" && (
        <section className="space-y-4 border border-border bg-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="max-w-xl text-sm text-muted-foreground">Lance les moteurs réels de ConstructionAgent jusqu'à la prochaine validation humaine.</p>
            <Button onClick={run} disabled={running || !!offline || !!state?.pending_gate}>{running ? "Exécution…" : "Lancer l'exécution"}</Button>
          </div>
          {state?.pending_gate && gates[state.pending_gate]?.status === "OPEN" && (
            <GateDecisionCard projectId={id} gate={state.pending_gate} openedAt={gates[state.pending_gate]?.opened_at ?? null} onDone={refresh} />
          )}
          {runBlock && <p className="text-sm text-destructive">Exécution refusée par ConstructionAgent : {runBlock}</p>}
          {lastRun && (
            <div>
              <p className="text-sm">Run <span className="font-mono">{lastRun.id}</span> · statut <strong className="font-mono">{lastRun.status}</strong>{lastRun.stopped_at ? ` · arrêt : ${lastRun.stopped_at}` : ""}</p>
              <ol className="mt-2 space-y-1">
                {lastRun.steps.map((s, i) => <li key={i} className="font-mono text-xs">{s.engine} — {s.status}{s.cause ? ` (${s.cause})` : ""}</li>)}
              </ol>
            </div>
          )}
          <div>
            <p className="label-mono text-muted-foreground">Gates</p>
            {Object.entries(gates).map(([g, v]) => <p key={g} className="font-mono text-xs">{g} : {v.status}</p>)}
          </div>
        </section>
      )}

      {tab === "3d" && (
        <div className="space-y-3">
          <p className="border border-border bg-card p-3 text-sm text-muted-foreground">La maquette n'est pas encore alimentée par ConstructionAgent : elle sera branchée sur le BIM réel à l'étape suivante.</p>
          <ModelPanel projectId={id} model={model} />
        </div>
      )}
    </div>
  );
}

function ExtractionCard({ x }: { x: Extraction }) {
  return (
    <div className="max-w-[80%] border border-border bg-background p-3 text-sm">
      <p className="label-mono text-primary">ConstructionAgent · extraction ({x.status})</p>
      <p className="mt-1"><span className="text-muted-foreground">Fourni : </span>{x.user_provided.length ? x.user_provided.map(label).join(", ") : "rien de nouveau"}</p>
      <p><span className="text-muted-foreground">Toujours inconnu : </span>{x.unknown.map(label).join(", ") || "—"}</p>
      {x.rooms_with_surface > 0 && <p className="text-muted-foreground">Pièces avec surface : {x.rooms_with_surface}</p>}
    </div>
  );
}
