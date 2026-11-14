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
| v1 | 14/11/2026 | Sintético 1.500 (+300 val) | YOLO11n | 480 | 20 | ⏳ | ⏳ | ⏳ | ⏳ | CPU (teste) |

## Detalhes
