# Magnus v2 — pipeline de treino moderno

Segunda geração do modelo de detecção de defeitos de pintura. Sai de 4
classes (`lx0xk`, YOLOv8n, mAP50=0.989) para **8 classes** com dataset
curado de múltiplas fontes e arquitetura maior (**YOLO11s, ~9M params**).

## Por que v2 — a lição de curadoria

Auditamos 13 datasets do Roboflow/Kaggle (~67k imagens "brutas"). Descoberta
central: **a maior parte é lixo de domínio**.

- Os datasets `weld-dataset/*` (~46k imgs, 68% do total) misturam closeups
  de pintura com **carros capotados, amassados e rodas**, com labels
  numéricas `0-7` inconsistentes entre si. Inúteis sem curadoria pesada.
- `car-damage-zxk33` (13k) é 90% dano de lataria (dents), não pintura.
- Vários têm **augmentation embutido** (3× por imagem-fonte) — o "número de
  imagens" reportado é inflado.

**Pool limpo real: ~3.000 imagens** de 3 fontes curadas. Princípio: dataset
pequeno e bem rotulado supera dataset grande e ruidoso. Isso é a contribuição
científica defensável — não "usei 100k imagens", mas "demonstrei que
curadoria > volume".

## As 8 classes (config.py)

| Classe | Origem dos rótulos |
|---|---|
| `casca_de_laranja` | orange_peel |
| `escorrimento` | runs_sags, dripping_curtaining |
| `bolha` | solvent_pop + bubbling + blistering (mesclados) |
| `water_spotting` | water_spotting |
| `descascamento` | peel_off, Paint-fading, paint-chip |
| `risco` | scratch, Crack |
| `sujeira` | dirt |
| `oxidacao` | Rust |

## Fontes curadas (config.SOURCES)

1. `baopersonal/paint-defect-combine-3` — base, 8 classes, ~2.8k imgs
2. `cardetecion/car-paint-damage-detection` — oxidação/risco, ~456 imgs
3. `cat-ln1ow/paint-defect-detection-j7imb` — raras + negativos, ~73 imgs

Datasets excluídos (e o porquê) estão documentados no fim de `config.py`.

## Arquivos

| Arquivo | Função |
|---|---|
| `config.py` | Taxonomia, mapa de classes, fontes (single source of truth) |
| `build_dataset.py` | Download + remap + dedup por fonte + escreve YOLO dir |
| `train.py` | YOLO11s com augmentation moderna + WandB + push HF |
| `evaluate.py` | TTA + matriz de confusão + métricas por classe |
| `colab.md` | Passo a passo copy-paste pro Colab |

## Como rodar

Ver [`colab.md`](./colab.md). Resumo: 6 células no Colab GPU — instalar,
clonar, `build()`, `run_training()`, `evaluate()`, visualizar.

## Diferenças vs v1 (`training/`)

| | v1 | v2 |
|---|---|---|
| Modelo | YOLOv8n (3M) | YOLO11s (9M) |
| Classes | 4 | 8 |
| Fontes | 1 (lx0xk) | 3 curadas |
| Dedup | sha256 | por imagem-fonte (remove aug embutido) |
| Augmentation | default | + MixUp, CopyPaste, close_mosaic |
| Schedule | default | cosine LR, label smoothing, warmup, early stop |
| Tracking | print | WandB opcional |
| Avaliação | mAP simples | TTA + matriz de confusão + por classe |

## Fase 3 (futuro) — active learning

Os ~15k imgs do `weld-dataset` ficam reservados. Depois do v2 treinado:
rodar Magnus v2 neles, manter só os closeups de pintura com confiança na
zona de incerteza (0.4-0.7), curar e re-treinar. Crescimento de dataset
com qualidade, sem despejar ruído.
