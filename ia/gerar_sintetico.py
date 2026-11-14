"""Gera imagens sintéticas de peças com furos, já rotuladas no formato YOLO.

Cada imagem simula uma peça na mesa giratória vista pela câmera inclinada,
com luz frontal (ring light): furos com parede visível, reflexos, sujeira,
marcadores no prato, ruído e desfoque. Os rótulos saem automaticamente
porque sabemos onde cada furo foi desenhado.

Uso:
    python gerar_sintetico.py --saida dados/sintetico --treino 3000 --val 500
    python gerar_sintetico.py --saida dados/sintetico --treino 20 --val 5 --previa 8
"""
import argparse
import math
import os
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

TAM = 640          # tamanho da imagem final (px)
CANVAS = 1000      # tela de desenho "vista de cima" antes da perspectiva
NOME_CLASSE = "furo"


# ---------------------------------------------------------------- utilidades
def clip8(img):
    return np.clip(img, 0, 255).astype(np.uint8)


def ruido_textura(rng, h, w, escala, intensidade):
    """Ruído suave (manchas) para dar textura a superfícies."""
    pequeno = rng.normal(0, 1, (max(2, h // escala), max(2, w // escala))).astype(np.float32)
    grande = cv2.resize(pequeno, (w, h), interpolation=cv2.INTER_CUBIC)
    return grande * intensidade


def escovado(rng, h, w, intensidade):
    """Textura de metal escovado (riscos finos numa direção)."""
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    k = int(rng.integers(15, 61))
    kernel = np.zeros((k, k), np.float32)
    kernel[k // 2, :] = 1.0 / k
    ang = rng.uniform(0, 180)
    rot = cv2.getRotationMatrix2D((k / 2, k / 2), ang, 1.0)
    kernel = cv2.warpAffine(kernel, rot, (k, k))
    kernel /= max(kernel.sum(), 1e-6)
    return cv2.filter2D(n, -1, kernel) * intensidade * 3


def gradiente(rng, h, w, intensidade):
    ang = rng.uniform(0, 2 * math.pi)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = (xx * math.cos(ang) + yy * math.sin(ang)) / max(h, w)
    return (g - g.mean()) * intensidade


def pontos_circulo(cx, cy, r, n=48):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1).astype(np.float32)


# ---------------------------------------------------------------- peça
def poligono_peca(rng):
    """Contorno da peça na vista de cima (coordenadas do canvas)."""
    c = CANVAS / 2
    w = rng.uniform(300, 720)
    h = rng.uniform(260, 720)
    tipo = rng.choice(["retangulo", "chanfrado", "L", "disco", "flange"])
    if tipo in ("disco", "flange"):
        r = min(w, h) / 2
        pts = pontos_circulo(c, c, r, 96)
    elif tipo == "L":
        a, b = rng.uniform(0.35, 0.65), rng.uniform(0.35, 0.65)
        x0, y0, x1, y1 = c - w / 2, c - h / 2, c + w / 2, c + h / 2
        xm, ym = x0 + w * a, y0 + h * b
        pts = np.array([[x0, y0], [xm, y0], [xm, ym], [x1, ym], [x1, y1], [x0, y1]], np.float32)
    else:
        x0, y0, x1, y1 = c - w / 2, c - h / 2, c + w / 2, c + h / 2
        if tipo == "chanfrado":
            k = rng.uniform(20, min(w, h) / 4)
            pts = np.array([[x0 + k, y0], [x1 - k, y0], [x1, y0 + k], [x1, y1 - k],
                            [x1 - k, y1], [x0 + k, y1], [x0, y1 - k], [x0, y0 + k]], np.float32)
        else:
            pts = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32)
    rot = cv2.getRotationMatrix2D((c, c), rng.uniform(0, 360), 1.0)
    pts = cv2.transform(pts[None], rot)[0]
    return pts, tipo


def sortear_furos(rng, mascara_peca, tipo):
    """Escolhe centros e raios de furos dentro da peça, sem sobrepor."""
    furos = []
    dist = cv2.distanceTransform(mascara_peca, cv2.DIST_L2, 5)
    alvo = int(rng.integers(0, 9))
    if tipo == "flange" and alvo < 3:
        alvo = int(rng.integers(3, 9))
    ys, xs = np.nonzero(dist > 20)
    if len(xs) == 0:
        return furos
    for _ in range(alvo * 30):
        if len(furos) >= alvo:
            break
        i = int(rng.integers(len(xs)))
        cx, cy = float(xs[i]), float(ys[i])
        r_max = min(dist[ys[i], xs[i]] - 12, 70)
        if r_max < 6:
            continue
        r = float(rng.uniform(6, r_max))
        if all(math.hypot(cx - fx, cy - fy) > r + fr + 10 for fx, fy, fr, _ in furos):
            furos.append((cx, cy, r, rng.random() < 0.6))  # True = passante
    return furos


def desenhar_furo(rng, img, cx, cy, r, passante, cor_peca, cor_fundo, dir_parede):
    """Furo visto com luz frontal: parede iluminada de um lado, fundo escuro."""
    h, w = img.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    cv2.circle(mask, (int(cx), int(cy)), int(r), 255, -1, cv2.LINE_AA)
    # parede (gradiente do claro para o escuro)
    cor_parede = cor_peca * rng.uniform(0.35, 0.75)
    camada = np.empty_like(img)
    camada[:] = cor_parede
    camada += gradiente(rng, h, w, 60)[..., None]
    # abertura do fundo, deslocada (efeito da inclinação da câmera)
    prof = r * rng.uniform(0.2, 0.9)
    ox, oy = dir_parede[0] * prof, dir_parede[1] * prof
    fundo = np.zeros((h, w), np.uint8)
    cv2.circle(fundo, (int(cx + ox), int(cy + oy)), int(r * rng.uniform(0.85, 1.0)), 255, -1, cv2.LINE_AA)
    fundo = cv2.bitwise_and(fundo, mask)
    if passante:
        cor_buraco = cor_fundo * rng.uniform(0.15, 0.6)
    else:
        cor_buraco = cor_peca * rng.uniform(0.05, 0.3)
    m = (mask.astype(np.float32) / 255)[..., None]
    f = (cv2.GaussianBlur(fundo, (0, 0), max(0.6, r * 0.04)).astype(np.float32) / 255)[..., None]
    img[:] = img * (1 - m) + camada * m
    img[:] = img * (1 - f) + (np.ones_like(img) * cor_buraco) * f
    # chanfro / escareado (anel mais claro em volta)
    if rng.random() < 0.3:
        espessura = max(2, int(r * rng.uniform(0.1, 0.35)))
        cv2.circle(img, (int(cx), int(cy)), int(r + espessura / 2), tuple(float(v) for v in cor_peca * 1.25),
                   espessura, cv2.LINE_AA)
    # brilho na borda (reflexo do ring light no canto do furo)
    if rng.random() < 0.6:
        a0 = math.degrees(math.atan2(-dir_parede[1], -dir_parede[0])) + rng.uniform(-40, 40)
        cv2.ellipse(img, (int(cx), int(cy)), (int(r), int(r)), 0, a0 - 50, a0 + 50,
                    (235, 235, 235), max(1, int(r * 0.06)), cv2.LINE_AA)


def distratores(rng, img, mascara_peca):
    """Coisas que NÃO são furos: sujeira, riscos, reflexo do anel, marcas."""
    h, w = img.shape[:2]
    ys, xs = np.nonzero(mascara_peca)
    if len(xs) == 0:
        return
    # sujeira / manchas escuras irregulares
    for _ in range(int(rng.integers(0, 6))):
        i = int(rng.integers(len(xs)))
        blob = np.zeros((h, w), np.uint8)
        for _ in range(int(rng.integers(2, 6))):
            cv2.circle(blob, (int(xs[i] + rng.normal(0, 8)), int(ys[i] + rng.normal(0, 8))),
                       int(rng.uniform(2, 14)), 255, -1)
        b = (cv2.GaussianBlur(blob, (0, 0), rng.uniform(1, 4)).astype(np.float32) / 255)[..., None]
        img[:] = img * (1 - b * rng.uniform(0.3, 0.8))
    # riscos
    for _ in range(int(rng.integers(0, 5))):
        i = int(rng.integers(len(xs)))
        ang = rng.uniform(0, 2 * math.pi)
        L = rng.uniform(20, 200)
        p1 = (int(xs[i]), int(ys[i]))
        p2 = (int(xs[i] + L * math.cos(ang)), int(ys[i] + L * math.sin(ang)))
        v = float(rng.choice([40, 220]))
        cv2.line(img, p1, p2, (v, v, v), 1, cv2.LINE_AA)
    # reflexo do ring light (anel claro) — o distrator mais importante
    if rng.random() < 0.5:
        i = int(rng.integers(len(xs)))
        ring = np.zeros((h, w), np.uint8)
        R = int(rng.uniform(40, 220))
        cv2.ellipse(ring, (int(xs[i]), int(ys[i])), (R, int(R * rng.uniform(0.5, 1.0))),
                    rng.uniform(0, 180), 0, 360, 255, int(rng.uniform(6, 25)), cv2.LINE_AA)
        ring = cv2.bitwise_and(ring, mascara_peca)
        rr = (cv2.GaussianBlur(ring, (0, 0), rng.uniform(3, 10)).astype(np.float32) / 255)[..., None]
        img[:] = img * (1 - rr) + 250 * rr
    # marcações escuras redondas mas rasas (ex.: ponto de centro, adesivo)
    for _ in range(int(rng.integers(0, 3))):
        i = int(rng.integers(len(xs)))
        cv2.circle(img, (int(xs[i]), int(ys[i])), int(rng.uniform(2, 6)), (60, 60, 60), -1, cv2.LINE_AA)


def marcadores_prato(rng, img):
    """Quadrados preto e branco na borda, como os ArUco do prato giratório."""
    for _ in range(int(rng.integers(0, 9))):
        lado = int(rng.uniform(30, 70))
        ang = rng.uniform(0, 2 * math.pi)
        raio = CANVAS * rng.uniform(0.42, 0.5)
        cx = int(CANVAS / 2 + raio * math.cos(ang))
        cy = int(CANVAS / 2 + raio * math.sin(ang))
        cv2.rectangle(img, (cx - lado // 2, cy - lado // 2), (cx + lado // 2, cy + lado // 2), (15, 15, 15), -1)
        n = 4
        cel = lado / (n + 2)
        for a in range(n):
            for b in range(n):
                if rng.random() < 0.5:
                    x = int(cx - lado / 2 + cel * (a + 1))
                    y = int(cy - lado / 2 + cel * (b + 1))
                    cv2.rectangle(img, (x, y), (int(x + cel), int(y + cel)), (240, 240, 240), -1)


# ---------------------------------------------------------------- perspectiva
def homografia(rng):
    """Simula a câmera inclinada (0–50°) olhando o prato, com giro e zoom."""
    c = CANVAS
    inclin = rng.uniform(0.0, 0.45)            # quanto a borda de cima "encolhe"
    zoom = rng.uniform(0.55, 1.05)
    src = np.float32([[0, 0], [c, 0], [c, c], [0, c]])
    meia = TAM * zoom / 2
    topo = meia * (1 - inclin)
    alt = meia * (1 - inclin * 0.6)
    cx = TAM / 2 + rng.normal(0, TAM * 0.06)
    cy = TAM / 2 + rng.normal(0, TAM * 0.06)
    dst = np.float32([[cx - topo, cy - alt], [cx + topo, cy - alt], [cx + meia, cy + alt], [cx - meia, cy + alt]])
    dst += rng.normal(0, TAM * 0.015, dst.shape).astype(np.float32)
    rot = np.vstack([cv2.getRotationMatrix2D((c / 2, c / 2), rng.uniform(0, 360), 1.0), [0, 0, 1]])
    H = cv2.getPerspectiveTransform(src, dst) @ rot
    return H, inclin


def pos_processar(rng, img):
    img = img.astype(np.float32)
    img = img * rng.uniform(0.7, 1.3) + rng.uniform(-30, 30)                       # brilho/contraste
    img *= np.array([rng.uniform(0.92, 1.08) for _ in range(3)], np.float32)       # temperatura de cor
    if rng.random() < 0.5:                                                          # vinheta (lente 120°)
        yy, xx = np.mgrid[0:TAM, 0:TAM].astype(np.float32)
        d = np.hypot(xx - TAM / 2, yy - TAM / 2) / (TAM / 2)
        img *= (1 - rng.uniform(0.1, 0.45) * d ** 2)[..., None]
    img += rng.normal(0, rng.uniform(1, 9), img.shape)                              # ruído do sensor
    img = clip8(img)
    if rng.random() < 0.4:
        img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.5, 1.8))                  # desfoque
    if rng.random() < 0.2:
        k = int(rng.integers(3, 9))
        kern = np.zeros((k, k), np.float32)
        kern[k // 2, :] = 1 / k
        img = cv2.filter2D(img, -1, kern)                                           # tremido
    q = int(rng.integers(55, 96))
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


# ---------------------------------------------------------------- amostra
def gerar_amostra(rng):
    # fundo / prato giratório
    cor_fundo = np.array([rng.uniform(15, 235)] * 3, np.float32) * np.array(
        [rng.uniform(0.85, 1.15) for _ in range(3)], np.float32)
    img = np.empty((CANVAS, CANVAS, 3), np.float32)
    img[:] = cor_fundo
    img += ruido_textura(rng, CANVAS, CANVAS, 40, rng.uniform(2, 12))[..., None]
    marcadores_prato(rng, img)

    # peça
    pts, tipo = poligono_peca(rng)
    mask = np.zeros((CANVAS, CANVAS), np.uint8)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255, cv2.LINE_AA)
    metal = rng.random() < 0.75
    base = rng.uniform(80, 215) if metal else rng.uniform(20, 230)
    cor_peca = np.array([base] * 3, np.float32)
    if not metal:
        cor_peca *= np.array([rng.uniform(0.5, 1.3) for _ in range(3)], np.float32)
    cor_peca = np.clip(cor_peca, 10, 245)

    # sombra e espessura (lateral da peça)
    dir_luz = rng.normal(0, 1, 2)
    dir_luz /= np.linalg.norm(dir_luz) + 1e-6
    esp = rng.uniform(4, 40)
    if rng.random() < 0.6:
        sombra = np.zeros_like(mask)
        cv2.fillPoly(sombra, [(pts + dir_luz * esp * 1.5).astype(np.int32)], 255)
        s = (cv2.GaussianBlur(sombra, (0, 0), esp * 0.8).astype(np.float32) / 255)[..., None]
        img = img * (1 - 0.5 * s)
    lateral = np.zeros_like(mask)
    cv2.fillPoly(lateral, [(pts + dir_luz * esp).astype(np.int32)], 255, cv2.LINE_AA)
    lat = (lateral.astype(np.float32) / 255)[..., None]
    img = img * (1 - lat) + (cor_peca * rng.uniform(0.4, 0.8)) * lat

    superficie = np.empty_like(img)
    superficie[:] = cor_peca
    superficie += gradiente(rng, CANVAS, CANVAS, rng.uniform(10, 70))[..., None]
    if metal and rng.random() < 0.7:
        superficie += escovado(rng, CANVAS, CANVAS, rng.uniform(4, 14))[..., None]
    superficie += ruido_textura(rng, CANVAS, CANVAS, 25, rng.uniform(1, 8))[..., None]
    m = (mask.astype(np.float32) / 255)[..., None]
    img = img * (1 - m) + superficie * m

    # furos
    furos = sortear_furos(rng, mask, tipo)
    for cx, cy, r, passante in furos:
        desenhar_furo(rng, img, cx, cy, r, passante, cor_peca, cor_fundo, dir_luz)
    distratores(rng, img, mask)

    # perspectiva da câmera
    H, _ = homografia(rng)
    saida = cv2.warpPerspective(clip8(img), H, (TAM, TAM), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # fora do canvas: continua o mesmo fundo (sem bordas nem cópias da peça)
    cobre = cv2.warpPerspective(np.full((CANVAS, CANVAS), 255, np.uint8), H, (TAM, TAM),
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    cobre = cv2.erode(cobre, np.ones((3, 3), np.uint8), iterations=2)
    cobre = (cv2.GaussianBlur(cobre, (0, 0), 1.5).astype(np.float32) / 255)[..., None]
    fora = np.empty((TAM, TAM, 3), np.float32)
    fora[:] = cor_fundo
    fora += ruido_textura(rng, TAM, TAM, 30, rng.uniform(2, 12))[..., None]
    saida = clip8(saida.astype(np.float32) * cobre + fora * (1 - cobre))
    saida = pos_processar(rng, saida)

    # rótulos
    rotulos = []
    for cx, cy, r, _ in furos:
        poly = cv2.perspectiveTransform(pontos_circulo(cx, cy, r)[None], H)[0]
        x0, y0 = poly.min(0)
        x1, y1 = poly.max(0)
        vis = np.clip(poly, 0, TAM - 1)
        area_total = (x1 - x0) * (y1 - y0)
        vx0, vy0 = vis.min(0)
        vx1, vy1 = vis.max(0)
        area_vis = max(0, vx1 - vx0) * max(0, vy1 - vy0)
        if area_total <= 0 or area_vis / area_total < 0.6 or min(vx1 - vx0, vy1 - vy0) < 4:
            continue
        rotulos.append(vis)
    return saida, rotulos


def linha_yolo(poly, seg):
    if seg:
        coords = " ".join(f"{v / TAM:.6f}" for p in poly for v in p)
        return f"0 {coords}"
    x0, y0 = poly.min(0)
    x1, y1 = poly.max(0)
    return f"0 {(x0 + x1) / 2 / TAM:.6f} {(y0 + y1) / 2 / TAM:.6f} {(x1 - x0) / TAM:.6f} {(y1 - y0) / TAM:.6f}"


def gerar_lote(args):
    """Gera um lote de imagens (roda em paralelo, cada lote com sua semente)."""
    raiz, split, inicio, n, semente, seg, previa = args
    rng = np.random.default_rng(semente)
    for k in range(inicio, inicio + n):
        img, rot = gerar_amostra(rng)
        nome = f"sint_{split}_{k:05d}"
        cv2.imwrite(str(raiz / "images" / split / f"{nome}.jpg"), img)
        (raiz / "labels" / split / f"{nome}.txt").write_text("\n".join(linha_yolo(p, seg) for p in rot))
        if k - inicio < previa:
            prev = img.copy()
            for p in rot:
                x0, y0 = p.min(0).astype(int)
                x1, y1 = p.max(0).astype(int)
                cv2.rectangle(prev, (x0, y0), (x1, y1), (0, 255, 0), 1)
            cv2.imwrite(str(raiz / "previa" / f"{nome}.jpg"), prev)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", default="dados/sintetico", help="pasta do dataset")
    ap.add_argument("--treino", type=int, default=3000, help="nº de imagens de treino")
    ap.add_argument("--val", type=int, default=500, help="nº de imagens de validação")
    ap.add_argument("--seg", action="store_true", help="rótulos de segmentação (polígono) em vez de caixa")
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--previa", type=int, default=0, help="salva N imagens com os rótulos desenhados")
    ap.add_argument("--processos", type=int, default=os.cpu_count() or 1)
    a = ap.parse_args()

    raiz = Path(a.saida)
    (raiz / "previa").mkdir(parents=True, exist_ok=True)
    tarefas = []
    lote = 50
    for s_i, (split, n) in enumerate((("train", a.treino), ("val", a.val))):
        (raiz / "images" / split).mkdir(parents=True, exist_ok=True)
        (raiz / "labels" / split).mkdir(parents=True, exist_ok=True)
        for inicio in range(0, n, lote):
            semente = a.semente * 1_000_003 + s_i * 100_003 + inicio
            previa = a.previa if (split == "train" and inicio == 0) else 0
            tarefas.append((raiz, split, inicio, min(lote, n - inicio), semente, a.seg, previa))

    total = 0
    with Pool(max(1, a.processos)) as pool:
        for feitos in pool.imap_unordered(gerar_lote, tarefas):
            total += feitos
            print(f"{total}/{a.treino + a.val} imagens", end="\r", flush=True)

    (raiz / "data.yaml").write_text(
        f"path: {raiz.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: {NOME_CLASSE}\n")
    print(f"\nPronto: {total} imagens em {raiz.resolve()}")


if __name__ == "__main__":
    main()
