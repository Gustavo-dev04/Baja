"""Etapa 2 do fluxo (Localização): o YOLO11n treinado acha os furos e confere a medição clássica.

A IA localiza; quem mede em milímetros é a geometria calibrada (medicao.py).
Cada furo medido recebe "confirmado_ia" e cada caixa do YOLO sem furo medido
vira um alerta ("ia_sem_medida") – sinal de furo perdido ou de reflexo.
"""
from __future__ import annotations

import numpy as np

_MODELOS = {}


def _modelo(caminho: str):
    if caminho not in _MODELOS:
        from ultralytics import YOLO
        _MODELOS[caminho] = YOLO(caminho)
    return _MODELOS[caminho]


def detectar_furos(modelo: str, img, conf: float = 0.4, recorte=None, imgsz: int = 640):
    """Caixas [x0, y0, x1, y1] em pixels da foto inteira. `recorte` = (x0, y0, x1, y1) limita a busca à peça."""
    x0, y0 = 0, 0
    if recorte is not None:
        x0, y0, x1, y1 = [int(v) for v in recorte]
        img = img[y0:y1, x0:x1]
    r = _modelo(modelo).predict(img, conf=conf, imgsz=imgsz, verbose=False)[0]
    out = []
    for b in r.boxes:
        bx = b.xyxy[0].tolist()
        out.append({"caixa_px": [round(bx[0] + x0, 1), round(bx[1] + y0, 1), round(bx[2] + x0, 1), round(bx[3] + y0, 1)],
                    "confianca": round(float(b.conf[0]), 3)})
    return out


def conferir_furos(modelo: str, img, medidor, res: dict, conf: float = 0.25, margem_mm: float = 8.0,
                   lado_min_mm: float = 110.0) -> dict:
    """Roda o YOLO só na região da peça e cruza com os furos medidos. Altera `res` (campos novos) e devolve um resumo."""
    e = res["espessura_mm"]
    px = medidor.mm_para_pixels(res["contorno_pontos_mm"], e)
    mpp = medidor.cal["mm_por_pixel_centro"]
    m = margem_mm / mpp
    h, w = img.shape[:2]
    # recorte quadrado em volta da peça, com lado mínimo: o modelo foi treinado com furos pequenos no quadro,
    # então um recorte justo demais deixa os furos grandes (Ø > 10 mm) fora da escala que ele conhece
    cx, cy = (px[:, 0].min() + px[:, 0].max()) / 2, (px[:, 1].min() + px[:, 1].max()) / 2
    lado = max(np.ptp(px[:, 0]) + 2 * m, np.ptp(px[:, 1]) + 2 * m, lado_min_mm / mpp)
    rec = (max(0, cx - lado / 2), max(0, cy - lado / 2), min(w, cx + lado / 2), min(h, cy + lado / 2))
    caixas = detectar_furos(modelo, img, conf=conf, recorte=rec)
    usadas = set()
    for f in res["furos"]:
        c = medidor.mm_para_pixels([f["centro"]], e)[0]
        f["confirmado_ia"] = None
        melhor = None
        for i, b in enumerate(caixas):
            x0, y0, x1, y1 = b["caixa_px"]
            if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
                d = np.hypot(c[0] - (x0 + x1) / 2, c[1] - (y0 + y1) / 2)
                if melhor is None or d < melhor[0]:
                    melhor = (d, i)
        if melhor is not None:
            usadas.add(melhor[1])
            f["confirmado_ia"] = caixas[melhor[1]]["confianca"]
    sobras = [b for i, b in enumerate(caixas) if i not in usadas]
    resumo = {"caixas": caixas, "furos_confirmados": sum(f["confirmado_ia"] is not None for f in res["furos"]),
              "furos_medidos": len(res["furos"]), "ia_sem_medida": sobras}
    res["ia"] = resumo
    return resumo


def desenhar(img, resumo: dict):
    """Caixas do YOLO na imagem de conferência: amarelo = confirmou um furo medido, magenta = alerta."""
    import cv2
    out = img
    sobras = {id(b) for b in resumo["ia_sem_medida"]}
    for b in resumo["caixas"]:
        x0, y0, x1, y1 = [int(v) for v in b["caixa_px"]]
        cor = (255, 0, 255) if id(b) in sobras else (0, 220, 255)
        cv2.rectangle(out, (x0, y0), (x1, y1), cor, 3)
        cv2.putText(out, f"IA {b['confianca']:.2f}", (x0, max(0, y0 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, cor, 3, cv2.LINE_AA)
    return out
