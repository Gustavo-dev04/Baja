# 04 — Modelo de IA

## Arquitetura escolhida: YOLO (You Only Look Once)

Família de modelos de **detecção de objetos** em uma única passagem pela
rede neural. Escolhida por:

- Balanceamento entre velocidade e precisão adequado a inspeção quase
  em tempo real.
- Ecossistema maduro (biblioteca **Ultralytics**) com utilitários de
  treino, exportação e inferência.
- Pesos pré-treinados em COCO disponíveis gratuitamente.
- Fine-tuning viável com poucas centenas de imagens.

Variante inicial: **YOLOv8n** (`yolov8n.pt`, ~6 MB, mAP@50 ≈ 37 em COCO).
Evolução futura: YOLOv8s/m ou YOLO11 conforme restrições de latência.

## Estratégia em duas fases

### Fase 1 — Protótipo (modo demo)

O backend carrega `yolov8n.pt` pré-treinado em COCO. Como as 80 classes
COCO não incluem defeitos de pintura, aplicamos um **mapeamento de
demonstração** em `backend/app/config.py::DEMO_CLASS_MAP` para que a UI
exiba rótulos de defeitos enquanto o pipeline end-to-end é validado.

O campo `demo_mode: true` na resposta da API sinaliza explicitamente
essa situação e a UI exibe um aviso ao usuário.

### Fase 2 — Modelo fine-tuned

Substituir os pesos por um checkpoint treinado com imagens reais de
chassis pintados.

**Classes alvo (6):**

| Classe              | Descrição                                        |
|---------------------|--------------------------------------------------|
| `escorrimento`      | Acúmulo de tinta que escorre formando cordão.    |
| `casca_de_laranja`  | Textura irregular com aparência de casca.        |
| `falha_cobertura`   | Regiões onde a tinta não cobriu o substrato.     |
| `bolha`             | Bolhas de ar/solvente sob a película.            |
| `risco`             | Arranhões longitudinais.                         |
| `oxidacao`          | Pontos de ferrugem/óxido visíveis.               |

## Dataset

- **Meta inicial:** 500–1000 imagens rotuladas.
- **Origem:**
  - Coleta própria dos chassis da equipe (protótipos + carros de
    temporadas anteriores).
  - Augmentation (rotação, brilho, blur) durante treino.
  - Datasets complementares do Roboflow Universe sobre *surface
    defects* para transfer learning intermediário.
- **Rotulagem:** ferramenta **Roboflow** (web) ou **CVAT** (local).
- **Formato:** YOLO txt (`class x_center y_center w h` normalizados).
- **Split:** 70% treino / 20% validação / 10% teste.

## Treinamento

Comando padrão Ultralytics:

```bash
yolo detect train \
  model=yolov8n.pt \
  data=baja.yaml \
  epochs=100 \
  imgsz=640 \
  batch=16 \
  name=baja_paint_v1
```

`baja.yaml` define paths das pastas `images/` e `labels/` e a lista de
classes acima.

## Métricas

- **Precisão (Precision)** e **Revocação (Recall)** por classe.
- **mAP@0.5** e **mAP@0.5:0.95** (conforme COCO).
- **Matriz de confusão** para identificar classes mais confundidas.
- **Tempo de inferência** (ms) — meta: < 200 ms por imagem em CPU, < 50 ms
  em GPU.

## Deploy do checkpoint

Ver [`05-deploy-nuvem.md`](./05-deploy-nuvem.md). O backend aceita a
variável de ambiente `BAJA_MODEL_WEIGHTS` apontando para um caminho
local (ex.: `models/baja_paint.pt`).
