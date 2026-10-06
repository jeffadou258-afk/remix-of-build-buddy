import { useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { supabase } from "@/integrations/supabase/client";
import { applyEdit, emptyInputs, FIELD_META, FIELDS, formatValue, inputsSchema, type Entry, type FieldKey, type Inputs } from "@/lib/extraction/inputs";

function parse(key: FieldKey, raw: string): unknown | null {
  const s = raw.trim();
  if (!s) return null;
  const k = FIELD_META[key].kind;
  if (k === "int") { const n = parseInt(s, 10); if (Number.isNaN(n) || n < 0) throw new Error("Nombre entier attendu"); return n; }
  if (k === "number") { const n = Number(s.replace(",", ".")); if (Number.isNaN(n) || n <= 0) throw new Error("Nombre attendu"); return n; }
  if (k === "bool") { if (/^(oui|o|yes|true)$/i.test(s)) return true; if (/^(non|n|no|false)$/i.test(s)) return false; throw new Error("Oui ou Non"); }
  if (k === "dims") { const m = s.match(/^(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)$/i); if (!m) throw new Error("Format : 20 x 30"); return [Number(m[1].replace(",", ".")), Number(m[2].replace(",", "."))]; }
  if (s.length > 100) throw new Error("100 caractères max");
  return s;
}

function Badges({ e }: { e: Entry }) {
  if (e.status === "UNKNOWN") return <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">⚪ Inconnu — à renseigner</span>;
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[11px] uppercase tracking-wider">
      <span className="text-emerald-500">🟢 Fourni par le client{e.source?.origin === "formulaire" ? " (formulaire)" : ""}</span>
      <span className="text-amber-500">🟠 Non validé techniquement</span>
    </div>
  );
}

function Row({ label, value, entry, editing, onEdit, onSave, onCancel }: { label: string; value: string; entry: Entry; editing: boolean; onEdit: () => void; onSave: (raw: string) => void; onCancel: () => void }) {
  const [raw, setRaw] = useState("");
  return (
    <div className="flex flex-col gap-2 border-b border-border py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={`font-display text-lg ${entry.status === "UNKNOWN" ? "text-muted-foreground" : ""}`}>{value}</p>
        <Badges e={entry} />
        {entry.source?.excerpt && <p className="mt-1 text-xs italic text-muted-foreground">« {entry.source.excerpt} »</p>}
      </div>
      {editing ? (
        <form className="flex gap-2" onSubmit={(ev) => { ev.preventDefault(); onSave(raw); }}>
          <Input autoFocus value={raw} onChange={(ev) => setRaw(ev.target.value)} placeholder="Vide = inconnu" className="w-44" maxLength={100} />
          <Button size="sm" type="submit">OK</Button>
          <Button size="sm" variant="ghost" type="button" onClick={onCancel}>Annuler</Button>
        </form>
      ) : (
        <Button size="sm" variant="outline" onClick={() => { setRaw(""); onEdit(); }}>{entry.status === "UNKNOWN" ? "Renseigner" : "Modifier"}</Button>
      )}
    </div>
  );
}

export function InputsPanel({ projectId, initial }: { projectId: string; initial: Inputs | null }) {
  const [d, setD] = useState<Inputs>(initial ?? emptyInputs(projectId));
  const [editing, setEditing] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function persist(next: Inputs) {
    const { error } = await supabase.from("projects").update({ inputs: next as never }).eq("id", projectId);
    if (error) { toast.error("Enregistrement impossible"); return; }
    setD(next); setEditing(null);
  }
  async function save(key: FieldKey | "budget_declared", raw: string) {
    try {
      let v: unknown | null;
      if (key === "budget_declared") {
        const n = Number(raw.replace(/\s/g, "").replace(",", "."));
        v = raw.trim() ? (Number.isNaN(n) || n <= 0 ? (() => { throw new Error("Montant attendu"); })() : { amount: Math.round(n), currency: "XOF" }) : null;
      } else v = parse(key, raw);
      const { data } = await supabase.auth.getUser();
      await persist(applyEdit(d, { [key]: v }, data.user?.id ?? null));
    } catch (e) { toast.error((e as Error).message); }
  }
  async function importFile(f: File) {
    try {
      const r = inputsSchema.safeParse(JSON.parse(await f.text()));
      if (!r.success) { toast.error("Fichier non conforme au module d'extraction (inputs.json v1)"); return; }
      await persist(r.data); toast.success("Données extraites importées");
    } catch { toast.error("Fichier illisible"); }
  }

  const provided = FIELDS.filter((k) => d.fields[k]?.status === "USER_PROVIDED");
  const unknown = FIELDS.filter((k) => d.fields[k]?.status !== "USER_PROVIDED");
  const rowProps = (k: FieldKey) => ({ label: FIELD_META[k].label, entry: d.fields[k], value: formatValue(k, d.fields[k]?.value), editing: editing === k, onEdit: () => setEditing(k), onCancel: () => setEditing(null), onSave: (raw: string) => save(k, raw) });
  const Section = ({ n, title, children }: { n: string; title: string; children: React.ReactNode }) => (
    <section className="border border-border bg-card p-5">
      <h3 className="mb-2 flex items-baseline gap-3 font-display text-lg"><span className="font-mono text-xs text-primary">{n}</span>{title}</h3>
      {children}
    </section>
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-border bg-card p-4 text-sm">
        <p className="max-w-xl text-muted-foreground">Une information fournie par vous est enregistrée comme telle, mais elle n'est <strong>pas validée techniquement</strong>. Rien n'est complété automatiquement.</p>
        <div className="flex gap-2">
          <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={(e) => e.target.files?.[0] && importFile(e.target.files[0])} />
          <Button size="sm" variant="outline" onClick={() => fileRef.current?.click()}>Importer l'extraction</Button>
          <Button size="sm" variant="outline" onClick={() => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 2)], { type: "application/json" })); a.download = "inputs.json"; a.click(); }}>Exporter</Button>
        </div>
      </div>

      <Section n="01" title="Informations fournies">
        {provided.length === 0 ? <p className="py-3 text-sm text-muted-foreground">Aucune information fournie pour l'instant.</p> : provided.map((k) => <Row key={k} {...rowProps(k)} />)}
        {d.rooms.map((r, i) => <div key={i} className="border-t border-border py-3 text-sm"><span className="text-muted-foreground">Pièce · {r.name} : </span>{formatValue("", r.surface_m2.value)} m² <Badges e={r.surface_m2} /></div>)}
      </Section>

      <Section n="02" title="Informations inconnues">
        {unknown.map((k) => <Row key={k} {...rowProps(k)} />)}
      </Section>

      <Section n="03" title="Budget">
        <Row label="Budget annoncé par le client" entry={d.budget.declared} value={formatValue("", d.budget.declared.value)} editing={editing === "budget_declared"} onEdit={() => setEditing("budget_declared")} onCancel={() => setEditing(null)} onSave={(raw) => save("budget_declared", raw)} />
        <div className="py-4">
          <p className="text-sm text-muted-foreground">Estimation ConstructionAgent</p>
          {d.budget.estimate.status === "NOT_EXECUTED"
            ? <p className="font-mono text-sm uppercase tracking-wider text-amber-500">Estimation non exécutée</p>
            : <p className="font-display text-lg">{formatValue("", d.budget.estimate.value)} <span className="font-mono text-xs">({d.budget.estimate.status})</span></p>}
          {d.budget.estimate.reason && <p className="text-xs text-muted-foreground">{d.budget.estimate.reason}</p>}
        </div>
      </Section>

      <Section n="04" title="Hypothèses">
        <p className="mb-2 text-xs text-muted-foreground">Séparées des informations fournies. Elles ne deviennent jamais des données client.</p>
        {d.hypotheses.length === 0 ? <p className="text-sm text-muted-foreground">Aucune hypothèse.</p> : d.hypotheses.map((h, i) => (
          <div key={i} className="border-t border-border py-2 text-sm"><span className="font-mono text-[11px] text-amber-500">HYPOTHÈSE</span> · {FIELD_META[h.field as FieldKey]?.label ?? h.field} : {formatValue(h.field, h.value)}{h.reason ? ` — ${h.reason}` : ""}</div>
        ))}
      </Section>

      <Section n="05" title="Historique des modifications">
        {d.history.length === 0 ? <p className="text-sm text-muted-foreground">Aucune modification.</p> : [...d.history].reverse().map((h, i) => {
          const key = h.field === "budget.declared" ? "budget_declared" : h.field;
          const label = h.field === "budget.declared" ? "Budget annoncé" : FIELD_META[key as FieldKey]?.label ?? h.field;
          return <p key={i} className="border-t border-border py-2 font-mono text-xs">{h.replaced_at.replace("T", " ")} · {label} : {formatValue(h.field, h.previous.value)} → <NextVal d={d} idx={d.history.length - 1 - i} /></p>;
        })}
      </Section>
    </div>
  );
}

/** Valeur qui a remplacé l'entrée d'historique idx : la prochaine entrée du même champ, sinon la valeur courante. */
function NextVal({ d, idx }: { d: Inputs; idx: number }) {
  const h = d.history[idx];
  const later = d.history.slice(idx + 1).find((x) => x.field === h.field);
  const v = later ? later.previous.value : h.field === "budget.declared" ? d.budget.declared.value : d.fields[h.field]?.value;
  return <>{formatValue(h.field, v)}</>;
}
