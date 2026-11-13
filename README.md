# RevScan – Scanner de Engenharia Reversa

> Nome provisório.

Scanner de bancada com **NVIDIA Jetson Orin Nano**. Ele fotografa uma peça mecânica e gera o modelo digital dela, pronto para CAD:

- **Modo 2D** (entrega mínima): para peças planas (chapas, juntas, flanges). Gera o contorno vetorial em **DXF/SVG**, em milímetros. Meta: erro ≤ 0,5 mm.
- **Modo 3D** (meta estendida): uma mesa giratória captura de 36 a 72 fotos e a fotogrametria gera a malha em **STL/OBJ**. Meta: erro ≤ 1 mm.

Todo o processamento roda no próprio Jetson. A operação é por uma interface web, acessível pelo celular ou pelo notebook.

Projeto de extensão do curso de Mecatrônica Industrial da FATEC Santo André.

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [`docs/Proposta_RevScan.docx`](docs/Proposta_RevScan.docx) | Proposta de projeto no modelo FATEC (os campos em amarelo ainda precisam ser preenchidos) |
| [`docs/Apresentacao_RevScan.pptx`](docs/Apresentacao_RevScan.pptx) | Apresentação para o Seminário de Projetos de Extensão 2026 (com anotações do apresentador) |

## Arquitetura proposta

```
Câmera ──► Calibração (lente + escala ArUco) ──┬──► 2D: segmentação ► contorno ► linhas/arcos ► DXF/SVG
                                               └──► 3D: fotos 360° ► SfM/MVS ► nuvem de pontos ► malha STL/OBJ
```

| Camada | Tecnologia prevista |
|---|---|
| Hardware | Jetson Orin Nano 8 GB, câmera ≥ 8 MP (CSI/USB), NEMA 17 + driver, LEDs difusos |
| Visão / 2D | OpenCV (calibração, ArUco/ChArUco, contornos), ezdxf |
| 3D | COLMAP (CUDA), Open3D (nuvem de pontos, reconstrução Poisson) |
| Interface | FastAPI + front-end web servido pelo Jetson |

## Status

Fase de definição de escopo. O código ainda não foi iniciado.
