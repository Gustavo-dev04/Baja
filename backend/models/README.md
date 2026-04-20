# Pesos do modelo

Este diretório armazena checkpoints do YOLO. Ele é ignorado pelo git
(`*.pt` em `.gitignore`) para não versionar arquivos grandes.

- Protótipo: o Ultralytics baixa `yolov8n.pt` automaticamente no primeiro
  uso (cache em `~/.cache/ultralytics/`).
- Fine-tuning: salve `best.pt` aqui como `baja_paint.pt` e defina:

  ```bash
  export BAJA_MODEL_WEIGHTS=models/baja_paint.pt
  ```
