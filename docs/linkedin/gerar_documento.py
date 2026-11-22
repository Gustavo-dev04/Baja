"""Gera o kit de publicação do LinkedIn (docx). Uso: python3 docs/linkedin/gerar_documento.py"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AQUI = Path(__file__).resolve().parent
SLATE = RGBColor(0x2E, 0x48, 0x5A)
ACENTO = RGBColor(0xE4, 0x57, 0x2E)
CINZA = RGBColor(0x55, 0x62, 0x6D)

POST_COMPLETO = """Peça quebrou e não existe desenho técnico. E agora?

Quem já trabalhou com manutenção conhece a cena: alguém pega o paquímetro, mede tudo e redesenha a peça no CAD, à mão. Demora, depende de quem mede e fica difícil em formas complexas.

Foi para atacar esse problema que meu grupo começou o ScanParts, projeto de extensão do curso de Mecatrônica Industrial da FATEC Santo André: um scanner de bancada de baixo custo que transforma a foto de uma peça em um modelo CAD editável.

Como funciona
• Uma câmera IMX219 com ring light fotografa a peça
• Um NVIDIA Jetson Orin Nano processa tudo no próprio aparelho, sem nuvem
• Uma IA (YOLO11n) localiza os furos e a geometria mede centro e diâmetro em milímetros
• A medida é interpretada pela norma: Ø 9,0 mm vira "furo passante para M8"
• No fim, sai um script que recria a peça no Fusion 360, com histórico editável

O que já fizemos
• Um gerador de imagens sintéticas que cria milhares de fotos de peças com os furos já marcados, sem custo de anotação
• O treino do detector de furos no Google Colab: 94% de precisão e 93% de recall nas imagens sintéticas de validação
• Um primeiro teste em fotos reais: o modelo achou os furos de porcas sem nunca ter visto uma foto de verdade
• O projeto da bancada no Fusion, com prato giratório, laser de linha e o Jetson integrados

O que queremos de diferente: não parar na malha 3D, como a maioria dos scanners acessíveis, e sim entregar CAD editável, com equipamento barato e processamento local.

Ainda tem bastante coisa pela frente: calibrar a câmera, medir o desempenho em fotos da nossa própria bancada e apresentar a demonstração no Seminário de Projetos de Extensão, em dezembro.

Obrigado ao [@orientador] pela orientação e aos colegas [@integrante] [@integrante] [@integrante].

Se você trabalha com manutenção, usinagem ou CAD: que tipo de peça vocês mais precisam redesenhar?

#EngenhariaReversa #VisaoComputacional #InteligenciaArtificial #Mecatronica #EdgeAI"""

POST_CURTO = """Da foto ao CAD editável: esse é o ScanParts, projeto de extensão que meu grupo está desenvolvendo no curso de Mecatrônica Industrial da FATEC Santo André.

A ideia: fotografar uma peça mecânica e receber um modelo pronto no Fusion 360, sem medir no paquímetro e redesenhar à mão. Tudo roda num NVIDIA Jetson Orin Nano, sem nuvem.

Já treinamos uma IA (YOLO11n) que localiza furos, com 94% de precisão nas imagens sintéticas de validação, e ela já encontrou furos em fotos reais de peças sem nunca ter visto uma. O próximo passo é a demonstração no Seminário de Projetos de Extensão, em dezembro.

Os detalhes estão no carrossel. 👉

#EngenhariaReversa #VisaoComputacional #EdgeAI #Mecatronica"""

COMENTARIO = """O código, os notebooks de treino e a documentação do projeto estão abertos no GitHub: https://github.com/Gustavo-dev04/Baja"""

PROJETO_NOME = "ScanParts – Scanner de engenharia reversa com IA embarcada"
PROJETO_DESC = """Scanner de bancada de baixo custo que gera modelos CAD editáveis (Autodesk Fusion) a partir de fotos de peças mecânicas de até 10 cm, com meta de precisão de ±1 mm. Projeto de extensão do curso de Mecatrônica Industrial da FATEC Santo André.

• Gerador de imagens sintéticas com rotulagem automática (Python, OpenCV), que eliminou o custo de anotação manual
• Detector de furos YOLO11n treinado no Google Colab: precisão de 0,94 e recall de 0,93 na validação sintética
• Processamento embarcado previsto em NVIDIA Jetson Orin Nano (TensorRT)
• Bancada projetada no Fusion: câmera IMX219, ring light 6500 K com filtro polarizador, prato giratório com alvos de referência e laser de linha
• Saída como script do Fusion, que recria a peça com histórico paramétrico"""
COMPETENCIAS = "Visão computacional · Deep learning · YOLO · Python · OpenCV · NVIDIA Jetson · Sistemas embarcados · Engenharia reversa · Autodesk Fusion 360 · Impressão 3D · Google Colab"

POST_DEPOIS = """[Texto para depois do seminário – anexar um vídeo de 30 a 60 segundos da demonstração]

Ontem apresentamos o ScanParts no Seminário de Projetos de Extensão da FATEC Santo André. 🎉

No vídeo: o suporte vai para o prato, a câmera tira uma foto de cima, o Jetson Orin Nano encontra o contorno e os furos e, segundos depois, a peça aparece pronta no Fusion 360.

Para provar a medida, medimos um furo com paquímetro na frente da banca: [valor real] mm. O sistema mediu [valor do sistema] mm.

[uma frase sobre o que aprenderam ou o que vem a seguir]

Obrigado ao [@orientador] e aos colegas [@integrantes].

#EngenhariaReversa #VisaoComputacional #EdgeAI #Mecatronica"""

SLIDES = [
    "Capa: nome do projeto, frase de impacto e a bancada em 3D",
    "O problema: peça sem desenho técnico e o que existe no mercado",
    "Como funciona: o fluxo em 5 etapas, com a IA destacada",
    "A bancada: render do Fusion e os principais componentes",
    "Os dados sintéticos: treinar a IA sem fotografar nenhuma peça",
    "Resultados: precisão, recall e mAP50, deixando claro que são dados sintéticos",
    "Teste em fotos reais: as porcas detectadas, com o crédito das fotos",
    "Próximos passos e convite para acompanhar o projeto",
]

DICAS = [
    ("Formato", "Publique como **Documento** (botão “+” → Adicionar documento) com o arquivo ScanParts_carrossel_LinkedIn.pdf. O LinkedIn mostra como slides que a pessoa desliza. Título sugerido: “ScanParts: da foto ao CAD editável”."),
    ("Marcações", "Marque a página da FATEC Santo André, o orientador e os colegas (peça licença antes). Cada pessoa marcada leva o post para a própria rede."),
    ("Link", "Coloque o link do GitHub no **primeiro comentário**, não no texto do post. Posts com link externo costumam ter menos alcance."),
    ("Horário", "Dias úteis, de manhã (8h–10h) ou no almoço, costumam funcionar melhor. Responda os comentários na primeira hora."),
    ("Colegas", "Cada integrante pode compartilhar com um comentário próprio dizendo o que fez no projeto (IA, mecânica, eletrônica, documentação)."),
    ("Perfil", "Adicione o projeto na seção **Projetos** do perfil (texto pronto abaixo) e associe à FATEC Santo André, com os colegas como colaboradores."),
    ("Depois do seminário", "Faça um segundo post com **vídeo curto** da demonstração funcionando. Vídeo de algo funcionando de verdade é o conteúdo que mais chama atenção."),
    ("Repositório", "O repositório se chama “Baja”. Para o LinkedIn, vale renomear para “scanparts” no GitHub (Settings → Repository name); o link antigo continua redirecionando."),
]

CUIDADOS = [
    "**Diga sempre “nas imagens sintéticas”** junto dos 94% e 93%. Ainda não existe nota medida em fotos reais. Isso é honesto e passa credibilidade para quem é da área.",
    "**Evite “inédito” ou “o primeiro”.** Na pesquisa não achamos solução barata que entregue CAD editável, mas isso não prova que não exista. Prefira “o que queremos de diferente”.",
    "**Não diga que já funciona no Jetson** antes de testar lá: o treino e os testes foram no Colab e no computador.",
    "**Fotos das porcas (slide 7)** são do dataset Mechanical Parts, licença CC BY-NC-SA 4.0: mantenha o crédito que está no slide.",
    "**Logo da FATEC:** use só se a instituição permitir; o carrossel não usa o logo, só o nome.",
    "**Dados pessoais:** não publiquem RA, e-mail institucional ou fotos de colegas sem autorização.",
]


def sombrear(cel, cor="F1F4F7"):
    tcPr = cel._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), cor)
    tcPr.append(shd)


def rich(par, texto, tam=11, cor=None):
    import re
    for i, parte in enumerate(re.split(r"(\*\*[^*]+\*\*)", texto)):
        if not parte:
            continue
        r = par.add_run(parte[2:-2] if parte.startswith("**") else parte)
        r.bold = parte.startswith("**")
        r.font.size = Pt(tam)
        if cor:
            r.font.color.rgb = cor


def caixa_texto(doc, conteudo, rotulo):
    """Texto pronto para copiar, dentro de uma caixa cinza."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    sombrear(c)
    c.paragraphs[0].text = ""
    r = c.paragraphs[0].add_run(rotulo.upper())
    r.bold = True; r.font.size = Pt(8); r.font.color.rgb = ACENTO
    for linha in conteudo.split("\n"):
        p = c.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(linha)
        run.font.size = Pt(10.5)
    c.add_paragraph()
    doc.add_paragraph()


def h(doc, texto, nivel=1, nova_pagina=False):
    p = doc.add_heading(texto, level=nivel)
    p.paragraph_format.page_break_before = nova_pagina
    for r in p.runs:
        r.font.color.rgb = SLATE
        r.font.name = "Arial"
    return p


doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2)
st = doc.styles["Normal"]
st.font.name = "Arial"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")

p = doc.add_paragraph()
r = p.add_run("ScanParts no LinkedIn"); r.bold = True; r.font.size = Pt(26); r.font.color.rgb = SLATE
p = doc.add_paragraph()
r = p.add_run("Kit de publicação: textos prontos, carrossel com imagens e dicas"); r.font.size = Pt(13); r.font.color.rgb = CINZA
doc.add_picture(str(AQUI / "carrossel" / "slide_01.png"), width=Cm(8))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

h(doc, "1. Como publicar")
for titulo, txt in DICAS:
    par = doc.add_paragraph(style="List Bullet")
    rich(par, f"**{titulo}:** {txt}")

h(doc, "2. Texto do post (versão completa)", nova_pagina=True)
p = doc.add_paragraph(); rich(p, "Para publicar junto com o carrossel. Troque os **[@...]** pelas marcações reais (digite @ e o nome).", 10, CINZA)
caixa_texto(doc, POST_COMPLETO, f"Copiar e colar · {len(POST_COMPLETO)} de 3.000 caracteres")

h(doc, "3. Texto do post (versão curta)", nova_pagina=True)
caixa_texto(doc, POST_CURTO, f"Copiar e colar · {len(POST_CURTO)} caracteres")

h(doc, "4. Primeiro comentário (com o link)")
caixa_texto(doc, COMENTARIO, "Comentar logo depois de publicar")

h(doc, "5. Carrossel (8 slides)", nova_pagina=True)
p = doc.add_paragraph()
rich(p, "Arquivo para publicar: **ScanParts_carrossel_LinkedIn.pdf**. As imagens separadas, em 1080 × 1350 px, estão na pasta **carrossel/** (servem também para post com imagens ou para os stories).", 10, CINZA)
tab = doc.add_table(rows=4, cols=2)
tab.alignment = WD_TABLE_ALIGNMENT.CENTER
for i in range(8):
    cel = tab.rows[i // 2].cells[i % 2]
    cel.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cel.paragraphs[0].add_run().add_picture(str(AQUI / "carrossel" / f"slide_{i + 1:02d}.png"), width=Cm(6.2))
    cp = cel.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rich(cp, f"**{i + 1}.** {SLIDES[i]}", 9, CINZA)

h(doc, "6. Seção “Projetos” do perfil", nova_pagina=True)
caixa_texto(doc, f"Nome: {PROJETO_NOME}\nAssociado a: FATEC Santo André\nData: nov. 2026 – atual\n\nDescrição:\n{PROJETO_DESC}", "Copiar para o perfil")
p = doc.add_paragraph(); rich(p, f"**Competências para adicionar:** {COMPETENCIAS}")

h(doc, "7. Segundo post, depois do seminário", nova_pagina=True)
caixa_texto(doc, POST_DEPOIS, "Modelo – completar depois da demonstração")

h(doc, "8. Cuidados")
for txt in CUIDADOS:
    par = doc.add_paragraph(style="List Bullet")
    rich(par, txt)

h(doc, "9. Hashtags")
p = doc.add_paragraph()
rich(p, "Use de 3 a 5 por post. Sugestões: #EngenhariaReversa #VisaoComputacional #InteligenciaArtificial #Mecatronica #EdgeAI #NVIDIAJetson #YOLO #Fusion360 #Industria40 #FATEC")

doc.save(AQUI / "ScanParts_LinkedIn.docx")
print("ok – post completo:", len(POST_COMPLETO), "caracteres; curto:", len(POST_CURTO))
