# ScanParts

Gera um **CAD editável** de uma peça a partir de fotos.

- **Hardware:** NVIDIA Jetson Orin Nano + câmera IMX219 (120°) + mesa giratória impressa em 3D com motor de passo
- **Peças:** planas e gerais, com precisão de ± 1 mm
- **Saída:** arquivos que abrem editáveis no Fusion 360

Projeto de extensão – FATEC Santo André.

**Software (código + testes):** [docs/03-software.md](docs/03-software.md) – foto → medida em mm → DXF + script do Fusion.

**Relatório atual do software:** [docs/relatorio-software.md](docs/relatorio-software.md) · versão ABNT: [Word](docs/relatorio/Relatorio_ScanParts_ABNT.docx) / [PDF](docs/relatorio/Relatorio_ScanParts_ABNT.pdf)

## Etapas

| # | Etapa | Status |
|---|---|---|
| 0 | [Definição](docs/00-definicao.md) | Em andamento |
| 1 | [Pesquisa](docs/01-pesquisa.md) | Em andamento |
| 2 | [Arquitetura](docs/02-arquitetura.md) | Em andamento |
| 3 | Mesa giratória | – |
| 4 | [Câmera e calibração](docs/03-software.md) | Código pronto, testado em sintético |
| 5 | [Peças planas → DXF / Fusion](docs/03-software.md) | Código pronto, testado em sintético |
| 6 | Peças gerais → CAD | – |
| 7 | [IA de detecção de furos](docs/07-ia-furos.md) | Modelo v1/v2 treinado; integrado como conferência |
| 8 | Validação e apresentação | – |

## Rodar rápido (sem hardware)

```bash
pip3 install -r requirements.txt
python3 -m scanparts simular --saida demo --peca suporte_L --espessura 3
python3 -m scanparts calibrar --fotos "demo/calibracao/*.jpg" --referencia demo/referencia_prato.jpg --saida demo/calibracao.json
python3 -m scanparts medir demo/suporte_L.jpg --calibracao demo/calibracao.json --espessura 3 --saida demo/resultado
```

Teste completo com gabarito: `python3 testes/teste_sintetico.py --saida resultados_teste`
