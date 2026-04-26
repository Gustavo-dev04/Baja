# Treinar YOLO no Colab

Pipeline: Supabase → Colab GPU → fine-tune → `best.pt` → HF Hub.

## Pré-requisito: GPU

No Colab: `Runtime → Change runtime type → T4 GPU`. (Free.)

## Pré-requisito: Colab Secrets

Lateral esquerda do Colab tem um ícone de **chave** (Secrets). Adicione:

| Secret | Valor | Notebook access |
|---|---|---|
| `SUPABASE_URL` | `https://aclabwtsdzzdmpumtjbx.supabase.co` | ON |
| `SUPABASE_SERVICE_ROLE_KEY` | a service_role key | ON |
| `HF_TOKEN` | token write do Hugging Face | ON |

Esses valores **nunca** ficam no notebook — ficam no perfil do Google.

## Célula 1 — Instalar deps

```python
!pip install -q ultralytics supabase huggingface_hub
```

## Célula 2 — Carregar secrets e clonar repo

```python
from google.colab import userdata
import os

os.environ["SUPABASE_URL"] = userdata.get("SUPABASE_URL")
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = userdata.get("SUPABASE_SERVICE_ROLE_KEY")
os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")

!git clone -b claude/paint-inspection-ai-FRk8g https://github.com/gustavo-dev04/baja.git
%cd /content/baja
```

## Célula 3 — Treinar

```python
import sys
sys.path.insert(0, "/content/baja")
from training.train_yolo import run_training

best_pt = run_training(
    dataset_name="paint-defects-pretrain",
    output_dir="/content/runs",
    epochs=50,           # 30-100 é razoável; comece com 30 pra ver tempo
    img_size=640,
    batch=16,
    model="yolov8n.pt",  # n=nano, s=small, m=medium (mais lento, mais preciso)
    push_to_hub=True,
    hf_repo="Guguinhaxd/baja-paint-models",  # vai ser criado se não existir
)
print("Pesos finais:", best_pt)
```

## Output esperado

```
=== Materializando dataset 'paint-defects-pretrain' ===
Imagens no banco: 1850
Imagens com pelo menos uma anotação válida: 1820
Manifest YOLO: /content/runs/yolo-data/data.yaml

=== Treinando (yolov8n.pt, 50 epochs) ===
[ultralytics logs ...]
mAP50: 0.74  mAP50-95: 0.49

✅ best.pt salvo em: /content/baja/baja/paint-defects-pretrain-ft/weights/best.pt
✅ Upload no HF Hub: https://huggingface.co/Guguinhaxd/baja-paint-models
```

Tempo: ~30-60 min para 50 epochs em T4 (depende do tamanho do dataset).

## Próximo passo

Ativar o modelo em produção (semana 4 do roadmap — endpoint
`POST /api/v1/models/{id}/activate` faz hot-swap sem rebuild do Space).

## Troubleshooting

| Erro | Solução |
|---|---|
| `CUDA out of memory` | `batch=8` ou `img_size=480` |
| `RuntimeError: SUPABASE_URL ...` | confere Colab Secrets, célula 2 |
| `mAP=0` após treino | provavelmente labels vazios — debug: olhe `/content/runs/yolo-data/labels/train` |
| Treino muito lento | confirma GPU: `import torch; print(torch.cuda.is_available())` deve dar `True` |
