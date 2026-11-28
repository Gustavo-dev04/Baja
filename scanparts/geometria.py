"""Geometria 2D: ajuste de círculo e conversão de contorno medido em retas e arcos (mm)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


# ---------------------------------------------------------------- entidades CAD
@dataclass
class Linha:
    p0: tuple
    p1: tuple
    tipo: str = "linha"


@dataclass
class Arco:
    centro: tuple
    raio: float
    p0: tuple          # início (sentido do contorno)
    p1: tuple          # fim
    meio: tuple        # um ponto no meio do arco (define o lado)
    tipo: str = "arco"


@dataclass
class Circulo:
    centro: tuple
    raio: float
    tipo: str = "circulo"


@dataclass
class Polilinha:
    pontos: list = field(default_factory=list)
    tipo: str = "polilinha"


# ---------------------------------------------------------------- círculos
def ajustar_circulo(pts: np.ndarray):
    """Ajuste de círculo por mínimos quadrados (Kasa + refinamento geométrico).
    Retorna (cx, cy, r, rms)."""
    x, y = pts[:, 0].astype(float), pts[:, 1].astype(float)
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    b = x ** 2 + y ** 2
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = c[0], c[1]
    r = math.sqrt(max(c[2] + cx ** 2 + cy ** 2, 1e-12))
    for _ in range(15):
        dx, dy = x - cx, y - cy
        ri = np.hypot(dx, dy) + 1e-12
        J = np.c_[-dx / ri, -dy / ri, -np.ones_like(ri)]
        delta, *_ = np.linalg.lstsq(J, -(ri - r), rcond=None)
        cx, cy, r = cx + delta[0], cy + delta[1], r + delta[2]
        if np.abs(delta).max() < 1e-7:
            break
    rms = float(np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2)))
    return float(cx), float(cy), float(abs(r)), rms


def area_poligono(pts: np.ndarray) -> float:
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


# ---------------------------------------------------------------- contorno
def reamostrar_fechado(pts: np.ndarray, passo: float) -> np.ndarray:
    P = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    n = max(int(s[-1] / passo), 8)
    alvo = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[np.interp(alvo, s, P[:, 0]), np.interp(alvo, s, P[:, 1])]


def _runs_circular(mask: np.ndarray):
    """Sequências contíguas (circulares) de True/False: lista de (valor, ini, comprimento)."""
    n = len(mask)
    if mask.all() or (~mask).all():
        return [(bool(mask[0]), 0, n)]
    ini = int(np.argmax(mask != mask[0]))  # começa numa troca
    runs, i = [], 0
    while i < n:
        j = i
        v = mask[(ini + i) % n]
        while j < n and mask[(ini + j) % n] == v:
            j += 1
        runs.append((bool(v), (ini + i) % n, j - i))
        i = j
    return runs


def _suavizar_fechado(P: np.ndarray, sigma_pts: float) -> np.ndarray:
    r = int(3 * sigma_pts) + 1
    t = np.arange(-r, r + 1)
    g = np.exp(-0.5 * (t / sigma_pts) ** 2)
    g /= g.sum()
    ext = np.vstack([P[-r:], P, P[:r]])
    return np.c_[np.convolve(ext[:, 0], g, "same"), np.convolve(ext[:, 1], g, "same")][r:-r]


def _limpar_mascara(m: np.ndarray, min_falso: int, min_verdadeiro: int) -> np.ndarray:
    """Remove falhas curtas: trechos 'não reto' curtos dentro de retas e retas curtas demais."""
    m = m.copy()
    n = len(m)
    for v, i, L in _runs_circular(m):
        if not v and L < min_falso:
            m[(i + np.arange(L)) % n] = True
    for v, i, L in _runs_circular(m):
        if v and L < min_verdadeiro:
            m[(i + np.arange(L)) % n] = False
    return m


def _ajustar_reta(Q: np.ndarray):
    c = Q.mean(axis=0)
    _, _, vt = np.linalg.svd(Q - c)
    u = vt[0]
    return c, u / np.linalg.norm(u)


def _intersecao(p, u, q, v):
    M = np.array([u, -v]).T
    if abs(np.linalg.det(M)) < 1e-9:
        return None
    a, _ = np.linalg.solve(M, q - p)
    return p + a * u


def _concordancia(c1, u1, c2, u2, V, Q, tol):
    """Arco tangente às retas (c1,u1) e (c2,u2) que melhor passa pelos pontos Q.
    Retorna (T1, T2, C, r, M) ou None."""
    cosa = float(np.clip(np.dot(-u1, u2), -1, 1))
    alfa = math.acos(cosa)                       # ângulo interno entre as retas
    if alfa < math.radians(5) or alfa > math.radians(175):
        return None
    b = -u1 + u2
    b = b / np.linalg.norm(b)                    # bissetriz (lado de dentro da curva)
    def geo(r):
        C = V + b * r / math.sin(alfa / 2)
        t = r / math.tan(alfa / 2)
        return C, V - u1 * t, V + u2 * t
    def custo(r):
        C, _, _ = geo(r)
        return float(np.median(np.abs(np.hypot(*(Q - C).T) - r)))
    # busca grosseira + refinamento
    dist_max = float(np.max(np.hypot(*(Q - V).T))) + 1e-6
    candidatos = np.linspace(0.2, max(dist_max * 4, 1.0), 200)
    r = float(candidatos[np.argmin([custo(x) for x in candidatos])])
    passo = candidatos[1] - candidatos[0]
    for _ in range(30):
        passo /= 2
        r = min((r - passo, r, r + passo), key=custo)
    if custo(r) > tol:
        return None
    r = _arredondar(r)
    C, T1, T2 = geo(r)
    M = C - b * r
    return T1, T2, C, r, M


def _arredondar(valor, passo=0.5, tol=0.25):
    alvo = round(valor / passo) * passo
    return alvo if abs(alvo - valor) <= tol else valor


def segmentar_contorno(pts_mm: np.ndarray, passo: float = 0.2, raio_reta: float = 60.0,
                       min_reta: float = 2.5, tol_arco: float = 0.12, desvio_aceito: float = 0.4):
    """Transforma um contorno fechado (N×2, mm) em entidades CAD: retas + arcos de concordância.

    - trechos com curvatura menor que 1/raio_reta viram retas (se tiverem pelo menos min_reta mm);
    - entre duas retas: canto vivo (interseção) ou arco tangente (raio ajustado aos pontos);
    - se algo não encaixa, o trecho vira polilinha (nunca perde geometria).
    Retorna (entidades, info)."""
    P = reamostrar_fechado(pts_mm, passo)
    if area_poligono(P) < 0:          # padroniza sentido anti-horário
        P = P[::-1]
    n = len(P)
    k = max(3, int(round(1.0 / passo)))          # margem (pontos) usada nas pontas das retas
    kc = max(4, int(round(2.0 / passo)))         # meia-janela da curvatura (~2 mm)
    Ps = _suavizar_fechado(P, sigma_pts=max(1.0, 0.4 / passo))   # só para classificar
    d = np.roll(Ps, -kc, 0) - np.roll(Ps, kc, 0)  # direção local, base de ~4 mm
    th = np.arctan2(d[:, 1], d[:, 0])
    dth = np.angle(np.exp(1j * (np.roll(th, -kc) - np.roll(th, kc))))
    kappa = dth / (2 * kc * passo)               # variação de direção ao longo de ~4 mm
    cx0, cy0, r0, rms0 = ajustar_circulo(P)
    if rms0 < tol_arco:
        return [Circulo((cx0, cy0), _arredondar(r0, 0.05, 0.03))], {"tipo": "circulo", "rms": rms0}
    # limiar adaptativo: acima do ruído da curvatura (estimado nos trechos mais retos), limitado a R 15 mm
    ruido_k = 1.4826 * np.percentile(np.abs(kappa), 30)
    limiar = float(np.clip(5 * ruido_k, 1.0 / raio_reta, 1.0 / 15.0))
    reto = np.abs(kappa) < limiar
    reto = _limpar_mascara(reto, min_falso=int(1.5 / passo), min_verdadeiro=int(min_reta / passo))

    # círculo inteiro (sem retas)?
    runs = _runs_circular(reto)
    retas = [(i, L) for v, i, L in runs if v and L * passo >= min_reta]
    if not retas:
        cx, cy, r, rms = ajustar_circulo(P)
        if rms < tol_arco:
            return [Circulo((cx, cy), _arredondar(r, 0.05, 0.03))], {"tipo": "circulo", "rms": rms}
        return [Polilinha([tuple(p) for p in P[::max(1, int(1 / passo))]])], {"tipo": "polilinha"}

    # mascara final: só retas longas contam como reta
    reta_final = np.zeros(n, bool)
    for i, L in retas:
        reta_final[(i + np.arange(L)) % n] = True
    runs = _runs_circular(reta_final)
    # gira a lista para começar numa reta
    while not runs[0][0]:
        runs = runs[1:] + runs[:1]

    margem = k
    linhas = []   # (c, u, ini, L)
    curvas = []   # pontos entre a reta i e i+1
    for idx, (v, i, L) in enumerate(runs):
        if v:
            m = min(margem, max(0, (L - 4) // 2))
            Q = P[(i + np.arange(m, L - m)) % n]
            c, u = _ajustar_reta(Q)
            # orienta u no sentido do contorno
            if np.dot(P[(i + L - 1) % n] - P[i], u) < 0:
                u = -u
            linhas.append((c, u, Q))
            nxt = runs[(idx + 1) % len(runs)]
            if nxt[0]:
                curvas.append(np.empty((0, 2)))
            else:
                _, j, Lj = nxt
                ext = min(margem, Lj)
                curvas.append(P[(j + np.arange(Lj)) % n] if Lj > 0 else np.empty((0, 2)))

    # juntar retas consecutivas quase colineares (trecho curvo espúrio entre elas)
    mudou = True
    while mudou and len(linhas) > 2:
        mudou = False
        for a in range(len(linhas)):
            b = (a + 1) % len(linhas)
            (c1, u1, Q1), (c2, u2, Q2) = linhas[a], linhas[b]
            ang = abs(math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], np.dot(u1, u2))))
            desloc = abs((c2[0] - c1[0]) * u1[1] - (c2[1] - c1[1]) * u1[0])
            if ang < 4 and desloc < 0.4:
                Qm = np.vstack([Q1, curvas[a], Q2])
                c, u = _ajustar_reta(Qm)
                if np.dot(u, u1) < 0:
                    u = -u
                linhas[a] = (c, u, Qm)
                curvas[a] = curvas[b]
                del linhas[b], curvas[b]
                mudou = True
                break
    linhas = [(c, u) for c, u, _ in linhas]

    # junções entre retas consecutivas
    juncoes = []
    nl = len(linhas)
    for a in range(nl):
        c1, u1 = linhas[a]
        c2, u2 = linhas[(a + 1) % nl]
        Q = curvas[a]
        V = _intersecao(c1, u1, c2, u2)
        if V is not None:
            ref = Q.mean(axis=0) if len(Q) else (c1 + c2) / 2
            alcance = (len(Q) * passo) + 3.0
            if np.linalg.norm(V - ref) > alcance:
                V = None   # retas quase paralelas: vértice longe demais, não confiável
        giro = math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], np.dot(u1, u2)))
        comprimento_curva = len(Q) * passo
        if V is not None and (comprimento_curva < 1.6 or abs(giro) < 3):
            juncoes.append(("canto", V))
            continue
        if V is not None and len(Q):
            # canto vivo: os pontos do trecho curvo já estão sobre as duas retas
            d1 = np.abs((Q[:, 0] - c1[0]) * u1[1] - (Q[:, 1] - c1[1]) * u1[0])
            d2 = np.abs((Q[:, 0] - c2[0]) * u2[1] - (Q[:, 1] - c2[1]) * u2[0])
            dist = np.minimum(d1, d2)
            if np.median(dist) < tol_arco and np.percentile(dist, 90) < 2.5 * tol_arco:
                juncoes.append(("canto", V))
                continue
        if len(Q) >= 5 and V is not None:
            arco = _concordancia(c1, u1, c2, u2, V, Q, tol_arco)
            if arco is not None:
                juncoes.append(("arco",) + arco)
                continue
        # não deu: polilinha simplificada entre as retas
        if V is None:
            V = Q.mean(axis=0) if len(Q) else (c1 + c2) / 2
        pts = _simplificar(Q, 0.1) if len(Q) else []
        juncoes.append(("poli", pts, V))

    # monta as entidades: reta a vai do fim da junção a-1 ao começo da junção a
    def inicio_juncao(j):
        return j[1] if j[0] == "canto" else (j[1] if j[0] == "arco" else (np.array(j[1][0]) if len(j[1]) else j[2]))

    def fim_juncao(j):
        return j[1] if j[0] == "canto" else (j[2] if j[0] == "arco" else (np.array(j[1][-1]) if len(j[1]) else j[2]))

    ents = []
    for a in range(nl):
        ja, jb = juncoes[a - 1], juncoes[a]
        p0, p1 = fim_juncao(ja), inicio_juncao(jb)
        if np.linalg.norm(np.asarray(p1) - np.asarray(p0)) > 1e-6:
            ents.append(Linha(tuple(map(float, p0)), tuple(map(float, p1))))
        if jb[0] == "arco":
            _, T1, T2, C, r, M = jb
            ents.append(Arco(tuple(map(float, C)), float(r), tuple(map(float, T1)), tuple(map(float, T2)), tuple(map(float, M))))
        elif jb[0] == "poli" and len(jb[1]) >= 2:
            ents.append(Polilinha([tuple(map(float, p)) for p in jb[1]]))
    info = {"tipo": "retas_arcos", "retas": sum(e.tipo == "linha" for e in ents),
            "arcos": sum(e.tipo == "arco" for e in ents), "polilinhas": sum(e.tipo == "polilinha" for e in ents)}
    # rede de segurança: se o CAD reconstruído se afasta dos pontos medidos, usa polilinha fiel
    dmax, dmed = desvio_maximo(P[::2], amostrar_entidades(ents, 0.05))
    info["desvio_max_mm"], info["desvio_medio_mm"] = round(dmax, 3), round(dmed, 3)
    if dmax > desvio_aceito:
        pts = _simplificar(np.vstack([P, P[:1]]), 0.05)
        info = {"tipo": "polilinha", "motivo": f"ajuste em retas/arcos desviou {dmax:.2f} mm", "desvio_max_mm": 0.05}
        return [Polilinha([tuple(map(float, p)) for p in pts])], info
    return ents, info


def _simplificar(Q: np.ndarray, tol: float):
    import cv2
    a = cv2.approxPolyDP(Q.astype(np.float32).reshape(-1, 1, 2), tol, False).reshape(-1, 2)
    return a


def amostrar_entidades(ents, passo: float = 0.1) -> np.ndarray:
    """Pontos densos ao longo das entidades (para medir desvio)."""
    out = []
    for e in ents:
        if e.tipo == "linha":
            p0, p1 = np.array(e.p0), np.array(e.p1)
            n = max(2, int(np.linalg.norm(p1 - p0) / passo))
            out.append(p0 + np.linspace(0, 1, n)[:, None] * (p1 - p0))
        elif e.tipo == "circulo":
            t = np.linspace(0, 2 * np.pi, max(16, int(2 * np.pi * e.raio / passo)))
            out.append(np.c_[e.centro[0] + e.raio * np.cos(t), e.centro[1] + e.raio * np.sin(t)])
        elif e.tipo == "arco":
            a0, a1 = angulos_arco(e)
            n = max(4, int(abs(a1 - a0) * e.raio / passo))
            t = np.linspace(a0, a1, n)
            out.append(np.c_[e.centro[0] + e.raio * np.cos(t), e.centro[1] + e.raio * np.sin(t)])
        elif e.tipo == "polilinha":
            out.append(np.array(e.pontos))
    return np.vstack(out) if out else np.empty((0, 2))


def angulos_arco(e: Arco):
    """Ângulos (rad) de início e fim, no sentido que passa pelo ponto do meio."""
    C = np.array(e.centro)
    a0 = math.atan2(e.p0[1] - C[1], e.p0[0] - C[0])
    a1 = math.atan2(e.p1[1] - C[1], e.p1[0] - C[0])
    am = math.atan2(e.meio[1] - C[1], e.meio[0] - C[0])
    # sentido anti-horário de a0 a a1 contém am?
    def ccw(a, b):
        return (b - a) % (2 * math.pi)
    if ccw(a0, am) <= ccw(a0, a1):
        return a0, a0 + ccw(a0, a1)
    return a0, a0 - ccw(a1, a0)


def desvio_maximo(medido: np.ndarray, referencia: np.ndarray) -> tuple:
    """Distância de cada ponto medido ao ponto mais próximo da referência (mm). Retorna (máx, média)."""
    ref = np.asarray(referencia, float)
    d = np.empty(len(medido))
    for i in range(0, len(medido), 2000):
        bloco = np.asarray(medido[i:i + 2000], float)
        dd = ((bloco[:, None, :] - ref[None, :, :]) ** 2).sum(-1)
        d[i:i + 2000] = np.sqrt(dd.min(axis=1))
    return float(d.max()), float(d.mean())


# ---------------------------------------------------------------- alinhamento para o CAD
def _rot(p, c, s, t):
    x, y = p
    return (c * x - s * y + t[0], s * x + c * y + t[1])


def transformar_entidades(ents, ang: float, t=(0.0, 0.0)):
    """Gira (ang, rad, em torno da origem) e depois translada as entidades."""
    c, s = math.cos(ang), math.sin(ang)
    out = []
    for e in ents:
        if e.tipo == "linha":
            out.append(Linha(_rot(e.p0, c, s, t), _rot(e.p1, c, s, t)))
        elif e.tipo == "arco":
            out.append(Arco(_rot(e.centro, c, s, t), e.raio, _rot(e.p0, c, s, t), _rot(e.p1, c, s, t), _rot(e.meio, c, s, t)))
        elif e.tipo == "circulo":
            out.append(Circulo(_rot(e.centro, c, s, t), e.raio))
        elif e.tipo == "polilinha":
            out.append(Polilinha([_rot(p, c, s, t) for p in e.pontos]))
    return out


def angulo_alinhamento(ents, pontos: np.ndarray) -> float:
    """Ângulo que deixa a maior aresta reta na horizontal (ou o retângulo mínimo, se não houver retas)."""
    linhas = [e for e in ents if e.tipo == "linha"]
    if linhas:
        e = max(linhas, key=lambda l: math.dist(l.p0, l.p1))
        a = math.atan2(e.p1[1] - e.p0[1], e.p1[0] - e.p0[0])
    elif any(e.tipo == "circulo" for e in ents):
        return 0.0
    else:
        import cv2
        (_, _), (w, h), a_graus = cv2.minAreaRect(pontos.astype(np.float32))
        a = math.radians(a_graus + (90 if h > w else 0))
    a = -a
    return (a + math.pi / 2) % math.pi - math.pi / 2          # a reta não tem sentido: giro equivalente em ±90°
