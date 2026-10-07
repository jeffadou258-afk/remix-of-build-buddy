import { Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";

const NAV = [
  { label: "Services", href: "#services" },
  { label: "Projets", to: "/projets" as const },
  { label: "Comment ça marche", href: "#parcours" },
  { label: "Tarifs", to: "/tarifs" as const },
  { label: "À propos", href: "#a-propos" },
];

export function HomeHeader() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [solid, setSolid] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const on = () => setSolid(window.scrollY > 40);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  const light = !solid && !open;
  const tone = light ? "text-on-image" : "text-foreground";
  const linkCls = `text-[13px] tracking-wide transition-opacity hover:opacity-100 ${light ? "opacity-85" : "opacity-70"}`;

  const items = NAV.map((n) =>
    n.to ? (
      <Link key={n.label} to={n.to} className={linkCls} onClick={() => setOpen(false)}>{n.label}</Link>
    ) : (
      <a key={n.label} href={n.href} className={linkCls} onClick={() => setOpen(false)}>{n.label}</a>
    ),
  );

  return (
    <header className={`fixed inset-x-0 top-0 z-40 transition-colors duration-500 ${light ? "bg-transparent" : "border-b border-border bg-background/90 backdrop-blur-md"} ${tone}`}>
      <div className="mx-auto grid h-16 max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 md:h-20 md:px-8 lg:grid-cols-[auto_1fr_auto]">
        <Link to="/" className="min-w-0 truncate text-[13px] font-semibold tracking-[0.32em]">CONSTRUCTIONAGENT</Link>
        <nav className="hidden items-center justify-center gap-8 lg:flex" aria-label="Navigation principale">{items}</nav>
        <div className="flex shrink-0 items-center gap-3">
          {user ? (
            <>
              <Link to="/projets" className={`hidden sm:inline ${linkCls}`}>Mes projets</Link>
              <button className={`hidden sm:inline ${linkCls}`} onClick={async () => { await supabase.auth.signOut(); navigate({ to: "/" }); }}>Déconnexion</button>
            </>
          ) : (
            <Link to="/auth" className={`hidden sm:inline ${linkCls}`}>Connexion</Link>
          )}
          <Link to="/projets" className={`hidden rounded-full border px-5 py-2 text-[13px] tracking-wide transition-colors sm:inline-flex ${light ? "border-on-image/60 hover:bg-on-image hover:text-foreground" : "border-foreground bg-foreground text-background hover:bg-transparent hover:text-foreground"}`}>Commencer</Link>
          <button className="lg:hidden" aria-label={open ? "Fermer le menu" : "Ouvrir le menu"} aria-expanded={open} onClick={() => setOpen((o) => !o)}>
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t border-border bg-background px-5 pb-8 pt-4 lg:hidden">
          <nav className="flex flex-col gap-5 text-foreground [&>*]:text-lg [&>*]:opacity-90">{items}</nav>
          <div className="mt-8 flex flex-col gap-3">
            {!user && <Link to="/auth" className="rounded-full border border-foreground py-3 text-center text-sm">Connexion</Link>}
            <Link to="/projets" className="rounded-full bg-foreground py-3 text-center text-sm text-background">Commencer</Link>
          </div>
        </div>
      )}
    </header>
  );
}
