"""Utilidades de câmera independentes da versão do OpenCV (4.x no Jetson, 5.x no PC)."""
from __future__ import annotations

import numpy as np


def desdistorcer(pts_px: np.ndarray, K: np.ndarray, dist: np.ndarray, iteracoes: int = 60) -> np.ndarray:
    """Pixels (N×2) -> coordenadas normalizadas sem distorção (N×2). Modelo de Brown com 5 ou 8 coeficientes
    (padrão ou racional do OpenCV), resolvido por iteração de ponto fixo (preciso nas bordas da lente)."""
    p = np.asarray(pts_px, np.float64).reshape(-1, 2)
    d = np.zeros(8)
    dist = np.asarray(dist, np.float64).ravel()
    d[: min(8, len(dist))] = dist[:8]
    k1, k2, p1, p2, k3, k4, k5, k6 = d
    xd = (p[:, 0] - K[0, 2]) / K[0, 0]
    yd = (p[:, 1] - K[1, 2]) / K[1, 1]
    x, y = xd.copy(), yd.copy()
    for _ in range(iteracoes):
        r2 = x * x + y * y
        radial = (1 + k1 * r2 + k2 * r2 ** 2 + k3 * r2 ** 3) / (1 + k4 * r2 + k5 * r2 ** 2 + k6 * r2 ** 3)
        dx = 2 * p1 * x * y + p2 * (r2 + 2 * x * x)
        dy = p1 * (r2 + 2 * y * y) + 2 * p2 * x * y
        x = (xd - dx) / radial
        y = (yd - dy) / radial
    return np.c_[x, y]
