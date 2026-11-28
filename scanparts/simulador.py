"""Simulador físico da bancada ScanParts (para testar o software sem o hardware).

Modela a câmera IMX219 (3280×2464, lente ~120° com distorção), montada a ~130 mm acima do
prato preto, olhando para baixo, com pequeno desalinhamento. A peça é uma chapa com espessura
real: a imagem mostra o topo da peça, a parede dos furos (paralaxe) e o prato através dos furos.
Também gera fotos do tabuleiro de calibração em várias inclinações.

Convenção do mundo: plano do prato z = 0, eixo z para cima (em direção à câmera), unidades em mm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np


# ---------------------------------------------------------------- câmera
@dataclass
class Camera:
    K: np.ndarray
    dist: np.ndarray
    R_cw: np.ndarray       # câmera -> mundo
    C_w: np.ndarray        # centro óptico no mundo (mm)
    W: int = 3280
    H: int = 2464
    _raios: tuple = field(default=None, repr=False)

    @staticmethod
    def imx219(altura=130.0, fx=1767.0, inclinacao_graus=(0.8, -0.6, 1.5), deslocamento=(3.0, -2.0),
               W=3280, H=2464, dist=(-0.20, 0.03, 0.0004, -0.0003, 0.0)):
        """fx=1767 px + distorção em barril: ~120° na diagonal e ~100° na horizontal (lente grande-angular)."""
        K = np.array([[fx, 0, W / 2 + 6.5], [0, fx, H / 2 - 4.0], [0, 0, 1]], float)
        base = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)   # colunas: eixos da câmera no mundo
        rx, ry, rz = (math.radians(a) for a in inclinacao_graus)
        Rs, _ = cv2.Rodrigues(np.array([rx, ry, rz]))
        return Camera(K, np.array(dist, float), base @ Rs, np.array([deslocamento[0], deslocamento[1], altura]), W, H)

    def raios(self):
        """Direções (mundo) de cada pixel, já sem distorção. Cache."""
        if self._raios is None:
            u, v = np.meshgrid(np.arange(self.W, dtype=np.float32), np.arange(self.H, dtype=np.float32))
            from .camera_util import desdistorcer
            # calcula numa grade de 4 px e interpola (a função é suave): rápido e preciso
            passo = 4
            gu, gv = np.meshgrid(np.arange(0, self.W + passo, passo, dtype=np.float64),
                                 np.arange(0, self.H + passo, passo, dtype=np.float64))
            und = desdistorcer(np.c_[gu.ravel(), gv.ravel()], self.K, self.dist)
            ux = und[:, 0].reshape(gu.shape).astype(np.float32)
            uy = und[:, 1].reshape(gu.shape).astype(np.float32)
            mx = (u / passo).astype(np.float32)
            my = (v / passo).astype(np.float32)
            ux = cv2.remap(ux, mx, my, cv2.INTER_LINEAR).ravel()
            uy = cv2.remap(uy, mx, my, cv2.INTER_LINEAR).ravel()
            d_c = np.c_[ux, uy, np.ones(len(ux), np.float32)].astype(np.float32)
            d_w = d_c @ self.R_cw.T.astype(np.float32)
            self._raios = tuple(d_w[:, i].reshape(self.H, self.W) for i in range(3))
        return self._raios

    def intersecao_plano_z(self, z):
        dx, dy, dz = self.raios()
        s = (z - self.C_w[2]) / dz
        return (self.C_w[0] + s * dx).astype(np.float32), (self.C_w[1] + s * dy).astype(np.float32)

    def projetar(self, pts_w):
        R_wc = self.R_cw.T
        t = -R_wc @ self.C_w
        rvec, _ = cv2.Rodrigues(R_wc)
        img, _ = cv2.projectPoints(np.asarray(pts_w, float).reshape(-1, 1, 3), rvec, t, self.K, self.dist)
        return img.reshape(-1, 2)


# ---------------------------------------------------------------- peças
def contorno_com_raios(vertices, raios, passo=0.05):
    """Polígono (anti-horário) com cantos arredondados (raio 0 = canto vivo). Retorna pontos densos."""
    V = np.asarray(vertices, float)
    n = len(V)
    pts = []
    for i in range(n):
        a, b, c = V[i - 1], V[i], V[(i + 1) % n]
        r = raios[i]
        u1 = (b - a) / np.linalg.norm(b - a)
        u2 = (c - b) / np.linalg.norm(c - b)
        if r <= 0:
            pts.append(b)
            continue
        alfa = math.acos(np.clip(np.dot(-u1, u2), -1, 1))
        t = r / math.tan(alfa / 2)
        T1, T2 = b - u1 * t, b + u2 * t
        bis = (-u1 + u2) / np.linalg.norm(-u1 + u2)
        C = b + bis * r / math.sin(alfa / 2)
        a0 = math.atan2(T1[1] - C[1], T1[0] - C[0])
        a1 = math.atan2(T2[1] - C[1], T2[0] - C[0])
        cruz = u1[0] * u2[1] - u1[1] * u2[0]
        if cruz > 0:      # curva à esquerda (convexo, anti-horário)
            while a1 < a0:
                a1 += 2 * math.pi
        else:
            while a1 > a0:
                a1 -= 2 * math.pi
        m = max(4, int(abs(a1 - a0) * r / passo))
        for ang in np.linspace(a0, a1, m):
            pts.append(C + r * np.array([math.cos(ang), math.sin(ang)]))
    P = np.array(pts)
    from .geometria import reamostrar_fechado
    return reamostrar_fechado(P, passo)


@dataclass
class Peca:
    nome: str
    contorno: np.ndarray            # pontos densos (mm), referencial da peça
    furos: list                     # [(x, y, diâmetro), ...]
    descricao: str = ""


def suporte_retangular():
    v = [(-40, -25), (40, -25), (40, 25), (-40, 25)]
    furos = [(32, 17, 6.6), (-32, 17, 6.6), (-32, -17, 6.6), (32, -17, 6.6), (0, 0, 9.0), (15, 10, 3.4), (-15, 10, 3.4)]
    return Peca("suporte_retangular", contorno_com_raios(v, [5, 5, 5, 5]), furos, "Chapa 80×50 mm, cantos R5, 7 furos")


def suporte_L():
    v = [(0, 0), (70, 0), (70, 22), (22, 22), (22, 55), (0, 55)]
    furos = [(11, 11, 5.5), (58, 11, 5.5), (35, 11, 4.5), (11, 44, 11.0)]
    P = contorno_com_raios(v, [3, 3, 3, 0, 3, 3])
    return Peca("suporte_L", P - np.array([35, 27.5]), [(x - 35, y - 27.5, d) for x, y, d in furos],
                "Suporte em L 70×55 mm, canto interno vivo, 4 furos")


def flange():
    t = np.linspace(0, 2 * np.pi, 4000, endpoint=False)
    P = np.c_[30 * np.cos(t), 30 * np.sin(t)]
    furos = [(22.5 * math.cos(a), 22.5 * math.sin(a), 6.6) for a in np.radians([45, 135, 225, 315])] + [(0, 0, 13.5)]
    return Peca("flange", P, furos, "Flange Ø60 mm, 4 furos Ø6,6 em Ø45 + furo central Ø13,5")


PECAS = {"suporte_retangular": suporte_retangular, "suporte_L": suporte_L, "flange": flange}


# ---------------------------------------------------------------- cena
def _transformar(P, ang, tx, ty):
    c, s = math.cos(ang), math.sin(ang)
    return P @ np.array([[c, s], [-s, c]]) + np.array([tx, ty])


def _rasterizar(polys_fill, polys_hole, x0, y0, res, W, H):
    m = np.zeros((H, W), np.uint8)
    def conv(P):
        return np.round(np.c_[(P[:, 0] - x0) / res, (P[:, 1] - y0) / res] * 16).astype(np.int32)
    for P in polys_fill:
        cv2.fillPoly(m, [conv(P)], 255, cv2.LINE_AA, shift=4)
    for P in polys_hole:
        cv2.fillPoly(m, [conv(P)], 0, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255.0


def _amostrar(img, X, Y, x0, y0, res, borda=0.0):
    mx = ((X - x0) / res).astype(np.float32)
    my = ((Y - y0) / res).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=borda)


def _imagem_prato(rng, raio_prato=90.0, res=0.1, meia=170.0):
    """Prato preto fosco Ø180 com 24 alvos brancos (a cada 15°) sobre base de MDF."""
    n = int(2 * meia / res)
    img = np.empty((n, n, 3), np.float32)
    img[:] = (95, 135, 175)                                     # MDF (BGR)
    img += rng.normal(0, 6, (n, n, 1)).astype(np.float32)
    c = n // 2
    cv2.circle(img, (c, c), int(raio_prato / res), (24, 24, 26), -1, cv2.LINE_AA)
    for k in range(24):
        a = math.radians(15 * k)
        cx, cy = 83 * math.cos(a), 83 * math.sin(a)
        rect = ((c + cx / res, c + cy / res), (4 / res, 8 / res), math.degrees(a) + 90)
        cv2.fillPoly(img, [cv2.boxPoints(rect).astype(np.int32)], (235, 235, 235), cv2.LINE_AA)
    img += rng.normal(0, 2.0, img.shape).astype(np.float32)
    return img, -meia, -meia, res


def renderizar_peca(cam: Camera, peca: Peca, espessura: float, ang: float, tx: float, ty: float,
                    seed: int = 0, brilho: float = 1.0):
    """Foto sintética da peça sobre o prato. Retorna (imagem BGR uint8, gabarito em coordenadas do mundo)."""
    rng = np.random.default_rng(seed)
    contorno_w = _transformar(peca.contorno, ang, tx, ty)
    furos_w = []
    polys_furo = []
    for x, y, d in peca.furos:
        cx, cy = _transformar(np.array([[x, y]]), ang, tx, ty)[0]
        furos_w.append((cx, cy, d))
        t = np.linspace(0, 2 * np.pi, max(64, int(math.pi * d / 0.03)), endpoint=False)
        polys_furo.append(np.c_[cx + d / 2 * np.cos(t), cy + d / 2 * np.sin(t)])
    res = 0.02
    x0, y0 = contorno_w.min(0) - 3
    x1, y1 = contorno_w.max(0) + 3
    Wm, Hm = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    solido = _rasterizar([contorno_w], polys_furo, x0, y0, res, Wm, Hm)       # chapa sem furos
    externo = _rasterizar([contorno_w], [], x0, y0, res, Wm, Hm)              # chapa cheia
    furo = np.clip(externo - solido, 0, 1)
    textura = (rng.normal(0, 1, (Hm // 8 + 1, Wm // 8 + 1)).astype(np.float32))
    textura = cv2.resize(textura, (Wm, Hm), interpolation=cv2.INTER_CUBIC)
    riscos = cv2.blur(rng.normal(0, 1, (Hm, Wm)).astype(np.float32), (61, 1))   # metal escovado
    metal = np.clip(172 * brilho + 9 * textura + 30 * riscos, 0, 255).astype(np.float32)

    Xt, Yt = cam.intersecao_plano_z(espessura)
    Xb, Yb = cam.intersecao_plano_z(0.0)
    topo = _amostrar(solido, Xt, Yt, x0, y0, res)
    sobre_furo = _amostrar(furo, Xt, Yt, x0, y0, res)
    ext_topo = _amostrar(externo, Xt, Yt, x0, y0, res)
    sol_base = _amostrar(solido, Xb, Yb, x0, y0, res)
    furo_base = _amostrar(furo, Xb, Yb, x0, y0, res)
    cor_metal = _amostrar(metal, Xt, Yt, x0, y0, res, borda=170)

    prato, px0, py0, pres = _imagem_prato(rng)
    cor_prato = np.dstack([_amostrar(prato[:, :, i], Xb, Yb, px0, py0, pres, borda=120) for i in range(3)])

    w_topo = topo
    w_atraves = sobre_furo * furo_base
    w_parede_furo = sobre_furo * (1 - furo_base)
    fora = 1 - ext_topo
    w_parede_ext = fora * sol_base
    w_prato = fora * (1 - sol_base) + w_atraves
    parede = 78.0 * brilho
    img = (w_topo[..., None] * cor_metal[..., None] * np.array([0.98, 1.0, 1.03], np.float32)
           + (w_parede_furo + w_parede_ext)[..., None] * parede
           + w_prato[..., None] * cor_prato)
    # iluminação do ring light (queda radial) + vinheta da lente
    r_mundo = np.hypot(Xb, Yb) / 100.0
    img *= (1 - 0.12 * r_mundo ** 2)[..., None]
    u = (np.arange(cam.W) - cam.W / 2) / (cam.W / 2)
    v = (np.arange(cam.H) - cam.H / 2) / (cam.W / 2)
    rr = u[None, :] ** 2 + v[:, None] ** 2
    img *= (1 - 0.30 * rr)[..., None]
    img = cv2.GaussianBlur(img, (0, 0), 0.8)
    img += rng.normal(0, 2.5, img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    gabarito = {"contorno_w": contorno_w, "furos_w": furos_w, "espessura": espessura,
                "ang": ang, "tx": tx, "ty": ty, "peca": peca.nome}
    return img, gabarito


def renderizar_tabuleiro(cam: Camera, R_bw: np.ndarray, t_bw: np.ndarray, seed: int = 0):
    """Foto sintética do tabuleiro ChArUco com pose (tabuleiro -> mundo)."""
    from .calibracao import criar_tabuleiro, imagem_tabuleiro
    rng = np.random.default_rng(seed)
    board, spec = criar_tabuleiro()
    ppmm = 12.0
    tex = imagem_tabuleiro(board, spec, ppmm).astype(np.float32)
    dx, dy, dz = cam.raios()
    Rt = R_bw.T
    C_b = Rt @ (cam.C_w - t_bw)
    db = [Rt[i, 0] * dx + Rt[i, 1] * dy + Rt[i, 2] * dz for i in range(3)]
    s = -C_b[2] / db[2]
    Xb = (C_b[0] + s * db[0]).astype(np.float32)
    Yb = (C_b[1] + s * db[1]).astype(np.float32)
    cor = cv2.remap(tex, (Xb * ppmm).astype(np.float32), (Yb * ppmm).astype(np.float32), cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=-1)
    dentro = (cor >= 0) & (s > 0)
    Xp, Yp = cam.intersecao_plano_z(0.0)
    prato, px0, py0, pres = _imagem_prato(rng)
    fundo = np.dstack([_amostrar(prato[:, :, i], Xp, Yp, px0, py0, pres, borda=120) for i in range(3)])
    papel = np.where(dentro, np.clip(cor, 0, 255) * 0.92 + 12, 0)
    img = np.where(dentro[..., None], papel[..., None], fundo)
    u = (np.arange(cam.W) - cam.W / 2) / (cam.W / 2)
    v = (np.arange(cam.H) - cam.H / 2) / (cam.W / 2)
    img *= (1 - 0.30 * (u[None, :] ** 2 + v[:, None] ** 2))[..., None]
    img = cv2.GaussianBlur(img.astype(np.float32), (0, 0), 0.8)
    img += rng.normal(0, 2.5, img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def pose_tabuleiro_plano(centro=(0.0, 0.0)):
    """Tabuleiro deitado no prato, centralizado (referência do prato)."""
    from .calibracao import criar_tabuleiro
    _, spec = criar_tabuleiro()
    R = np.diag([1.0, -1.0, -1.0])     # x do tabuleiro = X, y = -Y, z = -Z (para dentro da mesa)
    t = np.array([centro[0] - spec["largura_mm"] / 2, centro[1] + spec["altura_mm"] / 2, 0.0])
    return R, t


def poses_calibracao(n=16, seed=1):
    """Poses variadas (inclinações de até ~35°) para a calibração da lente."""
    from .calibracao import criar_tabuleiro
    _, spec = criar_tabuleiro()
    rng = np.random.default_rng(seed)
    poses = []
    w, h = spec["largura_mm"], spec["altura_mm"]
    for i in range(n):
        tilt = np.radians(rng.uniform(-35, 35, 2))
        giro = np.radians(rng.uniform(-30, 30))
        Rz, _ = cv2.Rodrigues(np.array([0, 0, giro]))
        Rx, _ = cv2.Rodrigues(np.array([tilt[0], 0, 0]))
        Ry, _ = cv2.Rodrigues(np.array([0, tilt[1], 0]))
        R = Rx @ Ry @ Rz @ np.diag([1.0, -1.0, -1.0])
        centro = np.array([rng.uniform(-60, 60), rng.uniform(-45, 45), rng.uniform(15, 45)])
        t = centro - R @ np.array([w / 2, h / 2, 0])
        poses.append((R, t))
    return poses
