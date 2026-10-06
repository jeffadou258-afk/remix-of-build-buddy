import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { requireAdminSection } from "@/lib/security/admin-access.functions";
import { sectionById, type AdminSectionId } from "@/lib/security/admin-sections";

export function AdminDenied({ message = "Accès refusé. Votre compte n'a pas la permission requise." }: { message?: string | undefined }) {
  return (
    <div className="border border-destructive/40 bg-destructive/5 p-6">
      <p className="font-display text-lg font-semibold">Accès refusé</p>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

export function NotConnected() {
  return (
    <div className="border border-dashed border-border p-8 text-center">
      <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Non mesuré</p>
      <p className="mt-2 text-sm text-muted-foreground">Données non encore branchées. Aucune valeur n'est affichée tant qu'une source réelle n'est pas connectée.</p>
    </div>
  );
}

export function AdminSection({ id, children }: { id: AdminSectionId; children?: ReactNode }) {
  const def = sectionById(id);
  const check = useServerFn(requireAdminSection);
  const q = useQuery({ queryKey: ["admin-section", id], queryFn: () => check({ data: { section: id } }) });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-semibold">{def.label}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{def.description}</p>
        <p className="mt-2 font-mono text-xs text-muted-foreground">Permission requise : {def.anyOf.length > 3 ? "au moins une permission admin" : def.anyOf.join(" ou ")}</p>
      </header>
      {q.isLoading ? (
        <p className="text-sm text-muted-foreground">Vérification des droits…</p>
      ) : q.isError || !q.data?.allowed ? (
        <AdminDenied message={q.data?.suspended ? "Compte suspendu." : undefined} />
      ) : (
        children ?? <NotConnected />
      )}
    </div>
  );
}
