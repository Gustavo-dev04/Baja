"""Calibração da câmera (lente de 120°) e referência métrica do prato, com tabuleiro ChArUco.

Fluxo:
1. `tabuleiro`: gera o PDF do tabuleiro para imprimir em escala 1:1 (conferir a régua de 50 mm).
2. Fotos do tabuleiro em 12–20 posições/inclinações diferentes -> parâmetros da lente (K, distorção).
3. Uma foto do tabuleiro DEITADO no prato, no centro -> posição do prato em relação à câmera
   (é isso que permite medir em milímetros e corrigir a paralaxe pela espessura da peça).
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import cv2
import numpy as np

TABULEIRO = {"colunas": 9, "linhas": 7, "quadrado_mm": 12.0, "marcador_mm": 9.0, "dicionario": "DICT_4X4_50"}


def criar_tabuleiro(spec=None):
    spec = dict(spec or TABULEIRO)
    dic = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, spec["dicionario"]))
    board = cv2.aruco.CharucoBoard((spec["colunas"], spec["linhas"]), spec["quadrado_mm"], spec["marcador_mm"], dic)
    spec["largura_mm"] = spec["colunas"] * spec["quadrado_mm"]
    spec["altura_mm"] = spec["linhas"] * spec["quadrado_mm"]
    return board, spec


def imagem_tabuleiro(board, spec, px_por_mm: float):
    w = int(round(spec["largura_mm"] * px_por_mm))
    h = int(round(spec["altura_mm"] * px_por_mm))
    return board.generateImage((w, h), marginSize=0, borderBits=1)


def gerar_pdf_tabuleiro(caminho: Path, dpi: int = 300):
    """PDF A4 com o tabuleiro em escala real + régua de 50 mm para conferir a impressão."""
    from PIL import Image, ImageDraw, ImageFont
    board, spec = criar_tabuleiro()
    ppmm = dpi / 25.4
    tab = Image.fromarray(imagem_tabuleiro(board, spec, ppmm))
    A4 = (int(210 * ppmm), int(297 * ppmm))
    pag = Image.new("L", A4, 255)
    x0, y0 = int((A4[0] - tab.width) / 2), int(40 * ppmm)
    pag.paste(tab, (x0, y0))
    d = ImageDraw.Draw(pag)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", int(4 * ppmm))
    except OSError:
        f = ImageFont.load_default()
    d.text((x0, int(15 * ppmm)), "ScanParts - tabuleiro de calibração ChArUco", font=f, fill=0)
    d.text((x0, int(22 * ppmm)), f"{spec['colunas']}x{spec['linhas']} quadrados de {spec['quadrado_mm']:g} mm "
                                 f"({spec['dicionario']}). Imprimir em 100% (sem ajustar à página).", font=f, fill=0)
    yr = y0 + tab.height + int(20 * ppmm)
    d.rectangle([x0, yr, x0 + int(50 * ppmm), yr + int(2 * ppmm)], fill=0)
    d.text((x0, yr + int(4 * ppmm)), "Régua de conferência: esta barra deve medir 50 mm", font=f, fill=0)
    d.text((x0, yr + int(12 * ppmm)), "Cole o tabuleiro numa superfície rígida e plana (MDF, acrílico).", font=f, fill=0)
    pag.save(caminho, "PDF", resolution=dpi)


def detectar(img, board):
    """Cantos ChArUco: (pontos_objeto Nx3, pontos_imagem Nx2) ou (None, None)."""
    cinza = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    det = cv2.aruco.CharucoDetector(board)
    cantos, ids, _, _ = det.detectBoard(cinza)
    if ids is None or len(ids) < 8:
        return None, None
    obj, imgp = board.matchImagePoints(cantos, ids)
    return obj.reshape(-1, 3).astype(np.float32), imgp.reshape(-1, 2).astype(np.float32)


def calibrar(fotos, foto_referencia, racional: bool = False, log=print):
    board, spec = criar_tabuleiro()
    objs, imgs, usadas, tam = [], [], [], None
    for f in fotos:
        img = cv2.imread(str(f))
        if img is None:
            continue
        tam = (img.shape[1], img.shape[0])
        o, p = detectar(img, board)
        if o is None:
            log(f"  {Path(f).name}: tabuleiro não encontrado (ignorada)")
            continue
        objs.append(o); imgs.append(p); usadas.append(str(f))
    if len(objs) < 6:
        raise RuntimeError(f"Só {len(objs)} fotos válidas; tire pelo menos 10, com o tabuleiro inclinado em várias direções.")
    flags = cv2.CALIB_RATIONAL_MODEL if racional else 0
    rms, K, dist, _, _ = cv2.calibrateCamera(objs, imgs, tam, None, None, flags=flags)
    log(f"  lente: {len(objs)} fotos, erro de reprojeção {rms:.3f} px")

    ref = cv2.imread(str(foto_referencia))
    o, p = detectar(ref, board)
    if o is None:
        raise RuntimeError("Tabuleiro não encontrado na foto de referência do prato.")
    ok, rvec, tvec = cv2.solvePnP(o, p, K, dist, flags=cv2.SOLVEPNP_ITERATIVE)
    proj, _ = cv2.projectPoints(o, rvec, tvec, K, dist)
    erro_ref = float(np.sqrt(np.mean(np.sum((proj.reshape(-1, 2) - p) ** 2, axis=1))))
    R, _ = cv2.Rodrigues(rvec)
    C_b = (-R.T @ tvec).ravel()
    altura = float(abs(C_b[2]))
    mm_px = altura / K[0, 0]
    log(f"  prato: câmera a {altura:.1f} mm, {mm_px:.3f} mm/pixel no centro, reprojeção {erro_ref:.3f} px")
    return {
        "versao": 1,
        "tamanho_imagem": list(tam),
        "K": K.tolist(), "dist": dist.ravel().tolist(),
        "rms_lente_px": float(rms), "fotos_usadas": len(objs),
        "rvec_prato": rvec.ravel().tolist(), "tvec_prato": tvec.ravel().tolist(),
        "erro_referencia_px": erro_ref, "altura_camera_mm": altura, "mm_por_pixel_centro": mm_px,
        "centro_prato_mm": [spec["largura_mm"] / 2, spec["altura_mm"] / 2],
        "raio_roi_mm": 80.0, "tabuleiro": spec,
    }


def salvar(cal: dict, caminho: Path):
    Path(caminho).write_text(json.dumps(cal, indent=1), encoding="utf-8")


def carregar(caminho: Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def expandir(padrao: str):
    return sorted(glob.glob(padrao))
