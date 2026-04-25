# Backend — API de Inspeção de Pintura

FastAPI + Ultralytics YOLO + Supabase. Expõe inferência pública e endpoints
admin para gerenciar datasets, imagens, anotações, runs de treino e modelos.

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Defina pelo menos `BAJA_ADMIN_PASSWORD` se for testar endpoints admin.
Para operar o data plane, configure também `SUPABASE_URL` e
`SUPABASE_SERVICE_ROLE_KEY` (ver tabela abaixo). Sem Supabase, os
endpoints `/api/v1/*` retornam 503; `/health` e `/inspect` continuam OK.

## Endpoints públicos (contrato preservado)

| Método | Rota       | Descrição                                        |
|--------|------------|--------------------------------------------------|
| GET    | `/health`  | Status + nome do modelo + `demo_mode`.           |
| POST   | `/inspect` | `multipart/form-data` com `file` (imagem).       |

```bash
curl -F "file=@sample.jpg" http://localhost:8000/inspect
```

## Endpoints admin (`/api/v1`)

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/admin-token` | senha | troca senha por JWT (24h) |
| GET | `/api/v1/datasets` | público | lista datasets |
| POST | `/api/v1/datasets` | admin | cria dataset |
| GET | `/api/v1/datasets/{id}` | público | detalhe + contagens |
| PATCH | `/api/v1/datasets/{id}` | admin | atualiza |
| DELETE | `/api/v1/datasets/{id}` | admin | soft-delete (`is_active=false`) |
| POST | `/api/v1/datasets/{id}/images` | admin | upload bulk (até 20) |
| GET | `/api/v1/datasets/{id}/images` | público | lista paginada |
| GET | `/api/v1/images/{id}` | público | detalhe + URLs assinadas |
| PATCH | `/api/v1/images/{id}` | admin | muda `status`/`split` |
| DELETE | `/api/v1/images/{id}` | admin | remove (cascade nas annotations) |
| GET | `/api/v1/images/{id}/annotations` | público | lista boxes |
| POST | `/api/v1/images/{id}/annotations` | admin | substitui todas |

Header de auth: `Authorization: Bearer <token>`.

## Variáveis de ambiente

| Var | Default | Quando setar |
|---|---|---|
| `BAJA_MODEL_WEIGHTS` | `yolov8n.pt` | mudar para `best.pt` fine-tunado |
| `BAJA_CONF_THRESHOLD` | `0.25` | sintonizar precisão/recall |
| `BAJA_ALLOWED_ORIGINS` | `localhost:3000` | adicionar domínio Vercel |
| `BAJA_MODEL_CACHE_DIR` | `/tmp/baja-models` | cache p/ modelos baixados |
| `BAJA_PERSIST_INSPECTIONS` | `true` | flag p/ desligar persistência |
| `SUPABASE_URL` | — | URL do projeto |
| `SUPABASE_SERVICE_ROLE_KEY` | — | secret, escrita via backend |
| `SUPABASE_BUCKET_IMAGES` | `baja-images` | bucket de imagens |
| `SUPABASE_BUCKET_MODELS` | `baja-models` | bucket de modelos (fallback) |
| `BAJA_ADMIN_PASSWORD` | — | senha do login admin |
| `BAJA_JWT_SECRET` | `dev-only-change-me` | trocar em produção |
| `BAJA_JWT_EXPIRE_HOURS` | `24` | duração do token |
| `HF_TOKEN` | — | upload de modelos no HF Hub |
| `BAJA_HF_MODEL_REPO` | — | repo HF default |

## Testes

```bash
pytest
```

Cobertura atual: 11 testes (auth, storage, inference, registro de rotas).
Mocks de Ultralytics e Supabase, então não baixa pesos nem conecta em
serviços externos.

## Estrutura

```
app/
├── main.py                # monta routers, CORS, warmup
├── config.py              # shim de retrocompat → core.config
├── inference.py           # Detector + DEMO_CLASS_MAP
├── core/
│   ├── config.py          # todas as env vars
│   ├── supabase.py        # client singleton
│   ├── auth.py            # JWT admin
│   └── storage.py         # uploads + thumbs + signed URLs
├── routers/
│   ├── inspect.py         # /health, /inspect (intactos)
│   ├── auth.py            # /api/v1/auth/admin-token
│   ├── datasets.py        # CRUD datasets
│   ├── images.py          # upload + CRUD images
│   └── annotations.py     # replace-all anotações
└── schemas/
    ├── inspection.py      # Detection, InspectionResult, HealthResponse
    ├── dataset.py
    ├── image.py
    ├── annotation.py
    └── auth.py
```

## Modo demo × modelo fine-tuned

Até existir dataset rotulado, o backend carrega `yolov8n.pt` (COCO) e
remapeia classes via `DEMO_CLASS_MAP` em `core/config.py`. Quando
houver um modelo fine-tunado:

1. Treinar via `training/baja_yolo_finetune.ipynb` (Colab).
2. Upload do `best.pt` para HF Hub ou Supabase Storage.
3. `POST /api/v1/models/{id}/activate` (Semana 4 do roadmap) faz hot-swap
   sem restart do container.

## Deploy

Ver [`../DEPLOY.md`](../DEPLOY.md) e [`../supabase/README.md`](../supabase/README.md).
