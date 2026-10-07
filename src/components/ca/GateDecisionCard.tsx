/** Carte de validation humaine : envoie la vraie décision à ConstructionAgent via le relais. Aucune règle locale. */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ca, CaError } from "@/lib/ca/client";

type Props = { projectId: string; gate: string; openedAt: string | null; onDone: () => Promise<unknown> };

export function GateDecisionCard({ projectId, gate, openedAt, onDone }: Props) {
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<null | "reject" | "modify">(null);
  const [comment, setComment] = useState("");
  const summary = useQuery({
    queryKey: ["ca", projectId, "artifact", gate],
    queryFn: () => ca<{ artifact: unknown }>(projectId, "GET", `artifacts/${gate}`),
    enabled: gate === "design",
    retry: false,
  });

  async function decide(decision: "approve" | "reject") {
    setBusy(true);
    try {
      await ca(projectId, "POST", `gates/${gate}/decision`, { decision, comment: comment.trim().slice(0, 1000) || undefined });
      toast.success(decision === "approve" ? "Validation enregistrée par ConstructionAgent." : "Refus enregistré par ConstructionAgent.");
      setMode(null); setComment("");
      await onDone();
    } catch (e) {
      toast.error(e instanceof CaError ? `ConstructionAgent : ${e.message}` : (e as Error).message);
    } finally { setBusy(false); }
  }

  async function requestChange() {
    const t = comment.trim();
    if (!t) { toast.error("Précisez ce que vous voulez modifier."); return; }
    setBusy(true);
    try {
      // La Gate n'est pas décidée : la demande est enregistrée comme message utilisateur réel.
      await ca(projectId, "POST", "messages", { text: `Demande de modification (${gate}) : ${t}`.slice(0, 5000) });
      toast.success("Demande enregistrée. La validation reste en attente.");
      setMode(null); setComment("");
      await onDone();
    } catch (e) { toast.error((e as Error).message); } finally { setBusy(false); }
  }

  const art = summary.data?.artifact;
  return (
    <div className="space-y-4 border border-primary/40 bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-lg font-semibold">Validation requise · {gate}</p>
        <span className="font-mono text-xs uppercase text-primary">Statut : OPEN{openedAt ? ` · depuis ${new Date(openedAt).toLocaleString("fr-FR")}` : ""}</span>
      </div>
      <p className="text-sm text-muted-foreground">
        ConstructionAgent s'est arrêté avant l'étape suivante. Il attend votre décision sur le résultat « {gate} ». Rien ne continue sans vous.
      </p>
      {gate === "design" && (
        <div>
          <p className="label-mono text-muted-foreground">Résultat Design (fourni par ConstructionAgent)</p>
          {summary.isLoading && <p className="text-sm">Chargement…</p>}
          {summary.error && <p className="text-sm text-destructive">Résultat indisponible : {(summary.error as Error).message}</p>}
          {art !== undefined && <pre className="mt-2 max-h-72 overflow-auto bg-muted p-3 text-xs">{JSON.stringify(art, null, 2)}</pre>}
        </div>
      )}
      {mode && (
        <Textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} maxLength={1000}
          placeholder={mode === "modify" ? "Ce que vous voulez modifier…" : "Motif du refus (facultatif)"} />
      )}
      <div className="flex flex-wrap gap-2">
        {!mode && <>
          <Button disabled={busy} onClick={() => decide("approve")}>Approuver</Button>
          <Button disabled={busy} variant="outline" onClick={() => setMode("reject")}>Refuser</Button>
          <Button disabled={busy} variant="outline" onClick={() => setMode("modify")}>Demander une modification</Button>
        </>}
        {mode === "reject" && <Button disabled={busy} variant="destructive" onClick={() => decide("reject")}>Confirmer le refus</Button>}
        {mode === "modify" && <Button disabled={busy} onClick={requestChange}>Envoyer la demande</Button>}
        {mode && <Button disabled={busy} variant="ghost" onClick={() => { setMode(null); setComment(""); }}>Annuler</Button>}
      </div>
    </div>
  );
}
