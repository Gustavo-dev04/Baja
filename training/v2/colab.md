# Magnus v2 — treino no Colab

Pipeline novo: dataset curado multi-fonte → YOLO11s → avaliação completa.

## Pré-requisitos

1. **Runtime GPU:** Runtime → Change runtime type → **T4 GPU**.
2. **Colab Secrets** (ícone de chave na lateral):
   | Secret | Valor |
   |---|---|
   | `ROBOFLOW_API_KEY` | `Zvf7pXUHiqiquiE4dE3a` |
   | `HF_TOKEN` | seu token write do Hugging Face |
   | `WANDB_API_KEY` | (opcional) token do Weights & Biases |

## Célula 1 — Instalar

```python
!pip install -q ultralytics roboflow pyyaml huggingface_hub wandb
```

## Célula 2 — Clonar repo + secrets

```python
from google.colab import userdata
import os

os.environ["ROBOFLOW_API_KEY"] = userdata.get("ROBOFLOW_API_KEY")
os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
try:
    os.environ["WANDB_API_KEY"] = userdata.get("WANDB_API_KEY")
except Exception:
    pass

!git clone -b claude/paint-inspection-ai-FRk8g https://github.com/gustavo-dev04/baja.git 2>/dev/null || (cd /content/baja && git pull)
%cd /content/baja
```

## Célula 3 — Construir o dataset unificado

```python
import sys
sys.path.insert(0, "/content/baja")
from training.v2.build_dataset import build

data_yaml = build(output_dir="/content/magnus_v2")
print("data.yaml:", data_yaml)
```

Saída esperada (resumo):
```
📦 Total de imagens-fonte únicas: ~3000
DATASET MAGNUS v2
Splits: train=2250 val=450 test=300
Instâncias por classe (consolidado):
  casca_de_laranja     507
  escorrimento         862
  bolha                682
  water_spotting      1087
  descascamento        264
  risco                509
  sujeira             1272
  oxidacao             ...
```

## Célula 4 — Treinar YOLO11s

```python
from training.v2.train import run_training

best = run_training(
    data_yaml=data_yaml,
    model="yolo11s.pt",
    epochs=150,
    batch=16,
    use_wandb=True,                         # gráficos online (opcional)
    push_to_hub=True,
    hf_repo="Guguinhaxd/magnus-v2",         # criado automaticamente
)
print("Pesos:", best)
```

Tempo: ~40-70 min em T4 (150 epochs, early stopping em 40 de paciência).

## Célula 5 — Avaliar (TTA + matriz de confusão)

```python
from training.v2.evaluate import evaluate

results = evaluate(
    weights=best,
    data_yaml=data_yaml,
    use_tta=True,
    split="test",
)
print(results)
```

Gera `magnus_v2/eval/confusion_matrix.png` — mostra quais defeitos o
modelo confunde. Material direto pro relatório/artigo.

## Célula 6 — Visualizar a matriz de confusão

```python
from IPython.display import Image as IPImage
IPImage("/content/baja/magnus_v2/eval/confusion_matrix.png")
```

## Ativar no backend (produção)

Depois do push, atualize a env var no HF Space:
```
BAJA_MODEL_WEIGHTS = hf://Guguinhaxd/magnus-v2/best.pt
```
E faça Factory rebuild. O frontend Magnus passa a usar o modelo de 8 classes.

⚠️ Atualize também o frontend: `ResultsPanel.tsx` e `DetectionOverlay.tsx`
têm os mapas de severidade/labels — adicione `descascamento`, `sujeira`,
`oxidacao` se ainda não estiverem (já estão previstos no código).

## Troubleshooting

| Erro | Solução |
|---|---|
| `ROBOFLOW_API_KEY não definido` | Confere Colab Secrets, célula 2 |
| `CUDA out of memory` | `batch=8` na célula 4 |
| Dataset com poucas imagens | Roda célula 3 de novo, confere logs de download |
| mAP baixo numa classe | Olha a matriz de confusão; classe rara pode precisar de mais dados (Fase 3 active learning) |
