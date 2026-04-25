# Supabase — Configuração do banco

## Setup inicial (uma vez por projeto)

1. Criar projeto grátis em https://supabase.com/dashboard/new/project.
2. No painel do projeto, anotar:
   - **Project URL** → vai em `SUPABASE_URL`
   - **API Keys**:
     - `anon` (pública) → vai em `NEXT_PUBLIC_SUPABASE_ANON_KEY`
     - `service_role` (secreta) → vai em `SUPABASE_SERVICE_ROLE_KEY` (nunca exponha no frontend)

## Rodar a migration

Abrir **SQL Editor** no painel do Supabase e colar o conteúdo de
`migrations/0001_init.sql`. Clicar em **Run**.

Tabelas criadas:
- `datasets` — agrupamentos lógicos de imagens.
- `images` — raw frames apontando pro Storage.
- `annotations` — bounding boxes (formato YOLO normalizado).
- `training_runs` — cada tentativa de fine-tuning.
- `models` — checkpoints produzidos (com flag `is_active`).
- `inspections` — histórico de cada chamada `/inspect`.

## Buckets do Storage

Ainda no painel, em **Storage**, criar dois buckets **privados**:

| Nome | Privado | Uso |
|---|---|---|
| `baja-images` | sim | raw frames, thumbs, inspeções, exports YOLO |
| `baja-models` | sim | fallback para weights quando HF Hub não disponível |

Estrutura esperada (o backend cria automaticamente):

```
baja-images/
├── raw/{dataset_id}/{image_uuid}.jpg
├── thumbs/{dataset_id}/{image_uuid}.jpg
├── inspections/{yyyy-mm-dd}/{inspection_id}.jpg
└── yolo-exports/{dataset_id}/{export_timestamp}/...

baja-models/
└── {model_name}/{version}/best.pt
```

## RLS (Row Level Security)

Leitura pública para todas as tabelas. Escrita só pelo backend usando
`SUPABASE_SERVICE_ROLE_KEY` (service_role bypassa RLS). Quando a Fase B
da auth chegar, trocar as policies por `auth.uid()`.

## Dataset padrão (opcional)

Depois da migration, criar um dataset default para começar:

```sql
insert into public.datasets (name, description)
values ('default', 'Dataset inicial do projeto Baja');
```

Ou via API: `POST /api/v1/datasets`.
