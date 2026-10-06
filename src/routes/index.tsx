import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/SiteHeader";
import hero from "@/assets/hero-villa.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Bâtir — Votre projet de construction conçu par un agent expert" },
      { name: "description", content: "Décrivez votre projet : l'agent Bâtir établit le programme, la conception, les plans et la documentation, étape par étape." },
      { property: "og:title", content: "Bâtir — Agent de conception architecturale" },
      { property: "og:description", content: "Du besoin aux plans : un agent expert qui conçoit votre maison ou votre bâtiment avec vous." },
    ],
  }),
  component: Index,
});

const steps = [
  ["01", "Découverte", "Besoins, budget et analyse de votre terrain."],
  ["02", "Programme", "Espaces, surfaces et liens entre les pièces, contrôlés."],
  ["03", "Conception", "2 à 3 variantes comparées, adaptées au climat. Vous choisissez."],
  ["04", "Plans", "Dimensions, plans par niveau et trame de structure indicative."],
  ["05", "Documentation", "Rapport, notice, budget par lot et contrôle qualité."],
];

function Index() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <section className="bg-grid">
        <div className="mx-auto grid max-w-6xl gap-10 px-5 py-16 md:grid-cols-[1.1fr_1fr] md:py-24 items-center">
          <div>
            <p className="label-mono text-accent">Agent de conception · Côte d'Ivoire & au-delà</p>
            <h1 className="mt-4 text-5xl font-bold leading-[1.02] md:text-7xl">
              De l'idée<br />aux plans,<br /><span className="text-primary">sans détour.</span>
            </h1>
            <p className="mt-6 max-w-md text-lg text-muted-foreground">
              Particuliers et professionnels : décrivez votre projet, l'agent Bâtir le conçoit avec vous, étape par étape. Vous validez chaque étape.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg"><Link to="/projets">Démarrer un projet</Link></Button>
              <Button asChild size="lg" variant="outline"><Link to="/tarifs">Voir les tarifs</Link></Button>
            </div>
          </div>
          <div className="relative">
            <span aria-hidden className="absolute -left-2 -top-2 font-mono text-accent">+</span>
            <span aria-hidden className="absolute -right-2 -top-2 font-mono text-accent">+</span>
            <span aria-hidden className="absolute -bottom-2 -left-2 font-mono text-accent">+</span>
            <span aria-hidden className="absolute -bottom-2 -right-2 font-mono text-accent">+</span>
            <img src={hero} alt="Villa contemporaine en terre de latérite" width={1600} height={1008} className="w-full border border-border object-cover aspect-[4/3]" />
            <div className="absolute -bottom-4 -left-4 border border-primary bg-card px-4 py-3 text-foreground">
              <p className="label-mono text-accent">Règle</p>
              <p className="font-display text-lg">Preuve > affirmation</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20">
        <p className="label-mono text-muted-foreground">Le déroulé</p>
        <h2 className="mt-2 text-3xl font-bold md:text-4xl">Cinq étapes, une validation à chaque fois.</h2>
        <div className="mt-10 grid border-t border-l border-border sm:grid-cols-2 lg:grid-cols-5">
          {steps.map(([n, t, d]) => (
            <div key={n} className="border-b border-r border-border p-6 bg-card">
              <p className="label-mono text-primary">{n}</p>
              <h3 className="mt-3 text-xl font-semibold">{t}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-ink text-ink-foreground">
        <div className="mx-auto max-w-6xl px-5 py-16 md:flex items-center justify-between gap-8">
          <div>
            <h2 className="text-3xl font-bold">Prêt à poser la première pierre ?</h2>
            <p className="mt-2 opacity-70">La découverte de votre projet est gratuite.</p>
          </div>
          <Button asChild size="lg" variant="outline" className="mt-6 md:mt-0 border-ink-foreground/40 bg-transparent text-ink-foreground hover:bg-ink-foreground/10"><Link to="/projets">Commencer gratuitement</Link></Button>
        </div>
      </section>
      <footer className="mx-auto max-w-6xl px-5 py-8 text-xs text-muted-foreground">
        Documents conceptuels, sans valeur contractuelle. À faire valider par un architecte et un ingénieur agréés.
      </footer>
    </div>
  );
}
