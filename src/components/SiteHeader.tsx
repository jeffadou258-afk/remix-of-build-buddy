import { Link, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";

export function SiteHeader() {
  const { user } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur sticky top-0 z-30">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center bg-ink text-ink-foreground font-display font-bold">B</span>
          <span className="font-display text-lg font-semibold">Bâtir</span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-3">
          <Link to="/tarifs" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground">Tarifs</Link>
          {user ? (
            <>
              <Link to="/projets" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground">Mes projets</Link>
              <Button variant="ghost" size="sm" onClick={async () => { await supabase.auth.signOut(); navigate({ to: "/" }); }}>
                Déconnexion
              </Button>
            </>
          ) : (
            <Button asChild size="sm"><Link to="/auth">Se connecter</Link></Button>
          )}
        </nav>
      </div>
    </header>
  );
}
