"""Junta datasets YOLO (sintético, Roboflow, fotos próprias) num só, com a classe única "furo".

Cada fonte é passada como  PASTA  ou  PASTA:IDS , onde IDS são as classes da
fonte que viram "furo" (as outras são descartadas). Sem IDS, todas viram "furo".

Aceita as duas organizações comuns:
    fonte/images/train + fonte/labels/train      (Ultralytics)
    fonte/train/images + fonte/train/labels      (exportação do Roboflow)
As pastas "valid" e "test" vão para a validação.

Exemplo:
    python juntar_datasets.py --destino dados/final \\
        dados/sintetico  dados/roboflow_furos:0  dados/fotos_grupo
"""
import argparse
import shutil
from pathlib import Path

SPLITS = {"train": "train", "val": "val", "valid": "val", "test": "val"}
EXT_IMG = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def pares(fonte: Path):
    """Encontra (pasta_imagens, pasta_rotulos, split_destino)."""
    for nome, destino in SPLITS.items():
        for img, lab in ((fonte / "images" / nome, fonte / "labels" / nome),
                         (fonte / nome / "images", fonte / nome / "labels")):
            if img.is_dir():
                yield img, lab, destino


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--destino", required=True)
    ap.add_argument("fontes", nargs="+", help="PASTA ou PASTA:IDS (ex.: dados/rf:0,2)")
    a = ap.parse_args()

    dest = Path(a.destino)
    for split in ("train", "val"):
        (dest / "images" / split).mkdir(parents=True, exist_ok=True)
        (dest / "labels" / split).mkdir(parents=True, exist_ok=True)

    for k, fonte_txt in enumerate(a.fontes):
        caminho, _, ids = fonte_txt.partition(":")
        fonte = Path(caminho)
        manter = {int(i) for i in ids.split(",")} if ids else None
        cont = {"train": 0, "val": 0}
        objetos = 0
        for pasta_img, pasta_lab, split in pares(fonte):
            for img in pasta_img.iterdir():
                if img.suffix.lower() not in EXT_IMG:
                    continue
                novo = f"f{k}_{img.stem}"
                shutil.copy2(img, dest / "images" / split / f"{novo}{img.suffix.lower()}")
                linhas = []
                lab = pasta_lab / f"{img.stem}.txt"
                if lab.exists():
                    for ln in lab.read_text().splitlines():
                        partes = ln.split()
                        if not partes:
                            continue
                        if manter is None or int(partes[0]) in manter:
                            linhas.append("0 " + " ".join(partes[1:]))
                (dest / "labels" / split / f"{novo}.txt").write_text("\n".join(linhas))
                objetos += len(linhas)
                cont[split] += 1
        print(f"{fonte}: {cont['train']} treino, {cont['val']} val, {objetos} furos")

    (dest / "data.yaml").write_text(
        f"path: {dest.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: furo\n")
    print(f"Dataset final em {dest.resolve()}")


if __name__ == "__main__":
    main()
