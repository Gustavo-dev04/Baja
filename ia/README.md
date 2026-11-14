# IA de detecção de furos

Modelo **YOLO11n** (detecção por caixa) que acha furos em fotos de peças.
A IA só **localiza** o furo. A medida (centro e diâmetro) é feita depois por geometria clássica, dentro da caixa.

> Por que caixa e não segmentação? A medida precisa vem da geometria, então a caixa basta.
> Isso também permite usar datasets públicos, que quase sempre têm só caixas.

## Arquivos

| Arquivo | O que faz |
|---|---|
| [`treino_furos_colab.ipynb`](treino_furos_colab.ipynb) | Notebook do Google Colab: gera os dados, treina, avalia, exporta (passo a passo) |
| [`gerar_sintetico.py`](gerar_sintetico.py) | Gera imagens sintéticas de peças com furos, já rotuladas |
| [`juntar_datasets.py`](juntar_datasets.py) | Junta sintético + Roboflow + fotos do grupo num dataset só (classe `furo`) |

## Como usar no Colab

1. Abra o notebook no Colab: **Arquivo → Abrir notebook → GitHub**, cole a URL do repositório e escolha a branch.
2. **Ambiente de execução → Alterar o tipo → GPU T4**.
3. Rode as células na ordem. Tudo que importa fica salvo em `MyDrive/scanparts_ia/`.

Para gastar menos unidades: gere o dataset sintético **sem GPU** (ele vai para o Drive em `.zip`) e só ligue a T4 na hora do treino.
O Kaggle Notebooks (GPU grátis, ~30 h/semana) também roda o mesmo código.

## Rodar no computador (teste rápido)

```bash
pip install opencv-python-headless numpy
python ia/gerar_sintetico.py --saida dados/sintetico --treino 50 --val 10 --previa 10
```

As imagens com os rótulos desenhados ficam em `dados/sintetico/previa/`.

## Dados

| Fonte | Tamanho | Rótulo | Licença |
|---|---|---|---|
| **Sintético** (`gerar_sintetico.py`) | Quantas quiser | Automático | Nosso |
| [drill-hole-detection](https://universe.roboflow.com/corbinian-rehm-master-thesis/drill-hole-detection) (Roboflow) | 260 imagens | Caixa | CC BY 4.0 (citar o autor) |
| [Holes & Fasteners](https://universe.roboflow.com/low-effort-programming-for-flexible-assembly-task/holes-fasteners) (Roboflow) | ? | Caixa (furo + parafuso) | Verificar |
| [Holes Object Detection in Industrial Scene](https://datasetninja.com/holes-object-detection) (Kaggle) | 493 imagens | Caixa | **Não confirmada**, não usar até verificar |
| [Open Stamped Parts Dataset](https://arxiv.org/abs/2403.10369) | 1.680 rotuladas | Máscaras com furos (chapa estampada) | Verificar |
| [Mechanical Parts](https://universe.roboflow.com/mazhar-cakir/mechanical-parts) (Roboflow, Mazhar Cakir) | ~2.250 imagens | Caixa: porca, parafuso, rolamento, engrenagem (**não marca furos**) | CC BY-NC-SA 4.0 (uso não comercial) |
| **Fotos do grupo** (CVAT / Label Studio) | Meta: 200–500 | Caixa | Nosso |

> **Atenção com o Mechanical Parts:** porcas, rolamentos e engrenagens têm furo, mas o furo não está rotulado.
> Se essas imagens entrarem no treino como estão, a IA aprende que "furo não é furo". Usar só para **teste**
> ou depois de rotular os furos (pré-rótulo com o modelo + correção no CVAT).

As **fotos reais do grupo são as mais importantes**: o sintético ensina o conceito de furo, mas só as fotos reais
ensinam como a IMX219 e o ring light de vocês enxergam as peças.

### O que o gerador sintético simula

- Peças (retângulo, chanfrada, em L, disco, flange) em metal escovado ou plástico, com espessura e sombra
- Furos passantes e cegos, com parede visível, chanfro e brilho na borda
- Câmera inclinada (0–50°), girada e com zoom variado
- **Distratores que não são furos:** reflexo do ring light, sujeira, riscos, marcas de centro e marcadores ArUco do prato
- Ruído, desfoque, vinheta da lente de 120°, variação de cor e compressão JPEG

## Teste feito

Testado localmente com o Ultralytics 8.4: geração, junção de datasets, 1 época de treino e validação rodaram sem erro.
