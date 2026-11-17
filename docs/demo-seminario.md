# Demonstração do seminário (04/12/2026)

Status: **definido** (17/11/2026)

## O que será mostrado

Engenharia reversa de uma **peça plana** (o suporte cheio de furos) com **uma foto de cima**, gerando a peça 3D no Fusion 360 por **extrusão**.
A mesa giratória não participa da demonstração.

| Decisão | Escolha |
|---|---|
| Peça | Suporte em **chapa plana, sem dobra**, espessura única, cheio de furos passantes |
| Captura | Uma foto de cima (câmera a 90°) |
| Iluminação | **Fundo preto fosco + ring light + filtro CPL** (decidido em 17/11). Peça metálica clara sobre fundo escuro; os furos passantes aparecem pretos |
| Saída | **Script Python do Fusion 360**: cria o sketch e extruda pela espessura, com histórico editável. DXF junto como plano B |
| Espessura | Informada (medida com paquímetro) |

## Roteiro

1. Calibração da câmera feita antes (tabuleiro ChArUco impresso).
2. Colocar o suporte sobre o fundo preto fosco, ring light ligado, e tirar a foto.
3. Jetson: contorno externo (retas e arcos) + furos (centro, diâmetro, interpretação da medida).
4. Tela: foto com as cotas sobrepostas.
5. Rodar o script no Fusion: o suporte aparece em 3D.
6. Comparar uma medida com o paquímetro na frente da banca.
7. Extra: a IA de furos marcando os furos na mesma foto (ela foi treinada justamente para luz frontal).

## Limitações conhecidas

- A foto de cima só vê o que atravessa a peça: furos cegos, rebaixos e chanfros não aparecem.
- A precisão depende da calibração da lente de 120° e da correção de paralaxe pela espessura.
- Com luz frontal, a parede interna dos furos aparece como uma faixa cinza nos furos fora do centro da imagem; a medição usa a borda de cima do furo.
- Peça escura ou oxidada perde contraste no fundo preto: usar peça clara/metálica na demo.

## Pendências

- [ ] Receber o desenho técnico do suporte (referência para validar as medidas)
- [ ] Foto de cima do suporte para desenvolvimento
- [ ] Código: calibração → contorno/furos → DXF + script do Fusion
