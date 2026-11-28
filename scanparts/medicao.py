"""Medição da peça plana a partir de uma foto de cima (modo 1 – peça plana → extrusão).

1. Separa a peça (clara) do prato preto (limiar de Otsu dentro da região do prato).
2. Acha o contorno externo e os furos (topologia do OpenCV).
3. Refina cada ponto da borda com precisão subpixel (cruzamento do limiar ao longo da normal).
4. Converte pixels -> milímetros no PLANO DO TOPO da peça (corrige a paralaxe pela espessura).
5. Furos: ajuste de círculo + interpretação por norma. Contorno: retas e arcos de concordância.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from .camera_util import desdistorcer
from .geometria import (ajustar_circulo, amostrar_entidades, angulo_alinhamento, area_poligono,
                        segmentar_contorno, transformar_entidades)
from .normas import interpretar_furo


class Medidor:
    def __init__(self, cal: dict):
        self.cal = cal
        self.K = np.array(cal["K"], float)
        self.dist = np.array(cal["dist"], float)
        self.rvec = np.array(cal["rvec_prato"], float)
        self.tvec = np.array(cal["tvec_prato"], float)
        self.R, _ = cv2.Rodrigues(self.rvec)
        self.C_b = (-self.R.T @ self.tvec.reshape(3, 1)).ravel()     # câmera no referencial do tabuleiro
        self.sinal = -1.0 if self.C_b[2] < 0 else 1.0                 # lado da câmera (normalmente z < 0)

    # ---------------------------------------------------------------- conversões
    def pixels_para_mm(self, pts_px: np.ndarray, espessura: float) -> np.ndarray:
        """Pixels -> (x, y) em mm no plano do topo da peça, já no referencial do CAD (Y para cima)."""
        und = desdistorcer(pts_px, self.K, self.dist)
        d_c = np.c_[und, np.ones(len(und))]
        d_b = d_c @ self.R          # = (R^T d_c^T)^T
        z = self.sinal * espessura
        s = (z - self.C_b[2]) / d_b[:, 2]
        P = self.C_b + s[:, None] * d_b
        return np.c_[P[:, 0], -P[:, 1]]

    def mm_para_pixels(self, pts_mm: np.ndarray, espessura: float) -> np.ndarray:
        pts_mm = np.asarray(pts_mm, float).reshape(-1, 2)
        P = np.c_[pts_mm[:, 0], -pts_mm[:, 1], np.full(len(pts_mm), self.sinal * espessura)]
        img, _ = cv2.projectPoints(P.reshape(-1, 1, 3), self.rvec, self.tvec, self.K, self.dist)
        return img.reshape(-1, 2)

    def mascara_roi(self, shape, espessura: float):
        cx, cy = self.cal["centro_prato_mm"]
        r = self.cal.get("raio_roi_mm", 80.0)
        t = np.linspace(0, 2 * np.pi, 180, endpoint=False)
        pts = np.c_[cx + r * np.cos(t), -(cy + r * np.sin(t))]     # centro do tabuleiro (y do CAD = -y)
        px = self.mm_para_pixels(pts, espessura)
        m = np.zeros(shape[:2], np.uint8)
        cv2.fillPoly(m, [np.round(px).astype(np.int32)], 255)
        return m

    # ---------------------------------------------------------------- medição
    def medir(self, img, espessura: float, arredondar_furos: bool = True, min_furo_mm: float = 1.0) -> dict:
        cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        cinza_s = cv2.GaussianBlur(cinza, (0, 0), 1.0)
        roi = self.mascara_roi(cinza.shape, espessura)
        valores = cinza_s[roi > 0].reshape(-1, 1)
        limiar, _ = cv2.threshold(valores, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binaria = ((cinza_s > limiar) & (roi > 0)).astype(np.uint8) * 255
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        contornos, hier = cv2.findContours(binaria, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        if not contornos:
            raise RuntimeError("Nenhuma peça encontrada: confira a iluminação e se a peça está no prato.")
        hier = hier[0]
        externos = [i for i in range(len(contornos)) if hier[i][3] == -1]
        i_peca = max(externos, key=lambda i: cv2.contourArea(contornos[i]))
        if cv2.contourArea(contornos[i_peca]) < 2000:
            raise RuntimeError("A região clara encontrada é pequena demais para ser a peça.")
        filhos = [i for i in range(len(contornos)) if hier[i][3] == i_peca]

        externo_px = _refinar_subpixel(cinza_s, contornos[i_peca].reshape(-1, 2).astype(float), float(limiar))
        externo_mm = self.pixels_para_mm(externo_px, espessura)
        entidades, info = segmentar_contorno(externo_mm)

        furos = []
        for i in filhos:
            pts_px = contornos[i].reshape(-1, 2).astype(float)
            if len(pts_px) < 12:
                continue
            pts_px = _refinar_subpixel(cinza_s, pts_px, float(limiar))
            pts_mm = self.pixels_para_mm(pts_px, espessura)
            cx, cy, r, rms = ajustar_circulo(pts_mm)
            if 2 * r < min_furo_mm:
                continue
            # circularidade: razão entre os eixos da elipse ajustada
            (ex, ey), (a, b), _ = cv2.fitEllipse(pts_mm.astype(np.float32))
            redondo = min(a, b) / max(a, b) > 0.93 and rms < 0.15
            d = 2 * r
            interp = interpretar_furo(d)
            d_cad = interp["nominal"] if (arredondar_furos and interp["tipo"] != "livre") else round(d, 2)
            furos.append({
                "centro": (round(cx, 3), round(cy, 3)), "diametro_medido": round(d, 3), "rms_mm": round(rms, 3),
                "redondo": bool(redondo), "diametro_cad": d_cad, "raio_cad": d_cad / 2,
                "interpretacao": interp, "contorno_mm": None if redondo else pts_mm[::3].round(3).tolist(),
            })
        furos.sort(key=lambda f: (-f["centro"][1], f["centro"][0]))

        largura, altura = _dimensoes(externo_mm)
        return {
            "espessura_mm": espessura, "limiar": float(limiar),
            "contorno": entidades, "contorno_info": info, "contorno_pontos_mm": externo_mm,
            "furos": furos, "dimensoes_mm": {"largura": round(largura, 2), "altura": round(altura, 2)},
            "area_mm2": round(abs(area_poligono(externo_mm)) - sum(math.pi * f["diametro_medido"] ** 2 / 4 for f in furos), 1),
        }

    # ---------------------------------------------------------------- imagem de conferência
    def sobreposicao(self, img, res: dict):
        out = img.copy()
        e = res["espessura_mm"]
        pts = amostrar_entidades(res["contorno"], 0.3)
        px = self.mm_para_pixels(pts, e)
        cv2.polylines(out, [np.round(px).astype(np.int32)], False, (60, 220, 60), 5, cv2.LINE_AA)
        esc = img.shape[1] / 3280
        for k, f in enumerate(res["furos"], 1):
            cx, cy = f["centro"]
            t = np.linspace(0, 2 * np.pi, 90)
            circ = self.mm_para_pixels(np.c_[cx + f["raio_cad"] * np.cos(t), cy + f["raio_cad"] * np.sin(t)], e)
            cv2.polylines(out, [np.round(circ).astype(np.int32)], True, (40, 40, 240), 4, cv2.LINE_AA)
            c = self.mm_para_pixels([[cx, cy]], e)[0]
            rot = f"{k}: D{f['diametro_medido']:.2f}"
            org = (int(c[0] + 40 * esc), int(c[1] - 30 * esc))
            cv2.putText(out, rot, org, cv2.FONT_HERSHEY_SIMPLEX, 1.4 * esc, (0, 0, 0), int(8 * esc), cv2.LINE_AA)
            cv2.putText(out, rot, org, cv2.FONT_HERSHEY_SIMPLEX, 1.4 * esc, (255, 255, 255), int(3 * esc), cv2.LINE_AA)
        info = f"ScanParts  {res['dimensoes_mm']['largura']:.1f} x {res['dimensoes_mm']['altura']:.1f} mm  esp. {e:.1f} mm  {len(res['furos'])} furos"
        cv2.putText(out, info, (int(40 * esc), int(90 * esc)), cv2.FONT_HERSHEY_SIMPLEX, 2.0 * esc, (0, 0, 0), int(10 * esc), cv2.LINE_AA)
        cv2.putText(out, info, (int(40 * esc), int(90 * esc)), cv2.FONT_HERSHEY_SIMPLEX, 2.0 * esc, (255, 255, 255), int(4 * esc), cv2.LINE_AA)
        return out


def _dimensoes(pts_mm: np.ndarray):
    """Largura × altura no retângulo mínimo (orientação própria da peça)."""
    (_, _), (w, h), _ = cv2.minAreaRect(pts_mm.astype(np.float32))
    return max(w, h), min(w, h)


def _refinar_subpixel(cinza: np.ndarray, pts: np.ndarray, limiar: float, alcance: float = 3.0, passo: float = 0.25):
    """Move cada ponto da borda (centro de pixel) para onde a intensidade cruza o limiar, ao longo da normal."""
    n = len(pts)
    k = 3
    tang = np.roll(pts, -k, 0) - np.roll(pts, k, 0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    normal = np.c_[-tang[:, 1], tang[:, 0]]
    s = np.arange(-alcance, alcance + passo / 2, passo)
    mx = (pts[:, 0:1] + s[None, :] * normal[:, 0:1]).astype(np.float32)
    my = (pts[:, 1:2] + s[None, :] * normal[:, 1:2]).astype(np.float32)
    perfil = cv2.remap(cinza.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) - limiar
    out = pts.copy()
    centro = len(s) // 2
    m = int(round(1.5 / passo))          # ~1,5 px de cada lado da borda
    for i in range(n):
        p = perfil[i]
        sinal = np.sign(p)
        idx = np.nonzero(sinal[:-1] * sinal[1:] <= 0)[0]
        if len(idx) == 0:
            continue
        j = idx[np.argmin(np.abs(idx + 0.5 - centro))]
        # nível local: meio-termo entre o lado claro e o lado escuro logo ao lado desta borda
        lado_a = p[max(0, j - m - 2): max(1, j - m + 1)]
        lado_b = p[min(len(p) - 1, j + m): min(len(p), j + m + 3)]
        if len(lado_a) and len(lado_b):
            nivel = 0.5 * (float(np.mean(lado_a)) + float(np.mean(lado_b)))
            q = p - nivel
            sq = np.sign(q)
            idq = np.nonzero(sq[:-1] * sq[1:] <= 0)[0]
            if len(idq):
                jj = idq[np.argmin(np.abs(idq - j))]
                if abs(jj - j) <= m:
                    j, p = jj, q
        a, b = p[j], p[j + 1]
        f = a / (a - b) if a != b else 0.5
        out[i] = pts[i] + (s[j] + f * passo) * normal[i]
    return out


def alinhar(res: dict) -> dict:
    """Cópia do resultado no referencial do CAD: maior aresta reta na horizontal, canto inferior esquerdo na origem."""
    ang = angulo_alinhamento(res["contorno"], res["contorno_pontos_mm"])
    circ = [e for e in res["contorno"] if e.tipo == "circulo"]
    if circ and res["furos"]:
        # peça redonda: gira até o furo fora do centro mais próximo de um eixo cair em cima dele (ex.: furos de flange a 0/90/180/270°)
        cx, cy = circ[0].centro
        fora = [f for f in res["furos"] if math.hypot(f["centro"][0] - cx, f["centro"][1] - cy) > 1.0]
        if fora:
            angs = [math.atan2(f["centro"][1] - cy, f["centro"][0] - cx) for f in fora]
            giros = [(-a + math.pi / 4) % (math.pi / 2) - math.pi / 4 for a in angs]
            ang = min(giros, key=abs)
    c, s_ = math.cos(ang), math.sin(ang)
    R = np.array([[c, -s_], [s_, c]])
    pts = res["contorno_pontos_mm"] @ R.T
    t = -pts.min(axis=0)
    novo = dict(res)
    novo["contorno"] = transformar_entidades(res["contorno"], ang, t)
    novo["contorno_pontos_mm"] = pts + t
    furos = []
    for f in res["furos"]:
        g = dict(f)
        g["centro"] = tuple(np.round(R @ np.array(f["centro"]) + t, 3))
        if f.get("contorno_mm"):
            g["contorno_mm"] = (np.array(f["contorno_mm"]) @ R.T + t).round(3).tolist()
        furos.append(g)
    novo["furos"] = sorted(furos, key=lambda f: (round(-f["centro"][1], 1), f["centro"][0]))
    novo["alinhamento"] = {"giro_graus": round(math.degrees(ang), 3), "translacao_mm": t.round(3).tolist()}
    return novo
