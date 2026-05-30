-- Rotina Viva Pro — Fase 1: Postgres + Auth + RLS + JSONB
-- Executar no SQL Editor do Supabase ou via CLI: supabase db push

-- ---------------------------------------------------------------------------
-- Perfis (RBAC) — 1:1 com auth.users
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  role text not null check (role in ('gestao', 'educador', 'familia')),
  display_name text not null,
  student_id integer,
  allow_mutations boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.profiles is 'RBAC: gestão, educador, família (vinculada a student_id)';

-- ---------------------------------------------------------------------------
-- Alunos (substitui info_alunos.csv)
-- ---------------------------------------------------------------------------
create table if not exists public.students (
  id integer primary key,
  name text not null,
  class_name text,
  allergies text,
  parent_contact text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles
  add constraint profiles_student_id_fkey
  foreign key (student_id) references public.students (id)
  on delete set null;

create index if not exists idx_students_name on public.students using gin (to_tsvector('portuguese', name));

-- ---------------------------------------------------------------------------
-- Diário (substitui diario_estruturado.csv)
-- ---------------------------------------------------------------------------
create table if not exists public.diary_entries (
  id integer primary key,
  student_id integer not null references public.students (id) on delete cascade,
  entry_date date,
  breakfast text,
  lunch text,
  afternoon_snack text,
  extra_dinner text,
  bathroom_changes integer,
  bowel_movement text,
  medications text,
  sleep_start text,
  sleep_end text,
  sleep_quality text,
  day_activity text,
  social_interaction text,
  teacher_note text,
  extras jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_diary_student_date on public.diary_entries (student_id, entry_date desc);

-- ---------------------------------------------------------------------------
-- Chat IA — mensagens em JSONB (substitui ficheiros .rotina_chat/)
-- ---------------------------------------------------------------------------
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  data_source_mode text not null default 'auto'
    check (data_source_mode in ('auto', 'structured', 'documents')),
  crew_ai_enabled boolean not null default false,
  predictive_ml_enabled boolean not null default false,
  messages jsonb not null default '[]'::jsonb,
  report_state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_chat_sessions_user on public.chat_sessions (user_id, updated_at desc);

-- ---------------------------------------------------------------------------
-- Chat directo família ↔ educador
-- ---------------------------------------------------------------------------
create table if not exists public.direct_messages (
  id uuid primary key default gen_random_uuid(),
  student_id integer not null references public.students (id) on delete cascade,
  sender_id uuid not null references auth.users (id) on delete cascade,
  sender_role text not null check (sender_role in ('gestao', 'educador', 'familia')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_direct_messages_student on public.direct_messages (student_id, created_at);

-- ---------------------------------------------------------------------------
-- Trigger: perfil automático ao registar (metadata em raw_user_meta_data)
-- ---------------------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, role, display_name, student_id, allow_mutations, metadata)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'role', 'familia'),
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)),
    nullif(new.raw_user_meta_data ->> 'student_id', '')::integer,
    coalesce((new.raw_user_meta_data ->> 'allow_mutations')::boolean, false),
    coalesce(new.raw_user_meta_data -> 'metadata', '{}'::jsonb)
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Helpers RLS
-- ---------------------------------------------------------------------------
create or replace function public.current_profile_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where id = auth.uid();
$$;

create or replace function public.current_profile_student_id()
returns integer
language sql
stable
security definer
set search_path = public
as $$
  select student_id from public.profiles where id = auth.uid();
$$;

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.students enable row level security;
alter table public.diary_entries enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.direct_messages enable row level security;

-- profiles: cada um vê o próprio; gestão vê todos
create policy profiles_select_own on public.profiles
  for select using (id = auth.uid() or public.current_profile_role() = 'gestao');

create policy profiles_update_own on public.profiles
  for update using (id = auth.uid());

-- students
create policy students_select_staff on public.students
  for select using (public.current_profile_role() in ('gestao', 'educador'));

create policy students_select_family on public.students
  for select using (
    public.current_profile_role() = 'familia'
    and id = public.current_profile_student_id()
  );

create policy students_write_gestao on public.students
  for all using (public.current_profile_role() = 'gestao')
  with check (public.current_profile_role() = 'gestao');

-- diary_entries
create policy diary_select_staff on public.diary_entries
  for select using (public.current_profile_role() in ('gestao', 'educador'));

create policy diary_select_family on public.diary_entries
  for select using (
    public.current_profile_role() = 'familia'
    and student_id = public.current_profile_student_id()
  );

create policy diary_write_staff on public.diary_entries
  for insert with check (
    public.current_profile_role() in ('gestao', 'educador')
    and (
      public.current_profile_role() = 'gestao'
      or exists (
        select 1 from public.profiles p
        where p.id = auth.uid() and p.allow_mutations = true
      )
    )
  );

create policy diary_update_staff on public.diary_entries
  for update using (
    public.current_profile_role() in ('gestao', 'educador')
    and (
      public.current_profile_role() = 'gestao'
      or exists (
        select 1 from public.profiles p
        where p.id = auth.uid() and p.allow_mutations = true
      )
    )
  );

create policy diary_delete_gestao on public.diary_entries
  for delete using (public.current_profile_role() = 'gestao');

-- chat_sessions: só o dono
create policy chat_sessions_owner on public.chat_sessions
  for all using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- direct_messages: staff vê tudo; família só do filho
create policy direct_select_staff on public.direct_messages
  for select using (public.current_profile_role() in ('gestao', 'educador'));

create policy direct_select_family on public.direct_messages
  for select using (
    public.current_profile_role() = 'familia'
    and student_id = public.current_profile_student_id()
  );

create policy direct_insert_authenticated on public.direct_messages
  for insert with check (sender_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Storage (PDFs institucionais — Fase 2 RAG)
-- Bucket criado no dashboard ou CLI; política base:
-- ---------------------------------------------------------------------------
-- insert into storage.buckets (id, name, public) values ('rotina-documents', 'rotina-documents', false);
-- Políticas de storage aplicar após criar bucket (ver docs/FASE1_SUPABASE.md)
