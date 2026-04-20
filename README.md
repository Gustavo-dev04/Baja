# Baja — Sistema de Inspeção de Pintura por IA

Protótipo de um sistema de inspeção visual automatizada da pintura de
chassis estilo **BAJA SAE** (ou veículos de competição). Câmeras instaladas
em uma câmara fechada capturam imagens da pintura e enviam para um serviço
de **IA na nuvem** que identifica, em tempo real, defeitos (escorrimento,
casca de laranja, falhas de cobertura, bolhas) e desgaste (riscos, oxidação).

## Arquitetura

```
 Câmeras → Frontend (Next.js) → API FastAPI → Modelo YOLO (nuvem) → JSON
                                                                        │
                                                                        ▼
                                                            Overlay + relatório
```

- **Backend** (`backend/`): FastAPI + Ultralytics YOLO servindo um endpoint
  REST `/inspect`.
- **Frontend** (`frontend/`): Next.js + React com captura de webcam, upload
  de imagens e visualização das detecções sobre a imagem.
- **Documentação** (`docs/`): arquitetura, hardware da câmara, escolha do
  modelo, deploy em nuvem, roadmap e referências.

## Como rodar localmente

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

Teste rápido:

```bash
curl -F "file=@alguma_imagem.jpg" http://localhost:8000/inspect
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:3000`.

## Status

- Semestre 2026/1 — projeto científico-tecnológico.
- Branch de desenvolvimento: `claude/paint-inspection-ai-FRk8g`.
- Entregável do semestre: protótipo funcional + documentação.

Consulte [`docs/`](./docs/) para detalhes técnicos e científicos.
