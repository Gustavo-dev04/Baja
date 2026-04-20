# 06 — Roadmap

## Fase 0 — Planejamento ✅

- Escolha da arquitetura (cloud + YOLO + FastAPI + Next.js).
- Documentação inicial.

## Fase 1 — Protótipo funcional (este semestre) ✅

- Backend FastAPI expondo `/inspect` com YOLO pré-treinado.
- Frontend Next.js com webcam, upload e overlay.
- Testes de integração do pipeline end-to-end (modo demo).
- Documentação inicial completa.

## Fase 2 — Dataset próprio

- Construção do banco de imagens (500–1000) do chassi BAJA com e sem
  defeitos.
- Rotulagem em Roboflow / CVAT.
- Primeiro treinamento fine-tuned (`yolov8n.pt` → `baja_paint.pt`).
- Publicar métricas (mAP, matriz de confusão) em
  `docs/07-resultados.md` (a criar).

## Fase 3 — Câmara física

- Construção da câmara de inspeção conforme
  [`03-hardware-camara.md`](./03-hardware-camara.md).
- Integração com microcontrolador para trigger automático.
- Múltiplas câmeras sincronizadas.

## Fase 4 — Produção e validação

- Deploy estável (HF Spaces ou Render → AWS/Azure).
- Validação cruzada com inspeção humana (concordância κ de Cohen).
- Artigo científico submetido a evento da SAE Brasil ou congresso de
  visão computacional.

## Fase 5 — Evoluções

- Segmentação semântica (U-Net / YOLO-seg) para defeitos sutis.
- Relatório histórico por chassi (banco de dados).
- Integração com linha de produção.
