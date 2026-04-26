# Training pipeline

Scripts e notebooks para fine-tuning do modelo YOLO usando datasets
externos (Roboflow Universe) e o dataset próprio armazenado no Supabase.

## Estrutura prevista

| Arquivo | Função |
|---|---|
| `import_roboflow.py` | Baixa dataset do Roboflow, mapeia classes, sobe imagens + anotações via API |
| `train.ipynb` (futuro) | Pull do Supabase → fine-tune YOLOv8 → upload pro HF Hub |
| `evaluate.ipynb` (futuro) | Métricas (mAP, precision, recall por classe) |

## Mapeamento de classes (Roboflow → Baja)

Definido em `import_roboflow.py` (`CLASS_MAP`):

| Roboflow | Baja |
|---|---|
| `orange_peel` | `casca_de_laranja` |
| `runs_sags` | `escorrimento` |
| `solvent_pop` | `bolha` |
| `water_spotting` | `water_spotting` |
| `null` | (ignorado, é negativo) |

Para outros datasets com classes diferentes, edite `CLASS_MAP`.

## Como rodar (Colab)

Ver `import_roboflow_colab.md` (passos copy-paste).

## Como rodar (local)

```bash
pip install requests pyyaml roboflow
python -m roboflow download ...
python training/import_roboflow.py \
  --api-url https://<user>-baja-paint-inspection-api.hf.space \
  --password '<BAJA_ADMIN_PASSWORD>' \
  --dataset-root ./paint-defect-detection-1 \
  --name paint-defects-pretrain
```
