"""Sensibilidade: o que acontece com a medida quando algo foge do ideal.

- espessura digitada errada (afeta a correção de paralaxe);
- peça mais escura (menos contraste com o prato preto);
- câmera levou um esbarrão depois da calibração (altura e inclinação mudaram).

Uso: python3 testes/teste_sensibilidade.py --saida resultados_sens
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scanparts import calibracao as cb  # noqa: E402
from scanparts import simulador as sm  # noqa: E402
from scanparts.geometria import amostrar_entidades, desvio_maximo  # noqa: E402
from scanparts.medicao import Medidor  # noqa: E402
from teste_sintetico import para_cad  # noqa: E402


def avaliar(med, img, esp_informada, gab, R_bw, t_bw):
    res = med.medir(img, esp_informada)
    esp = gab["espessura"]
    gt_f = [(*para_cad([[x, y]], esp, R_bw, t_bw)[0], d) for x, y, d in gab["furos_w"]]
    gt_c = para_cad(gab["contorno_w"], esp, R_bw, t_bw)
    ed, ec = [], []
    for gx, gy, gd in gt_f:
        f = min(res["furos"], key=lambda f: math.hypot(f["centro"][0] - gx, f["centro"][1] - gy))
        ed.append(abs(f["diametro_medido"] - gd)); ec.append(math.hypot(f["centro"][0] - gx, f["centro"][1] - gy))
    dmax, _ = desvio_maximo(amostrar_entidades(res["contorno"], 0.1), gt_c)
    (_, _), (w, h), _ = cv2.minAreaRect(gt_c.astype(np.float32))
    return {"furos": f"{len(res['furos'])}/{len(gt_f)}", "erro_diam_max": round(max(ed), 3), "erro_centro_max": round(max(ec), 3),
            "contorno_desvio_max": round(dmax, 3), "largura_medida": res["dimensoes_mm"]["largura"], "largura_real": round(max(w, h), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="resultados_sens")
    a = ap.parse_args()
    out = Path(a.saida)
    (out / "calib").mkdir(parents=True, exist_ok=True)
    cam = sm.Camera.imx219()
    fotos = []
    for i, (R, t) in enumerate(sm.poses_calibracao(12, seed=3)):
        f = out / "calib" / f"t{i:02d}.jpg"
        cv2.imwrite(str(f), sm.renderizar_tabuleiro(cam, R, t, seed=i)); fotos.append(f)
    R_bw, t_bw = sm.pose_tabuleiro_plano()
    cv2.imwrite(str(out / "ref.jpg"), sm.renderizar_tabuleiro(cam, R_bw, t_bw, seed=50))
    cal = cb.calibrar(fotos, out / "ref.jpg", log=lambda m: None)
    med = Medidor(cal)
    peca = sm.suporte_retangular()
    linhas = []

    img, gab = sm.renderizar_peca(cam, peca, 3.0, math.radians(25), 8, -5, seed=11)
    linhas.append(("Referência (espessura 3,0 mm informada certa)", avaliar(med, img, 3.0, gab, R_bw, t_bw)))
    for erro in (0.2, 0.5, 1.0, -3.0):
        linhas.append((f"Espessura informada errada em {erro:+.1f} mm", avaliar(med, img, 3.0 + erro, gab, R_bw, t_bw)))
    for b in (0.7, 0.5):
        img_b, gab_b = sm.renderizar_peca(cam, peca, 3.0, math.radians(25), 8, -5, seed=11, brilho=b)
        linhas.append((f"Peça mais escura ({int(b * 100)}% do brilho)", avaliar(med, img_b, 3.0, gab_b, R_bw, t_bw)))
    for nome, kw in (("Câmera 1 mm mais baixa depois da calibração", dict(altura=129.0)),
                     ("Câmera inclinou +1° depois da calibração", dict(inclinacao_graus=(1.8, -0.6, 1.5)))):
        cam2 = sm.Camera.imx219(**kw)
        img2, gab2 = sm.renderizar_peca(cam2, peca, 3.0, math.radians(25), 8, -5, seed=11)
        linhas.append((nome, avaliar(med, img2, 3.0, gab2, R_bw, t_bw)))

    for nome, r in linhas:
        print(f"{nome:50s} furos {r['furos']} | Ø {r['erro_diam_max']:.3f} | centro {r['erro_centro_max']:.3f} | "
              f"contorno {r['contorno_desvio_max']:.3f} | largura {r['largura_medida']:.2f} (real {r['largura_real']:.2f}) mm")
    (out / "sensibilidade.json").write_text(json.dumps(linhas, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
