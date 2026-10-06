/** Appels navigateur → relais /api/ca (jamais directement vers ConstructionAgent). */
import { supabase } from "@/integrations/supabase/client";

export class CaError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function ca<T = unknown>(projectId: string, method: "GET" | "POST" | "PATCH", sub = "", body?: unknown): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const res = await fetch(`/api/ca/${projectId}${sub ? "/" + sub : ""}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {}),
    },
    body: body === undefined ? (method === "GET" ? undefined : "{}") : JSON.stringify(body),
  });
  const json = (await res.json().catch(() => ({}))) as { error?: string };
  if (!res.ok) throw new CaError(res.status, json.error ?? `Erreur ${res.status}`);
  return json as T;
}

export type CaGate = { status: string; opened_at: string | null; decision: unknown };
export type CaState = { status: string; completed: string[]; pending_gate: string | null; last_run_id: string | null; updated_at: string };
export type CaStep = { engine: string; status: string; cause?: string; details?: Record<string, unknown> };
export type CaRun = { id: string; at: string; started_at_engine: string | null; status: string; stopped_at: string | null; steps: CaStep[] };
export type CaMessage = { id: string; role: string; text: string; at: string };
