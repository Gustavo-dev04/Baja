# Registro de resultados – IA de furos

Cada treino ganha uma linha na tabela e uma seção com os detalhes. Nada é apagado: os resultados ruins também ficam, porque mostram a evolução.

## Como ler as métricas

| Métrica | O que significa | Meta |
|---|---|---|
| **Precisão (P)** | Das caixas que a IA marcou, quantas eram furo de verdade | ≥ 0,90 |
| **Recall (R)** | Dos furos que existiam, quantos a IA achou | ≥ 0,90 |
| **mAP50** | Nota geral de detecção (0 a 1), aceitando caixa com ≥ 50% de sobreposição | ≥ 0,90 |
| **mAP50-95** | Nota mais exigente: também cobra caixa bem ajustada | Quanto maior, melhor |

## Resumo

| ID | Data | Dados de treino | Modelo | Img | Épocas | P | R | mAP50 | mAP50-95 | Onde |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 14/11/2026 | Sintético 1.500 (+300 val) | YOLO11n | 416 | 12 | 0,909 | 0,828 | 0,889 | 0,475 | CPU (teste) |

## Detalhes

### v1 – Referência só com dados sintéticos (14/11/2026)

**Objetivo:** ver se o modelo consegue aprender o conceito de furo com dados 100% sintéticos, e ter um número de partida.

**Configuração**

| Item | Valor |
|---|---|
| Dados | `gerar_sintetico.py`, semente 1: 1.500 imagens de treino (5.056 furos) + 300 de validação (1.275 furos) |
| Modelo | YOLO11n pré-treinado (COCO), detecção por caixa |
| Treino | 12 épocas, imagem de 416 px, batch 16, flips horizontal/vertical, rotação ±15° |
| Máquina | CPU, 4 núcleos (sem GPU), 25 min |

**Resultado (validação sintética)**

| Precisão | Recall | mAP50 | mAP50-95 | Inferência (CPU) |
|---|---|---|---|---|
| 0,909 | 0,828 | 0,889 | 0,475 | 16 ms/imagem |

![Rótulos (esquerda) × previsões (direita)](img/ia/v1_rotulos_vs_previsao.jpg)

![Curvas de treino](img/ia/v1_curvas.jpg)

**O que observamos**
- **Aprendeu o conceito de furo:** acerta os furos visíveis com boa confiança (0,7–0,9).
- **Ignora o reflexo do ring light:** os anéis claros não foram confundidos com furos.
- **Erra mais nos furos minúsculos:** 23% dos furos da validação têm menos de 10 px, e é aí que o recall cai.
- **Alguns falsos positivos** em manchas escuras (sujeira e marcas de centro).
- **Ainda estava melhorando** na última época: com mais épocas o número sobe.

**Limitações**
- Mede só o desempenho em imagens **sintéticas**. Não diz nada ainda sobre fotos reais.
- No gerador, a peça muitas vezes aparece **pequena** na imagem. No ScanParts real (peça de até 10 cm, câmera perto) ela ocupa boa parte da foto, e os furos ficam maiores e mais fáceis.

**Próximos passos sugeridos (v2)**
1. Gerador: aumentar o zoom para a peça ocupar mais da imagem, como no uso real.
2. Treinar no Colab (GPU T4) com 640 px, 3.000 imagens e até 80 épocas.
3. Assim que houver fotos reais, criar um **conjunto de teste real separado** e registrar a nota nele.
