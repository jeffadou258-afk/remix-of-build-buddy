<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Agent chat streams through `src/routes/api/chat.ts` (bearer-token checked, project read under RLS); the system prompt lives in `src/lib/ai/agent-prompt.server.ts`. Why: keeps AI key and prompt server-side.
- Conversation and stage are stored on the `projects` row (`messages` jsonb); stage advances when the agent emits `[[ETAPE:x]]`. Why: one row per project keeps the MVP simple.
- Building model (`src/lib/bim/schema.ts`, versioned JSON on `projects.building_model`) is the single source for the in-browser 3D viewer and future Blender renders (`render_jobs.model_snapshot`); the agent emits it as a ```bim block. Why: Blender/RunPod can be plugged in later without reshaping data.
- Every building-model element carries a data status (missing = hypothesis), the model lists unknowns and app-filled defaults, and extracted models are never marked validated. Why: the 3D must never present invented data as proven.
- The "Informations" form (`src/components/extraction/InputsPanel.tsx`) reads/writes `projects.inputs` in the exact `construction-agent.inputs` v1 format of `engines/extraction/engine.py` and mirrors only its `edit()` semantics (`src/lib/extraction/inputs.ts`); extraction itself stays in the Python repo. Why: no second business engine in Lovable.
- Projects linked to ConstructionAgent (`projects.ca_project_id`) talk only to the real API /v1 through the server relay `src/routes/api/ca.$.ts` (session + RLS ownership check, `CA_API_KEY`/`CA_API_URL` server-side, allowlist in `src/lib/ca/allowlist.ts`); the local `/api/chat` assistant remains only for unlinked legacy projects. Why: no second business engine and no API key in the browser.
