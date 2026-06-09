"""Generate Magnus v0 progression report PDF.

Self-contained snapshot of the model at v0 — meant to be sent to another
Claude Code project that will track progression across model versions.

Usage:
    python docs/progression/generate_v0_pdf.py
Creates docs/progression/magnus_v0_snapshot.pdf.
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
CANVAS = colors.HexColor("#fbfaf6")


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


def make_table(rows, col_widths=None, header=True):
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
    t.setStyle(TableStyle(style))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    # Header band
    canvas.setFillColor(GREEN)
    canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(1.5 * cm, A4[1] - 0.75 * cm, "MAGNUS — Progression Report")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        A4[0] - 1.5 * cm, A4[1] - 0.75 * cm,
        "v0 (baseline)  ·  2026-05-19",
    )
    # Footer
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
        title="Magnus v0 — Progression Snapshot",
        author="Magnus / Baja",
    )
    s = build_styles()
    story = []

    def P(text, style="body"):
        story.append(Paragraph(text, s[style]))

    def sp(h=6):
        story.append(Spacer(1, h))

    # === COVER ===
    P("Magnus v0", "title")
    P(
        "Snapshot do modelo de visão computacional do Magnus em sua "
        "primeira geração funcional, antes do fine-tuning com dataset "
        "expandido. Documento gerado para registrar a baseline e "
        "permitir comparação objetiva com versões futuras.",
        "subtitle",
    )

    # === 1. Resumo executivo ===
    P("1. Resumo executivo", "h1")
    P(
        "O Magnus é um sistema de inspeção visual automatizada da "
        "pintura de chassis estilo BAJA SAE. Capta imagens via webcam "
        "ou upload, executa detecção de defeitos em servidor de IA "
        "hospedado em nuvem e devolve bounding boxes + classes + "
        "confiança em tempo quase real. Esta é a versão <b>v0</b> — "
        "primeira iteração com modelo fine-tunado em dataset público "
        "real, sucessora da fase <i>demo</i> que rodava YOLO genérico "
        "(COCO) com remapeamento simbólico de classes.",
        "body",
    )

    sp()
    P("Status atual", "h2")
    story.append(make_table([
        ["Componente", "Status"],
        ["Backend (FastAPI + YOLO)", "Em produção — Hugging Face Spaces"],
        ["Frontend (Next.js + Magnus UI)", "Em produção — Vercel"],
        ["Banco de dados", "Supabase Postgres + Storage (1.999 imagens)"],
        ["Modelo", "YOLOv8n fine-tuned, 4 classes, mAP50 = 0.989"],
        ["Origem do checkpoint", "hf://Guguinhaxd/baja-paint-models/best.pt"],
        ["Latência observada", "~60 ms inferência CPU · ~350 ms round-trip"],
        ["Custo mensal de infra", "R$ 0,00 (free tier em todos os serviços)"],
    ], col_widths=[6 * cm, 11 * cm]))

    # === 2. Arquitetura ===
    P("2. Arquitetura", "h1")
    P(
        "Pipeline cloud serverless em três serviços conectados, com "
        "modelo versionado em hub externo:",
        "body",
    )
    P(
        "Frontend Vercel  →  FastAPI Hugging Face Spaces  →  YOLO best.pt<br/>"
        "                                ↓<br/>"
        "                  Supabase (Postgres + Storage)",
        "code",
    )

    sp()
    P("Convenções importantes", "h2")
    P(
        "<b>Esquema de pesos hf://</b> — implementação custom no backend "
        "(<font name='Courier' size='9'>backend/app/inference.py</font>) "
        "aceita <font name='Courier' size='9'>BAJA_MODEL_WEIGHTS=hf://owner/repo/file.pt</font>. "
        "No boot do Space, baixa o checkpoint via huggingface_hub, "
        "cacheia em <font name='Courier' size='9'>BAJA_MODEL_CACHE_DIR</font> e carrega no Ultralytics. "
        "Permite hot-swap de modelo trocando uma variável de ambiente.",
        "body",
    )
    P(
        "<b>Separação de credenciais</b> — service_role do Supabase só "
        "no backend (escrita autenticada via JWT admin); anon key no "
        "frontend (leitura via RLS pública).",
        "body",
    )
    P(
        "<b>Modo demo automático</b> — se o checkpoint carregado for um "
        "yolov8/yolo11/yolov5 stock, a resposta marca <font name='Courier' size='9'>demo_mode: true</font> "
        "e aplica <font name='Courier' size='9'>DEMO_CLASS_MAP</font>; com checkpoint fine-tunado, "
        "<font name='Courier' size='9'>demo_mode</font> é false e os rótulos vêm direto do modelo.",
        "body",
    )

    # === 3. Modelo v0 ===
    P("3. Modelo v0 — detalhes técnicos", "h1")
    story.append(make_table([
        ["Atributo", "Valor"],
        ["Arquitetura", "YOLOv8n (Ultralytics)"],
        ["Parâmetros (treináveis)", "3.011.628"],
        ["Parâmetros (após fusão para inferência)", "3.006.428"],
        ["Camadas", "130 (73 após fusão)"],
        ["GFLOPs por inferência", "8,2"],
        ["Tamanho em disco", "6,25 MB (best.pt)"],
        ["Classes (4)", "casca_de_laranja · escorrimento · bolha · water_spotting"],
        ["Origem do pré-treino", "yolov8n.pt (COCO)"],
        ["Dataset de fine-tuning", "baopersonal/paint-defect-detection-lx0xk (Roboflow)"],
        ["Tamanho do dataset", "2.000 imagens (1.600 train / 399 val)"],
        ["Hardware de treino", "Colab T4 GPU (free tier)"],
        ["Epochs", "80 (com early stopping)"],
        ["Image size", "640"],
        ["Batch size", "16"],
        ["Tempo total de treino", "~42 min"],
    ], col_widths=[7 * cm, 10 * cm]))

    # === 4. Métricas ===
    P("4. Métricas v0 (conjunto de validação)", "h1")
    P("Métricas globais", "h2")
    story.append(make_table([
        ["Métrica", "Valor"],
        ["mAP@50", "0,989"],
        ["mAP@50–95", "0,864"],
        ["Precision (média)", "0,970"],
        ["Recall (média)", "0,966"],
    ], col_widths=[7 * cm, 5 * cm]))

    sp()
    P("Por classe (mAP@50)", "h2")
    story.append(make_table([
        ["Classe", "mAP@50", "mAP@50–95", "Instâncias val"],
        ["bolha", "0,985", "0,828", "116"],
        ["casca_de_laranja", "0,995", "0,919", "93"],
        ["escorrimento", "0,992", "0,850", "84"],
        ["water_spotting", "0,987", "0,857", "106"],
    ], col_widths=[5 * cm, 3 * cm, 3 * cm, 4 * cm]))

    sp()
    P(
        "<b>Leitura honesta.</b> O mAP elevado reflete um conjunto de "
        "validação restrito ao mesmo domínio do treino (closeups "
        "industriais com iluminação controlada, do Roboflow Universe). "
        "Em fotos de chassi inteiro com câmera de celular o desempenho "
        "cai sensivelmente — caracterizando lacuna de generalização "
        "(domain gap). É essa lacuna que o ciclo de fine-tuning v1 "
        "pretende reduzir.",
        "body",
    )

    story.append(PageBreak())

    # === 5. Stack tecnológica ===
    P("5. Stack tecnológica", "h1")
    story.append(make_table([
        ["Camada", "Tecnologia", "Hospedagem"],
        ["Frontend", "Next.js 14 + TypeScript + Tailwind", "Vercel"],
        ["Identidade visual", "Inter font · paleta verde sóbria · logo SVG de coroa de louros", "—"],
        ["Backend", "FastAPI + Uvicorn + Pydantic v2", "Hugging Face Spaces (Docker)"],
        ["Inferência", "Ultralytics YOLO (PyTorch)", "Mesmo container"],
        ["Banco", "Supabase Postgres (RLS público read-only)", "Supabase"],
        ["Storage", "Supabase Storage (buckets privados)", "Supabase"],
        ["Modelos", "Hugging Face Hub (repos públicos)", "Hugging Face"],
        ["Treino", "Colab notebook + Ultralytics", "Google Colab T4"],
        ["Versionamento", "Git em GitHub", "github.com/gustavo-dev04/baja"],
        ["Autenticação", "JWT HS256 admin password-based", "Backend"],
        ["CORS", "lista exata + regex (cobre previews Vercel)", "Backend"],
    ], col_widths=[3.5 * cm, 8 * cm, 5.5 * cm]))

    # === 6. Dataset ===
    P("6. Dataset v0", "h1")
    story.append(make_table([
        ["Atributo", "Valor"],
        ["Fonte única", "Roboflow Universe — baopersonal/paint-defect-detection-lx0xk"],
        ["Licença", "CC BY 4.0"],
        ["Imagens totais", "2.000"],
        ["Distribuição por classe", "Balanceada — 500 imagens por classe"],
        ["Splits", "Train 1.600 · Validation 399 · Test 1"],
        ["Resolução", "640×640 (preprocess Roboflow)"],
        ["Anotação", "Bounding boxes YOLO (xywh normalizado)"],
        ["Domínio", "Closeups industriais de superfície pintada"],
        ["Persistência no projeto", "Importado para Supabase via training/import_roboflow.py"],
        ["Dataset id (Supabase)", "paint-defects-pretrain"],
    ], col_widths=[5 * cm, 12 * cm]))

    # === 7. Endpoints ===
    P("7. API pública (contratos preservados em v1)", "h1")
    story.append(make_table([
        ["Método", "Endpoint", "Descrição"],
        ["GET", "/health", "Status + nome do modelo + demo_mode"],
        ["POST", "/inspect", "Recebe multipart com 'file', devolve InspectionResult"],
        ["POST", "/api/v1/auth/admin-token", "Troca senha por JWT (24h)"],
        ["GET", "/api/v1/datasets", "Lista pública de datasets"],
        ["POST", "/api/v1/datasets", "Cria dataset (admin)"],
        ["POST", "/api/v1/datasets/{id}/images", "Upload bulk (até 20, admin)"],
        ["GET", "/api/v1/images/{id}/annotations", "Lista anotações"],
        ["POST", "/api/v1/images/{id}/annotations", "Replace-all (admin)"],
    ], col_widths=[2.5 * cm, 7 * cm, 7.5 * cm]))

    sp()
    P("Formato da resposta /inspect (resumido)", "h2")
    P(
        '{"detections": [{"label": "casca_de_laranja", "raw_label": '
        '"casca_de_laranja", "confidence": 0.95, "bbox": [x1,y1,x2,y2]}], '
        '"image_size": [w,h], "inference_ms": 66.0, "model": '
        '"hf://Guguinhaxd/baja-paint-models/best.pt", "demo_mode": false}',
        "code",
    )

    # === 8. Limitações ===
    P("8. Limitações conhecidas (gaps que v1 atacará)", "h1")
    story.append(make_table([
        ["Limitação", "Causa", "Plano para v1"],
        ["Apenas 4 classes detectadas",
         "Dataset v0 só tinha 4 classes nomeadas",
         "Expandir para 8 classes via união curada de 6 datasets"],
        ["Generalização ruim para fotos zoom-out",
         "Dataset v0 é só closeup industrial",
         "Adicionar fotos próprias do chassi BAJA na Fase 3"],
        ["Sem persistência de inspeções",
         "Handler /inspect não grava no banco",
         "Adicionar persistência após v1 estar estável"],
        ["replace_annotations não transacional",
         "Supabase SDK sem suporte a transações explícitas",
         "Migrar para Postgres function (RPC) se virar problema"],
        ["@app.on_event deprecated",
         "FastAPI moveu para lifespan",
         "Migrar para context manager lifespan"],
        ["3 classes do schema sem treino",
         "falha_cobertura, risco, oxidacao sem dataset",
         "v1 cobre risco e oxidacao via car-paint-damage; falha_cobertura precisa de fotos próprias"],
    ], col_widths=[4.5 * cm, 5.5 * cm, 7 * cm]))

    # === 9. Próximo (v1) ===
    P("9. O que muda em v1 (fine-tuning planejado)", "h1")
    story.append(make_table([
        ["Aspecto", "v0 (este snapshot)", "v1 (próximo)"],
        ["Arquitetura", "YOLOv8n", "YOLO11s"],
        ["Parâmetros", "3,0 M", "9,0 M"],
        ["Classes", "4", "8"],
        ["Fontes de dataset", "1 (lx0xk)", "6 curadas com dedup cross-source"],
        ["Receita de treino",
         "default Ultralytics",
         "cosine LR + MixUp + CopyPaste + warmup + close_mosaic + oversampling de raras"],
        ["Avaliação",
         "mAP simples no val",
         "TTA + matriz de confusão + per-class no test split"],
        ["Tracking", "logs stdout", "Weights & Biases opcional"],
        ["Pipeline location", "training/", "training/v2/"],
        ["Modelo no Hub", "Guguinhaxd/baja-paint-models", "Guguinhaxd/magnus-v2"],
        ["mAP@50 esperado",
         "0,989 (dataset de validação restrito)",
         "0,80–0,90 (mais classes, mais difícil — número honesto)"],
    ], col_widths=[3.5 * cm, 6 * cm, 7.5 * cm]))

    sp()
    P("Insight metodológico", "h2")
    P(
        "Auditoria de 13 datasets públicos identificou que <b>~68% do "
        "volume aparente é ruído de domínio</b> (carros capotados, "
        "amassados, rodas) ou augmentation embutido (3× por imagem-"
        "fonte). O pool útil curado é de ~3.000–5.500 imagens, "
        "dependendo do overlap entre versões do mesmo autor. A "
        "contribuição científica defensável de v1 não é <i>volume</i> "
        "mas <i>curadoria</i>: demonstrar que dataset pequeno e bem "
        "rotulado supera dataset grande e ruidoso.",
        "body",
    )

    # === 10. Referências ===
    P("10. Referências de código (commits-âncora)", "h1")
    P(
        "Branch ativa: <font name='Courier' size='9'>claude/paint-inspection-ai-FRk8g</font><br/>"
        "Repositório: <font name='Courier' size='9'>github.com/gustavo-dev04/baja</font>",
        "body",
    )
    story.append(make_table([
        ["Componente", "Arquivos principais"],
        ["Inferência (hf:// scheme)", "backend/app/inference.py · backend/app/core/config.py"],
        ["Routers da API", "backend/app/routers/{inspect,auth,datasets,images,annotations}.py"],
        ["Auth JWT", "backend/app/core/auth.py"],
        ["UI Magnus", "frontend/app/page.tsx · components/Logo.tsx · components/ResultsPanel.tsx"],
        ["Pipeline v0 (treinou este modelo)", "training/import_roboflow.py · training/train_yolo.py"],
        ["Pipeline v1 (próximo treino)", "training/v2/{config,build_dataset,train,evaluate}.py"],
        ["Schema do banco", "supabase/migrations/0001_init.sql"],
        ["Deploy", "DEPLOY.md · backend/Dockerfile"],
    ], col_widths=[5 * cm, 12 * cm]))

    # === Footer info ===
    sp(20)
    P(
        f"Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        "Documento auto-suficiente, destinado a outro projeto Claude "
        "Code que registrará a progressão entre versões do Magnus.",
        "small",
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return path


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "magnus_v0_snapshot.pdf"
    build_pdf(out_path)
    print(f"✅ PDF gerado: {out_path}")
    print(f"   {out_path.stat().st_size:,} bytes")
