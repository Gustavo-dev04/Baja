# 02 — Arquitetura

## Diagrama de blocos

```mermaid
flowchart LR
    subgraph Camara["Câmara de Inspeção"]
      C1[Câmera 1]
      C2[Câmera 2]
      Cn[Câmera N]
      LED[Iluminação LED difusa]
    end

    subgraph Edge["Gateway Local"]
      FE[Frontend Next.js]
    end

    subgraph Cloud["Nuvem"]
      API[FastAPI /inspect]
      YOLO[Modelo YOLO pré-treinado + fine-tuned]
    end

    C1 --> FE
    C2 --> FE
    Cn --> FE
    FE -- "POST imagem" --> API
    API --> YOLO
    YOLO -- "JSON detecções" --> API
    API -- "JSON" --> FE
```

## Fluxo de inspeção (sequence)

```mermaid
sequenceDiagram
    actor Op as Operador
    participant UI as Frontend (Next.js)
    participant API as Backend (FastAPI)
    participant IA as Modelo YOLO

    Op->>UI: Aciona "Capturar e Inspecionar"
    UI->>UI: Captura frame via getUserMedia
    UI->>API: POST /inspect (multipart image)
    API->>IA: model.predict(image)
    IA-->>API: boxes + classes + conf
    API-->>UI: JSON InspectionResult
    UI->>Op: Overlay + lista de defeitos
```

## Decisões arquiteturais

### Nuvem vs. Edge

Optamos por **inferência na nuvem via API REST** por três razões:

1. **Custo inicial zero** — serviços como Hugging Face Spaces e Render
   oferecem tier gratuito suficiente para protótipo e demonstração.
2. **Escalabilidade do modelo** — atualizar o modelo significa apenas
   re-deployar a API; não exige atualizar hardware dentro da câmara.
3. **Flexibilidade didática** — o projeto pode comparar provedores
   (Roboflow, AWS Rekognition Custom Labels, Azure Custom Vision) sem
   reescrever o cliente.

Trade-off: dependência de rede. Mitigação prevista em fases futuras:
buffer local de imagens e retry exponencial.

### Protocolo

`HTTP/REST` com `multipart/form-data` é suficiente para o regime alvo
(<2 s por inspeção). WebSocket/RTSP ficam como evolução para streaming
contínuo.

### Contratos

Ver [`04-modelo-ia.md`](./04-modelo-ia.md) para o schema de resposta
(`InspectionResult`) e [`05-deploy-nuvem.md`](./05-deploy-nuvem.md) para
a topologia de deploy.
