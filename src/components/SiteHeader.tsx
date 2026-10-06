import { Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getAdminAccess } from "@/lib/security/admin-access.functions";

function AdminLink() {
  const fetchAccess = useServerFn(getAdminAccess);
  const q = useQuery({ queryKey: ["admin-access"], queryFn: () => fetchAccess(), retry: false });
  if (!q.data?.allowed) return null;
  return <Link to="/admin" className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground">Admin</Link>;
}

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
              <AdminLink />
              <Button variant="ghost" size="sm" onClick={async () => { await supabase.auth.signOut(); navigate({ to: "/" }); }}>
                Déconnexion
              </Button>
            </>
          ) : (
            <Button asChild size="sm"><Link to="/auth">Se connecter</Link></Button>
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
