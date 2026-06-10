"""Magnus v2 — unified taxonomy and dataset sources.

Single source of truth for:
1. The 8 paint-defect classes Magnus v2 detects.
2. The mapping from each external dataset's class names to ours.
3. Which Roboflow projects are clean enough to include (curated, correct
   domain). Noisy / mixed-domain datasets (the `weld-dataset` projects) are
   deliberately excluded — see notebooks/README for the curation rationale.
"""

from __future__ import annotations

# =========================================================
# Unified taxonomy — 8 classes, fixed order = YOLO class ids
# =========================================================

UNIFIED_CLASSES: list[str] = [
    "casca_de_laranja",   # 0
    "escorrimento",       # 1
    "bolha",              # 2  (solvent_pop + bubbling + blistering merged)
    "water_spotting",     # 3
    "descascamento",      # 4
    "risco",              # 5
    "sujeira",            # 6
    "oxidacao",           # 7
]

CLASS_TO_ID: dict[str, int] = {c: i for i, c in enumerate(UNIFIED_CLASSES)}

# Friendly pt-BR labels for UI / reports.
FRIENDLY: dict[str, str] = {
    "casca_de_laranja": "Casca de laranja",
    "escorrimento": "Escorrimento",
    "bolha": "Bolha",
    "water_spotting": "Mancha de água",
    "descascamento": "Descascamento",
    "risco": "Risco",
    "sujeira": "Sujeira",
    "oxidacao": "Oxidação",
}

# =========================================================
# Class mapping — every external label → our taxonomy.
# Anything not in this map is dropped (e.g. `good_paint` becomes a
# negative/background sample, `dent`/`Headlight-Damage` are body damage
# outside Magnus's scope).
# =========================================================

CLASS_MAP: dict[str, str] = {
    # casca de laranja
    "orange_peel": "casca_de_laranja",
    # escorrimento
    "runs_sags": "escorrimento",
    "runs": "escorrimento",
    "dripping_curtaining": "escorrimento",
    # bolha (merged bubble-type defects)
    "solvent_pop": "bolha",
    "bubbling": "bolha",
    "blistering": "bolha",
    "pinholes_cratering": "bolha",
    # mancha d'água
    "water_spotting": "water_spotting",
    "water spot": "water_spotting",
    # descascamento
    "peel_off": "descascamento",
    "Paint-fading": "descascamento",
    "paint-fading": "descascamento",
    "paint-chip": "descascamento",
    # risco
    "scratch": "risco",
    "Scratch": "risco",
    "Crack": "risco",
    "Paint-Crack": "risco",
    "doorouter-scratch": "risco",
    "front-bumper-scratch": "risco",
    "rear-bumper-scratch": "risco",
    # sujeira
    "dirt": "sujeira",
    # oxidação
    "Rust": "oxidacao",
    "rust": "oxidacao",
}

# Labels that mark an image as a legitimate NEGATIVE (clean paint).
# Images whose only annotations are these are kept as background samples.
NEGATIVE_OK: set[str] = {"good_paint"}

# Explicitly-ignored labels (documented so future contributors know it was a
# decision, not an oversight). Maps to None.
IGNORED: set[str] = {
    "good_paint",            # negative sample — kept as background
    "mottling", "Alligatoring", "wrinkling",  # rare, too few samples for v2
    "PDR-Dent", "Dent", "dent", "paint-trace",
    # ... all body-damage classes from car-damage-zxk33
}


# =========================================================
# Curated source datasets (Roboflow Universe)
# Only clean, correctly-domained, named-class projects.
# =========================================================

class Source:
    def __init__(self, workspace: str, project: str, role: str):
        self.workspace = workspace
        self.project = project
        self.role = role  # human-readable note on why it's included

    def __repr__(self) -> str:
        return f"{self.workspace}/{self.project}"


SOURCES: list[Source] = [
    Source(
        "baopersonal", "paint-defect-combine-3",
        "base principal — 8 classes nomeadas, ~2.8k imagens",
    ),
    Source(
        "baopersonal", "paint-defect-combine-2-vsprw",
        "complementar — mesmas 8 classes, ~3.2k imagens (dedup remove overlap)",
    ),
    Source(
        "baopersonal", "paint-defect-detection-lx0xk",
        "subset balanceado v1 — 4 classes, ~2k imagens (dedup remove overlap)",
    ),
    Source(
        "cardetecion", "car-paint-damage-detection",
        "oxidação/risco — Rust, Scratch, Paint-fading (~456 imgs)",
    ),
    Source(
        "cat-ln1ow", "paint-defect-detection-j7imb",
        "raras + negativos — blistering, good_paint (~73 imgs)",
    ),
]

# Removido: politeknik-sultan-azlan-shah/car-paint-surface-defect — é um
# projeto do tipo `multilabel-classification` (sem bounding boxes), logo
# incompatível com detecção YOLO. Só ~40 imagens, perda desprezível.

# Datasets deliberately EXCLUDED (kept here so the decision is auditable):
#   weld-dataset/paint-new (22k)            — mixed domain (carros inteiros,
#   weld-dataset/paint-defect-detection-6eskq (23k)  rodas), labels 0-7
#       numéricas inconsistentes entre si. Reservados para Fase 3 (active
#       learning: rodar Magnus v2 neles e curar só os closeups de pintura).
#   car-damage-zxk33 (13k)  — 90% dano de lataria (dents), não pintura.
#   building-fault.../paint-damage-det — pintura de prédio, domínio diverge.
#   drink-tracker/car-detection — detecção de carro inteiro, classe única.
#   fardas-workspace/dataset-baret — sem relação com pintura.
