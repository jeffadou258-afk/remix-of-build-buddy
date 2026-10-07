import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/SiteHeader";
import { pageHead, serviceNode, breadcrumbNode } from "@/lib/seo";

export const Route = createFileRoute("/tarifs")({
  head: () => ({
    ...pageHead({
      title: "Tarifs — ConstructionAgent, paiement par projet",
      description:
        "Payez par projet : découverte gratuite, forfait Particulier à 50 000 FCFA par maison, forfait Professionnel à 150 000 FCFA tous bâtiments.",
      path: "/tarifs",
      jsonLd: [
        serviceNode({
          name: "Forfait Particulier — conception de maison",
          description:
            "Programme des espaces, conception et plans, notice et budget indicatif pour un projet de maison.",
          path: "/tarifs",
          offer: {
            name: "Particulier",
            price: "50000",
            currency: "XOF",
            description: "Par projet de maison.",
          },
        }),
        serviceNode({
          name: "Forfait Professionnel — tous bâtiments",
          description:
            "Tout le forfait Particulier, plus les projets multi-niveaux et une documentation détaillée par lot.",
          path: "/tarifs",
          offer: {
            name: "Professionnel",
            price: "150000",
            currency: "XOF",
            description: "Par projet, tous bâtiments.",
          },
        }),
        breadcrumbNode([
          { name: "Accueil", path: "/" },
          { name: "Tarifs", path: "/tarifs" },
        ]),
      ],
    }),
  }),
  component: Tarifs,
});

const plans = [
  { name: "Découverte", price: "Gratuit", desc: "Pour cadrer votre idée.", items: ["Questions de l'agent", "Synthèse de votre besoin"] },
  { name: "Particulier", price: "50 000 FCFA", desc: "Par projet de maison.", items: ["Programme des espaces", "Conception et plans", "Notice et budget indicatif"], featured: true },
  { name: "Professionnel", price: "150 000 FCFA", desc: "Par projet, tous bâtiments.", items: ["Tout le forfait Particulier", "Projets multi-niveaux", "Documentation détaillée par lot"] },
];

function Tarifs() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <section className="mx-auto max-w-6xl px-5 py-16">
        <p className="label-mono text-primary">Paiement par projet</p>
        <h1 className="mt-2 text-4xl font-bold md:text-5xl">Vous payez quand le projet avance.</h1>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {plans.map((p) => (
            <div key={p.name} className={`border p-8 ${p.featured ? "bg-ink text-ink-foreground border-ink" : "bg-card border-border"}`}>
              <p className="label-mono opacity-70">{p.name}</p>
              <p className="mt-4 font-display text-4xl font-bold">{p.price}</p>
              <p className="mt-1 text-sm opacity-70">{p.desc}</p>
              <ul className="mt-6 space-y-2 text-sm">
                {p.items.map((i) => <li key={i}>— {i}</li>)}
              </ul>
              <Button asChild className="mt-8 w-full" variant={p.featured ? "default" : "outline"}>
                <Link to="/projets">Commencer</Link>
              </Button>
            </div>
          ))}
        </div>
        <p className="mt-8 text-sm text-muted-foreground">Le paiement en ligne arrive bientôt.</p>
      </section>
    </div>
  );
}
