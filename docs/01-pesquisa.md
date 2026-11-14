# Etapa 1 – Pesquisa

Status: **em andamento** (iniciado em 14/11/2026)

Objetivo: saber o que já existe, onde está a lacuna e qual é o diferencial do ScanParts.

---

## 1. Artigo de referência: comparação de métodos MVS

**Li, Y.; Vosselman, G.; Nex, F.** *A Comparison of Multi-View Stereo Methods for Photogrammetric 3D Reconstruction: From Traditional to Learning-Based Approaches.* arXiv:2604.10246, abr. 2026 (também nos ISPRS Annals, 2026).

**O que é:** compara métodos de reconstrução 3D a partir de várias fotos (MVS). Ele separa em três grupos:

| Grupo | Exemplos | Como funciona |
|---|---|---|
| Tradicional | COLMAP, OpenMVS | Acha pontos em comum entre fotos, calcula a posição da câmera e triangula os pontos |
| Aprendizado guiado por geometria | MVSNet, PatchMatchNet, MVSFormer++ | Rede neural dentro do fluxo tradicional |
| Ponta a ponta (end-to-end) | DUSt3R, MASt3R, VGGT, Fast3R | A rede recebe as fotos e já devolve o 3D |

**Conclusões principais:**
- **VGGT** teve o melhor equilíbrio entre qualidade e tempo, e se manteve estável com mais fotos.
- **MASt3R** é bom com poucas fotos, mas piora muito quando o número de fotos cresce.
- **COLMAP** gera resultado mais esparso e é lento em cenas grandes.
- Os métodos com IA **ainda têm erros grandes** (camadas e inconsistências locais), o que limita o uso onde se exige alta precisão.

**O que isso significa para o ScanParts:**
- O artigo testa **cenas aéreas** (ilhas e áreas urbanas), não peças pequenas na bancada. Os resultados servem de direção, mas não se transferem direto para o nosso caso.
- Todos esses métodos param na **nuvem de pontos ou malha**, ou seja, na etapa de digitalização. Nenhum entrega CAD editável. A parte de engenharia reversa continua sendo trabalho nosso.
- **VGGT no Jetson Orin Nano é arriscado.** O modelo tem ~1,2 bilhão de parâmetros, e um estudo sobre dispositivos de borda aponta a memória do Jetson como o gargalo. Não achamos nenhum teste publicado no Orin Nano (8 GB). Para nós, VGGT é um **experimento opcional**, não a base do projeto.
- Para precisão em peça pequena com mesa giratória, o caminho mais seguro é o **tradicional + silhueta**: os ângulos da mesa são conhecidos, o que facilita muito a calibração.

## 2. O que já existe (concorrentes)

| Solução | O que faz | Preço aprox. | Entrega CAD editável? |
|---|---|---|---|
| **OpenScan** (open source) | Scanner com mesa giratória + Raspberry Pi, fotogrametria. Mini: peças de até ~9 cm | Kit barato (DIY) | ❌ Só malha. O processamento roda na nuvem ou num PC, não no Raspberry |
| **Revopoint POP 3 Plus** | Scanner 3D de mão com luz estruturada | ~US$ 530–620 | ❌ Só malha (STL/OBJ/PLY) |
| **Apps de celular** (Polycam, RealityScan) | Fotogrametria com o celular | Grátis / assinatura | ❌ Só malha |
| **Shaper Trace** | Moldura + app: foto de uma peça plana vira vetor | US$ 99 | ⚠️ Gera SVG (contorno), sem cotas nem features |
| **Geomagic Design X** | Software profissional de scan-to-CAD: reconhece planos, cilindros, cones e gera árvore de features | ~US$ 4.000–5.000 (pacote) | ✅ Mas exige scanner + software caro e operador treinado |

**Resumo:** existe scanner barato que gera malha, e existe software caro que transforma malha em CAD. **Não achamos uma solução barata que faça as duas coisas e entregue CAD editável direto.**

## 3. Pesquisa acadêmica em "scan-to-CAD"

| Trabalho | O que faz | Por que importa |
|---|---|---|
| **CAD-Recode** (Rukhovich et al., ICCV 2025) | Recebe uma nuvem de pontos e gera **código Python (CadQuery)** que reconstrói a peça com sketch + extrusão. Usa um LLM pequeno (Qwen2-1.5B). Código público | É exatamente a ideia de "gerar um script que recria a peça". Mesmo conceito do script do Fusion 360 |
| **Img2CAD** (Chen et al., arXiv 2410.03417) | De **uma única imagem** gera a sequência de sketch + extrusão | Mostra que dá para ir de foto para CAD paramétrico |
| **Visual hull / silhueta** (ex.: EyeBox, MIT) | Reconstrói o volume pelas silhuetas vistas de vários ângulos | Barato, rápido e robusto a metal brilhante. **Limitação: não enxerga cavidades** |

## 4. Lacuna e diferencial do ScanParts

**Lacuna:** quem é barato entrega malha, e quem entrega CAD editável é caro.

**Diferencial proposto:**
1. **Saída em CAD editável no Fusion 360** (DXF para peças planas e script Python do Fusion com histórico para peças gerais), não só malha.
2. **Equipamento barato e autônomo:** Jetson + IMX219 + mesa impressa em 3D, com processamento no próprio aparelho.
3. **Foco em peças mecânicas pequenas (≤ 10 cm) e precisão de ± 1 mm**, que é o que a manutenção e o Baja precisam.
4. **Mesa giratória com ângulo conhecido**, que simplifica e estabiliza a reconstrução em comparação com fotos soltas de celular.

> Cuidado: "não achamos" não é o mesmo que "não existe". Antes de afirmar que é inédito, falta pesquisar patentes.

## 5. Pendências da Etapa 1

- [ ] Ler o PDF completo do artigo 2604.10246 (tabelas de erro e tempo)
- [ ] Busca de patentes: INPI e Google Patents ("scan to CAD", "turntable 3D scanner", "engenharia reversa fotografia")
- [ ] Busca no oasisbr (TCCs e dissertações brasileiras parecidas)
- [ ] Ver se o CAD-Recode roda no Jetson Orin Nano (modelo de 1,5B; talvez com quantização)

## Referências

- LI, Y.; VOSSELMAN, G.; NEX, F. A Comparison of Multi-View Stereo Methods for Photogrammetric 3D Reconstruction: From Traditional to Learning-Based Approaches. arXiv:2604.10246, 2026. https://arxiv.org/abs/2604.10246
- RUKHOVICH, D. et al. CAD-Recode: Reverse Engineering CAD Code from Point Clouds. ICCV, 2025. https://arxiv.org/abs/2412.14042
- CHEN, T. et al. Img2CAD: Conditioned 3D CAD Model Generation from Single Image with Structured Visual Geometry. arXiv:2410.03417, 2024. https://arxiv.org/abs/2410.03417
- WANG, J. et al. VGGT: Visual Geometry Grounded Transformer. CVPR, 2025. https://github.com/facebookresearch/vggt
- SCHÖNBERGER, J. L.; FRAHM, J.-M. Structure-from-Motion Revisited. CVPR, 2016. (COLMAP)
- OpenScan – open source 3D scanner. https://www.openscan.eu
- Shaper Trace. https://shapertools.com/trace
- Geomagic Design X. https://www.solidworks.com/partner-product/design-x
- Revopoint POP 3. https://www.revopoint3d.com/products/pop3-3d-scanner
- EyeBox: A Cheap, Effective 3D Scanner (MIT Media Lab). https://acg.media.mit.edu/people/simong/eyebox/index.html
