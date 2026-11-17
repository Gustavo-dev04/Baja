// Gera "Material_Relatorio_ScanParts.docx": figuras com legenda/fonte ABNT + referências NBR 6023.
// Uso: node gerar_material.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, HeadingLevel, LevelFormat, PageBreak,
} = require("docx");

const AQUI = __dirname;
const IMGS = path.join(AQUI, "imagens");
const CM = 567;
const LARG = 600; // px (~16 cm)

function runs(texto, base = {}) {
  return texto.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).filter(Boolean).map((p) =>
    p.startsWith("**") ? new TextRun({ ...base, text: p.slice(2, -2), bold: true })
      : p.startsWith("*") ? new TextRun({ ...base, text: p.slice(1, -1), italics: true })
      : new TextRun({ ...base, text: p }));
}
const par = (t, o = {}) => new Paragraph({ alignment: o.al || AlignmentType.JUSTIFIED, spacing: { line: 360, after: o.after ?? 120 }, children: runs(t, o.run || {}) });
const titulo = (t, nivel = HeadingLevel.HEADING_1, quebra = false) => new Paragraph({ heading: nivel, pageBreakBefore: quebra, children: [new TextRun(t)] });

// ------------------------------------------------------------------ FIGURAS
const AUT = "Elaborado pelos autores (2026).";
const FIGURAS = [
  ["fig01_fluxo_scanparts.png", "Fluxo de engenharia reversa do ScanParts", AUT, "Introdução ou Materiais e métodos (visão geral do sistema)"],
  ["fig02_bancada_v5_isometrica.jpg", "Modelo 3D da bancada do ScanParts (versão 5) – vista isométrica", "Elaborado pelos autores (2026), no software Autodesk Fusion.", "Materiais e métodos (hardware)"],
  ["fig03_bancada_v5_lateral.jpg", "Modelo 3D da bancada do ScanParts (versão 5) – vista lateral", "Elaborado pelos autores (2026), no software Autodesk Fusion.", "Materiais e métodos (hardware)"],
  ["fig04_taxonomia_mvs_li_et_al_2026.png", "Classificação dos métodos de reconstrução 3D por múltiplas vistas (MVS)", "Li, Vosselman e Nex (2026). Licença CC BY 4.0.", "Fundamentação teórica (reconstrução 3D a partir de imagens)"],
  ["fig05_exemplos_sinteticos.jpg", "Exemplos de imagens sintéticas com os furos rotulados automaticamente", AUT, "Materiais e métodos (gerador de dados sintéticos)"],
  ["fig06_v1_rotulos_vs_previsoes.jpg", "Rótulos (esquerda) e previsões do modelo v1 (direita) em imagens sintéticas de validação", AUT, "Resultados (treino v1)"],
  ["fig07_v1_curvas_treino.jpg", "Curvas de perda e métricas ao longo das 12 épocas do treino v1", "Elaborado pelos autores (2026), gerado pela biblioteca Ultralytics.", "Resultados (treino v1) ou apêndice"],
  ["fig08_v2_curvas_treino.jpg", "Curvas de perda e métricas ao longo das 80 épocas do treino v2", "Elaborado pelos autores (2026), gerado pela biblioteca Ultralytics.", "Resultados (treino v2)"],
  ["fig09_v2_previsoes_sinteticas.jpg", "Previsões do modelo v2 em imagens sintéticas", AUT, "Resultados (treino v2). As versões separadas estão em fig09a, fig09b e fig09c"],
  ["fig10_teste_real_porcas.jpg", "Detecções do modelo v1 em fotografias reais de porcas e parafusos", "Elaborado pelos autores (2026), sobre imagens do conjunto Mechanical Parts (CAKIR, [2023?]).", "Resultados (teste em fotografias reais). Versões separadas: fig10a e fig10b"],
];
const TAM = {};
const { execSync } = require("child_process");
for (const [f] of FIGURAS) {
  const out = execSync(`python3 -c "from PIL import Image;im=Image.open('${path.join(IMGS, f)}');print(im.size[0],im.size[1])"`).toString().trim().split(" ");
  TAM[f] = { w: +out[0], h: +out[1] };
}
const figuras = FIGURAS.flatMap(([arq, tit, fonte, onde], i) => {
  const { w, h } = TAM[arq];
  const larg = h / w > 0.7 ? 480 : LARG;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 360, after: 120, line: 240 },
      children: [new TextRun({ text: `Figura ${i + 1} – `, bold: true, size: 20 }), new TextRun({ text: tit, size: 20 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 0 },
      children: [new ImageRun({ type: arq.endsWith(".png") ? "png" : "jpg", data: fs.readFileSync(path.join(IMGS, arq)),
        transformation: { width: larg, height: Math.round((larg * h) / w) }, altText: { title: tit, description: tit, name: arq } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60, line: 240 },
      children: [new TextRun({ text: "Fonte: ", size: 20 }), ...runs(fonte, { size: 20 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240, line: 240 },
      children: [new TextRun({ text: `Arquivo: imagens/${arq}  ·  Onde usar: ${onde}`, size: 16, color: "666666", italics: true })] }),
  ];
});

// ------------------------------------------------------------------ REFERÊNCIAS (NBR 6023)
const CITADAS = [
  "BRADSKI, G. The OpenCV library. **Dr. Dobb's Journal of Software Tools**, [*s. l.*], v. 25, n. 11, p. 120-125, 2000.",
  "CAKIR, M. **Mechanical Parts Dataset**. [*S. l.*]: Roboflow Universe, [2023?]. Disponível em: https://universe.roboflow.com/mazhar-cakir/mechanical-parts. Acesso em: 14 nov. 2026.",
  "EVERINGHAM, M. *et al.* The PASCAL Visual Object Classes (VOC) challenge. **International Journal of Computer Vision**, [*s. l.*], v. 88, n. 2, p. 303-338, 2010.",
  "JOCHER, G.; QIU, J. **Ultralytics YOLO11**. Versão 11.0.0. [*S. l.*]: Ultralytics, 2024. Disponível em: https://github.com/ultralytics/ultralytics. Acesso em: 14 nov. 2026.",
  "LI, Y.; VOSSELMAN, G.; NEX, F. **A comparison of multi-view stereo methods for photogrammetric 3D reconstruction**: from traditional to learning-based approaches. arXiv:2604.10246, 2026. Disponível em: https://arxiv.org/abs/2604.10246. Acesso em: 14 nov. 2026.",
  "LIN, H. *et al.* **Depth Anything 3**: recovering the visual space from any views. arXiv:2511.10647, 2025. Disponível em: https://arxiv.org/abs/2511.10647. Acesso em: 14 nov. 2026.",
  "LIN, T.-Y. *et al.* Microsoft COCO: common objects in context. *In*: EUROPEAN CONFERENCE ON COMPUTER VISION, 13., 2014, Zurique. **Proceedings** [...]. Cham: Springer, 2014. p. 740-755.",
  "NVIDIA. **NVIDIA Jetson Orin**. Santa Clara: NVIDIA, [2024?]. Disponível em: https://www.nvidia.com/pt-br/autonomous-machines/embedded-systems/jetson-orin/. Acesso em: 14 nov. 2026.",
  "PADILLA, R.; NETTO, S. L.; SILVA, E. A. B. A survey on performance metrics for object-detection algorithms. *In*: INTERNATIONAL CONFERENCE ON SYSTEMS, SIGNALS AND IMAGE PROCESSING, 27., 2020, Niterói. **Proceedings** [...]. Niterói: IEEE, 2020. p. 237-242.",
  "RAJA, V.; FERNANDES, K. J. (ed.). **Reverse engineering**: an industrial perspective. London: Springer, 2008.",
  "REDMON, J. *et al.* You only look once: unified, real-time object detection. *In*: IEEE CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION, 2016, Las Vegas. **Proceedings** [...]. Las Vegas: IEEE, 2016. p. 779-788.",
  "SEEED STUDIO. **Deploy Depth Anything V3 on Jetson AGX Orin**. [*S. l.*]: Seeed Studio Wiki, [2026?]. Disponível em: https://wiki.seeedstudio.com/deploy_depth_anything_v3_jetson_agx_orin/. Acesso em: 14 nov. 2026.",
  "TOBIN, J. *et al.* Domain randomization for transferring deep neural networks from simulation to the real world. *In*: IEEE/RSJ INTERNATIONAL CONFERENCE ON INTELLIGENT ROBOTS AND SYSTEMS, 2017, Vancouver. **Proceedings** [...]. Vancouver: IEEE, 2017. p. 23-30.",
  "VÁRADY, T.; MARTIN, R. R.; COX, J. Reverse engineering of geometric models: an introduction. **Computer-Aided Design**, [*s. l.*], v. 29, n. 4, p. 255-268, 1997.",
];
const COMPLEMENTARES = [
  "3D SYSTEMS. **Geomagic Design X**. Rock Hill: 3D Systems, [2025?]. Disponível em: https://www.solidworks.com/partner-product/design-x. Acesso em: 14 nov. 2026.",
  "ANTILES, S.; TALATHI, S. **Open Stamped Parts Dataset**. arXiv:2403.10369, 2024. Disponível em: https://arxiv.org/abs/2403.10369. Acesso em: 14 nov. 2026.",
  "CHEN, T. *et al.* **Img2CAD**: conditioned 3D CAD model generation from single image with structured visual geometry. arXiv:2410.03417, 2024. Disponível em: https://arxiv.org/abs/2410.03417. Acesso em: 14 nov. 2026.",
  "DATASONIC. **Jetson Orin Nano 8GB**: IA embarcada. [*S. l.*]: Datasonic, [2025?]. Disponível em: https://blog.datasonic.com.br/jetson-orin-nano-8gb-ia-embarcada/. Acesso em: 14 nov. 2026.",
  "EYEBOX: a cheap, effective 3D scanner for volumetric reconstruction and object recognition. Cambridge: MIT Media Lab, [2002?]. Disponível em: https://acg.media.mit.edu/people/simong/eyebox/index.html. Acesso em: 14 nov. 2026.",
  "GARRIDO-JURADO, S. *et al.* Automatic generation and detection of highly reliable fiducial markers under occlusion. **Pattern Recognition**, [*s. l.*], v. 47, n. 6, p. 2280-2292, 2014.",
  "HARTLEY, R.; ZISSERMAN, A. **Multiple view geometry in computer vision**. 2. ed. Cambridge: Cambridge University Press, 2004.",
  "LI, C. **Holes object detection in industrial scene**. [*S. l.*]: Kaggle, [2023?]. Disponível em: https://www.kaggle.com/datasets/lichengyuan988/holes-object-detection-in-industrial-scene. Acesso em: 14 nov. 2026.",
  "OPENSCAN. **OpenScan**: open source 3D scanner. [*S. l.*]: OpenScan, [2024?]. Disponível em: https://www.openscan.eu. Acesso em: 14 nov. 2026.",
  "REHM, C. **Drill-hole-detection**. [*S. l.*]: Roboflow Universe, [2023?]. Disponível em: https://universe.roboflow.com/corbinian-rehm-master-thesis/drill-hole-detection. Acesso em: 14 nov. 2026.",
  "REVOPOINT. **POP 3 3D scanner**. [*S. l.*]: Revopoint, [2024?]. Disponível em: https://www.revopoint3d.com/products/pop3-3d-scanner. Acesso em: 14 nov. 2026.",
  "RUKHOVICH, D. *et al.* CAD-Recode: reverse engineering CAD code from point clouds. *In*: IEEE/CVF INTERNATIONAL CONFERENCE ON COMPUTER VISION, 2025, Honolulu. **Proceedings** [...]. Honolulu: IEEE, 2025.",
  "SCHÖNBERGER, J. L.; FRAHM, J.-M. Structure-from-motion revisited. *In*: IEEE CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION, 2016, Las Vegas. **Proceedings** [...]. Las Vegas: IEEE, 2016.",
  "SHAPER TOOLS. **Shaper Trace**. [*S. l.*]: Shaper Tools, [2024?]. Disponível em: https://shapertools.com/trace. Acesso em: 14 nov. 2026.",
  "SZELISKI, R. **Computer vision**: algorithms and applications. 2. ed. Cham: Springer, 2022.",
  "WANG, J. *et al.* VGGT: visual geometry grounded transformer. *In*: IEEE/CVF CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION, 2025, Nashville. **Proceedings** [...]. Nashville: IEEE, 2025.",
  "ZHANG, Z. A flexible new technique for camera calibration. **IEEE Transactions on Pattern Analysis and Machine Intelligence**, [*s. l.*], v. 22, n. 11, p. 1330-1334, 2000.",
];
const NORMAS_FERRAMENTAS = [
  "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e documentação: referências: elaboração. Rio de Janeiro: ABNT, 2018.",
  "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10520**: informação e documentação: citações em documentos: apresentação. Rio de Janeiro: ABNT, 2023.",
  "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 10719**: informação e documentação: relatório técnico e/ou científico: apresentação. Rio de Janeiro: ABNT, 2015.",
  "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.",
  "AUTODESK. **Autodesk Fusion**. San Rafael: Autodesk, 2026. Disponível em: https://www.autodesk.com/products/fusion-360. Acesso em: 17 nov. 2026.",
  "GOOGLE. **Google Colaboratory**. Mountain View: Google, 2026. Disponível em: https://colab.research.google.com. Acesso em: 14 nov. 2026.",
  "INTERNATIONAL ORGANIZATION FOR STANDARDIZATION. **ISO 273**: fasteners: clearance holes for bolts and screws. Geneva: ISO, 1979.",
  "INTERNATIONAL ORGANIZATION FOR STANDARDIZATION. **ISO 54**: cylindrical gears for general engineering and for heavy engineering: modules. Geneva: ISO, 1996.",
  "PASZKE, A. *et al.* PyTorch: an imperative style, high-performance deep learning library. *In*: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS, 32., 2019, Vancouver. **Proceedings** [...]. Red Hook: Curran Associates, 2019. p. 8024-8035.",
];
const ref = (r) => new Paragraph({ alignment: AlignmentType.LEFT, spacing: { line: 240, after: 240 }, children: runs(r) });

const CONFERIR = [
  "**Datasonic:** não foi possível abrir a página nesta pesquisa; confirmem o título exato e a data do artigo no próprio site.",
  "**Datas entre colchetes com interrogação** (ex.: [2023?], [2024?]): a página não mostra a data de publicação. A NBR 6023 aceita essa forma; se acharem a data, substituam.",
  "**Img2CAD:** confiram o nome completo do primeiro autor (Chen) no artigo.",
  "**Figura 4:** é uma figura do artigo de Li, Vosselman e Nex (2026), publicada sob licença CC BY 4.0, que permite reproduzir desde que a fonte seja citada. Mantenham a fonte embaixo da figura.",
  "**Figura 10:** usa fotos do conjunto Mechanical Parts, de licença CC BY-NC-SA 4.0 (uso não comercial, citar a fonte).",
  "**Mechanical Parts:** o ano de publicação não está confirmado; o relatório técnico já usa (CAKIR, [2023?]). Se acharem o ano no Roboflow, substituam.",
];

const CITAR = [
  "Citação indireta com autor no fim da frase: \"... técnica conhecida como randomização de domínio (TOBIN *et al.*, 2017).\"",
  "Citação indireta com autor no texto: \"Li, Vosselman e Nex (2026) compararam métodos tradicionais e baseados em aprendizado...\"",
  "Três ou mais autores: use o sobrenome do primeiro seguido de *et al.*, ex.: (REDMON *et al.*, 2016).",
  "Data incerta: (SEEED STUDIO, [2026?]); (NVIDIA, [2024?]).",
];

const doc = new Document({
  creator: "Equipe ScanParts",
  title: "Material para o relatório – figuras e referências",
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 28, bold: true }, paragraph: { spacing: { before: 240, after: 240 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 24, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "marcadores", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 3 * CM, left: 3 * CM, bottom: 2 * CM, right: 2 * CM } } },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "SCANPARTS", bold: true, size: 32 })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: "Material para o relatório: figuras e referências (ABNT)", size: 26 })] }),
      par("Este documento reúne as imagens e as referências usadas no desenvolvimento do projeto até 17/11/2026. As figuras já estão com **legenda acima** e **fonte abaixo**, no padrão da NBR 14724, e as referências seguem a **NBR 6023**, em ordem alfabética. Para usar: copiem a figura com a legenda e a fonte para o relatório e renumerem conforme a ordem em que aparecerem lá. Os arquivos originais, em alta resolução, estão na pasta *imagens/*."),
      titulo("1 Figuras"),
      ...figuras,
      titulo("2 Referências citadas no relatório técnico", HeadingLevel.HEADING_1, true),
      ...CITADAS.map(ref),
      titulo("3 Referências complementares (pesquisa e próximas etapas)"),
      par("Fontes consultadas na pesquisa de mercado (Etapa 1), nos conjuntos de dados avaliados e nas técnicas previstas para as próximas etapas (calibração, reconstrução 3D, scan-to-CAD). Usem conforme o conteúdo que entrar no relatório.", { after: 240 }),
      ...COMPLEMENTARES.map(ref),
      titulo("4 Normas e ferramentas"),
      ...NORMAS_FERRAMENTAS.map(ref),
      titulo("5 Itens a conferir antes de entregar"),
      ...CONFERIR.map((t) => new Paragraph({ numbering: { reference: "marcadores", level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 300, after: 80 }, children: runs(t) })),
      titulo("6 Como citar no texto (NBR 10520)"),
      ...CITAR.map((t) => new Paragraph({ numbering: { reference: "marcadores", level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 300, after: 80 }, children: runs(t) })),
    ],
  }],
});
Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(path.join(AQUI, "Material_Relatorio_ScanParts.docx"), b);
  console.log("ok:", FIGURAS.length, "figuras,", CITADAS.length + COMPLEMENTARES.length + NORMAS_FERRAMENTAS.length, "referências");
});
