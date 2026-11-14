// Gera o relatório técnico do ScanParts em formato ABNT (NBR 10719 / NBR 14724).
// Uso: node gerar_relatorio.js [paginas.json]   -> Relatorio_ScanParts_ABNT.docx
// O build.sh roda duas passagens para preencher os números de página do sumário e das listas.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  HeadingLevel, WidthType, BorderStyle, ShadingType, Header, Footer, PageNumber, LevelFormat,
  PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader, TabStopType,
  VerticalAlign, Tab,
} = require("docx");

const AQUI = __dirname;
const IMG = path.join(AQUI, "..", "img", "ia");
const PAGINAS = process.argv[2] && fs.existsSync(process.argv[2]) ? JSON.parse(fs.readFileSync(process.argv[2])) : {};
const pg = (chave) => (PAGINAS[chave] !== undefined ? String(PAGINAS[chave]) : "0");

// ---------------------------------------------------------------- medidas (DXA)
const CM = 567;
const LARG_TEXTO = 11906 - 3 * CM - 2 * CM; // A4 com margens 3/2 cm
const FONTE = "Arial";

// ---------------------------------------------------------------- texto com *itálico* e **negrito**
function runs(texto, base = {}) {
  const partes = texto.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).filter(Boolean);
  return partes.map((p) => {
    if (p.startsWith("`")) return new TextRun({ ...base, text: p.slice(1, -1), font: "Courier New", size: (base.size || 24) - 2 });
    if (p.startsWith("**")) return new TextRun({ ...base, text: p.slice(2, -2), bold: true });
    if (p.startsWith("*")) return new TextRun({ ...base, text: p.slice(1, -1), italics: true });
    return new TextRun({ ...base, text: p });
  });
}

const corpo = (texto) =>
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, before: 0, after: 0 },
    indent: { firstLine: Math.round(1.25 * CM) },
    children: runs(texto),
  });

const espaco = (n = 1) => Array.from({ length: n }, () => new Paragraph({ spacing: { line: 360 }, children: [] }));

// ---------------------------------------------------------------- alíneas a), b), c)
let instancia = 0;
const alineas = (itens) => {
  instancia += 1;
  return itens.map((t, i) =>
    new Paragraph({
      numbering: { reference: "alineas", level: 0, instance: instancia },
      alignment: AlignmentType.JUSTIFIED,
      spacing: { line: 360, before: 0, after: 0 },
      children: runs(t + (i === itens.length - 1 ? "." : ";")),
    })
  );
};

// ---------------------------------------------------------------- seções e sumário
const SUMARIO = [];
const h1 = (num, titulo) => {
  const texto = num ? `${num} ${titulo.toUpperCase()}` : titulo.toUpperCase();
  SUMARIO.push({ nivel: 1, num, titulo: titulo.toUpperCase(), chave: "h:" + texto });
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: true,
    alignment: num ? AlignmentType.LEFT : AlignmentType.CENTER,
    children: [new TextRun(texto)],
  });
};
const h2 = (num, titulo) => {
  const texto = `${num} ${titulo.toUpperCase()}`;
  SUMARIO.push({ nivel: 2, num, titulo: titulo.toUpperCase(), chave: "h:" + texto });
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(texto)] });
};
const h3 = (num, titulo) => {
  const texto = `${num} ${titulo}`;
  SUMARIO.push({ nivel: 3, num, titulo, chave: "h:" + texto });
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(texto)] });
};

// ---------------------------------------------------------------- ilustrações
const LISTAS = { Figura: [], Quadro: [], Tabela: [] };
const legenda = (tipo, titulo) => {
  const n = LISTAS[tipo].length + 1;
  LISTAS[tipo].push({ n, titulo, chave: `${tipo} ${n} –` });
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    keepNext: true,
    keepLines: true,
    spacing: { before: 240, after: 120, line: 240 },
    children: [
      new TextRun({ text: `${tipo} ${n} – `, bold: true, size: 20 }),
      new TextRun({ text: titulo, size: 20 }),
    ],
  });
};
const fonte = (texto, alinhar = AlignmentType.CENTER) =>
  new Paragraph({
    alignment: alinhar,
    spacing: { before: 60, after: 240, line: 240 },
    children: [new TextRun({ text: "Fonte: ", size: 20 }), ...runs(texto, { size: 20 })],
  });

function figura(titulo, arquivo, largura, fonteTxt, alt) {
  const caminho = path.join(IMG, arquivo);
  const { w, h } = TAMANHOS[arquivo];
  const altura = Math.round((largura * h) / w);
  const tipo = arquivo.endsWith(".png") ? "png" : "jpg";
  return [
    legenda("Figura", titulo),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: true,
      spacing: { before: 0, after: 0 },
      children: [
        new ImageRun({
          type: tipo,
          data: fs.readFileSync(caminho),
          transformation: { width: largura, height: altura },
          altText: { title: titulo, description: alt, name: arquivo },
        }),
      ],
    }),
    fonte(fonteTxt),
  ];
}
const TAMANHOS = {
  "fluxo_scanparts.png": { w: 2400, h: 640 },
  "exemplos_sinteticos.jpg": { w: 1600, h: 800 },
  "v1_rotulos_vs_previsao.jpg": { w: 1400, h: 696 },
  "v2_curvas.jpg": { w: 2000, h: 1000 },
  "v2_previsoes_sinteticas.jpg": { w: 1276, h: 420 },
  "teste_real_porcas_v1.jpg": { w: 848, h: 420 },
};

// tabela (dados numéricos, laterais abertas) ou quadro (texto, todas as bordas)
function grade(tipo, titulo, cab, linhas, largurasCm, fonteTxt, alinhamentos) {
  const total = largurasCm.reduce((a, b) => a + b, 0);
  const larg = largurasCm.map((c) => Math.round((c / total) * LARG_TEXTO));
  larg[larg.length - 1] += LARG_TEXTO - larg.reduce((a, b) => a + b, 0);
  const quadro = tipo === "Quadro";
  const fina = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const grossa = { style: BorderStyle.SINGLE, size: 8, color: "000000" };
  const nada = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const celula = (texto, j, cabecalho) =>
    new TableCell({
      width: { size: larg[j], type: WidthType.DXA },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 50, bottom: 50, left: 90, right: 90 },
      shading: cabecalho && quadro ? { type: ShadingType.CLEAR, color: "auto", fill: "E7E6E6" } : undefined,
      borders: quadro
        ? { top: fina, bottom: fina, left: fina, right: fina }
        : { top: cabecalho ? grossa : nada, bottom: cabecalho ? fina : nada, left: nada, right: nada },
      children: [
        new Paragraph({
          alignment: cabecalho ? AlignmentType.CENTER : (alinhamentos && alinhamentos[j]) || AlignmentType.LEFT,
          keepNext: true, // mantém a tabela inteira (e a fonte) na mesma página
          keepLines: true,
          spacing: { line: 240, before: 0, after: 0 },
          children: runs(texto, { size: 20, bold: cabecalho || undefined }),
        }),
      ],
    });
  const rows = [
    new TableRow({ tableHeader: true, cantSplit: true, children: cab.map((t, j) => celula(t, j, true)) }),
    ...linhas.map((l) => new TableRow({ cantSplit: true, children: l.map((t, j) => celula(t, j, false)) })),
  ];
  const tabela = new Table({
    width: { size: LARG_TEXTO, type: WidthType.DXA },
    columnWidths: larg,
    borders: quadro
      ? { top: fina, bottom: fina, left: fina, right: fina, insideHorizontal: fina, insideVertical: fina }
      : { top: grossa, bottom: grossa, left: nada, right: nada, insideHorizontal: nada, insideVertical: nada },
    rows,
  });
  return [legenda(tipo, titulo), tabela, fonte(fonteTxt, AlignmentType.LEFT)];
}

// equação numerada: centralizada, número à direita
const equacao = (expr, n) =>
  new Paragraph({
    spacing: { before: 120, after: 120, line: 360 },
    tabStops: [
      { type: TabStopType.CENTER, position: Math.round(LARG_TEXTO / 2) },
      { type: TabStopType.RIGHT, position: LARG_TEXTO },
    ],
    children: [new TextRun({ children: [new Tab(), expr, new Tab(), `(${n})`] })],
  });

const codigo = (linhas) =>
  linhas.map(
    (l) =>
      new Paragraph({
        spacing: { line: 240, before: 0, after: 0 },
        indent: { left: Math.round(0.5 * CM) },
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "F2F2F2" },
        children: [new TextRun({ text: l, font: "Courier New", size: 18 })],
      })
  );

// ---------------------------------------------------------------- CONTEÚDO
const DATA_FONTE = "Elaborado pelos autores (2026).";

const textual = [
  // 1 ------------------------------------------------------------------
  h1("1", "Introdução"),
  corpo("A manutenção de máquinas e veículos frequentemente esbarra em peças que não possuem desenho técnico: componentes de equipamentos antigos, peças importadas ou itens descontinuados pelo fabricante. Nesses casos, a peça costuma ser medida manualmente com paquímetro e redesenhada em um sistema CAD, processo lento, dependente da habilidade de quem mede e sujeito a erros, sobretudo em geometrias complexas. A obtenção de um modelo geométrico a partir de um objeto físico existente é o objeto da engenharia reversa (VÁRADY; MARTIN; COX, 1997; RAJA; FERNANDES, 2008)."),
  corpo("O **ScanParts** é um projeto de extensão da FATEC Santo André que propõe um equipamento de bancada de baixo custo para gerar um **modelo CAD editável** de peças mecânicas de até 10 cm, com precisão de ±1 mm, a partir de fotografias. O sistema é baseado no computador embarcado NVIDIA Jetson Orin Nano, em uma câmera IMX219 com lente de 120°, em uma mesa giratória impressa em 3D acionada por motor de passo e em iluminação por anel de LEDs (*ring light*) de 6500 K."),
  corpo("Entre as características geométricas de uma peça mecânica, o **furo** é uma das mais frequentes e a que mais carrega intenção de projeto: o diâmetro de um furo costuma indicar o parafuso ou a rosca para o qual ele foi feito. Por isso, o primeiro módulo de software desenvolvido foi uma rede neural capaz de localizar furos em fotografias. Este relatório documenta o desenvolvimento, o treinamento e os primeiros testes desse módulo."),
  h2("1.1", "Objetivos"),
  h3("1.1.1", "Objetivo geral"),
  corpo("Desenvolver e avaliar um modelo de inteligência artificial capaz de localizar furos em fotografias de peças mecânicas, sem custo de aquisição de dados e com tempo de execução compatível com um computador embarcado."),
  h3("1.1.2", "Objetivos específicos"),
  ...alineas([
    "desenvolver um gerador de imagens sintéticas de peças com furos, com rotulagem automática",
    "treinar um detector de objetos da família YOLO com esses dados, primeiro em CPU e depois em GPU na plataforma Google Colab",
    "avaliar o modelo com as métricas de precisão, *recall* e mAP, comparando-as com a meta de 0,90 definida no projeto",
    "realizar um primeiro teste qualitativo em fotografias reais de peças mecânicas",
    "registrar limitações, problemas encontrados e próximos passos",
  ]),

  // 2 ------------------------------------------------------------------
  h1("2", "Fundamentação teórica"),
  h2("2.1", "Engenharia reversa de peças mecânicas"),
  corpo("A engenharia reversa de modelos geométricos pode ser dividida em quatro etapas: digitalização da peça, processamento dos dados (limpeza, alinhamento e escala), reconstrução do modelo e validação (VÁRADY; MARTIN; COX, 1997). Uma malha triangular obtida por escaneamento cobre apenas as duas primeiras etapas. A engenharia reversa propriamente dita exige reconstruir as características (*features*) da peça, como planos, cilindros e furos, com suas dimensões, de modo que o modelo possa ser editado e fabricado (RAJA; FERNANDES, 2008)."),
  corpo("O ScanParts adota esse entendimento: o objetivo não é produzir uma imagem ou uma malha 3D, mas reconhecer características e suas medidas para gerar um arquivo CAD editável, aberto no Autodesk Fusion 360."),
  h2("2.2", "Reconstrução 3D a partir de imagens"),
  corpo("A reconstrução tridimensional a partir de múltiplas fotografias (*Multi-View Stereo*, MVS) pode ser feita por métodos tradicionais, como o COLMAP, ou por métodos baseados em aprendizado profundo. Li, Vosselman e Nex (2026) compararam essas abordagens em cenas aéreas e concluíram que o modelo VGGT obteve o melhor equilíbrio entre qualidade e tempo, mas que os métodos com aprendizado ainda produzem erros de reconstrução relevantes, como camadas e inconsistências locais, o que limita seu uso em aplicações de alta precisão."),
  corpo("Mais recentemente, o Depth Anything 3 (LIN *et al.*, 2025) passou a estimar, com um único transformador, a profundidade e a pose da câmera a partir de qualquer número de imagens, com ganhos relatados sobre o VGGT em precisão de pose e de geometria. Há exemplos de sua execução no Jetson AGX Orin com TensorRT (SEEED STUDIO, [2026?]). Esse tipo de modelo é candidato ao futuro módulo 3D do ScanParts, mas o AGX Orin tem muito mais memória e capacidade de processamento que o Orin Nano de 8 GB usado no projeto, e a precisão métrica exigida (±1 mm) ainda precisa ser verificada."),
  corpo("Esses métodos entregam nuvens de pontos ou malhas, ou seja, terminam na etapa de digitalização. Essa constatação reforçou a decisão do projeto de concentrar a inteligência artificial no reconhecimento de características (furos), deixando a medição para métodos geométricos clássicos."),
  h2("2.3", "Detecção de objetos com YOLO"),
  corpo("A família YOLO (*You Only Look Once*) trata a detecção de objetos como um único problema de regressão, prevendo de uma só vez as caixas delimitadoras e as classes a partir da imagem inteira, o que permite execução em tempo real (REDMON *et al.*, 2016). Neste trabalho foi utilizada a versão YOLO11 da biblioteca Ultralytics (JOCHER; QIU, 2024), na variante *nano* (YOLO11n), com cerca de 2,6 milhões de parâmetros e 5,5 MB, adequada a dispositivos embarcados."),
  h2("2.4", "Dados sintéticos e randomização de domínio"),
  corpo("Treinar um detector exige milhares de imagens anotadas, cuja produção manual é cara e demorada. Uma alternativa é gerar imagens sintéticas por computador, nas quais a posição de cada objeto é conhecida e o rótulo é produzido automaticamente. Tobin *et al.* (2017) mostraram que, ao variar aleatoriamente a aparência das imagens sintéticas (cores, texturas, iluminação, posição da câmera), o modelo passa a tratar o mundo real como mais uma variação, técnica conhecida como randomização de domínio. A diferença entre imagens sintéticas e reais (*domain gap*) continua sendo o principal risco dessa abordagem."),
  h2("2.5", "Inteligência artificial embarcada"),
  corpo("O NVIDIA Jetson Orin Nano de 8 GB possui GPU com 1.024 núcleos CUDA e 32 núcleos Tensor. No modo original, alcança até 40 TOPS (operações INT8 esparsas) com consumo entre 7 e 15 W; no modo Super, habilitado por atualização de software no kit de desenvolvimento, chega a 67 TOPS (NVIDIA, [2024?]). A execução otimizada de redes neurais nessa plataforma é feita com o TensorRT, que converte um modelo exportado no formato ONNX em um motor específico para a placa. É o mesmo caminho usado na implantação do Depth Anything 3 no Jetson AGX Orin (SEEED STUDIO, [2026?]) e o previsto para o detector de furos deste trabalho."),
  h2("2.6", "Métricas de avaliação"),
  corpo("Uma detecção é considerada correta (verdadeiro positivo, VP) quando a sobreposição entre a caixa prevista e a caixa real, medida pela razão entre a interseção e a união das áreas (IoU), supera um limiar. Detecções sem furo correspondente são falsos positivos (FP), e furos não detectados são falsos negativos (FN). A precisão (P) e o *recall* (R), também chamado de revocação, são dados pelas equações (1) e (2) (PADILLA; NETTO; SILVA, 2020)."),
  equacao("P = VP / (VP + FP)", 1),
  equacao("R = VP / (VP + FN)", 2),
  corpo("A precisão média (AP) resume a curva precisão × *recall* em um único número. O **mAP50** usa IoU mínimo de 0,50, critério do desafio PASCAL VOC (EVERINGHAM *et al.*, 2010), e o **mAP50-95** é a média para limiares de IoU de 0,50 a 0,95, critério do conjunto COCO (LIN *et al.*, 2014), que também cobra caixas bem ajustadas. Neste projeto, adotou-se como meta precisão, *recall* e mAP50 iguais ou superiores a 0,90."),

  // 3 ------------------------------------------------------------------
  h1("3", "Materiais e métodos"),
  h2("3.1", "Visão geral do sistema"),
  corpo("O fluxo de engenharia reversa do ScanParts foi dividido em cinco etapas, apresentadas na Figura 1. Este relatório trata da segunda etapa, a localização dos furos por inteligência artificial."),
  ...figura("Fluxo de engenharia reversa do ScanParts", "fluxo_scanparts.png", 600, DATA_FONTE,
    "Diagrama com cinco etapas em sequência: captura, localização por IA, medição, interpretação e saída em CAD. A etapa de localização está destacada como escopo do relatório."),
  corpo("A divisão de responsabilidades entre a IA, a geometria e as regras de interpretação está no Quadro 1. A IA apenas localiza o furo; a medida precisa é obtida por geometria clássica, que é mais exata e explicável; e a interpretação recupera a intenção de projeto a partir de tabelas de medidas padronizadas."),
  ...grade("Quadro", "Divisão de responsabilidades no tratamento dos furos",
    ["Etapa", "Responsável", "Justificativa"],
    [
      ["Localizar o furo na imagem", "IA (YOLO11n, detecção por caixa)", "Distingue furo de sujeira, sombra e reflexo; acha furos vistos de lado (elipses)"],
      ["Medir centro e diâmetro", "Geometria clássica (OpenCV)", "Ajuste de círculo/elipse com precisão subpixel, explicável"],
      ["Interpretar a medida", "Regra (tabela de medidas padrão)", "Recupera a intenção de projeto, ex.: Ø 9,0 mm → passante para M8"],
    ],
    [4, 4.5, 7.5], DATA_FONTE),
  h2("3.2", "Hardware previsto"),
  corpo("O módulo de IA foi desenvolvido para rodar no hardware do Quadro 2, que ainda está em montagem. Por isso, todos os treinamentos e testes deste relatório foram feitos em computadores convencionais e na nuvem."),
  ...grade("Quadro", "Hardware previsto para o ScanParts",
    ["Componente", "Especificação", "Função"],
    [
      ["NVIDIA Jetson Orin Nano", "Computador embarcado com GPU", "Processamento de imagens e execução da IA"],
      ["Câmera IMX219", "8 MP, lente de 120°, conector CSI de 22 pinos", "Captura das fotografias"],
      ["*Ring light*", "Anel de LEDs, 6500 K", "Luz frontal (mesa) ou luz de fundo (peças planas)"],
      ["Mesa giratória", "Impressa em 3D, motor NEMA 17, driver A4988, Arduino Uno/Nano via USB", "Girar a peça em ângulos conhecidos"],
      ["Suporte da câmera", "Haste impressa com travas em 90° e ~35°", "Posições repetíveis para vista superior e inclinada"],
    ],
    [4, 6.5, 5.5], DATA_FONTE),
  h2("3.3", "Gerador de dados sintéticos"),
  corpo("Para dispensar a anotação manual, foi desenvolvido o programa `gerar_sintetico.py`, em Python com OpenCV (BRADSKI, 2000). Cada imagem, de 640 × 640 pixels, simula uma peça sobre a mesa giratória vista pela câmera com luz frontal. Seguindo o princípio da randomização de domínio, o gerador varia aleatoriamente:"),
  ...alineas([
    "o formato da peça (retângulo, retângulo chanfrado, perfil em L, disco e flange), o material (metal escovado ou plástico), a espessura e a sombra",
    "a quantidade, o tamanho e o tipo dos furos (passantes ou cegos), com parede visível, chanfro e brilho na borda",
    "a perspectiva da câmera, por meio de uma homografia que simula inclinação, giro e distância",
    "distratores que não são furos: reflexo do anel de luz, sujeira, riscos, marcas de centro e marcadores ArUco do prato",
    "o pós-processamento: brilho, contraste, temperatura de cor, vinheta da lente de 120°, ruído, desfoque e compressão JPEG",
  ]),
  corpo("Como a posição de cada furo é conhecida no momento do desenho, o contorno do furo é transformado pela mesma perspectiva e convertido em uma caixa delimitadora no formato YOLO. Furos com menos de 60% da área visível ou menores que 4 pixels são descartados. A geração é paralelizada entre os núcleos do processador. Exemplos estão na Figura 2."),
  ...figura("Exemplos de imagens sintéticas com os furos rotulados automaticamente", "exemplos_sinteticos.jpg", 600, DATA_FONTE,
    "Oito imagens sintéticas de peças metálicas e plásticas sobre fundos variados, com caixas verdes nos furos e distratores sem rótulo."),
  h2("3.4", "Fontes de dados externas"),
  corpo("Foram avaliados conjuntos de dados públicos para complementar os dados sintéticos (Quadro 3). Nenhum deles foi usado no treinamento até o momento: a maioria não marca furos ou tem licença não confirmada. O conjunto Mechanical Parts foi usado apenas para teste."),
  ...grade("Quadro", "Conjuntos de dados públicos avaliados",
    ["Conjunto", "Tamanho", "Rótulo", "Licença", "Uso"],
    [
      ["drill-hole-detection (Roboflow)", "260 imagens", "Caixa (furo)", "CC BY 4.0", "Candidato ao treino"],
      ["Holes Object Detection (Kaggle)", "493 imagens", "Caixa (furo)", "Não confirmada", "Não usar até verificar"],
      ["Open Stamped Parts", "1.680 rotuladas", "Máscaras (chapa estampada)", "A verificar", "Candidato"],
      ["Mechanical Parts (Roboflow)", "2.249 imagens", "Peça inteira (não marca furos)", "CC BY-NC-SA 4.0", "Somente teste"],
    ],
    [4.5, 2.6, 3.6, 2.8, 3], DATA_FONTE),
  corpo("O conjunto Mechanical Parts exige cuidado: porcas, rolamentos e engrenagens têm furo, mas o furo não está rotulado. Se essas imagens entrassem no treino, o modelo aprenderia que um furo não é furo."),
  h2("3.5", "Procedimento de treinamento"),
  corpo("Foram realizados dois treinamentos, ambos partindo do YOLO11n pré-treinado no conjunto COCO, com uma única classe (`furo`), detecção por caixa delimitadora e aumento de dados por espelhamento horizontal e vertical, rotação de ±15° e mosaico (padrão da biblioteca). O treino v1 serviu de referência rápida em CPU; o v2 foi o treino completo em GPU no Google Colab. As configurações estão na Tabela 1."),
  ...grade("Tabela", "Configuração dos treinamentos",
    ["Parâmetro", "v1 (referência)", "v2 (completo)"],
    [
      ["Ambiente", "CPU, 4 núcleos (Intel Xeon 2,1 GHz)", "Google Colab, GPU NVIDIA L4 (22 GB)"],
      ["Imagens de treino / validação", "1.500 / 300", "3.000 / 500"],
      ["Furos rotulados (total)", "6.331", "15.007"],
      ["Resolução de entrada", "416 px", "640 px"],
      ["Épocas", "12", "80"],
      ["Tamanho do lote", "16", "32"],
      ["Otimizador", "AdamW (automático)", "AdamW (automático)"],
      ["Tempo de treinamento", "25 min", "26 min"],
      ["Biblioteca", "Ultralytics 8.4.212", "Ultralytics 8.4.212"],
    ],
    [5.5, 5.25, 5.25], DATA_FONTE, [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER]),
  h2("3.6", "Procedimento de teste em fotografias reais"),
  corpo("Para uma primeira verificação fora do domínio sintético, o modelo v1 foi aplicado a 30 imagens sorteadas (semente 0) entre as 2.249 do conjunto Mechanical Parts, com confiança mínima de 0,40. Como esse conjunto não marca furos, a avaliação foi apenas qualitativa: contagem de detecções e inspeção visual."),
  h2("3.7", "Artefatos de software"),
  corpo("O código está no repositório público do projeto (github.com/Gustavo-dev04/Baja), na pasta `ia/`. O Quadro 4 lista os artefatos produzidos."),
  ...grade("Quadro", "Artefatos de software produzidos",
    ["Arquivo", "Função", "Situação"],
    [
      ["ia/gerar_sintetico.py", "Gera imagens sintéticas rotuladas", "Concluído e testado"],
      ["ia/juntar_datasets.py", "Junta conjuntos de dados na classe única furo", "Concluído e testado"],
      ["ia/treino_furos_colab.ipynb", "Treino, avaliação e exportação no Google Colab", "Concluído (usado no v2)"],
      ["ia/modelos/furos_v1.pt", "Pesos do modelo v1 (5,5 MB)", "Publicado"],
      ["Pesos do modelo v2 (best.pt)", "Melhor modelo atual", "No Google Drive; a publicar"],
      ["Calibração, modo 2D, mesa, interface", "Demais módulos do ScanParts", "Não iniciados"],
    ],
    [5.5, 6.5, 4], DATA_FONTE),

  // 4 ------------------------------------------------------------------
  h1("4", "Resultados"),
  h2("4.1", "Treinamento de referência (v1)"),
  corpo("O treino v1 alcançou precisão de 0,909, *recall* de 0,828, mAP50 de 0,889 e mAP50-95 de 0,475 na validação sintética, com inferência de 16 ms por imagem em CPU. A Figura 3 compara os rótulos com as previsões. O modelo aprendeu o conceito de furo e ignorou os reflexos do anel de luz, mas errou mais nos furos muito pequenos: 23% dos furos da validação tinham menos de 10 pixels. As métricas ainda subiam na última época, indicando que mais treino traria ganho."),
  ...figura("Rótulos (esquerda) e previsões do modelo v1 (direita) em imagens sintéticas de validação", "v1_rotulos_vs_previsao.jpg", 600, DATA_FONTE,
    "Dois mosaicos de 16 imagens sintéticas: à esquerda os rótulos, à direita as previsões com nível de confiança."),
  h2("4.2", "Treinamento completo no Google Colab (v2)"),
  corpo("O treino v2 durou 26 minutos na GPU NVIDIA L4 e atingiu a meta do projeto nas três métricas principais (Tabela 2). Em relação ao v1, o *recall* subiu de 0,828 para 0,928 e o mAP50-95 de 0,475 para 0,760, efeito do maior volume de dados, da resolução de 640 pixels e do maior número de épocas, que favoreceram principalmente os furos pequenos."),
  ...grade("Tabela", "Resultados na validação sintética",
    ["Métrica", "v1", "v2", "Meta"],
    [
      ["Precisão", "0,909", "**0,940**", "≥ 0,90"],
      ["*Recall*", "0,828", "**0,928**", "≥ 0,90"],
      ["mAP50", "0,889", "**0,971**", "≥ 0,90"],
      ["mAP50-95", "0,475", "**0,760**", "–"],
      ["Inferência por imagem", "16 ms (CPU)", "1,7 ms (GPU L4)", "< 1 s (Jetson)"],
    ],
    [5.5, 3.5, 3.5, 3.5], DATA_FONTE, [AlignmentType.LEFT, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER]),
  corpo("As curvas de treinamento (Figura 4) mostram que as perdas de validação caíram junto com as de treino até o fim, sem sinal de sobreajuste. O mAP50 estabilizou em torno de 0,97 a partir da época 50, o que indica que mais épocas sobre os mesmos dados sintéticos trariam pouco ganho. O salto nas perdas de treino na época 71 é esperado: a biblioteca desliga o aumento por mosaico nas últimas dez épocas."),
  ...figura("Curvas de perda e métricas ao longo das 80 épocas do treino v2", "v2_curvas.jpg", 600, "Elaborado pelos autores (2026), gerado pela biblioteca Ultralytics.",
    "Dez gráficos: perdas de caixa, classe e distribuição em treino e validação, e precisão, recall, mAP50 e mAP50-95 por época."),
  corpo("A Figura 5 mostra previsões do v2. Na imagem da direita, a peça em L possui apenas manchas de sujeira e nenhuma detecção foi feita, comportamento correto."),
  ...figura("Previsões do modelo v2 em imagens sintéticas", "v2_previsoes_sinteticas.jpg", 600, DATA_FONTE,
    "Três imagens sintéticas: duas peças com furos detectados com confiança entre 0,85 e 0,90 e uma peça em L com sujeira, sem detecções."),
  h2("4.3", "Teste em fotografias reais"),
  corpo("O resultado do teste com o modelo v1 no conjunto Mechanical Parts está no Quadro 5 e na Figura 6."),
  ...grade("Quadro", "Teste do modelo v1 em fotografias reais",
    ["Item", "Valor"],
    [
      ["Conjunto", "Mechanical Parts: 2.249 imagens de porcas, parafusos, rolamentos e engrenagens"],
      ["Amostra", "30 imagens sorteadas (semente 0)"],
      ["Confiança mínima", "0,40"],
      ["Detecções", "108 (3,6 por imagem)"],
      ["Confiança nos furos das porcas", "0,70 a 0,81"],
    ],
    [5, 11], DATA_FONTE),
  ...figura("Detecções do modelo v1 em fotografias reais de porcas e parafusos", "teste_real_porcas_v1.jpg", 520,
    "Elaborado pelos autores (2026), sobre imagens do conjunto Mechanical Parts (CAKIR, 2023).",
    "Duas fotografias de porcas e parafusos sobre um prato branco, com caixas azuis marcadas como furo em volta das porcas."),
  corpo("Mesmo sem ter sido treinado com nenhuma fotografia real, o modelo encontrou os furos das porcas com confiança entre 0,70 e 0,81 e não marcou os parafusos, que não têm furo visível. Por outro lado, as caixas envolveram a porca inteira, e não apenas o furo. Não foi possível calcular precisão e *recall*, pois o conjunto não marca os furos."),
  h2("4.4", "Problemas encontrados e correções"),
  corpo("Durante o desenvolvimento foram encontrados os problemas do Quadro 6, todos corrigidos."),
  ...grade("Quadro", "Problemas encontrados e correções aplicadas",
    ["Problema", "Causa", "Correção"],
    [
      ["Borda quadrada e cópias espelhadas da peça, sem rótulo, nas imagens sintéticas", "Preenchimento da borda por reflexão", "Borda preenchida com textura de fundo, sem cópias"],
      ["Erro ao testar o modelo no Colab com o arquivo compactado", "O arquivo .zip foi passado como se fosse uma imagem", "Célula que descompacta e localiza as imagens automaticamente"],
      ["Modelo não encontrado no Colab", "Arquivo de pesos ausente em /content", "Pesos publicados no repositório e baixados por wget"],
      ["Célula de continuação iniciou um treino no conjunto coco8", "Continuação executada após o treino já ter terminado", "A célula verifica se o treino terminou e não faz nada nesse caso"],
    ],
    [5.5, 5, 5.5], DATA_FONTE),

  // 5 ------------------------------------------------------------------
  h1("5", "Discussão"),
  corpo("Os resultados mostram que um detector pequeno, treinado apenas com dados sintéticos gerados sem custo, aprende o conceito de furo e o diferencia de distratores como sujeira e reflexos. As metas de precisão, *recall* e mAP50 foram atingidas, e o tempo de inferência de 1,7 ms por imagem em GPU indica folga para a meta de menos de 1 segundo no Jetson Orin Nano, a ser confirmada no aparelho."),
  corpo("Esses números, porém, foram medidos em imagens sintéticas e não representam o desempenho no uso real. O teste com fotografias reais confirmou que o modelo generaliza parcialmente, mas revelou a diferença de domínio prevista por Tobin *et al.* (2017): as caixas ficam maiores que o furo. Para o ScanParts isso importa, porque a etapa de medição procura o círculo dentro da caixa. As principais limitações atuais são:"),
  ...alineas([
    "ausência de uma nota em fotografias reais, pois nenhum conjunto público disponível marca os furos",
    "caixas maiores que o furo em fotografias reais",
    "nenhuma imagem capturada pela câmera do projeto (IMX219 com *ring light*) foi usada até o momento",
    "o teste real foi feito com o modelo v1, e não com o v2",
    "o conjunto Mechanical Parts tem licença não comercial (CC BY-NC-SA 4.0)",
  ]),

  // 6 ------------------------------------------------------------------
  h1("6", "Considerações finais"),
  corpo("O primeiro módulo de software do ScanParts, a localização de furos por inteligência artificial, foi desenvolvido, treinado e testado sem custo. O gerador de dados sintéticos e o notebook de treino no Google Colab formam um fluxo reproduzível, e o modelo v2 superou a meta de 0,90 em precisão, *recall* e mAP50 nos dados sintéticos, com inferência rápida o suficiente para um computador embarcado."),
  corpo("O próximo passo decisivo é medir o desempenho em fotografias reais. As etapas planejadas são:"),
  ...alineas([
    "publicar os pesos do modelo v2 no repositório e repetir o teste em fotografias reais com ele",
    "anotar os furos de cerca de 100 fotografias reais na ferramenta CVAT, obtendo a primeira nota real",
    "treinar o modelo v3 com dados sintéticos e reais combinados",
    "montar um conjunto de teste fixo com fotografias da IMX219 e do *ring light* assim que a bancada estiver pronta",
    "iniciar os demais módulos: calibração da câmera e geração de DXF a partir de peças planas",
    "avaliar o Depth Anything 3 no Jetson Orin Nano como base do módulo de peças gerais (3D)",
  ]),
];

// ---------------------------------------------------------------- referências (NBR 6023)
const REFS = [
  "BRADSKI, G. The OpenCV library. **Dr. Dobb's Journal of Software Tools**, [*s. l.*], v. 25, n. 11, p. 120-125, 2000.",
  "CAKIR, M. **Mechanical Parts Dataset**. [*S. l.*]: Roboflow Universe, 2023. Disponível em: https://universe.roboflow.com/mazhar-cakir/mechanical-parts. Acesso em: 14 nov. 2026.",
  "EVERINGHAM, M. *et al.* The PASCAL Visual Object Classes (VOC) challenge. **International Journal of Computer Vision**, [*s. l.*], v. 88, n. 2, p. 303-338, 2010.",
  "JOCHER, G.; QIU, J. **Ultralytics YOLO11**. Versão 11.0.0. [*S. l.*]: Ultralytics, 2024. Disponível em: https://github.com/ultralytics/ultralytics. Acesso em: 14 nov. 2026.",
  "LI, Y.; VOSSELMAN, G.; NEX, F. **A comparison of multi-view stereo methods for photogrammetric 3D reconstruction**: from traditional to learning-based approaches. arXiv:2604.10246, 2026. Disponível em: https://arxiv.org/abs/2604.10246. Acesso em: 14 nov. 2026.",
  "LIN, H. *et al.* **Depth Anything 3**: recovering the visual space from any views. arXiv:2511.10647, 2025. Trabalho aceito na International Conference on Learning Representations (ICLR 2026). Disponível em: https://arxiv.org/abs/2511.10647. Acesso em: 14 nov. 2026.",
  "LIN, T.-Y. *et al.* Microsoft COCO: common objects in context. *In*: EUROPEAN CONFERENCE ON COMPUTER VISION, 13., 2014, Zurique. **Proceedings** [...]. Cham: Springer, 2014. p. 740-755.",
  "NVIDIA. **NVIDIA Jetson Orin**. Santa Clara: NVIDIA, [2024?]. Disponível em: https://www.nvidia.com/pt-br/autonomous-machines/embedded-systems/jetson-orin/. Acesso em: 14 nov. 2026.",
  "PADILLA, R.; NETTO, S. L.; SILVA, E. A. B. A survey on performance metrics for object-detection algorithms. *In*: INTERNATIONAL CONFERENCE ON SYSTEMS, SIGNALS AND IMAGE PROCESSING, 27., 2020, Niterói. **Proceedings** [...]. Niterói: IEEE, 2020. p. 237-242.",
  "RAJA, V.; FERNANDES, K. J. (ed.). **Reverse engineering**: an industrial perspective. London: Springer, 2008.",
  "REDMON, J. *et al.* You only look once: unified, real-time object detection. *In*: IEEE CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION, 2016, Las Vegas. **Proceedings** [...]. Las Vegas: IEEE, 2016. p. 779-788.",
  "SEEED STUDIO. **Deploy Depth Anything V3 on Jetson AGX Orin**. [*S. l.*]: Seeed Studio Wiki, [2026?]. Disponível em: https://wiki.seeedstudio.com/deploy_depth_anything_v3_jetson_agx_orin/. Acesso em: 14 nov. 2026.",
  "TOBIN, J. *et al.* Domain randomization for transferring deep neural networks from simulation to the real world. *In*: IEEE/RSJ INTERNATIONAL CONFERENCE ON INTELLIGENT ROBOTS AND SYSTEMS, 2017, Vancouver. **Proceedings** [...]. Vancouver: IEEE, 2017. p. 23-30.",
  "VÁRADY, T.; MARTIN, R. R.; COX, J. Reverse engineering of geometric models: an introduction. **Computer-Aided Design**, [*s. l.*], v. 29, n. 4, p. 255-268, 1997.",
];
const posTextual = [
  h1(null, "Referências"),
  ...REFS.map(
    (r) =>
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { line: 240, before: 0, after: 240 },
        children: runs(r),
      })
  ),
  h1(null, "Apêndice A – Como reproduzir o treinamento"),
  corpo("O treinamento pode ser reproduzido no Google Colab abrindo o notebook `ia/treino_furos_colab.ipynb` do repositório e executando as células em ordem, com a GPU ativada. Em um computador com Python, os comandos equivalentes são:"),
  ...espaco(1),
  ...codigo([
    "pip install ultralytics opencv-python-headless",
    "python ia/gerar_sintetico.py --saida dados/sintetico --treino 3000 --val 500",
    "python ia/juntar_datasets.py --destino dados/final dados/sintetico",
    "yolo detect train data=dados/final/data.yaml model=yolo11n.pt \\",
    "     epochs=80 imgsz=640 batch=32 fliplr=0.5 flipud=0.5 degrees=15",
  ]),
  ...espaco(1),
  corpo("Os resultados de cada treino são registrados no arquivo `docs/resultados-ia.md` do repositório."),
];

// ---------------------------------------------------------------- PRÉ-TEXTUAIS
const centro = (texto, opts = {}) =>
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: 360, before: opts.antes || 0, after: 0 },
    children: [new TextRun({ text: texto, bold: !!opts.negrito, size: opts.tam || 24 })],
  });
const tituloPre = (texto) =>
  new Paragraph({
    alignment: AlignmentType.CENTER,
    pageBreakBefore: true,
    spacing: { before: 0, after: 360, line: 360 },
    children: [new TextRun({ text: texto, bold: true })],
  });

const AUTORES = ["NOME DO INTEGRANTE 1", "NOME DO INTEGRANTE 2", "NOME DO INTEGRANTE 3", "NOME DO INTEGRANTE 4"];
const TITULO = "SCANPARTS";
const SUBTITULO = "detecção de furos por inteligência artificial para engenharia reversa de peças mecânicas";

const capa = [
  centro("FACULDADE DE TECNOLOGIA DE SANTO ANDRÉ", { negrito: true }),
  centro("CURSO SUPERIOR DE TECNOLOGIA EM MECATRÔNICA INDUSTRIAL", { negrito: true }),
  ...AUTORES.map((a, i) => centro(a, { antes: i === 0 ? 2400 : 0 })),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 3200, after: 0, line: 360 },
    children: [new TextRun({ text: TITULO + ":", bold: true, size: 28 })],
  }),
  centro(SUBTITULO.charAt(0).toUpperCase() + SUBTITULO.slice(1), { tam: 24 }),
];
const localAno = () =>
  new Footer({ children: [centro("SANTO ANDRÉ", { negrito: true }), centro("2026", { negrito: true })] });

const rosto = [
  ...AUTORES.map((a) => centro(a)),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 3000, after: 0, line: 360 },
    children: [new TextRun({ text: TITULO + ":", bold: true, size: 28 })],
  }),
  centro(SUBTITULO.charAt(0).toUpperCase() + SUBTITULO.slice(1)),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 8 * CM },
    spacing: { before: 1800, after: 240, line: 240 },
    children: [
      new TextRun({
        text: "Relatório técnico apresentado à Faculdade de Tecnologia de Santo André, como parte das atividades do Projeto de Extensão do Curso Superior de Tecnologia em Mecatrônica Industrial, referente ao módulo de inteligência artificial do projeto ScanParts.",
        size: 20,
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.LEFT,
    indent: { left: 8 * CM },
    spacing: { before: 0, after: 0, line: 240 },
    children: [new TextRun({ text: "Orientador: Prof. [Nome do orientador]", size: 20 })],
  }),
];

const RESUMO =
  "Este relatório apresenta o desenvolvimento do primeiro módulo de software do ScanParts, sistema de baixo custo destinado à engenharia reversa de peças mecânicas de até 10 cm a partir de fotografias, baseado no computador embarcado NVIDIA Jetson Orin Nano, em uma câmera IMX219 e em uma mesa giratória impressa em 3D. O módulo consiste em uma rede neural de detecção de objetos YOLO11n treinada para localizar furos, característica mais frequente em peças mecânicas, cuja medição é realizada posteriormente por métodos geométricos clássicos. Para eliminar o custo de anotação manual, foi desenvolvido um gerador de imagens sintéticas com rotulagem automática, que simula peças metálicas e plásticas, furos passantes e cegos, perspectiva da câmera e distratores como reflexos do anel de iluminação. Foram realizados dois treinamentos: um de referência em CPU e um completo em GPU na plataforma Google Colab. O treinamento completo, com 3.000 imagens, 80 épocas e resolução de 640 pixels, alcançou precisão de 0,940, recall de 0,928 e mAP50 de 0,971 no conjunto de validação sintético, superando a meta de 0,90, com tempo de inferência de 1,7 ms por imagem. Em teste qualitativo com 30 fotografias reais do conjunto público Mechanical Parts, o modelo de referência localizou os furos de porcas sem ter sido treinado com imagens reais, porém com caixas delimitadoras maiores que o furo. Conclui-se que os dados sintéticos são um ponto de partida viável e de custo zero, sendo necessária a inclusão de fotografias reais anotadas para validar o desempenho no ambiente de uso.";

const resumo = [
  tituloPre("RESUMO"),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 240, before: 0, after: 360 },
    children: [new TextRun(RESUMO)],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 240 },
    children: [
      new TextRun({ text: "Palavras-chave: ", bold: true }),
      new TextRun("engenharia reversa; visão computacional; detecção de furos; YOLO; dados sintéticos."),
    ],
  }),
];

const linhaLista = (esq, chave, recuo = 0, negrito = false) =>
  new Paragraph({
    spacing: { line: 360, before: 0, after: 0 },
    indent: { left: recuo, right: 567 },
    tabStops: [{ type: TabStopType.RIGHT, position: LARG_TEXTO, leader: "dot" }],
    children: [
      ...runs(esq, { bold: negrito || undefined }),
      new TextRun({ bold: negrito || undefined, children: [new Tab(), pg(chave)] }),
    ],
  });

const listaIlustracoes = (tipo, titulo) => [
  tituloPre(titulo),
  ...LISTAS[tipo].map((f) => linhaLista(`${tipo} ${f.n} – ${f.titulo}`, f.chave)),
];

const SIGLAS = [
  ["ABNT", "Associação Brasileira de Normas Técnicas"],
  ["AP", "Average Precision (precisão média)"],
  ["CAD", "Computer-Aided Design (projeto assistido por computador)"],
  ["COCO", "Common Objects in Context"],
  ["CPU", "Central Processing Unit (processador)"],
  ["CSI", "Camera Serial Interface"],
  ["CVAT", "Computer Vision Annotation Tool"],
  ["DXF", "Drawing Exchange Format"],
  ["FATEC", "Faculdade de Tecnologia"],
  ["FN", "Falso negativo"],
  ["FP", "Falso positivo"],
  ["GPU", "Graphics Processing Unit (processador gráfico)"],
  ["IA", "Inteligência artificial"],
  ["IoU", "Intersection over Union (interseção sobre união)"],
  ["mAP", "Mean Average Precision (média das precisões médias)"],
  ["MVS", "Multi-View Stereo"],
  ["ONNX", "Open Neural Network Exchange"],
  ["TOPS", "Trilhões de operações por segundo"],
  ["VP", "Verdadeiro positivo"],
  ["YOLO", "You Only Look Once"],
];
const siglas = [
  tituloPre("LISTA DE ABREVIATURAS E SIGLAS"),
  ...SIGLAS.map(
    ([s, d]) =>
      new Paragraph({
        spacing: { line: 360 },
        tabStops: [{ type: TabStopType.LEFT, position: Math.round(2.2 * CM) }],
        children: [new TextRun(s), new TextRun({ children: [new Tab(), d] })],
      })
  ),
];

function sumario() {
  const out = [tituloPre("SUMÁRIO")];
  for (const e of SUMARIO) {
    const rotulo = e.num ? `${e.num} ${e.titulo}` : e.titulo;
    const recuo = 0;
    out.push(linhaLista(rotulo, e.chave, recuo, e.nivel === 1 || e.nivel === 3));
  }
  return out;
}

// ---------------------------------------------------------------- documento
const pagina = {
  size: { width: 11906, height: 16838 },
  margin: { top: 3 * CM, left: 3 * CM, bottom: 2 * CM, right: 2 * CM, header: 2 * CM, footer: 2 * CM },
};
const vazio = () => new Header({ children: [new Paragraph({ children: [] })] });
const rodapeVazio = () => new Footer({ children: [new Paragraph({ children: [] })] });

// SUMARIO e LISTAS são preenchidos quando "textual" e "posTextual" são montados (acima)
const doc = new Document({
  creator: "Equipe ScanParts",
  title: "ScanParts – Relatório técnico do módulo de IA",
  description: "Relatório técnico em formato ABNT",
  styles: {
    default: { document: { run: { font: FONTE, size: 24 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTE, size: 24, bold: true, color: "000000" },
        paragraph: { spacing: { before: 0, after: 360, line: 360 }, keepNext: true, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTE, size: 24, bold: false, color: "000000" },
        paragraph: { spacing: { before: 360, after: 360, line: 360 }, keepNext: true, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTE, size: 24, bold: true, color: "000000" },
        paragraph: { spacing: { before: 360, after: 360, line: 360 }, keepNext: true, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "alineas",
        levels: [
          {
            level: 0,
            format: LevelFormat.LOWER_LETTER,
            text: "%1)",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: Math.round(1.25 * CM) + 400, hanging: 400 } } },
          },
        ],
      },
    ],
  },
  sections: [
    { properties: { page: pagina }, headers: { default: vazio() }, footers: { default: localAno() }, children: capa },
    {
      properties: { page: { ...pagina, pageNumbers: { start: 1 } } },
      headers: { default: vazio() },
      footers: { default: localAno() },
      children: rosto,
    },
    {
      properties: { page: pagina },
      headers: { default: vazio() },
      footers: { default: rodapeVazio() },
      children: [
        ...resumo,
        ...listaIlustracoes("Figura", "LISTA DE FIGURAS"),
        ...listaIlustracoes("Quadro", "LISTA DE QUADROS"),
        ...listaIlustracoes("Tabela", "LISTA DE TABELAS"),
        ...siglas,
        ...sumario(),
      ],
    },
    {
      properties: { page: pagina },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })],
            }),
          ],
        }),
      },
      footers: { default: rodapeVazio() },
      children: [...textual, ...posTextual],
    },
  ],
});

// chaves que a 2ª passagem precisa localizar no PDF
fs.writeFileSync(
  path.join(AQUI, "chaves.json"),
  JSON.stringify(
    [...SUMARIO.map((e) => e.chave), ...["Figura", "Quadro", "Tabela"].flatMap((t) => LISTAS[t].map((f) => f.chave))],
    null,
    1
  )
);
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(AQUI, "Relatorio_ScanParts_ABNT.docx"), buf);
  console.log("docx ok:", SUMARIO.length, "seções,", LISTAS.Figura.length, "figuras,", LISTAS.Quadro.length, "quadros,", LISTAS.Tabela.length, "tabelas");
});
