# 03 — Hardware da Câmara de Inspeção

## Dimensões mínimas

Considerando um chassi BAJA típico (~2,4 × 1,3 × 1,2 m), a câmara
interna deve ter, no mínimo:

- Comprimento: **3,0 m**
- Largura: **1,8 m**
- Altura: **1,8 m**

Isso reserva ~0,3 m de folga lateral para a distância focal mínima das
câmeras e circulação de ar para iluminação LED.

## Estrutura

- Chapas metálicas ou MDF pintado em **preto fosco** internamente para
  reduzir reflexos.
- Estrutura modular desmontável (parafusos) — importante para transporte
  a competições e feiras acadêmicas.
- Portas de acesso em uma extremidade; trilho/base para posicionar o
  chassi.

## Iluminação

**Iluminação difusa é o fator mais crítico** para reprodutibilidade das
imagens.

- Fitas/painéis de LED de **5000 K** (luz branca neutra) em teto e
  laterais superiores.
- Difusores (acrílico leitoso) para eliminar pontos brilhantes.
- Corrente estabilizada para evitar flicker.
- Alternativa profissional: dome lights polarizados.

## Câmeras

Para o protótipo, câmeras USB comuns são suficientes. A versão final
deve migrar para câmeras industriais.

| Uso        | Modelo sugerido              | Resolução | Obs.                         |
|------------|------------------------------|-----------|------------------------------|
| Protótipo  | Logitech C920 / C922         | 1080p     | Fácil acesso e driver USB.   |
| Avançado   | Intel RealSense D435         | 1080p + profundidade | Permite inspeção 3D.         |
| Produção   | Basler acA1920 / IDS uEye    | 2–5 MP    | GigE Vision, sync hardware.  |

Quantidade sugerida: **4 a 6 câmeras** em ângulos complementares (frente,
traseira, laterais, teto) para cobrir todo o chassi sem oclusões.

## Sensor de presença e trigger

- Sensor ultrassônico ou infravermelho (HC-SR04, E18-D80NK) na entrada
  da câmara para detectar chassi posicionado.
- Microcontrolador (ESP32/Arduino) dispara o ciclo de captura.
- Botão físico de "inspeção manual" também previsto.

## Alimentação e segurança

- Fonte 12 V para LEDs, fonte 5 V para microcontrolador.
- Aterramento da estrutura metálica.
- Interlock: a inspeção só inicia com a porta fechada (chave fim de
  curso).
