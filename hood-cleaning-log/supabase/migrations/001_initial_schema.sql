-- Hood Cleaning Log — Initial Schema
-- VIBE-20260511-5 | Technyder Vibe SaaS Ideas Engine

-- Extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================
-- TENANTS (organizations / restaurant groups)
-- ============================================================
create table tenants (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  slug          text unique not null,
  stripe_customer_id   text,
  stripe_subscription_id text,
  subscription_status  text default 'trialing',  -- trialing | active | past_due | canceled
  trial_ends_at  timestamptz default (now() + interval '14 days'),
  created_at    timestamptz default now(),
  updated_at    timestamptz default now(),
  deleted_at    timestamptz
);

-- ============================================================
-- USERS (tenant members)
-- ============================================================
create table user_profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  tenant_id   uuid references tenants(id) on delete cascade not null,
  full_name   text,
  role        text not null default 'manager',  -- owner | manager | viewer
  phone       text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- ============================================================
-- LOCATIONS (restaurant locations)
-- ============================================================
create table locations (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid references tenants(id) on delete cascade not null,
  name        text not null,
  address     text,
  city        text,
  state       text,
  zip         text,
  phone       text,
  contact_name text,
  contact_email text,
  active      boolean default true,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now(),
  deleted_at  timestamptz
);

-- ============================================================
-- VENDORS (hood cleaning companies)
-- ============================================================
create table vendors (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid references tenants(id) on delete cascade not null,
  name        text not null,
  phone       text,
  email       text,
  license_number text,
  active      boolean default true,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now(),
  deleted_at  timestamptz
);

-- ============================================================
-- HOODS (exhaust hoods per location)
-- ============================================================
create table hoods (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid references tenants(id) on delete cascade not null,
  location_id     uuid references locations(id) on delete cascade not null,
  name            text not null,              -- e.g. "Main Cook Line Hood #1"
  description     text,
  frequency_days  int not null default 90,   -- NFPA-96: 90 or 180 days
  qr_code         text unique not null default gen_random_uuid()::text,
  active          boolean default true,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  deleted_at      timestamptz
);

-- ============================================================
-- CLEANING RECORDS (vendor submissions)
-- ============================================================
create table cleaning_records (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid references tenants(id) on delete cascade not null,
  hood_id         uuid references hoods(id) on delete cascade not null,
  vendor_id       uuid references vendors(id) on delete set null,
  vendor_name     text not null,              -- denormalized for history
  tech_name       text not null,
  cleaned_at      timestamptz not null default now(),
  notes           text,
  before_photo_url text,
  after_photo_url  text,
  signature_url    text,                      -- base64 or storage URL
  next_due_at     timestamptz,               -- computed: cleaned_at + frequency_days
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

-- ============================================================
-- NOTIFICATION SETTINGS (per hood / per location)
-- ============================================================
create table notification_settings (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid references tenants(id) on delete cascade not null,
  location_id   uuid references locations(id) on delete cascade,
  hood_id       uuid references hoods(id) on delete cascade,
  phone         text,                         -- SMS recipient
  email         text,
  notify_days_before int[] default '{7,3,1}', -- days before due
  enabled       boolean default true,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- ============================================================
-- AUDIT PACKETS (generated export records)
-- ============================================================
create table audit_packets (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     uuid references tenants(id) on delete cascade not null,
  location_id   uuid references locations(id) on delete set null,
  generated_by  uuid references auth.users(id) on delete set null,
  date_from     date not null,
  date_to       date not null,
  pdf_url       text,
  share_token   text unique default gen_random_uuid()::text,
  created_at    timestamptz default now()
);

-- ============================================================
-- INDEXES
-- ============================================================
create index idx_hoods_location on hoods(location_id);
create index idx_hoods_qr on hoods(qr_code);
create index idx_cleaning_records_hood on cleaning_records(hood_id);
create index idx_cleaning_records_cleaned_at on cleaning_records(cleaned_at desc);
create index idx_locations_tenant on locations(tenant_id);
create index idx_user_profiles_tenant on user_profiles(tenant_id);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

create trigger trg_tenants_updated before update on tenants
  for each row execute function set_updated_at();
create trigger trg_locations_updated before update on locations
  for each row execute function set_updated_at();
create trigger trg_hoods_updated before update on hoods
  for each row execute function set_updated_at();
create trigger trg_cleaning_records_updated before update on cleaning_records
  for each row execute function set_updated_at();
create trigger trg_vendors_updated before update on vendors
  for each row execute function set_updated_at();

-- ============================================================
-- COMPUTED: next_due_at on insert/update of cleaning_records
-- ============================================================
create or replace function compute_next_due()
returns trigger language plpgsql as $$
declare freq int;
begin
  select frequency_days into freq from hoods where id = new.hood_id;
  new.next_due_at := new.cleaned_at + (freq || ' days')::interval;
  return new;
end; $$;

create trigger trg_compute_next_due
  before insert or update on cleaning_records
  for each row execute function compute_next_due();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table tenants            enable row level security;
alter table user_profiles      enable row level security;
alter table locations          enable row level security;
alter table hoods              enable row level security;
alter table cleaning_records   enable row level security;
alter table vendors            enable row level security;
alter table notification_settings enable row level security;
alter table audit_packets      enable row level security;

-- Helper: current user's tenant_id
create or replace function current_tenant_id()
returns uuid language sql stable as $$
  select tenant_id from user_profiles where id = auth.uid()
$$;

-- Tenant-scoped RLS for all tables
create policy "tenant_isolation" on tenants
  for all using (id = current_tenant_id());

create policy "tenant_isolation" on user_profiles
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on locations
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on hoods
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on cleaning_records
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on vendors
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on notification_settings
  for all using (tenant_id = current_tenant_id());

create policy "tenant_isolation" on audit_packets
  for all using (tenant_id = current_tenant_id());

-- Public: vendor form reads hood by QR code (no auth)
create policy "public_qr_lookup" on hoods
  for select using (active = true and deleted_at is null);

create policy "public_record_insert" on cleaning_records
  for insert with check (true);
