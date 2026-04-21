# Demo Kit — Apresentação do Protótipo

Este diretório reúne instruções e materiais para **apresentar o
protótipo ao vivo** (quarta-feira) mesmo sem um chassi BAJA real no
local.

## Roteiro sugerido (informal, ~10 min)

1. **Abertura (1 min)** — mostrar a tela inicial do dashboard em
   `http://localhost:3000`. Destacar o badge "API: online" e o
   indicador de status "Aguardando".
2. **Modo ao vivo (3-4 min)** — clicar em **Iniciar modo ao vivo**.
   A webcam passa a enviar um frame a cada 1,5 s automaticamente.
   Aponte para objetos diversos (garrafa, celular, livro) e mostre
   as bounding boxes aparecendo em tempo real com o rótulo
   remapeado (`escorrimento`, `bolha`, `risco`, etc.).
3. **Captura única (1 min)** — parar o modo ao vivo e usar
   "Capturar frame" para discutir um frame específico.
4. **Upload de imagem (2 min)** — carregar uma imagem do kit
   (ver seção abaixo) para mostrar que o sistema aceita fotos
   pré-existentes, não só webcam.
5. **Arquitetura (2-3 min)** — abrir `docs/02-arquitetura.md` e
   explicar o fluxo: frontend → FastAPI → YOLO → JSON → overlay.
   Mencionar o fine-tuning futuro com dataset próprio de defeitos.

## O que contar sobre o "modo demo"

Seja transparente: o modelo atual (`yolov8n.pt`) é o **pré-treinado
COCO** (garrafas, pessoas, celulares). A função `DEMO_CLASS_MAP`
renomeia essas detecções para nomes de defeitos de pintura. O
objetivo é **validar o pipeline end-to-end** (câmera → IA → UI).

O próximo passo técnico (semana 4-5 do semestre) é:
- Coletar ~500 fotos reais de chassis pintados.
- Rotular defeitos no Roboflow (`escorrimento`, `casca_de_laranja`,
  `falha_cobertura`, `bolha`, `risco`, `oxidacao`).
- Fazer fine-tuning do YOLO com essas imagens.

## Objetos "gatilho" que funcionam bem com o mapa de demo

Como a UI remapeia classes COCO, estes objetos produzem detecções
visíveis durante a demo ao vivo:

| Objeto físico (classe COCO) | Label exibido na UI   | Severidade |
|-----------------------------|-----------------------|------------|
| garrafa de água (`bottle`)  | `escorrimento`        | Alto       |
| xícara/caneca (`cup`)       | `bolha`               | Médio      |
| livro (`book`)              | `falha_cobertura`     | Alto       |
| celular (`cell phone`)      | `risco`               | Baixo      |
| controle (`remote`)         | `casca_de_laranja`    | Médio      |
| pessoa (`person`)           | `desgaste_generico`   | Baixo      |

Leve alguns desses objetos para a demo — a detecção é confiável
em boa iluminação.

## Imagens de chassis / defeitos de pintura para upload

Para o passo de upload (roteiro item 4), prepare 3-5 imagens.
Opções recomendadas:

### A. Imagens públicas (Wikimedia, Unsplash)
Busque no Google Images por termos como:
- "paint run defect car"
- "orange peel paint automotive"
- "car paint bubble defect"
- "chassis rust"

Salve em `demo-kit/images/` (crie o subdiretório). Use fotos com
CC BY-SA ou similares.

### B. Datasets públicos (Roboflow Universe)
- https://universe.roboflow.com/ — buscar por "paint defect" ou
  "surface defect". Baixar 5-10 imagens de amostra em formato JPG.

### C. Fotos próprias
Se a equipe tem acesso a um chassi pintado, tire fotos com o
celular em boa iluminação (5000K LED ideal). Salve em
`demo-kit/images/`.

## Checklist pré-demo (fazer na terça à noite)

- [ ] `cd backend && uvicorn app.main:app --port 8000` — backend sobe
      sem erro.
- [ ] `curl http://localhost:8000/health` retorna `{"status":"ok"}`.
- [ ] `cd frontend && npm run dev` — frontend em `localhost:3000`.
- [ ] Badge "API: online" aparece na tela.
- [ ] Webcam é detectada pelo navegador (permissão concedida).
- [ ] Modo ao vivo funciona por pelo menos 30 s sem travar.
- [ ] Upload de uma imagem de teste retorna detecções.
- [ ] 5-10 imagens de chassis/defeitos em `demo-kit/images/`.
- [ ] Notebook carregado + fonte extra (bateria).
- [ ] Plano B: se a internet cair, tudo roda local (não depende de
      nuvem).

## Dicas finais para a demo

- **Iluminação**: avise que em ambiente real teremos LED 5000K
  dentro da câmara. Para a demo, uma mesa bem iluminada basta.
- **Distância**: fique ~30-50 cm da webcam para detecções estáveis.
- **Latência**: mencione os ~100-300 ms por inferência — é "tempo
  real" para inspeção (não para controle de processo).
- **Perguntas prováveis**:
  - *"Por que não treinaram o modelo?"* — O foco do semestre é
    documentação + pipeline funcional. O fine-tuning exige dataset
    rotulado, que estamos coletando.
  - *"E se não tiver internet na fábrica?"* — O FastAPI pode rodar
    localmente (é o que está acontecendo agora) ou em GPU local.
  - *"Por que YOLO e não outra rede?"* — Velocidade, boa precisão
    em detecção de objetos, ecossistema Ultralytics maduro.
