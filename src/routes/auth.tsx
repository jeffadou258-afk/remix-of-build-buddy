import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SiteHeader } from "@/components/SiteHeader";
import { supabase } from "@/integrations/supabase/client";
import { lovable } from "@/integrations/lovable/index";
import { useAuth } from "@/hooks/useAuth";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Connexion — Bâtir" },
      { name: "description", content: "Connectez-vous ou créez un compte pour démarrer votre projet de construction." },
      { property: "og:title", content: "Connexion — Bâtir" },
      { property: "og:description", content: "Accédez à vos projets de construction." },
    ],
  }),
  component: AuthPage,
});

const schema = z.object({
  email: z.string().trim().email("Email invalide").max(255),
  password: z.string().min(6, "6 caractères minimum").max(72),
});

function AuthPage() {
  const [mode, setMode] = useState<"in" | "up">("in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { if (user) navigate({ to: "/projets" }); }, [user, navigate]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = schema.safeParse({ email, password });
    if (!parsed.success) return toast.error(parsed.error.issues[0].message);
    setBusy(true);
    const { error } = mode === "in"
      ? await supabase.auth.signInWithPassword(parsed.data)
      : await supabase.auth.signUp({ ...parsed.data, options: { emailRedirectTo: window.location.origin + "/projets" } });
    setBusy(false);
    if (error) return toast.error(error.message);
    if (mode === "up") toast.success("Compte créé. Vérifiez votre boîte mail pour confirmer.");
  }

  async function google() {
    const r = await lovable.auth.signInWithOAuth("google", { redirect_uri: window.location.origin });
    if (r.error) toast.error("Connexion Google impossible.");
  }

  return (
    <div className="min-h-screen bg-grid">
      <SiteHeader />
      <div className="mx-auto max-w-sm px-5 py-16">
        <div className="border border-border bg-card p-8">
          <h1 className="text-3xl font-bold">{mode === "in" ? "Connexion" : "Créer un compte"}</h1>
          <Button variant="outline" className="mt-6 w-full" onClick={google}>Continuer avec Google</Button>
          <div className="my-6 label-mono text-center text-muted-foreground">ou</div>
          <form onSubmit={submit} className="space-y-4">
            <div><Label htmlFor="email">Email</Label><Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
            <div><Label htmlFor="pw">Mot de passe</Label><Input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></div>
            <Button type="submit" className="w-full" disabled={busy}>{mode === "in" ? "Se connecter" : "Créer mon compte"}</Button>
          </form>
          <button className="mt-4 w-full text-sm text-muted-foreground hover:text-foreground" onClick={() => setMode(mode === "in" ? "up" : "in")}>
            {mode === "in" ? "Pas encore de compte ? Inscription" : "Déjà inscrit ? Connexion"}
          </button>
        </div>
      </div>
    </div>
  );
}
