-- Views compatíveis com nomes CSV (info_alunos / diario_estruturado)
-- Permitem reutilizar SQL gerado pelo chat (DuckDB → Postgres via ROTINA_DATA_BACKEND=supabase)

-- ---------------------------------------------------------------------------
-- Cadastro (espelho de info_alunos.csv)
-- ---------------------------------------------------------------------------
create or replace view public.info_alunos as
select
  s.id as id_aluno,
  s.name as nome,
  s.class_name as turma,
  s.allergies as alergias,
  s.parent_contact as contato_pais
from public.students s;

comment on view public.info_alunos is
  'Alias CSV para o motor de chat; dados em public.students';

create or replace function public.info_alunos_insert_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.students (id, name, class_name, allergies, parent_contact)
  values (new.id_aluno, new.nome, new.turma, new.alergias, new.contato_pais);
  return new;
end;
$$;

create or replace function public.info_alunos_update_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.students
  set
    name = new.nome,
    class_name = new.turma,
    allergies = new.alergias,
    parent_contact = new.contato_pais,
    updated_at = now()
  where id = old.id_aluno;
  return new;
end;
$$;

create or replace function public.info_alunos_delete_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from public.students where id = old.id_aluno;
  return old;
end;
$$;

drop trigger if exists info_alunos_insert_tr on public.info_alunos;
drop trigger if exists info_alunos_update_tr on public.info_alunos;
drop trigger if exists info_alunos_delete_tr on public.info_alunos;

create trigger info_alunos_insert_tr
  instead of insert on public.info_alunos
  for each row execute function public.info_alunos_insert_fn();

create trigger info_alunos_update_tr
  instead of update on public.info_alunos
  for each row execute function public.info_alunos_update_fn();

create trigger info_alunos_delete_tr
  instead of delete on public.info_alunos
  for each row execute function public.info_alunos_delete_fn();

-- ---------------------------------------------------------------------------
-- Diário (espelho de diario_estruturado.csv)
-- ---------------------------------------------------------------------------
create or replace view public.diario_estruturado as
select
  d.id as id_registro,
  d.student_id as id_aluno,
  coalesce(d.entry_date::text, '') as data,
  coalesce(d.breakfast, '') as cafe_manha,
  coalesce(d.lunch, '') as almoco,
  coalesce(d.afternoon_snack, '') as lanche_tarde,
  coalesce(d.extra_dinner, '') as jantar_extra,
  coalesce(d.bathroom_changes::text, '') as trocas_banheiro,
  coalesce(d.bowel_movement, '') as evacuacao,
  coalesce(d.medications, '') as medicamentos,
  coalesce(d.sleep_start::text, '') as hora_sono_inicio,
  coalesce(d.sleep_end::text, '') as hora_sono_fim,
  coalesce(d.sleep_quality, '') as qualidade_sono,
  coalesce(d.day_activity, '') as atividade_dia,
  coalesce(d.social_interaction, '') as interacao_social,
  coalesce(d.teacher_note, '') as recado_professora
from public.diary_entries d;

comment on view public.diario_estruturado is
  'Alias CSV para o motor de chat; dados em public.diary_entries';

create or replace function public.diario_estruturado_insert_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.diary_entries (
    id, student_id, entry_date,
    breakfast, lunch, afternoon_snack, extra_dinner,
    bathroom_changes, bowel_movement, medications,
    sleep_start, sleep_end, sleep_quality,
    day_activity, social_interaction, teacher_note
  )
  values (
    new.id_registro,
    new.id_aluno,
    nullif(trim(new.data), '')::date,
    nullif(trim(new.cafe_manha), ''),
    nullif(trim(new.almoco), ''),
    nullif(trim(new.lanche_tarde), ''),
    nullif(trim(new.jantar_extra), ''),
    nullif(trim(new.trocas_banheiro), '')::integer,
    nullif(trim(new.evacuacao), ''),
    nullif(trim(new.medicamentos), ''),
    nullif(trim(new.hora_sono_inicio), '')::time,
    nullif(trim(new.hora_sono_fim), '')::time,
    nullif(trim(new.qualidade_sono), ''),
    nullif(trim(new.atividade_dia), ''),
    nullif(trim(new.interacao_social), ''),
    nullif(trim(new.recado_professora), '')
  );
  return new;
end;
$$;

create or replace function public.diario_estruturado_update_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.diary_entries
  set
    student_id = new.id_aluno,
    entry_date = nullif(trim(new.data), '')::date,
    breakfast = nullif(trim(new.cafe_manha), ''),
    lunch = nullif(trim(new.almoco), ''),
    afternoon_snack = nullif(trim(new.lanche_tarde), ''),
    extra_dinner = nullif(trim(new.jantar_extra), ''),
    bathroom_changes = nullif(trim(new.trocas_banheiro), '')::integer,
    bowel_movement = nullif(trim(new.evacuacao), ''),
    medications = nullif(trim(new.medicamentos), ''),
    sleep_start = nullif(trim(new.hora_sono_inicio), '')::time,
    sleep_end = nullif(trim(new.hora_sono_fim), '')::time,
    sleep_quality = nullif(trim(new.qualidade_sono), ''),
    day_activity = nullif(trim(new.atividade_dia), ''),
    social_interaction = nullif(trim(new.interacao_social), ''),
    teacher_note = nullif(trim(new.recado_professora), ''),
    updated_at = now()
  where id = old.id_registro;
  return new;
end;
$$;

create or replace function public.diario_estruturado_delete_fn()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from public.diary_entries where id = old.id_registro;
  return old;
end;
$$;

drop trigger if exists diario_estruturado_insert_tr on public.diario_estruturado;
drop trigger if exists diario_estruturado_update_tr on public.diario_estruturado;
drop trigger if exists diario_estruturado_delete_tr on public.diario_estruturado;

create trigger diario_estruturado_insert_tr
  instead of insert on public.diario_estruturado
  for each row execute function public.diario_estruturado_insert_fn();

create trigger diario_estruturado_update_tr
  instead of update on public.diario_estruturado
  for each row execute function public.diario_estruturado_update_fn();

create trigger diario_estruturado_delete_tr
  instead of delete on public.diario_estruturado
  for each row execute function public.diario_estruturado_delete_fn();

grant select, insert, update, delete on public.info_alunos to service_role;
grant select, insert, update, delete on public.diario_estruturado to service_role;
