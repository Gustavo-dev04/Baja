# Frontend — Dashboard de Inspeção

Next.js 14 (App Router) + Tailwind. Mostra o feed da webcam, permite upload
de imagens e desenha as detecções vindas do backend sobre a imagem.

## Rodar localmente

```bash
npm install
npm run dev
```

Abra `http://localhost:3000`. O frontend chama `http://localhost:8000`
por padrão.

## Configuração

Use uma variável de ambiente para apontar a API em produção:

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://sua-api.huggingface.space
```

## Estrutura

- `app/page.tsx` — dashboard.
- `app/components/CameraFeed.tsx` — captura via `getUserMedia`.
- `app/components/UploadPanel.tsx` — upload alternativo.
- `app/components/DetectionOverlay.tsx` — desenha bounding boxes.
- `app/components/ResultsPanel.tsx` — lista de defeitos + metadados.
- `app/lib/api.ts` — cliente HTTP para `/inspect` e `/health`.
