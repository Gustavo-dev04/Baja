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

## Iluminação (ring light 6500 K)

O grupo vai usar **os dois modos**: luz de fundo (vista de cima) e luz frontal com ring light (mesa giratória).

| Modo | Montagem | O que a imagem mostra |
|---|---|---|
| Luz de fundo | Ring light **embaixo** de uma placa translúcida (acrílico leitoso ou papel vegetal), peça por cima | Silhueta preta + furos passantes como pontos de luz. Não precisa de IA |
| Luz frontal | Câmera **no centro** do ring light, apontada para a peça na mesa | Furos escuros sobre a superfície clara. Aqui entra a IA |

Cuidados com o ring light:
- **Reflexo em anel no metal:** o próprio anel aparece refletido em peça brilhante. Para evitar: difusor (papel vegetal sobre o anel) e/ou fosquear a peça (spray revelador, talco ou xampu a seco). A IA também precisa ver exemplos com reflexo no treino.
- **Cintilação (flicker):** com o brilho abaixo de 100%, alguns ring lights piscam (PWM) e aparecem faixas na imagem. Usar 100% de brilho ou ajustar o tempo de exposição.
- **Câmera em manual:** travar balanço de branco, exposição e ganho na IMX219, para que todas as fotos saiam iguais (importante para a IA e para a medição).
- **6500 K (luz do dia):** usar sempre a mesma luz nas fotos de treino e no uso real.

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
