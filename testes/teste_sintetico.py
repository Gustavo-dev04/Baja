"""Teste ponta a ponta com dados sintéticos: calibração + medição de peças com gabarito conhecido.

Simula a bancada (câmera IMX219 120° a ~130 mm, levemente desalinhada), calibra a lente com fotos
sintéticas do tabuleiro ChArUco, fotografa peças com medidas conhecidas em posições aleatórias e
compara o que o ScanParts mediu com o gabarito.

Uso:
    python3 testes/teste_sintetico.py --saida resultados_teste --poses 3
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scanparts import calibracao as cb  # noqa: E402
from scanparts import simulador as sm  # noqa: E402
from scanparts.exportar import exportar_dxf, exportar_fusion  # noqa: E402
from scanparts.geometria import amostrar_entidades, desvio_maximo  # noqa: E402
from scanparts.medicao import Medidor  # noqa: E402


def para_cad(P2, z, R_bw, t_bw):
    """Mundo (x, y no plano z) -> referencial do CAD usado pelo ScanParts (x do tabuleiro, -y do tabuleiro)."""
    Pw = np.c_[np.asarray(P2, float), np.full(len(P2), z)]
    Pb = (Pw - t_bw) @ R_bw
    return np.c_[Pb[:, 0], -Pb[:, 1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="resultados_teste")
    ap.add_argument("--poses", type=int, default=3, help="posições aleatórias por peça e espessura")
    ap.add_argument("--fotos-calibracao", type=int, default=15)
    ap.add_argument("--semente", type=int, default=7)
    a = ap.parse_args()
    out = Path(a.saida)
    (out / "calibracao").mkdir(parents=True, exist_ok=True)
    (out / "cenas").mkdir(exist_ok=True)
    rng = np.random.default_rng(a.semente)
    t0 = time.time()

    # ------------------------------------------------ bancada simulada + calibração
    cam = sm.Camera.imx219()
    print(f"Câmera simulada: fx={cam.K[0, 0]:.1f} px, altura {cam.C_w[2]:.1f} mm, inclinação (0,8°, -0,6°, 1,5°)")
    fotos = []
    for i, (R, t) in enumerate(sm.poses_calibracao(a.fotos_calibracao, seed=a.semente)):
        f = out / "calibracao" / f"tabuleiro_{i:02d}.jpg"
        cv2.imwrite(str(f), sm.renderizar_tabuleiro(cam, R, t, seed=100 + i))
        fotos.append(f)
    R_bw, t_bw = sm.pose_tabuleiro_plano()
    ref = out / "calibracao" / "referencia_prato.jpg"
    cv2.imwrite(str(ref), sm.renderizar_tabuleiro(cam, R_bw, t_bw, seed=999))
    print("Calibrando...")
    cal = cb.calibrar(fotos, ref, log=lambda m: print(m))
    cb.salvar(cal, out / "calibracao.json")
    erro_fx = cal["K"][0][0] - cam.K[0, 0]
    erro_alt = cal["altura_camera_mm"] - cam.C_w[2]
    print(f"  erro de fx: {erro_fx:+.2f} px | erro da altura da câmera: {erro_alt:+.3f} mm")
    med = Medidor(cal)

    # ------------------------------------------------ cenas
    casos = []
    for nome, fab in sm.PECAS.items():
        peca = fab()
        for esp in (3.0, 5.0):
            for k in range(a.poses):
                ang = rng.uniform(0, 2 * math.pi)
                tx, ty = rng.uniform(-20, 20, 2)
                seed = int(rng.integers(1e9))
                img, gab = sm.renderizar_peca(cam, peca, esp, ang, tx, ty, seed=seed)
                try:
                    res = med.medir(img, esp)
                except Exception as e:  # noqa: BLE001
                    print(f"  {nome} esp {esp} pose {k}: FALHOU – {e}")
                    casos.append({"peca": nome, "espessura": esp, "falhou": str(e)})
                    continue
                # gabarito no referencial do CAD
                furos_gt = [(*para_cad([[x, y]], esp, R_bw, t_bw)[0], d) for x, y, d in gab["furos_w"]]
                contorno_gt = para_cad(gab["contorno_w"], esp, R_bw, t_bw)
                erros_d, erros_c, interp_ok = [], [], 0
                usados = set()
                for gx, gy, gd in furos_gt:
                    if not res["furos"]:
                        break
                    j = int(np.argmin([math.hypot(f["centro"][0] - gx, f["centro"][1] - gy) for f in res["furos"]]))
                    f = res["furos"][j]
                    dist = math.hypot(f["centro"][0] - gx, f["centro"][1] - gy)
                    if dist > gd:      # não achou esse furo
                        continue
                    usados.add(j)
                    erros_d.append(f["diametro_medido"] - gd)
                    erros_c.append(dist)
                    interp_ok += int(abs(f["interpretacao"]["nominal"] - gd) < 1e-6)
                amostras = amostrar_entidades(res["contorno"], 0.1)
                dmax, dmed = desvio_maximo(amostras, contorno_gt)
                (_, _), (w_gt, h_gt), _ = cv2.minAreaRect(contorno_gt.astype(np.float32))
                caso = {
                    "peca": nome, "espessura": esp, "pose": k, "angulo_graus": round(math.degrees(ang), 1),
                    "furos_gabarito": len(furos_gt), "furos_achados": len(usados), "furos_extras": len(res["furos"]) - len(usados),
                    "erro_diametro_max_mm": round(float(np.max(np.abs(erros_d))), 3) if erros_d else None,
                    "erro_diametro_medio_mm": round(float(np.mean(erros_d)), 3) if erros_d else None,
                    "erro_centro_max_mm": round(float(np.max(erros_c)), 3) if erros_c else None,
                    "interpretacao_correta": f"{interp_ok}/{len(furos_gt)}",
                    "contorno_desvio_max_mm": round(dmax, 3), "contorno_desvio_medio_mm": round(dmed, 3),
                    "dimensoes_medidas": res["dimensoes_mm"], "dimensoes_gabarito": {"largura": round(max(w_gt, h_gt), 2), "altura": round(min(w_gt, h_gt), 2)},
                    "contorno": res["contorno_info"],
                    "raios_concordancia": sorted({e.raio for e in res["contorno"] if e.tipo in ("arco", "circulo")}),
                }
                casos.append(caso)
                print(f"  {nome:18s} esp {esp:.0f} mm pose {k}: furos {len(usados)}/{len(furos_gt)} | "
                      f"Ø erro máx {caso['erro_diametro_max_mm']} mm | centro erro máx {caso['erro_centro_max_mm']} mm | "
                      f"contorno desvio máx {dmax:.3f} mm | norma {caso['interpretacao_correta']} | {res['contorno_info']['tipo']}")
                if k == 0:
                    base = out / "cenas" / f"{nome}_esp{esp:.0f}"
                    cv2.imwrite(f"{base}_foto.jpg", img)
                    cv2.imwrite(f"{base}_resultado.jpg", med.sobreposicao(img, res))
                    exportar_dxf(Path(f"{base}.dxf"), res["contorno"], res["furos"], esp)
                    exportar_fusion(Path(f"{base}_fusion.py"), res["contorno"], res["furos"], esp)

    # ------------------------------------------------ resumo
    ok = [c for c in casos if "falhou" not in c]
    resumo = {
        "cenas": len(casos), "falhas": len(casos) - len(ok),
        "calibracao": {"rms_px": round(cal["rms_lente_px"], 3), "erro_fx_px": round(erro_fx, 2), "erro_altura_mm": round(erro_alt, 3),
                       "mm_por_pixel": round(cal["mm_por_pixel_centro"], 4)},
        "furos_achados": f"{sum(c['furos_achados'] for c in ok)}/{sum(c['furos_gabarito'] for c in ok)}",
        "furos_extras": sum(c["furos_extras"] for c in ok),
        "erro_diametro_max_mm": max(c["erro_diametro_max_mm"] for c in ok if c["erro_diametro_max_mm"] is not None),
        "erro_centro_max_mm": max(c["erro_centro_max_mm"] for c in ok if c["erro_centro_max_mm"] is not None),
        "contorno_desvio_max_mm": max(c["contorno_desvio_max_mm"] for c in ok),
        "contorno_desvio_medio_mm": round(float(np.mean([c["contorno_desvio_medio_mm"] for c in ok])), 3),
        "interpretacao_correta": f"{sum(int(c['interpretacao_correta'].split('/')[0]) for c in ok)}/{sum(c['furos_gabarito'] for c in ok)}",
        "tempo_total_s": round(time.time() - t0, 1),
    }
    (out / "resultado.json").write_text(json.dumps({"resumo": resumo, "casos": casos}, indent=1, ensure_ascii=False, default=float))
    print("\nRESUMO", json.dumps(resumo, indent=1, ensure_ascii=False))
    return resumo


if __name__ == "__main__":
    main()
