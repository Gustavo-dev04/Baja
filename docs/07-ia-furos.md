# Etapa 7 – IA de detecção de furos (plano)

Status: **planejado** (decidido em 14/11/2026)

## Decisão

A IA começa com **uma única tarefa: detectar furos**. É uma feature simples e controlada, e a mais comum em peças mecânicas. Outras features (rasgos, raios, chanfros) ficam para depois.

## Divisão de trabalho: IA × geometria

| Etapa | Quem faz | Por quê |
|---|---|---|
| 1. **Achar** o furo na imagem | **IA** (YOLO de segmentação) | Distingue furo de sujeira, sombra e reflexo, e acha furos vistos de lado (que aparecem como elipse) |
| 2. **Medir** centro e diâmetro | **Geometria clássica** (bordas subpixel + ajuste de círculo/elipse, OpenCV) | Mais preciso e explicável que a IA |
| 3. **Interpretar** a medida | **Regra** (tabela de medidas padrão) | Recupera a intenção de projeto, por exemplo "Ø 9,0 mm → furo passante para M8" |

Na vista de cima com luz de fundo, o furo passante aparece como um ponto de luz e dá para achar sem IA. A IA faz diferença nas **fotos da mesa giratória com luz frontal**, onde aparecem furos inclinados, furos cegos e reflexos.

## Classes

- Fase 1: `furo`
- Fase 2 (se der tempo): `furo_passante` e `furo_cego`

## Tabela de interpretação (exemplo)

| Diâmetro medido | Interpretação provável |
|---|---|
| 3,4 mm | Passante para M3 |
| 4,5 mm | Passante para M4 |
| 5,5 mm | Passante para M5 |
| 6,6 mm | Passante para M6 |
| 9,0 mm | Passante para M8 |
| 11,0 mm | Passante para M10 |
| 2,5 / 3,3 / 4,2 / 5,0 / 6,8 / 8,5 mm | Pré-furo para rosca M3 / M4 / M5 / M6 / M8 / M10 |

(Furos passantes pela série média da ISO 273. Pré-furos pela tabela usual de rosca métrica grossa. Conferir as tabelas na documentação final.)

## Dados (custo zero)

1. **Fotos reais:** 200–500 fotos de peças na mesa giratória, anotadas no CVAT ou no Label Studio.
2. **Dados sintéticos:** peças com furos renderizadas no Blender, com câmera e luz iguais às do ScanParts. O rótulo sai automático. Fontes de modelos: datasets ABC e Fusion 360 Gallery, ou peças simples geradas por script.

## Treino (custo zero)

| Etapa | Onde |
|---|---|
| Testes rápidos | CPU local, com poucos dados |
| Treino principal | Kaggle Notebooks (GPU grátis, ~30 h/semana) |
| Treino extra | Google Colab, GPU T4 (unidades do grupo) |
| Uso final | Jetson Orin Nano com TensorRT |

Cuidados:
- Salvar os checkpoints no Google Drive (a sessão do Colab cai).
- Usar o menor modelo YOLO de segmentação primeiro; só aumentar se a precisão não bastar.

## Critério de sucesso

- Detectar **≥ 90%** dos furos nas peças de teste.
- Diâmetro medido com erro **≤ ± 0,5 mm** (metade da tolerância do projeto).
- Rodar no Jetson em **menos de 1 s por imagem**.
