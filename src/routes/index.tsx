import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { HomeHeader } from "@/components/home/HomeHeader";
import { StepsCarousel } from "@/components/home/StepsCarousel";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { ca } from "@/lib/ca/client";

const PENDING_KEY = "ca:home-description";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ConstructionAgent — De l'idée à la construction" },
      { name: "description", content: "L'intelligence qui transforme votre vision en projet : programme, conception, 3D et documents, avec votre validation à chaque étape." },
      { property: "og:title", content: "ConstructionAgent — De l'idée à la construction" },
      { property: "og:description", content: "Décrivez votre projet. ConstructionAgent l'analyse, identifie ce qui manque et vous accompagne jusqu'à la construction." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [{ rel: "preload", as: "image", href: "/constructionagent/hero.webp", type: "image/webp" }],
  }),
  component: Home,
});

const PARCOURS = [
  ["Idée", "Vous décrivez simplement votre projet."],
  ["Programme", "Pièces, surfaces et besoins structurés."],
  ["Conception", "Des variantes adaptées à votre terrain."],
  ["Validation", "Vous choisissez avant toute suite."],
  ["Structure", "Un concept structurel indicatif."],
  ["3D / BIM", "Une maquette fidèle aux données du projet."],
  ["Documents", "Plans, notices et contrôle qualité."],
  ["Construction", "Un dossier prêt pour vos professionnels."],
] as const;

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll<HTMLElement>(".reveal");
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } }), { threshold: 0.15 });
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

function PrimaryCta({ children, to = "/projets", onImage = false }: { children: React.ReactNode; to?: "/projets"; onImage?: boolean }) {
  return (
    <Link to={to} className={`group inline-flex items-center gap-3 rounded-full px-8 py-4 text-sm tracking-wide transition-colors ${onImage ? "bg-on-image text-foreground hover:bg-champagne" : "bg-foreground text-background hover:bg-stone"}`}>
      {children}
      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
    </Link>
  );
}

function Describe() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const saved = sessionStorage.getItem(PENDING_KEY);
    if (saved) setText(saved);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const t = text.trim();
    if (!t) { ref.current?.focus(); return; }
    if (!user) {
      sessionStorage.setItem(PENDING_KEY, t.slice(0, 5000));
      toast("Connectez-vous pour lancer votre projet. Votre description est conservée.");
      navigate({ to: "/auth" });
      return;
    }
    setBusy(true);
    // Flux réel existant : projet → liaison ConstructionAgent → premier message (extraction réelle).
    const title = t.split(/[.\n]/)[0].slice(0, 80) || "Nouveau projet";
    const { data, error } = await supabase.from("projects").insert({ title, client_type: "particulier", user_id: user.id }).select("id").single();
    if (error || !data) { setBusy(false); toast.error("Création impossible."); return; }
    try {
      await ca(data.id, "POST", "link");
      await ca(data.id, "POST", "messages", { text: t.slice(0, 5000) });
      sessionStorage.removeItem(PENDING_KEY);
    } catch (err) {
      toast.error(`Projet créé, mais ConstructionAgent n'a pas répondu : ${(err as Error).message}`);
    }
    navigate({ to: "/projets/$id", params: { id: data.id } });
  }

  return (
    <section id="services" className="mx-auto max-w-4xl px-5 py-28 md:py-40">
      <div className="reveal text-center">
        <h2 className="text-4xl md:text-6xl">DÉCRIVEZ VOTRE PROJET.</h2>
        <p className="mt-4 text-muted-foreground">Une idée suffit pour commencer.</p>
      </div>
      <form onSubmit={submit} className="reveal mt-14">
        <label htmlFor="describe" className="sr-only">Description du projet</label>
        <textarea
          id="describe"
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={5000}
          rows={4}
          placeholder="Décrivez simplement ce que vous souhaitez construire..."
          className="w-full resize-none border-0 border-b border-border bg-transparent pb-5 font-serif text-2xl leading-snug outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-foreground md:text-3xl"
        />
        <div className="mt-6 grid grid-cols-1 items-center gap-6 sm:grid-cols-[minmax(0,1fr)_auto]">
          <button type="button" onClick={() => setText("Villa R+1 de 4 chambres sur 600 m²")} className="min-w-0 text-left text-sm italic text-muted-foreground hover:text-foreground">
            Exemple : « Villa R+1 de 4 chambres sur 600 m²... »
          </button>
          <button type="submit" disabled={busy} className="group inline-flex items-center justify-center gap-3 rounded-full bg-foreground px-8 py-4 text-sm tracking-wide text-background transition-colors hover:bg-stone disabled:opacity-60">
            {busy ? "Création…" : "Lancer mon projet"}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </form>
    </section>
  );
}

function Home() {
  useReveal();
  return (
    <div className="luxe min-h-screen overflow-x-hidden">
      <HomeHeader />

      {/* HERO */}
      <section className="relative h-[100svh] min-h-[560px] overflow-hidden text-on-image">
        <img src="/constructionagent/hero.webp" alt="Villa contemporaine avec piscine à débordement au coucher du soleil" fetchPriority="high" decoding="async" className="luxe-zoom absolute inset-0 h-full w-full object-cover object-[70%_center]" />
        <div className="shade-hero absolute inset-0" />
        <div className="relative mx-auto flex h-full max-w-7xl flex-col justify-end px-5 pb-20 md:px-8 md:pb-28">
          <p className="luxe-rise text-[11px] tracking-[0.4em] text-champagne">CONSTRUCTIONAGENT</p>
          <h1 className="luxe-rise mt-5 text-5xl leading-[0.98] [animation-delay:120ms] sm:text-6xl md:text-8xl">
            DE L’IDÉE À LA<br />CONSTRUCTION.
          </h1>
          <p className="luxe-rise mt-6 max-w-xl text-lg opacity-90 [animation-delay:240ms] md:text-xl">L’intelligence qui transforme votre vision en projet.</p>
          <div className="luxe-rise mt-10 [animation-delay:360ms]"><PrimaryCta onImage>Commencer mon projet</PrimaryCta></div>
        </div>
      </section>

      <StepsCarousel />

      <Describe />

      {/* PARCOURS */}
      <section id="parcours" className="border-t border-border bg-card">
        <div className="mx-auto max-w-7xl px-5 py-28 md:px-8 md:py-36">
          <h2 className="reveal max-w-3xl text-4xl md:text-6xl">DE L’IDÉE À LA CONSTRUCTION.</h2>
          <ol className="mt-16 grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">
            {PARCOURS.map(([t, d], k) => (
              <li key={t} className="reveal bg-card p-8" style={{ transitionDelay: `${(k % 4) * 80}ms` }}>
                <p className="text-xs tabular-nums tracking-[0.3em] text-stone">{String(k + 1).padStart(2, "0")}</p>
                <h3 className="mt-6 text-3xl">{t}</h3>
                <p className="mt-3 text-sm text-muted-foreground">{d}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* INTELLIGENCE */}
      <section id="a-propos" className="mx-auto max-w-7xl px-5 py-28 md:px-8 md:py-36">
        <div className="grid gap-16 lg:grid-cols-[1.1fr_1fr] lg:items-end">
          <div className="reveal">
            <h2 className="text-4xl md:text-6xl">UNE IA QUI COMPREND VOTRE PROJET.</h2>
            <p className="mt-6 max-w-md text-muted-foreground">ConstructionAgent analyse votre projet, identifie ce qui manque et vous accompagne à chaque étape.</p>
          </div>
          <div className="grid grid-cols-3 border-t border-foreground">
            {["Comprendre", "Analyser", "Agir"].map((w, k) => (
              <div key={w} className="reveal pt-6" style={{ transitionDelay: `${k * 100}ms` }}>
                <p className="text-xs tracking-[0.3em] text-stone">{String(k + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-serif text-2xl md:text-3xl">{w}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CONTRÔLE HUMAIN */}
      <section className="bg-foreground text-background">
        <div className="mx-auto max-w-7xl px-5 py-28 md:px-8 md:py-36">
          <h2 className="reveal text-4xl md:text-6xl">VOUS GARDEZ LE CONTRÔLE.</h2>
          <p className="reveal mt-6 font-serif text-2xl italic opacity-80 md:text-3xl">L’IA avance.<br />Vous validez.</p>
          <div className="reveal mt-16 flex flex-col gap-6 md:flex-row md:items-center md:gap-0">
            {["Analyse", "Proposition", "Validation", "Suite du projet"].map((w, k, a) => (
              <div key={w} className="flex items-center gap-6 md:flex-1">
                <span className={`text-lg tracking-wide ${w === "Validation" ? "text-champagne" : ""}`}>{w}</span>
                {k < a.length - 1 && <span aria-hidden className="hidden h-px flex-1 bg-background/25 md:block" />}
                {k < a.length - 1 && <span aria-hidden className="text-background/40 md:hidden">↓</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3D */}
      <section className="relative h-[90vh] min-h-[520px] overflow-hidden text-on-image">
        <img src="/constructionagent/visualisez.webp" alt="Rendu 3D d'une villa contemporaine" loading="lazy" decoding="async" className="absolute inset-0 h-full w-full object-cover" />
        <div className="shade-bottom absolute inset-0" />
        <div className="relative mx-auto flex h-full max-w-7xl flex-col justify-end px-5 pb-20 md:px-8 md:pb-28">
          <h2 className="reveal text-5xl md:text-7xl">VOYEZ AVANT DE CONSTRUIRE.</h2>
          <p className="reveal mt-4 text-lg opacity-90">Votre projet prend forme en 3D.</p>
          <div className="reveal mt-10"><PrimaryCta onImage>Explorer la visualisation</PrimaryCta></div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="relative overflow-hidden text-on-image">
        <img src="/constructionagent/final.webp" alt="" loading="lazy" decoding="async" className="absolute inset-0 h-full w-full object-cover" />
        <div className="shade-hero absolute inset-0" />
        <div className="relative mx-auto max-w-4xl px-5 py-40 text-center md:py-56">
          <h2 className="reveal text-5xl md:text-7xl">VOTRE PROJET COMMENCE ICI.</h2>
          <p className="reveal mt-5 text-lg opacity-90">De l’idée à la construction.</p>
          <div className="reveal mt-10"><PrimaryCta onImage>Commencer mon projet</PrimaryCta></div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="mx-auto max-w-7xl px-5 py-16 md:px-8">
        <div className="grid gap-12 md:grid-cols-[2fr_1fr_1fr]">
          <div>
            <p className="text-[13px] font-semibold tracking-[0.32em]">CONSTRUCTIONAGENT</p>
            <p className="mt-4 max-w-sm text-xs text-muted-foreground">Documents conceptuels, sans valeur contractuelle. À faire valider par un architecte et un ingénieur agréés.</p>
          </div>
          <nav className="flex flex-col gap-3 text-sm text-muted-foreground" aria-label="Navigation">
            <Link to="/projets" className="hover:text-foreground">Projets</Link>
            <a href="#services" className="hover:text-foreground">Services</a>
            <a href="#parcours" className="hover:text-foreground">Comment ça marche</a>
            <Link to="/tarifs" className="hover:text-foreground">Tarifs</Link>
            <a href="#a-propos" className="hover:text-foreground">À propos</a>
          </nav>
          <nav className="flex flex-col gap-3 text-sm text-muted-foreground" aria-label="Compte">
            <Link to="/auth" className="hover:text-foreground">Connexion</Link>
            <Link to="/projets" className="hover:text-foreground">Commencer</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
