-- MyPuppy database. Run once in Supabase > SQL Editor.

create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  email text not null,
  state jsonb,
  photos jsonb not null default '{}'::jsonb,
  puppy_name text,
  cur_day int not null default 1,
  last_active date,
  unlocked boolean not null default false,
  plan text,
  reminders boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.purchases (
  sale_id text primary key,
  email text not null,
  product text,
  refunded boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists purchases_email_idx on public.purchases (email);

alter table public.profiles enable row level security;
alter table public.purchases enable row level security;  -- no policies: only the payment function can touch it

drop policy if exists "read own profile" on public.profiles;
create policy "read own profile" on public.profiles for select using (auth.uid() = id);
drop policy if exists "update own profile" on public.profiles;
create policy "update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

-- Users may change their own plan data, but never the "unlocked" flag.
revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;
grant update (state, photos, puppy_name, cur_day, last_active, reminders, updated_at) on public.profiles to authenticated;
revoke all on public.purchases from anon, authenticated;

-- Create a profile row for every new account. If they already paid with this email, unlock straight away.
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, unlocked)
  values (new.id, lower(new.email),
          exists (select 1 from public.purchases p where p.email = lower(new.email) and not p.refunded))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Called by the app's "I've paid" button: unlock if a purchase exists for the signed-in email.
create or replace function public.claim_purchase() returns boolean
language plpgsql security definer set search_path = public as $$
declare ok boolean;
begin
  select exists (select 1 from public.purchases p where p.email = lower(auth.email()) and not p.refunded) into ok;
  if ok then update public.profiles set unlocked = true where id = auth.uid(); end if;
  return ok;
end $$;
revoke all on function public.claim_purchase() from public, anon;
grant execute on function public.claim_purchase() to authenticated;
