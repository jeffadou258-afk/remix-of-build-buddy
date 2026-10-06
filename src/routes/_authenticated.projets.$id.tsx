import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { supabase } from "@/integrations/supabase/client";
import { STAGES, type StageKey } from "@/lib/stages";
import { ModelPanel } from "@/components/bim/ModelPanel";
import { InputsPanel } from "@/components/extraction/InputsPanel";
import { inputsSchema, type Inputs } from "@/lib/extraction/inputs";
import { buildingModelSchema, extractModel, stripModelBlocks, type BuildingModel } from "@/lib/bim/schema";

export const Route = createFileRoute("/_authenticated/projets/$id")({
  head: () => ({
    meta: [
      { title: "Projet — Bâtir" },
      { name: "description", content: "Travaillez votre projet avec l'agent Bâtir." },
      { property: "og:title", content: "Projet — Bâtir" },
      { property: "og:description", content: "Conception de votre projet avec l'agent." },
    ],
  }),
  component: ProjectPage,
});

function ProjectPage() {
  const { id } = Route.useParams();
  const { data: project, isLoading } = useQuery({
    queryKey: ["project", id],
    queryFn: async () => {
      const { data, error } = await supabase.from("projects").select("*").eq("id", id).single();
      if (error) throw error;
      return data;
    },
  });
  if (isLoading) return <p className="p-10 text-center text-muted-foreground">Chargement…</p>;
  if (!project) return <p className="p-10 text-center">Projet introuvable.</p>;
  return <ProjectChat id={id} title={project.title} initialStage={project.stage as StageKey} initialMessages={(project.messages as unknown as UIMessage[]) ?? []} initialModel={buildingModelSchema.safeParse(project.building_model).data ?? null} initialInputs={inputsSchema.safeParse((project as { inputs?: unknown }).inputs).data ?? null} />;
}

const STAGE_TAG = /\[\[ETAPE:([a-z]+)\]\]/g;

function textOf(m: UIMessage) {
  return m.parts.map((p) => (p.type === "text" ? p.text : "")).join("");
}

function ProjectChat({ id, title, initialStage, initialMessages, initialModel, initialInputs }: { id: string; title: string; initialStage: StageKey; initialMessages: UIMessage[]; initialModel: BuildingModel | null; initialInputs: Inputs | null }) {
  const [model, setModel] = useState<BuildingModel | null>(initialModel);
  const [tab, setTab] = useState<"chat" | "3d" | "infos">("chat");
  const [stage, setStage] = useState<StageKey>(initialStage);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const transport = useMemo(() => new DefaultChatTransport({
    api: "/api/chat",
    headers: async (): Promise<Record<string, string>> => {
      const { data } = await supabase.auth.getSession();
      return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
    },
    body: { projectId: id },
  }), [id]);

  const { messages, sendMessage, status, error, stop } = useChat({
    id,
    messages: initialMessages,
    transport,
    onFinish: async ({ messages: all }) => {
      const last = all[all.length - 1];
      let next: StageKey | null = null;
      if (last?.role === "assistant") {
        for (const m of textOf(last).matchAll(STAGE_TAG)) {
          if (STAGES.some((s) => s.key === m[1])) next = m[1] as StageKey;
        }
      }
      const update: { messages: unknown; stage?: StageKey; building_model?: unknown } = { messages: all };
      const nm = last?.role === "assistant" ? extractModel(textOf(last)) : null;
      if (nm) { update.building_model = nm; setModel(nm); toast.success("Maquette 3D mise à jour"); }
      if (next) { update.stage = next; setStage(next); }
      await supabase.from("projects").update(update as never).eq("id", id);
    },
  });

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    if (initialMessages.length === 0 && messages.length === 0) {
      sendMessage({ text: `Bonjour, je souhaite démarrer mon projet : « ${title} ».` });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const busy = status === "submitted" || status === "streaming";
  const stageIdx = STAGES.findIndex((s) => s.key === stage);

  function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const t = input.trim();
    if (!t || busy) return;
    sendMessage({ text: t.slice(0, 4000) });
    setInput("");
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-5 py-8 lg:grid-cols-[220px_1fr]">
      <aside>
        <p className="label-mono text-muted-foreground">Projet</p>
        <h1 className="mt-1 text-2xl font-bold">{title}</h1>
        <ol className="mt-6 space-y-1">
          {STAGES.map((s, i) => (
            <li key={s.key} className={`flex items-center gap-3 px-3 py-2 text-sm ${i === stageIdx ? "bg-ink text-ink-foreground" : i < stageIdx ? "text-foreground" : "text-muted-foreground"}`}>
              <span className="label-mono">{String(i + 1).padStart(2, "0")}</span>{s.label}{i < stageIdx && " ✓"}
            </li>
          ))}
        </ol>
      </aside>

      <div>
      <div className="mb-3 flex gap-2">
        <Button size="sm" variant={tab === "chat" ? "default" : "outline"} onClick={() => setTab("chat")}>Assistant</Button>
        <Button size="sm" variant={tab === "3d" ? "default" : "outline"} onClick={() => setTab("3d")}>Maquette 3D{model ? "" : " (à venir)"}</Button>
        <Button size="sm" variant={tab === "infos" ? "default" : "outline"} onClick={() => setTab("infos")}>Informations</Button>
      </div>
      {tab === "3d" && <ModelPanel projectId={id} model={model} />}
      {tab === "infos" && <InputsPanel projectId={id} initial={initialInputs} />}
      <section className={`${tab === "chat" ? "flex" : "hidden"} min-h-[70vh] flex-col border border-border bg-card`}>
        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          {messages.map((m) => (
            <div key={m.id} className={m.role === "user" ? "flex justify-end" : ""}>
              <div className={m.role === "user" ? "max-w-[80%] bg-ink px-4 py-3 text-ink-foreground" : "prose-agent max-w-none"}>
                {m.role === "user"
                  ? textOf(m)
                  : <div className="space-y-3 text-sm leading-relaxed [&_h1]:text-xl [&_h2]:text-lg [&_h3]:font-semibold [&_table]:w-full [&_table]:text-xs [&_td]:border [&_td]:border-border [&_td]:p-2 [&_th]:border [&_th]:border-border [&_th]:bg-muted [&_th]:p-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:overflow-x-auto">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{stripModelBlocks(textOf(m).replace(STAGE_TAG, ""))}</ReactMarkdown>
                    </div>}
              </div>
            </div>
          ))}
          {status === "submitted" && <p className="label-mono text-muted-foreground animate-pulse">L'agent réfléchit…</p>}
          {error && <p className="text-sm text-destructive">{error.message || "Une erreur est survenue."}</p>}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={submit} className="flex gap-3 border-t border-border p-4">
          <Textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="Répondez à l'agent…" rows={2}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }} />
          {busy ? <Button type="button" variant="outline" onClick={() => stop()}>Arrêter</Button> : <Button type="submit">Envoyer</Button>}
        </form>
      </section>
      </div>
    </div>
  );
}
