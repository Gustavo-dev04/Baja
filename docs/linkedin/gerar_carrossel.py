"""Gera o carrossel do LinkedIn (slides 1080x1350 + PDF).

Uso: python3 docs/linkedin/gerar_carrossel.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
IMG = RAIZ / "docs" / "img"
MAT = RAIZ / "docs" / "relatorio" / "material" / "imagens"
SAIDA = AQUI / "carrossel"
SAIDA.mkdir(exist_ok=True)

W, H = 1080, 1350
M = 80  # margem lateral
F = "/usr/share/fonts/truetype/liberation/LiberationSans-"
def fonte(peso, tam):
    return ImageFont.truetype(F + {"r": "Regular", "b": "Bold", "i": "Italic"}[peso] + ".ttf", tam)

# tokens de cor
SLATE = (46, 72, 90)       # marca
SLATE_ESC = (31, 49, 62)
ACENTO = (228, 87, 46)     # destaque (usado com parcimônia)
FUNDO = (255, 255, 255)
FUNDO2 = (241, 244, 247)
TINTA = (31, 42, 51)       # texto primário
TINTA2 = (85, 98, 109)     # texto secundário
TINTA3 = (130, 140, 150)   # texto apagado
BORDA = (214, 221, 227)
TOTAL = 8


def quebrar(d, texto, f, larg):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=f) <= larg:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def texto(d, xy, conteudo, f, cor, larg, entre=1.25, alinhar="esq"):
    x, y = xy
    for ln in quebrar(d, conteudo, f, larg):
        dx = (larg - d.textlength(ln, font=f)) / 2 if alinhar == "centro" else 0
        d.text((x + dx, y), ln, font=f, fill=cor)
        y += int(f.size * entre)
    return y


def colar(base, caminho, caixa, raio=24, borda=True):
    """Encaixa a imagem dentro da caixa (x, y, w, h), centralizada, cantos arredondados."""
    x, y, w, h = caixa
    im = Image.open(caminho).convert("RGB")
    im = ImageOps.contain(im, (w, h), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=raio, fill=255)
    px, py = x + (w - im.size[0]) // 2, y + (h - im.size[1]) // 2
    base.paste(im, (px, py), mask)
    if borda:
        ImageDraw.Draw(base).rounded_rectangle([px, py, px + im.size[0] - 1, py + im.size[1] - 1], radius=raio, outline=BORDA, width=2)
    return py + im.size[1]


def moldura(n, escuro=False):
    im = Image.new("RGB", (W, H), SLATE_ESC if escuro else FUNDO)
    d = ImageDraw.Draw(im)
    cor_rotulo = (255, 255, 255) if escuro else SLATE
    d.text((M, 64), "SCANPARTS", font=fonte("b", 26), fill=ACENTO if not escuro else (255, 255, 255))
    cont = f"{n}/{TOTAL}"
    d.text((W - M - d.textlength(cont, font=fonte("r", 26)), 64), cont, font=fonte("r", 26), fill=TINTA3 if not escuro else (190, 200, 210))
    rod = "Projeto de extensão · Mecatrônica Industrial · FATEC Santo André"
    d.text((M, H - 84), rod, font=fonte("r", 24), fill=TINTA3 if not escuro else (190, 200, 210))
    if not escuro:
        d.rectangle([M, H - 104, W - M, H - 102], fill=BORDA)
    return im, d


def titulo(d, t, y=140, tam=64, cor=SLATE):
    return texto(d, (M, y), t, fonte("b", tam), cor, W - 2 * M, 1.12)


def marcadores(d, itens, y, tam=36, cor=TINTA, recuo=44, entre=18):
    f = fonte("r", tam)
    for it in itens:
        d.ellipse([M + 4, y + tam * 0.38, M + 18, y + tam * 0.38 + 14], fill=ACENTO)
        y = texto(d, (M + recuo, y), it, f, cor, W - 2 * M - recuo, 1.25) + entre
    return y


slides = []

# 1 — capa
im, d = moldura(1, escuro=True)
y = texto(d, (M, 150), "Da foto ao CAD editável", fonte("b", 40), (255, 190, 160), W - 2 * M)
y = texto(d, (M, y + 10), "ScanParts", fonte("b", 112), (255, 255, 255), W - 2 * M, 1.05)
y = texto(d, (M, y + 10), "Engenharia reversa de peças mecânicas com inteligência artificial embarcada", fonte("r", 40), (220, 228, 235), W - 2 * M, 1.25)
colar(im, IMG / "hardware" / "scanner_v5_isometrica.jpg", (M, y + 50, W - 2 * M, 560), raio=28, borda=False)
d.text((W - M - d.textlength("Deslize →", font=fonte("b", 32)), H - 150), "Deslize →", font=fonte("b", 32), fill=(255, 190, 160))
slides.append(im)

# 2 — problema
im, d = moldura(2)
y = titulo(d, "Peça quebrou e não existe desenho técnico?")
y = texto(d, (M, y + 30), "Hoje, alguém mede tudo no paquímetro e redesenha no CAD, à mão.", fonte("r", 40), TINTA, W - 2 * M, 1.3)
y = marcadores(d, ["Demora", "Depende de quem mede", "Fica difícil em formas curvas e complexas"], y + 40)
d.rounded_rectangle([M, y + 30, W - M, y + 400], radius=24, fill=FUNDO2)
yy = texto(d, (M + 40, y + 70), "No mercado:", fonte("b", 34), SLATE, W - 2 * M - 80)
yy = texto(d, (M + 40, yy + 12), "Scanners baratos entregam só uma malha 3D, que não dá para editar.", fonte("r", 34), TINTA, W - 2 * M - 80, 1.3)
yy = texto(d, (M + 40, yy + 16), "Softwares que geram CAD editável custam milhares de dólares.", fonte("r", 34), TINTA, W - 2 * M - 80, 1.3)
texto(d, (M, y + 450), "Nossa proposta: equipamento barato que entrega CAD editável.", fonte("b", 40), ACENTO, W - 2 * M, 1.25)
slides.append(im)

# 3 — como funciona
im, d = moldura(3)
y = titulo(d, "Como funciona")
y = colar(im, IMG / "ia" / "fluxo_scanparts.png", (M - 20, y + 40, W - 2 * M + 40, 300), raio=12, borda=False)
y = marcadores(d, [
    "A IA só localiza os furos na foto",
    "A geometria mede centro e diâmetro em milímetros",
    "A norma interpreta a medida: Ø 9,0 mm → furo passante para M8",
    "Sai um script que recria a peça no Fusion 360, com histórico editável",
], y + 60, tam=36)
d.rounded_rectangle([M, y + 40, W - M, y + 200], radius=24, fill=SLATE)
texto(d, (M + 40, y + 76), "Tudo roda no próprio aparelho, sem nuvem e sem computador externo.", fonte("b", 36), (255, 255, 255), W - 2 * M - 80, 1.3)
slides.append(im)

# 4 — bancada
im, d = moldura(4)
y = titulo(d, "A bancada")
y = colar(im, IMG / "hardware" / "scanner_v5_lateral.jpg", (M, y + 30, W - 2 * M, 520), raio=20)
marcadores(d, [
    "NVIDIA Jetson Orin Nano: IA rodando no próprio aparelho",
    "Câmera IMX219 120° + ring light 6500 K + filtro polarizador",
    "Prato giratório Ø180 mm com 24 alvos de referência",
    "Laser de linha 650 nm para o 3D",
    "Motor de passo 28BYJ-48 controlado por Arduino",
    "Projetada no Autodesk Fusion, peças impressas em 3D",
], y + 40, tam=33, entre=12)
slides.append(im)

# 5 — dados sintéticos
im, d = moldura(5)
y = titulo(d, "Treinamos a IA sem fotografar nenhuma peça")
y = colar(im, IMG / "ia" / "exemplos_sinteticos.jpg", (M, y + 30, W - 2 * M, 460), raio=20)
y = texto(d, (M, y + 40), "3.500 imagens geradas por código, com os furos marcados automaticamente.", fonte("b", 36), TINTA, W - 2 * M, 1.3)
texto(d, (M, y + 20), "Elas também trazem reflexos, sujeira e marcas que não são furos, para a IA aprender a ignorar. Custo de anotação: zero.", fonte("r", 34), TINTA2, W - 2 * M, 1.3)
slides.append(im)

# 6 — resultados (KPI row de stat tiles: valor em sans semibold, texto em tinta, sem cor de série)
im, d = moldura(6)
y = titulo(d, "Resultado do detector de furos")
y = texto(d, (M, y + 16), "YOLO11n · 2,6 milhões de parâmetros · treino de 26 min em GPU no Google Colab", fonte("r", 30), TINTA2, W - 2 * M, 1.3)
tiles = [("Precisão", "94%", "v1: 91%"), ("Recall", "93%", "v1: 83%"), ("mAP50", "97%", "v1: 89%")]
gap = 24
tw = (W - 2 * M - 2 * gap) // 3
ty = y + 50
for i, (rot, val, ant) in enumerate(tiles):
    x = M + i * (tw + gap)
    d.rounded_rectangle([x, ty, x + tw, ty + 300], radius=24, fill=FUNDO2, outline=BORDA, width=2)
    d.text((x + 32, ty + 34), rot, font=fonte("r", 32), fill=TINTA2)
    d.text((x + 28, ty + 90), val, font=fonte("b", 104), fill=TINTA)
    d.text((x + 32, ty + 228), ant, font=fonte("r", 28), fill=TINTA3)
d.rectangle([M, ty + 300 + 30, M + 8, ty + 300 + 30 + 120], fill=ACENTO)
texto(d, (M + 32, ty + 330), "Medido em 500 imagens sintéticas de validação. A nota em fotos reais da nossa câmera é o próximo passo.", fonte("r", 32), TINTA, W - 2 * M - 32, 1.3)
d.rounded_rectangle([M, ty + 520, W - M, ty + 700], radius=24, fill=FUNDO2)
texto(d, (M + 40, ty + 556), "1,7 ms por imagem na GPU do Colab. No Jetson será mais lento, mas a meta é menos de 1 s por foto: sobra folga.", fonte("r", 34), TINTA, W - 2 * M - 80, 1.3)
slides.append(im)

# 7 — teste real
im, d = moldura(7)
y = titulo(d, "E em fotos reais?")
lado = (W - 2 * M - 20) // 2
colar(im, MAT / "fig10a_teste_real_porcas_1.jpg", (M, y + 40, lado, lado), raio=20)
colar(im, MAT / "fig10b_teste_real_porcas_2.jpg", (M + lado + 20, y + 40, lado, lado), raio=20)
y = y + 40 + lado + 40
y = texto(d, (M, y), "Sem nunca ter visto uma foto real, o modelo encontrou os furos das porcas e ignorou os parafusos.", fonte("b", 36), TINTA, W - 2 * M, 1.3)
texto(d, (M, y + 20), "Ainda falta: caixas mais justas em volta do furo e testar com fotos da nossa própria bancada.", fonte("r", 33), TINTA2, W - 2 * M, 1.3)
d.text((M, H - 140), "Fotos: Mechanical Parts Dataset (M. Cakir, Roboflow Universe), licença CC BY-NC-SA 4.0", font=fonte("i", 22), fill=TINTA3)
slides.append(im)

# 8 — próximos passos
im, d = moldura(8, escuro=True)
y = texto(d, (M, 160), "Próximos passos", fonte("b", 64), (255, 255, 255), W - 2 * M, 1.1)
f = fonte("r", 38)
for i, it in enumerate([
    "Calibrar a câmera de 120°",
    "Peça plana: foto → DXF → sólido no Fusion 360",
    "Demonstração no Seminário de Projetos de Extensão, em dezembro",
    "Depois: 3D com laser e prato giratório",
]):
    y += 40
    d.ellipse([M, y + 2, M + 52, y + 54], fill=ACENTO)
    num = str(i + 1)
    d.text((M + 26 - d.textlength(num, font=fonte("b", 30)) / 2, y + 10), num, font=fonte("b", 30), fill=(255, 255, 255))
    y = texto(d, (M + 80, y + 4), it, f, (230, 236, 241), W - 2 * M - 80, 1.25)
y += 90
d.rectangle([M, y, W - M, y + 2], fill=(80, 104, 122))
y = texto(d, (M, y + 50), "Quer acompanhar o projeto?", fonte("b", 44), (255, 190, 160), W - 2 * M)
texto(d, (M, y + 14), "Siga, comente ou mande uma mensagem. Sugestões de quem trabalha com manutenção e CAD são muito bem-vindas.", fonte("r", 34), (220, 228, 235), W - 2 * M, 1.3)
slides.append(im)

for i, s in enumerate(slides, 1):
    s.save(SAIDA / f"slide_{i:02d}.png")
slides[0].save(AQUI / "ScanParts_carrossel_LinkedIn.pdf", save_all=True, append_images=slides[1:], resolution=150)
print(f"{len(slides)} slides salvos em {SAIDA} + PDF")
