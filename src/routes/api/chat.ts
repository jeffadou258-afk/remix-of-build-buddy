import { createFileRoute } from "@tanstack/react-router";
import { createOpenAI } from "@ai-sdk/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import { createClient } from "@supabase/supabase-js";
import { isSuspended } from "@/lib/security/guard.server";
import {
  createLovableAiGatewayRunIdFetch,
  getLovableAiGatewayRunId,
  withLovableAiGatewayRunIdHeader,
} from "@/lib/ai/run-id.server";
import { buildAgentInstructions } from "@/lib/ai/agent-prompt.server";

const MODEL = "openai/gpt-6-astra";

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export const Route = createFileRoute("/api/chat")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
        if (!token) return json(401, { error: "Connexion requise." });

        const url = process.env["SUPABASE_URL"]!;
        const key = process.env["SUPABASE_PUBLISHABLE_KEY"]!;
        const supabase = createClient(url, key, {
          auth: { persistSession: false },
          global: {
            headers: { Authorization: `Bearer ${token}` },
          },
        });
        const { data: userData, error: userErr } = await supabase.auth.getUser(token);
        if (userErr || !userData.user) return json(401, { error: "Session invalide." });
        if (await isSuspended(supabase, userData.user.id)) return json(403, { error: "Compte suspendu." });

        const body = (await request.json()) as { messages?: UIMessage[]; projectId?: string };
        if (!body.projectId || !Array.isArray(body.messages)) return json(400, { error: "Requête invalide." });
        if (body.messages.length > 200) return json(400, { error: "Conversation trop longue." });

        const { data: project } = await supabase
          .from("projects")
          .select("id, client_type, stage")
          .eq("id", body.projectId)
          .maybeSingle();
        if (!project) return json(404, { error: "Projet introuvable." });

        const apiKey = process.env["LOVABLE_API_KEY"];
        if (!apiKey) return json(500, { error: "Service IA non configuré." });

        const runIdFetch = createLovableAiGatewayRunIdFetch(getLovableAiGatewayRunId(request));
        const provider = createOpenAI({
          baseURL: "https://ai.gateway.lovable.dev/v1",
          apiKey,
          headers: { "Lovable-API-Key": apiKey, "X-Lovable-AIG-SDK": "vercel-ai-sdk" },
          fetch: runIdFetch.fetch,
        });

        const result = streamText({
          model: provider.responses(MODEL),
          instructions: buildAgentInstructions(project.client_type, project.stage),
          messages: await convertToModelMessages(body.messages),
          abortSignal: request.signal,
          providerOptions: {
            openai: {
              forceReasoning: true,
              reasoningEffort: "medium",
              reasoningSummary: "auto",
              store: false,
              include: ["reasoning.encrypted_content"],
            },
          },
        });

        return withLovableAiGatewayRunIdHeader(
          result.toUIMessageStreamResponse({
            sendReasoning: true,
            onError: (e) => {
              const status = (e as { statusCode?: number })?.statusCode;
              if (status === 402) return "Crédits IA épuisés. Réessayez plus tard.";
              if (status === 429) return "Trop de demandes, patientez un instant.";
              return "L'agent n'a pas pu répondre. Réessayez.";
            },
          }),
          runIdFetch,
        );
      },
    },
  },
});
