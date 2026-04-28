-- Run this once in your Supabase project's SQL editor.
-- Creates the table that stores every issued LPN with a UNIQUE constraint
-- so duplicate LPNs are impossible at the database level.

create table if not exists lpns (
  id          uuid primary key default gen_random_uuid(),
  lpn         text unique not null,
  client      text,
  issued_at   timestamptz not null default now()
);

create index if not exists lpns_issued_at_idx on lpns (issued_at desc);
