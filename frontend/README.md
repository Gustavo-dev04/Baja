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

## Configuração para produção

Use uma variável de ambiente para apontar a API pública:

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://sua-api.hf.space
```

Também existe um exemplo pronto em `frontend/.env.example`.

## Observações para acesso por URL

- O badge **API: online/offline** ajuda a validar a integração.
- Em celular, a webcam normalmente exige **HTTPS**.
- Se a API estiver em outro domínio, configure `BAJA_ALLOWED_ORIGINS`
  no backend.

## Estrutura

- `app/page.tsx` — dashboard.
- `app/components/CameraFeed.tsx` — captura via `getUserMedia`.
- `app/components/UploadPanel.tsx` — upload alternativo.
- `app/components/DetectionOverlay.tsx` — desenha bounding boxes.
- `app/components/ResultsPanel.tsx` — lista de defeitos + metadados.
- `app/lib/api.ts` — cliente HTTP para `/inspect` e `/health`.
