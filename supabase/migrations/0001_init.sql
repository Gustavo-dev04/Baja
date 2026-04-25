-- Baja Paint Inspection — initial schema
-- Run in Supabase SQL editor after creating the project.

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- =========================================================
-- datasets: logical grouping of images for a training run
-- =========================================================
create table public.datasets (
    id              uuid primary key default uuid_generate_v4(),
    name            text not null unique,
    description     text,
    classes         text[] not null default array[
        'escorrimento','casca_de_laranja','falha_cobertura',
        'bolha','risco','oxidacao'
    ],
    is_active       boolean not null default true,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);
create index idx_datasets_active on public.datasets (is_active);

-- =========================================================
-- images: raw frames pointing to Supabase Storage
-- =========================================================
create table public.images (
    id              uuid primary key default uuid_generate_v4(),
    dataset_id      uuid not null references public.datasets(id) on delete cascade,
    storage_path    text not null,
    width           int not null,
    height          int not null,
    sha256          text not null,
    original_name   text,
    content_type    text not null default 'image/jpeg',
    bytes           int,
    split           text not null default 'unassigned'
                    check (split in ('train','val','test','unassigned')),
    status          text not null default 'pending'
                    check (status in ('pending','labeled','reviewed','skipped')),
    captured_at     timestamptz,
    uploaded_by     uuid,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    unique (dataset_id, sha256)
);
create index idx_images_dataset_status on public.images (dataset_id, status);
create index idx_images_dataset_split on public.images (dataset_id, split);

-- =========================================================
-- annotations: bounding boxes in YOLO-friendly format
-- =========================================================
create table public.annotations (
    id              uuid primary key default uuid_generate_v4(),
    image_id        uuid not null references public.images(id) on delete cascade,
    class_name      text not null,
    x_center        double precision not null check (x_center between 0 and 1),
    y_center        double precision not null check (y_center between 0 and 1),
    width           double precision not null check (width  > 0 and width  <= 1),
    height          double precision not null check (height > 0 and height <= 1),
    confidence      double precision,
    source          text not null default 'human'
                    check (source in ('human','model','import')),
    created_by      uuid,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);
create index idx_annotations_image on public.annotations (image_id);
create index idx_annotations_class on public.annotations (class_name);

-- =========================================================
-- training_runs: record of every fine-tuning attempt
-- =========================================================
create table public.training_runs (
    id              uuid primary key default uuid_generate_v4(),
    dataset_id      uuid not null references public.datasets(id),
    status          text not null default 'queued'
                    check (status in ('queued','running','succeeded','failed','cancelled')),
    base_model      text not null default 'yolov8n.pt',
    epochs          int not null default 50,
    imgsz           int not null default 640,
    batch           int not null default 16,
    notebook_url    text,
    metrics         jsonb,
    logs_url        text,
    started_at      timestamptz,
    finished_at     timestamptz,
    error_message   text,
    triggered_by    uuid,
    created_at      timestamptz not null default now()
);
create index idx_runs_dataset_status on public.training_runs (dataset_id, status);
create index idx_runs_created on public.training_runs (created_at desc);

-- =========================================================
-- models: each fine-tuned checkpoint (best.pt)
-- =========================================================
create table public.models (
    id              uuid primary key default uuid_generate_v4(),
    training_run_id uuid references public.training_runs(id),
    name            text not null,
    version         text not null,
    storage_path    text,
    hf_repo_id      text,
    hf_filename     text default 'best.pt',
    classes         text[] not null,
    metrics         jsonb,
    bytes           int,
    is_active       boolean not null default false,
    notes           text,
    created_at      timestamptz not null default now(),
    unique (name, version)
);
-- only ONE active model at a time
create unique index only_one_active_model
    on public.models (is_active) where is_active = true;

-- =========================================================
-- inspections: history of every /inspect call
-- =========================================================
create table public.inspections (
    id              uuid primary key default uuid_generate_v4(),
    model_id        uuid references public.models(id),
    model_name      text not null,
    demo_mode       boolean not null default false,
    image_path      text,
    image_sha256    text,
    image_width     int not null,
    image_height    int not null,
    detections      jsonb not null,
    detection_count int not null default 0,
    inference_ms    double precision not null,
    client_ip       inet,
    user_agent      text,
    session_id      text,
    created_at      timestamptz not null default now()
);
create index idx_inspections_created on public.inspections (created_at desc);
create index idx_inspections_model on public.inspections (model_id);
create index idx_inspections_session on public.inspections (session_id);

-- =========================================================
-- updated_at triggers
-- =========================================================
create or replace function public.touch_updated_at() returns trigger as $$
begin
    new.updated_at := now();
    return new;
end $$ language plpgsql;

create trigger trg_datasets_updated
    before update on public.datasets
    for each row execute function public.touch_updated_at();

create trigger trg_images_updated
    before update on public.images
    for each row execute function public.touch_updated_at();

create trigger trg_annotations_updated
    before update on public.annotations
    for each row execute function public.touch_updated_at();

-- =========================================================
-- Row Level Security: public read; writes only via service_role
-- =========================================================
alter table public.datasets       enable row level security;
alter table public.images         enable row level security;
alter table public.annotations    enable row level security;
alter table public.training_runs  enable row level security;
alter table public.models         enable row level security;
alter table public.inspections    enable row level security;

create policy "public read datasets"     on public.datasets
    for select using (true);
create policy "public read images"       on public.images
    for select using (true);
create policy "public read annotations"  on public.annotations
    for select using (true);
create policy "public read models"       on public.models
    for select using (true);
create policy "public read inspections"  on public.inspections
    for select using (true);
create policy "public read runs"         on public.training_runs
    for select using (true);
-- Writes flow through FastAPI using SUPABASE_SERVICE_ROLE_KEY, which
-- bypasses RLS; no insert/update/delete policies for anon clients.
