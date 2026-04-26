# Importar dataset Roboflow no Colab

Passos copy-paste para um notebook Colab novo.

## Célula 1 — Instalar dependências

```python
!pip install -q roboflow requests pyyaml
```

## Célula 2 — Baixar dataset do Roboflow

Cole aqui o snippet que o Roboflow gerou no botão "Show Download Code"
(formato YOLOv8). Algo do tipo:

```python
from roboflow import Roboflow
rf = Roboflow(api_key="SUA_API_KEY_DO_ROBOFLOW")
project = rf.workspace("baopersonal").project("paint-defect-detection-lx0xk")
version = project.version(1)  # confira o número da versão na página
dataset = version.download("yolov8")
print("Baixado em:", dataset.location)
```

## Célula 3 — Clonar repositório (para usar o script)

```python
!git clone -b claude/paint-inspection-ai-FRk8g https://github.com/gustavo-dev04/baja.git
```

## Célula 4 — Importar para o backend

Substitua `SUA_SENHA` pela sua `BAJA_ADMIN_PASSWORD`.

```python
import sys
sys.path.insert(0, "/content/baja/training")
from import_roboflow import import_roboflow_dataset

import_roboflow_dataset(
    api_url="https://guguinhaxd-baja-paint-inspection-api.hf.space",
    admin_password="SUA_SENHA",
    dataset_root=dataset.location,  # vem da célula 2
    target_dataset_name="paint-defects-pretrain",
)
```

## Output esperado

```
Classes do Roboflow: {0: 'null', 1: 'orange_peel', 2: 'runs_sags', ...}
Classes mapeadas para Baja: ['bolha', 'casca_de_laranja', 'escorrimento', 'water_spotting']
Login admin…
Garantindo dataset 'paint-defects-pretrain'…
  dataset_id = abc123...
Importando split 'train'…
  → 1500 imagens em train
  uploaded=1500  skipped=0  annotated=1487
...
TOTAL  uploaded=1900  skipped=0  annotated=1880
```

## Verificar no backend

No PowerShell:
```powershell
Invoke-RestMethod "https://guguinhaxd-baja-paint-inspection-api.hf.space/api/v1/datasets"
```

Tem que aparecer o novo dataset `paint-defects-pretrain` com `image_count`
preenchido.

## Troubleshooting

| Erro | Causa | Solução |
|---|---|---|
| `401 Unauthorized` | senha errada | confere `BAJA_ADMIN_PASSWORD` no HF Space |
| `503 Service Unavailable` | Supabase desconectado | verifica `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` |
| `413 Payload Too Large` | imagens muito grandes | reduzir resolução antes de subir |
| Upload muito lento | CPU free do HF é modesto | normal, deixa rodar |
| Anotações com `class_name not in dataset.classes` | classe nova | edita `CLASS_MAP` no script ou adiciona à lista de classes do dataset |
