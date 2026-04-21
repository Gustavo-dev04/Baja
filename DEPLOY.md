# Deploy — Backend (Hugging Face Spaces) + Frontend (Vercel)

Guia para colocar o protótipo no ar em URLs públicas. Tempo estimado:
**20-30 minutos**, tudo grátis.

## Por que essa combinação

| Componente | Plataforma | Motivo |
|---|---|---|
| Backend (FastAPI + YOLO) | **Hugging Face Spaces** (Docker) | Grátis, 16 GB RAM, feito para IA. Render free tier (512 MB) não aguenta YOLO. |
| Frontend (Next.js) | **Vercel** | Grátis, integração nativa com Next.js, deploy em ~2 minutos. |

Fluxo final: `chassi-baja.vercel.app` → `gustavo-baja-api.hf.space` → YOLO.

---

## Parte 1 — Backend no Hugging Face Spaces

### 1.1. Criar conta
- Cadastro em https://huggingface.co/join (grátis).

### 1.2. Criar o Space
- https://huggingface.co/new-space
- **Owner**: seu usuário.
- **Space name**: `baja-paint-inspection-api` (ou o que preferir).
- **License**: MIT.
- **SDK**: selecione **Docker** → **Blank** (template vazio).
- **Hardware**: **CPU basic — free**.
- **Public** (para poder acessar sem autenticação).
- Clique em **Create Space**.

### 1.3. Enviar os arquivos
O Space é um repositório Git. Na tela do Space clique em **Files** e
depois em **+ Add file → Upload files**, e faça upload da pasta
`backend/` inteira. Precisa subir:

```
Dockerfile
pyproject.toml
app/            (pasta inteira)
models/         (só o README; os pesos baixam sozinhos)
```

**Importante:** no topo do Space precisa existir um `README.md` com
frontmatter YAML. Crie um arquivo `README.md` com este conteúdo e
faça upload:

```markdown
---
title: Baja Paint Inspection API
emoji: 🏁
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

FastAPI + YOLO servindo detecção de defeitos de pintura para chassis BAJA.
```

### 1.4. Aguardar o build
- Depois do upload o Space começa a buildar automaticamente (aba
  **Logs**). Leva uns 5-8 minutos na primeira vez (instala torch,
  ultralytics, baixa yolov8n.pt no startup).
- Quando aparecer "Running on..." no log, está pronto.

### 1.5. Testar
Sua URL vai ser:
`https://<seu-usuario>-baja-paint-inspection-api.hf.space`

```bash
curl https://<seu-usuario>-baja-paint-inspection-api.hf.space/health
# {"status":"ok","model":"yolov8n.pt","demo_mode":true}
```

**Anote essa URL** — vai usar no passo 2.3.

---

## Parte 2 — Frontend na Vercel

### 2.1. Push do código para o GitHub
O repositório `gustavo-dev04/baja` já está no GitHub, branch
`claude/paint-inspection-ai-FRk8g`. Se quiser, faça merge para a
`main` antes de deployar (Vercel escolhe a branch padrão).

### 2.2. Criar projeto na Vercel
- https://vercel.com/signup → faça login com GitHub.
- **Add New → Project** → selecione o repositório `baja`.
- **Root Directory**: `frontend` (IMPORTANTE — o frontend está numa
  subpasta).
- **Framework Preset**: Next.js (auto-detectado).
- **Build/Output**: deixe padrão.

### 2.3. Configurar a URL da API
Antes de clicar em Deploy, na mesma tela expanda
**Environment Variables** e adicione:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<seu-usuario>-baja-paint-inspection-api.hf.space` |

Sem barra no final.

### 2.4. Deploy
Clique em **Deploy**. Em ~2 minutos fica pronto. Vai te dar uma URL
tipo `baja-xxxxxxxx.vercel.app`.

---

## Parte 3 — Liberar CORS no backend

A Vercel gerou uma URL tipo `baja-xyz.vercel.app`. O backend precisa
aceitar requisições dessa origem.

No Space do HF, abra o arquivo onde configura variáveis (em
**Settings → Variables and secrets** do Space). Adicione:

| Nome | Valor |
|---|---|
| `BAJA_ALLOWED_ORIGINS` | `https://baja-xyz.vercel.app` |

(Substitua pela URL real da Vercel.)

O Space vai reiniciar automaticamente (~30 s). Depois disso,
abra a URL da Vercel no celular ou notebook — tudo funciona via
HTTPS, inclusive webcam.

---

## Parte 4 — Verificar no celular

1. Abra `https://baja-xyz.vercel.app` no Chrome/Safari do celular.
2. Badge **"API: online"** deve aparecer no canto superior direito.
3. Clique em **Iniciar modo ao vivo** → browser pede permissão de
   câmera → aceite.
4. Aponte para uma garrafa ou caneca → bounding boxes aparecem em
   tempo real.

## Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| Badge "API: offline" | URL errada em `NEXT_PUBLIC_API_URL` ou CORS bloqueando. | Confirme URL do Space e que `BAJA_ALLOWED_ORIGINS` inclui o domínio da Vercel. |
| "Failed to fetch" no console | Mixed content (HTTP vs HTTPS). | O Space tem que ser HTTPS. HF gera HTTPS por padrão, confira a URL. |
| Webcam não abre no celular | Permissão negada ou navegador antigo. | Use Chrome (Android) ou Safari (iOS) atualizados. Abra `chrome://settings/content/camera` para rever permissões. |
| Build do Space falha no HF | Imagem Docker muito grande ou erro de dependência. | Ver logs; costuma ser OOM em CPU free — tente rebuildar. |
| Inferência lenta (> 2s) | CPU free do HF é modesta. | Aceitável para demo; para produção, upgrade ($9/mês) ou GPU Space. |

## Alternativas se precisar

- **Backend em Render** (se HF Spaces falhar): plano Starter $7/mês
  com 512MB-2GB. Free tier não aguenta YOLO.
- **Frontend em Netlify**: igualmente grátis, configuração idêntica.
- **Tudo em uma única VM** (Railway, DigitalOcean droplet): se
  quiser domínio próprio depois.

## Checklist final

- [ ] Space HF buildou com sucesso e `/health` responde.
- [ ] Projeto Vercel tem `NEXT_PUBLIC_API_URL` setado.
- [ ] `BAJA_ALLOWED_ORIGINS` no HF inclui o domínio da Vercel.
- [ ] Badge "API: online" aparece no frontend em produção.
- [ ] Testado no celular via HTTPS: webcam + detecção funcionam.
- [ ] URL da Vercel anotada para apresentar na quarta.
