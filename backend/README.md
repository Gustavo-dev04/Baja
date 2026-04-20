# Backend — API de Inspeção de Pintura

FastAPI + Ultralytics YOLO expondo `POST /inspect` para detectar defeitos
de pintura em imagens de chassis BAJA.

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

O endpoint `GET /health` indica o modelo carregado e se está em modo demo.

## Endpoints

| Método | Rota       | Descrição                                        |
|--------|------------|--------------------------------------------------|
| GET    | `/health`  | Status + nome do modelo + `demo_mode`.           |
| POST   | `/inspect` | `multipart/form-data` com `file` (imagem).       |

Exemplo:

```bash
curl -F "file=@sample.jpg" http://localhost:8000/inspect
```

Resposta:

```json
{
  "detections": [
    {
      "label": "escorrimento",
      "raw_label": "bottle",
      "confidence": 0.87,
      "bbox": [10.0, 20.0, 30.0, 40.0]
    }
  ],
  "image_size": [640, 480],
  "inference_ms": 142.5,
  "model": "yolov8n.pt",
  "demo_mode": true
}
```

## Testes

```bash
pytest
```

Os testes usam mocks do Ultralytics e não exigem download de pesos.

## Modo demo × modelo fine-tuned

Até existir um dataset rotulado de defeitos de pintura, o backend carrega
`yolov8n.pt` (COCO) e mapeia classes genéricas para rótulos de defeito
via `DEMO_CLASS_MAP` em `app/config.py`. Isso permite validar o pipeline
ponta a ponta. Ao fine-tunar o modelo:

1. Treinar com `yolo train data=baja.yaml model=yolov8n.pt ...`.
2. Copiar `best.pt` para `backend/models/baja_paint.pt`.
3. Exportar `BAJA_MODEL_WEIGHTS=models/baja_paint.pt` antes de subir a API.

## Deploy

Ver [`../docs/05-deploy-nuvem.md`](../docs/05-deploy-nuvem.md).
