# Etapa 0 – Definição do projeto

Status: **em andamento** (iniciado em 14/11/2026)

## Nome

**ScanParts**

## Problema

Refazer o desenho técnico de uma peça existente (medindo à mão com paquímetro) é **lento e impreciso**.

## Objetivo

Gerar um **CAD editável** de uma peça a partir de fotos.

## Escopo

### Entra

| Item | Definição |
|---|---|
| Tipos de peça | **Planas** (chapas, suportes, flanges, juntas) e **gerais** (peças 3D) |
| Precisão | **± 1 mm** |
| Tamanho máximo da peça | **[definir] cm** |
| Saída | CAD editável, aberto no **Fusion 360** (ver formatos abaixo) |

### Fica de fora

- Peças **transparentes** ou muito brilhantes sem tratamento.
- Peças **muito complexas**, com detalhes que a câmera não consegue ver (cavidades internas, furos cegos profundos, geometrias escondidas).

### Formato de saída (proposta)

| Tipo de peça | Arquivo | Como abre no Fusion |
|---|---|---|
| Plana | **DXF** | Importa como sketch editável, depois é só extrudar |
| Geral | **STEP** | Abre como sólido editável |
| Geral (ideal) | **Script Python do Fusion** | Recria a peça com histórico (sketch + extrusão), 100% paramétrica |

## Hardware já definido

| Item | Escolha |
|---|---|
| Processamento | NVIDIA Jetson Orin Nano |
| Câmera | IMX219 com lente de 120° (plano B: câmera do celular) |
| Movimento | Mesa giratória impressa em 3D com motor de passo |

Critério para trocar para o celular: se o erro medido com a IMX219 numa peça de referência passar de **± 1 mm**.

## Equipe

4 integrantes.

| Nome | Função |
|---|---|
| [definir] | [definir] |
| [definir] | [definir] |
| [definir] | [definir] |
| [definir] | [definir] |

## Prazos

| Data | Entrega |
|---|---|
| **02/12/2026** | Entrega [confirmar: proposta escrita? protótipo?] |
| **04/12/2026** | Seminário de Projetos de Extensão |

## Pendências da Etapa 0

- [ ] Tamanho máximo da peça (em cm)
- [ ] Nomes e funções dos 4 integrantes
- [ ] Confirmar o que precisa estar pronto em 02/12 e em 04/12
