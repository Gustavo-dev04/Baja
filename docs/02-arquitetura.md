# Etapa 2 – Arquitetura

Status: **em andamento** (iniciado em 14/11/2026)

## Decisões tomadas

| Tema | Decisão |
|---|---|
| Controle do motor | **Arduino Uno/Nano via USB**: o Jetson manda comandos e o Arduino gera os passos |
| Driver do motor | **A4988** |
| Interface | **Página web** servida pelo Jetson, operada pelo celular ou notebook |
| Câmera na mesa giratória | **Ângulo fixo de ~30–45°** |
| Luz de fundo (modo 2D) | **Base separada**: caixa com o ring light dentro e tampa translúcida |
| Prioridade | **Peça plana → DXF** primeiro; peça geral 3D depois |

## Visão geral

```mermaid
flowchart LR
    subgraph Usuario["Usuário"]
        WEB["Celular / notebook<br/>(navegador)"]
    end
    subgraph Jetson["Jetson Orin Nano"]
        API["Servidor web<br/>(FastAPI)"]
        CAM["Captura<br/>(IMX219 ou celular)"]
        CAL["Calibração<br/>(ChArUco)"]
        P2D["Modo 2D<br/>contorno → DXF"]
        IA["IA de furos<br/>(YOLO + TensorRT)"]
        P3D["Modo 3D<br/>(depois)"]
        MESA["Controle da mesa<br/>(serial)"]
    end
    subgraph Bancada["Bancada"]
        IMX["Câmera IMX219 120°"]
        RING["Ring light 6500 K"]
        ARD["Arduino Uno/Nano"]
        A49["Driver A4988"]
        MOT["NEMA 17 + mesa giratória"]
    end
    WEB <--> API
    API --> CAM & MESA & P2D & P3D
    IMX --> CAM
    CAM --> CAL --> P2D & P3D
    P2D & P3D --> IA
    MESA -- USB --> ARD --> A49 --> MOT
    P2D --> DXF["Arquivo DXF"]
    P3D --> FUS["Script Fusion 360 / STEP"]
```

## Hardware

### Bancada: duas estações

| Estação | Uso | Montagem |
|---|---|---|
| **Base de luz (2D)** | Peças planas | Caixa impressa com o ring light dentro, tampa de acrílico leitoso ou papel vegetal. Câmera olhando **de cima (90°)** |
| **Mesa giratória (3D + furos)** | Peças gerais | Prato giratório. Ring light em volta da câmera, que olha a **~30–45°** |

**Ponto de projeto:** a câmera precisa de duas posições (90° para a base e ~35° para a mesa). Proposta: uma haste impressa com **duas travas fixas** de ângulo. Assim cada posição é repetível e a calibração continua valendo.

O ring light muda de lugar entre os modos (dentro da base ou em volta da câmera).

### Lista de componentes

| Item | Status |
|---|---|
| NVIDIA Jetson Orin Nano | ✅ Tem |
| Câmera IMX219 120° | ✅ Tem |
| Ring light 6500 K | ✅ Tem |
| Motor de passo NEMA 17 | ✅ Tem |
| Driver A4988 | ✅ Tem |
| Arduino Uno/Nano + cabo USB | ✅ Tem |
| Impressora 3D + filamento | ✅ Tem |
| Fonte 12 V (≥ 1,5 A) para o motor | ❓ Verificar |
| Capacitor eletrolítico 100 µF (entre VMOT e GND do A4988) | ❓ Verificar (protege o driver, custa centavos) |
| Rolamento 608 (de skate) para o prato | ❓ Verificar |
| Acrílico leitoso ou papel vegetal (tampa da base de luz) | ❓ Verificar |
| Cabo CSI adaptador 15→22 pinos (se a câmera for padrão Raspberry Pi) | ❓ Verificar |
| Tabuleiro ChArUco | Impresso em papel (custo zero) |

### Mesa giratória

| Parâmetro | Valor |
|---|---|
| Diâmetro do prato | 12–15 cm (peças de até 10 cm) |
| Micropasso no A4988 | 1/16 → 3.200 passos por volta do motor |
| Redução (engrenagem impressa ou correia GT2) | Proposta 1:4 → 12.800 passos por volta do prato (~0,03° por passo) |
| Posição zero (homing) | Pelos **marcadores ArUco no prato**, lidos pela câmera. Dispensa sensor de fim de curso |
| Corrente do motor | Ajustar o Vref do A4988 conforme a corrente do NEMA 17 e o resistor da placa |

### Comunicação Jetson ↔ Arduino (serial USB)

| Comando | Ação | Resposta |
|---|---|---|
| `R <graus>` | Gira o prato | `OK <posição>` |
| `Z` | Define a posição atual como zero | `OK 0` |
| `E 0/1` | Desliga/liga o motor | `OK` |
| `?` | Status | `POS <graus>` |

## Software

| Módulo | Função | Bibliotecas |
|---|---|---|
| `camera` | Captura da IMX219 (CSI) ou do celular (stream IP), com exposição e balanço de branco travados | GStreamer (nvarguscamerasrc), OpenCV |
| `mesa` | Comandos para o Arduino | pyserial |
| `calibracao` | Distorção da lente de 120° e escala em mm | OpenCV (ChArUco) |
| `modo_2d` | Silhueta → contorno → retas/arcos/círculos → DXF | OpenCV, NumPy, ezdxf |
| `furos` | IA acha os furos, a geometria mede, a regra interpreta | Ultralytics YOLO, TensorRT |
| `modo_3d` | Silhuetas da mesa giratória → volume → CAD (depois) | Open3D, CadQuery / API do Fusion |
| `web` | Interface pelo navegador | FastAPI |
| `firmware` | Código do Arduino | Arduino (C++), AccelStepper |

### Fluxo do modo 2D (prioridade)

1. Calibrar a câmera uma vez (tabuleiro ChArUco).
2. Colocar a peça na base de luz e informar a **espessura** (medida com paquímetro na v1).
3. Tirar a foto e corrigir a distorção da lente.
4. Separar a silhueta do fundo (limiar, sem IA).
5. Achar o contorno externo e os furos.
6. Ajustar retas, arcos e círculos.
7. Converter para mm e corrigir a paralaxe pela espessura.
8. Gerar o **DXF** e um relatório com as medidas (ex.: "furo Ø 6,6 mm → passante para M6").

## Pendências da Etapa 2

- [ ] Verificar os itens marcados com ❓
- [ ] Confirmar a versão do JetPack instalada no Jetson
- [ ] Desenhar a haste com duas travas e a base de luz (croqui)
