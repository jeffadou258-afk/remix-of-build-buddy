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
