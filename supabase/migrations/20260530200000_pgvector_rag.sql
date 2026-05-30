-- Rotina Viva Pro — Fase 2: pgvector (RAG na nuvem)
-- Dashboard → Database → Extensions → activar "vector" se o CREATE falhar

create extension if not exists vector with schema extensions;

create table if not exists public.rag_index_meta (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
  id bigserial primary key,
  source text not null,
  chunk_index integer not null,
  content text not null,
  embedding extensions.vector(1536) not null,
  metadata jsonb not null default '{}'::jsonb,
  index_profile text not null,
  created_at timestamptz not null default now(),
  unique (source, chunk_index, index_profile)
);

create index if not exists idx_document_chunks_profile on public.document_chunks (index_profile);
create index if not exists idx_document_chunks_source on public.document_chunks (source);

create index if not exists idx_document_chunks_embedding
  on public.document_chunks
  using hnsw (embedding extensions.vector_cosine_ops);

create or replace function public.match_document_chunks(
  query_embedding extensions.vector(1536),
  match_count integer default 10,
  filter_profile text default null,
  filter_sources text[] default null
)
returns table (
  id bigint,
  source text,
  chunk_index integer,
  content text,
  metadata jsonb,
  distance double precision
)
language sql
stable
as $$
  select
    dc.id,
    dc.source,
    dc.chunk_index,
    dc.content,
    dc.metadata,
    (dc.embedding <=> query_embedding)::double precision as distance
  from public.document_chunks dc
  where (filter_profile is null or dc.index_profile = filter_profile)
    and (filter_sources is null or dc.source = any (filter_sources))
  order by dc.embedding <=> query_embedding
  limit greatest(1, least(match_count, 100));
$$;

grant execute on function public.match_document_chunks(
  extensions.vector(1536), integer, text, text[]
) to authenticated, service_role;

alter table public.document_chunks enable row level security;
alter table public.rag_index_meta enable row level security;

create policy document_chunks_select_authenticated on public.document_chunks
  for select to authenticated
  using (true);

create policy rag_index_meta_select_authenticated on public.rag_index_meta
  for select to authenticated
  using (true);

create policy document_chunks_service_all on public.document_chunks
  for all to service_role
  using (true)
  with check (true);

create policy rag_index_meta_service_all on public.rag_index_meta
  for all to service_role
  using (true)
  with check (true);
