# Deploy rápido do protótipo por URL

Objetivo: deixar o sistema acessível por navegador, com uma URL pública
para o frontend e outra para o backend.

## Arquitetura recomendada

- **Backend (`backend/`)**: Hugging Face Spaces com Docker.
- **Frontend (`frontend/`)**: Vercel apontando para a URL do backend.

Fluxo final:

```text
Navegador -> Frontend (Vercel) -> Backend FastAPI + YOLO (HF Spaces)
```

## 1) Subir o backend

O caminho mais simples para o protótipo é usar **Hugging Face Spaces**.

### Arquivos mínimos

Suba a pasta `backend/` para um Space do tipo **Docker**.

Arquivos esperados na raiz do Space:

- `Dockerfile`
- `pyproject.toml`
- `app/`
- `README.md` com frontmatter do Hugging Face

### `README.md` mínimo para o Space

```md
---
title: Baja Paint Inspection API
emoji: 🏁
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

FastAPI + YOLO servindo detecção de defeitos de pintura.
```

### Variáveis de ambiente do backend

Use como base `backend/.env.example`.

Principalmente:

```bash
BAJA_ALLOWED_ORIGINS=https://seu-frontend.vercel.app
```

Depois do deploy, teste:

```bash
curl https://sua-api.hf.space/health
```

## 2) Subir o frontend

O jeito mais simples é usar **Vercel** com a pasta `frontend/` como root.

### Variável de ambiente do frontend

Use como base `frontend/.env.example`.

```bash
NEXT_PUBLIC_API_URL=https://sua-api.hf.space
```

## 3) Teste final

- Abra a URL do frontend.
- Confira se o badge **API: online** aparece.
- Teste upload de imagem.
- Teste webcam em HTTPS.

## Observações

- Em celular, a câmera costuma exigir **HTTPS**.
- O backend aceita porta dinâmica (`$PORT`) para funcionar melhor em
  Spaces, Render e Railway.
- Para este semestre, o fluxo por imagem/frame é suficiente; streaming
  contínuo pode ficar como evolução futura.
