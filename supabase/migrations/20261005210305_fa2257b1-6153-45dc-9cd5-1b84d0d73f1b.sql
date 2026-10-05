create type public.project_stage as enum ('decouverte','programme','conception','plans','documentation','livre');

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text not null default 'Nouveau projet',
  client_type text not null default 'particulier',
  stage public.project_stage not null default 'decouverte',
  messages jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
grant select, insert, update, delete on public.projects to authenticated;
grant all on public.projects to service_role;
alter table public.projects enable row level security;
create policy "own select" on public.projects for select to authenticated using (auth.uid() = user_id);
create policy "own insert" on public.projects for insert to authenticated with check (auth.uid() = user_id);
create policy "own update" on public.projects for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own delete" on public.projects for delete to authenticated using (auth.uid() = user_id);

create or replace function public.touch_updated_at() returns trigger language plpgsql set search_path = public as $$
begin new.updated_at = now(); return new; end; $$;
create trigger projects_touch before update on public.projects for each row execute function public.touch_updated_at();