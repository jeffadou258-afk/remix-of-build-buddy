import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { STAGES } from "@/lib/stages";

export const Route = createFileRoute("/_authenticated/projets/")({
  head: () => ({
    meta: [
      { title: "Mes projets — Bâtir" },
      { name: "description", content: "Retrouvez et poursuivez vos projets de construction." },
      { property: "og:title", content: "Mes projets — Bâtir" },
      { property: "og:description", content: "Vos projets de construction en cours." },
    ],
  }),
  component: Projets,
});

function Projets() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [clientType, setClientType] = useState<"particulier" | "professionnel">("particulier");
  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data, error } = await supabase.from("projects").select("id,title,stage,client_type,updated_at").order("updated_at", { ascending: false });
      if (error) throw error;
      return data;
    },
  });

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    const t = title.trim().slice(0, 120) || "Nouveau projet";
    const { data, error } = await supabase.from("projects").insert({ title: t, client_type: clientType, user_id: user.id }).select("id").single();
    if (error) return toast.error("Création impossible.");
    navigate({ to: "/projets/$id", params: { id: data.id } });
  }

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <h1 className="text-4xl font-bold">Mes projets</h1>
      <form onSubmit={create} className="mt-8 border border-border bg-card p-6 grid gap-4 md:grid-cols-[1fr_auto_auto] items-end">
        <div>
          <p className="label-mono text-muted-foreground mb-2">Nouveau projet</p>
          <Input placeholder="Ex : Villa familiale à Bingerville" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} />
        </div>
        <div className="flex border border-border">
          {(["particulier", "professionnel"] as const).map((c) => (
            <button type="button" key={c} onClick={() => setClientType(c)}
              className={`px-4 py-2 text-sm capitalize ${clientType === c ? "bg-ink text-ink-foreground" : "text-muted-foreground"}`}>{c}</button>
          ))}
        </div>
        <Button type="submit">Créer</Button>
      </form>

      <div className="mt-10 space-y-3">
        {isLoading && <p className="text-muted-foreground">Chargement…</p>}
        {data?.length === 0 && <p className="text-muted-foreground">Aucun projet pour l'instant.</p>}
        {data?.map((p) => (
          <Link key={p.id} to="/projets/$id" params={{ id: p.id }} className="flex items-center justify-between border border-border bg-card p-5 hover:border-primary">
            <div>
              <p className="font-display text-lg font-semibold">{p.title}</p>
              <p className="text-sm text-muted-foreground capitalize">{p.client_type}</p>
            </div>
            <span className="label-mono text-primary">{STAGES.find((s) => s.key === p.stage)?.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
