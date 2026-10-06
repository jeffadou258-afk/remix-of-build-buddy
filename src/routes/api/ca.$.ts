/**
 * Relais serveur vers l'API ConstructionAgent v1.
 * URL : /api/ca/{projetLovableId}/{sous-chemin}  — ou  POST /api/ca/{projetLovableId}/link
 * 1. vérifie la session ; 2. lit le projet sous RLS (appartenance) ;
 * 3. ajoute Bearer CA_API_KEY + X-Owner-Id ; 4. n'autorise que la liste blanche.
 * Aucune logique métier : les réponses de ConstructionAgent sont renvoyées telles quelles.
 */
import { createFileRoute } from "@tanstack/react-router";
import { createClient } from "@supabase/supabase-js";
import { isAllowed, upstreamPath } from "@/lib/ca/allowlist";
import { canDecideGate, isGateDecisionPath } from "@/lib/security/permissions";
import { audit, isSuspended, requestMeta } from "@/lib/security/guard.server";
import { redactBody } from "@/lib/security/redact.server";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

async function callCa(method: string, path: string, ownerId: string, body?: string) {
  const base = process.env["CA_API_URL"];
  const key = process.env["CA_API_KEY"];
  if (!base || !key) return json(503, { error: "Backend ConstructionAgent non configuré." });
  let res: Response;
  try {
    res = await fetch(base.replace(/\/+$/, "") + path, {
      method,
      headers: { Authorization: `Bearer ${key}`, "X-Owner-Id": ownerId, "Content-Type": "application/json" },
      body: body ?? null,
      signal: AbortSignal.timeout(180_000),
    });
  } catch {
    return json(502, { error: "Backend ConstructionAgent injoignable." });
  }
  const text = redactBody(await res.text()); // aucun secret ne ressort du relais
  return new Response(text, { status: res.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

async function handle(request: Request, splat: string) {
  const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!token) return json(401, { error: "Connexion requise." });
  const supabase = createClient(process.env["SUPABASE_URL"]!, process.env["SUPABASE_PUBLISHABLE_KEY"]!, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { headers: { Authorization: `Bearer ${token}` } },
  });
  const { data: u, error: ue } = await supabase.auth.getUser(token);
  if (ue || !u.user) return json(401, { error: "Session invalide." });
  if (await isSuspended(supabase, u.user.id)) return json(403, { error: "Compte suspendu." });

  const [projectId = "", ...restParts] = splat.split("/");
  const sub = restParts.join("/");
  if (!UUID.test(projectId)) return json(404, { error: "Projet introuvable." });

  const { data: project } = await supabase.from("projects").select("id, title, ca_project_id, user_id").eq("id", projectId).maybeSingle();
  if (!project) return json(404, { error: "Projet introuvable." });

  // Gate métier : seul le propriétaire du projet décide, quel que soit le rôle de l'appelant.
  if (isGateDecisionPath(sub) && !canDecideGate(u.user.id, project.user_id)) {
    await audit(supabase, "gates.decide", "gates.decide_on_behalf", "denied", { targetType: "project", targetId: project.id, ...requestMeta(request) });
    return json(403, { error: "Seul le client propriétaire peut décider de ce Gate." });
  }

  const method = request.method.toUpperCase();
  let body: string | undefined;
  if (method === "POST" || method === "PATCH") {
    body = await request.text();
    if (body.length > 20_000) return json(413, { error: "Requête trop volumineuse." });
    if (!body) body = "{}";
  }

  // Création du projet ConstructionAgent correspondant (POST /v1/projects)
  if (sub === "link" && method === "POST") {
    if (project.ca_project_id) return json(200, { ca_project_id: project.ca_project_id, created: false });
    const r = await callCa("POST", "/v1/projects", u.user.id, JSON.stringify({ title: project.title }));
    if (r.status !== 201) return r;
    const created = (await r.json()) as { project?: { id?: string } };
    const caId = created.project?.id;
    if (!caId) return json(502, { error: "Réponse ConstructionAgent inattendue." });
    const { error } = await supabase.from("projects").update({ ca_project_id: caId }).eq("id", project.id);
    if (error) return json(500, { error: "Liaison du projet impossible." });
    return json(201, { ca_project_id: caId, created: true });
  }

  if (!project.ca_project_id) return json(409, { error: "Projet non relié à ConstructionAgent." });
  if (!isAllowed(method, sub)) return json(404, { error: "Adresse non disponible." });
  return callCa(method, upstreamPath(project.ca_project_id, sub), u.user.id, body);
}

export const Route = createFileRoute("/api/ca/$")({
  server: {
    handlers: {
      GET: ({ request, params }) => handle(request, params._splat ?? ""),
      POST: ({ request, params }) => handle(request, params._splat ?? ""),
      PATCH: ({ request, params }) => handle(request, params._splat ?? ""),
    },
  },
});
