"""Generate Magnus v1 progression report PDF.

Self-contained snapshot of the model at v1 (first multi-source fine-tune,
YOLO11s, 8 classes) — sent to the external Claude Code project that tracks
model progression. All numbers are real, from the 2026-06-09 training run.

Usage:
    python docs/progression/generate_v1_pdf.py
Creates docs/progression/magnus_v1_snapshot.pdf.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


GREEN = colors.HexColor("#314f39")
GREEN_LIGHT = colors.HexColor("#dde9dd")
INK = colors.HexColor("#1d1d1a")
INK_MUTED = colors.HexColor("#6b6960")
LINE = colors.HexColor("#e8e5dc")
RED_SOFT = colors.HexColor("#fdf0ef")
AMBER_SOFT = colors.HexColor("#fdf6e7")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=26, leading=30,
            textColor=GREEN, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "Sub", parent=base["Normal"],
            fontName="Helvetica", fontSize=11, leading=14,
            textColor=INK_MUTED, spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=16, leading=20,
            textColor=GREEN, spaceBefore=18, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=12, leading=15,
            textColor=INK, spaceBefore=12, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=INK, alignment=TA_LEFT, spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "Code", parent=base["Normal"],
            fontName="Courier", fontSize=9, leading=12,
            textColor=INK, leftIndent=10, spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=INK_MUTED,
        ),
    }


def make_table(rows, col_widths=None, header=True, highlight_rows=None):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), GREEN),
        ]
    for row_idx, bg in (highlight_rows or {}).items():
        style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
    t.setStyle(TableStyle(style))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(1.5 * cm, A4[1] - 0.75 * cm, "MAGNUS — Progression Report")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        A4[0] - 1.5 * cm, A4[1] - 0.75 * cm,
        "v1 (multi-source fine-tune)  ·  2026-06-09",
    )
    canvas.setFillColor(INK_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        1.5 * cm, 1 * cm,
        "Baja Paint Inspection — branch claude/paint-inspection-ai-FRk8g",
    )
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"page {doc.page}")
    canvas.restoreState()


def build_pdf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2 * cm, bottomMargin=1.5 * cm,
        title="Magnus v1 — Progression Snapshot",
        author="Magnus / Baja",
    )
    s = build_styles()
    story = []

    def P(text, style="body"):
        story.append(Paragraph(text, s[style]))

    def sp(h=6):
        story.append(Spacer(1, h))

    # === COVER ===
    P("Magnus v1", "title")
    P(
        "Primeiro fine-tune multi-fonte: YOLO11s com 8 classes treinado "
        "em dataset curado de 3 fontes públicas. Dobra a cobertura de "
        "defeitos do v0 e produz o diagnóstico mais valioso do ciclo: o "
        "gargalo é qualidade/quantidade de rótulo por classe, não "
        "arquitetura.",
        "subtitle",
    )

    # === 1. Resumo executivo ===
    P("1. Resumo executivo", "h1")
    P(
        "O Magnus v1 expande o detector de defeitos de pintura de 4 para "
        "<b>8 classes</b>, triplicando os parâmetros (3M → 9,4M, YOLOv8n → "
        "YOLO11s) e dobrando o dataset (2.000 → ~4.500 imagens únicas de "
        "3 fontes curadas). O mAP50 agregado (0,655) cai versus o v0 "
        "(0,989) — <b>resultado esperado e diagnóstico</b>: o v0 media uma "
        "tarefa fácil (4 classes balanceadas, fonte única); o v1 mede uma "
        "tarefa realista. Cinco classes estão prontas para produção "
        "(mAP50 0,73–0,95); três falham por causas identificadas e "
        "endereçáveis (escassez de dados e taxonomia incoerente).",
        "body",
    )

    sp()
    P("Comparativo v0 → v1", "h2")
    story.append(make_table([
        ["Atributo", "v0", "v1"],
        ["Arquitetura", "YOLOv8n", "YOLO11s"],
        ["Parâmetros", "3.011.628", "9.430.888 (3,1×)"],
        ["GFLOPs", "8,2", "21,6"],
        ["Camadas (fused)", "73", "101"],
        ["Classes", "4", "8 (2×)"],
        ["Fontes de dataset", "1", "3 curadas (de 13 auditadas)"],
        ["Imagens de treino", "1.600", "3.548 (incl. oversampling de raras)"],
        ["mAP50 agregado", "0,989", "0,655"],
        ["mAP50 das 4 classes core", "0,989", "0,891 (média)"],
        ["Inferência (T4 GPU)", "—", "24,1 ms"],
        ["Inferência (CPU HF Spaces)", "~60 ms", "~130 ms estimado"],
        ["Checkpoint", "hf://Guguinhaxd/baja-paint-models/best.pt",
         "hf://Guguinhaxd/magnus-v2/best.pt"],
    ], col_widths=[5.5 * cm, 5 * cm, 6.5 * cm]))

    # === 2. Setup do treino ===
    P("2. Setup do treino", "h1")
    story.append(make_table([
        ["Atributo", "Valor"],
        ["Hardware", "Colab T4 GPU (free tier)"],
        ["Epochs", "150 (melhor checkpoint ~epoch 61, platô a partir de ~60)"],
        ["Batch / imgsz", "16 / 640"],
        ["Otimizador", "AdamW (auto), lr=0,000833, cosine schedule"],
        ["Augmentation", "mosaic 1.0 (close em 135), mixup 0,15, copy_paste 0,3, "
         "erasing 0,4, degrees ±10°, fliplr 0,5, HSV jitter"],
        ["Oversampling", "classes do quartil inferior ×3 (train apenas)"],
        ["Dataset splits", "3.548 train (215 bg) · 572 val (51 bg) · 381 test (21 bg)"],
        ["Dedup", "por imagem-fonte, escopo de workspace (remove aug 3× embutido "
         "do Roboflow e overlap entre projetos do mesmo autor)"],
        ["Negativos", "215+51+21 imagens 'good_paint' / sem anotação"],
        ["Avaliação", "test split com TTA (test-time augmentation)"],
    ], col_widths=[4.5 * cm, 12.5 * cm]))

    # === 3. Métricas ===
    P("3. Métricas v1 (test split, TTA)", "h1")
    P("Globais", "h2")
    story.append(make_table([
        ["Métrica", "Valor"],
        ["mAP@50", "0,655"],
        ["mAP@50–95", "0,428"],
        ["Precision (média)", "0,807"],
        ["Recall (média)", "0,617"],
        ["Velocidade", "2,1 ms pré + 24,1 ms inferência + 1,2 ms pós (T4)"],
    ], col_widths=[7 * cm, 9 * cm]))

    sp()
    P("Por classe — o resultado que importa", "h2")
    story.append(make_table([
        ["Classe", "mAP50", "mAP50-95", "P", "R", "Instâncias", "Veredito"],
        ["casca_de_laranja", "0,951", "0,797", "0,935", "0,909", "79", "produção"],
        ["water_spotting", "0,928", "0,758", "0,858", "0,907", "75", "produção"],
        ["escorrimento", "0,849", "0,649", "0,883", "0,829", "70", "produção"],
        ["bolha", "0,836", "0,596", "0,878", "0,805", "113", "produção"],
        ["sujeira", "0,732", "0,242", "0,745", "0,690", "58", "produção"],
        ["descascamento", "0,493", "0,248", "0,886", "0,450", "20", "faminto de dados"],
        ["risco", "0,253", "0,078", "0,358", "0,227", "66", "taxonomia incoerente"],
        ["oxidacao", "0,198", "0,059", "0,914", "0,118", "17", "faminto de dados"],
    ], col_widths=[3.6 * cm, 1.7 * cm, 2 * cm, 1.6 * cm, 1.6 * cm, 2.2 * cm, 3.8 * cm],
        highlight_rows={6: AMBER_SOFT, 7: RED_SOFT, 8: RED_SOFT}))

    sp()
    P(
        "<b>Padrão revelador:</b> descascamento e oxidacao têm precisão "
        "alta (0,89 e 0,91) com recall baixo (0,45 e 0,12) — o modelo "
        "<i>sabe reconhecer</i> mas não encontra tudo, assinatura clássica "
        "de escassez de amostras (20 e 17 instâncias). Já risco falha dos "
        "dois lados (P=0,36, R=0,23) — assinatura de classe visualmente "
        "incoerente.",
        "body",
    )

    story.append(PageBreak())

    # === 4. Matriz de confusão ===
    P("4. Análise da matriz de confusão", "h1")
    P(
        "A matriz de confusão (runs/detect/magnus_v2/eval/"
        "confusion_matrix.png) isola as causas com precisão cirúrgica:",
        "body",
    )
    story.append(make_table([
        ["Observação", "Números", "Diagnóstico"],
        ["5 classes com diagonal limpa",
         "bolha 92, casca 73, water_spotting 69,\nescorrimento 59, sujeira 46 acertos; "
         "confusão entre classes ≈ 0",
         "Produção-ready. O modelo separa\nbem os conceitos."],
        ["risco falha nos dois sentidos",
         "26 acertos · 40 riscos reais preditos como\nbackground · 54 backgrounds preditos como risco",
         "Fusão scratch+Crack+Paint-Crack criou\nclasse sem identidade visual. Arranhão\nfino confunde com textura de fundo."],
        ["oxidacao não encontra",
         "3 acertos · 13 perdidos para background ·\nquase nenhum falso positivo",
         "Não é confusão — é fome de dados\n(7 imagens no test)."],
        ["descascamento borderline",
         "8 acertos · 8 perdidos",
         "Idem: 13 imagens no test."],
    ], col_widths=[4 * cm, 7 * cm, 6 * cm]))

    sp()
    P("Conclusão científica do ciclo", "h2")
    P(
        "<b>O gargalo não é arquitetura — é dado.</b> Com rótulos "
        "consistentes e volume adequado, o YOLO11s entrega 0,84–0,95 por "
        "classe. Onde o rótulo é incoerente (risco) ou escasso "
        "(oxidacao), nenhum aumento de modelo resolve. A auditoria "
        "pré-treino já havia descartado ~68% do volume bruto disponível "
        "(46k imagens dos datasets weld) por ruído de domínio; este "
        "resultado valida quantitativamente a decisão: <b>curadoria "
        "supera volume</b>.",
        "body",
    )

    # === 5. Decisões para v1.1 e v2 ===
    P("5. Próximos passos", "h1")
    P("v1.1 — modelo de produção honesto (imediato)", "h2")
    P(
        "Re-treinar com as <b>6 classes saudáveis</b> (remover risco e "
        "oxidacao). Projeção: mAP50 agregado ~0,80 sem nenhuma outra "
        "mudança. O modelo passa a prometer apenas o que entrega. As "
        "classes removidas retornam na v2 com dados próprios.",
        "body",
    )
    P("v2 — dataset próprio (próximo ciclo)", "h2")
    story.append(make_table([
        ["Ação", "Resolve"],
        ["Fotografar chassi BAJA real (300–500 imgs, iluminação controlada)",
         "domain gap closeup→campo"],
        ["Rotular internamente com taxonomia própria (sem fusões de classes "
         "distintas)", "incoerência do risco"],
        ["Coleta dirigida de oxidação/descascamento (active learning nos "
         "15k weld reservados)", "fome de dados das raras"],
        ["Separar bolha de solvent_pop se amostras permitirem",
         "granularidade técnica"],
    ], col_widths=[10.5 * cm, 6.5 * cm]))

    # === 6. Artefatos ===
    P("6. Artefatos do ciclo", "h1")
    story.append(make_table([
        ["Artefato", "Localização"],
        ["Checkpoint v1 (best.pt, 18,4 MB)", "hf://Guguinhaxd/magnus-v2/best.pt"],
        ["Pipeline de dataset", "training/v2/build_dataset.py (dedup workspace-scoped, "
         "filtro de negativos envenenados, oversampling)"],
        ["Receita de treino", "training/v2/train.py"],
        ["Avaliação TTA + matriz", "training/v2/evaluate.py"],
        ["Taxonomia e fontes", "training/v2/config.py (com datasets excluídos documentados)"],
        ["Matriz de confusão", "runs/detect/magnus_v2/eval/confusion_matrix.png (Colab)"],
        ["Snapshot anterior", "docs/progression/magnus_v0_snapshot.pdf"],
    ], col_widths=[6 * cm, 11 * cm]))

    sp()
    P("Bugs corrigidos durante o ciclo (auditoria pré-treino)", "h2")
    P(
        "1. Dedup entre fontes não colapsava overlap do mesmo autor "
        "(risco de leakage train/test). 2. Imagens que perdiam todos os "
        "rótulos no remap viravam negativos envenenados. 3. "
        "label_smoothing removido do Ultralytics 8.4 quebraria o treino. "
        "Todos corrigidos antes da primeira execução — ver commit "
        "becb4f7.",
        "body",
    )

    sp(20)
    P(
        f"Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        "Documento auto-suficiente para o projeto de tracking de "
        "progressão. Sucede magnus_v0_snapshot.pdf; será sucedido por "
        "magnus_v1_1 (6 classes) e magnus_v2 (dataset próprio).",
        "small",
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return path


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "magnus_v1_snapshot.pdf"
    build_pdf(out_path)
    print(f"✅ PDF gerado: {out_path}")
    print(f"   {out_path.stat().st_size:,} bytes")
