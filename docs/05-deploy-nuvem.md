# 05 — Deploy em Nuvem

## Opções avaliadas

| Provedor                         | Treino custom | Custo protótipo | Facilidade | Escolhido |
|----------------------------------|---------------|-----------------|------------|-----------|
| **Hugging Face Spaces**          | Não (hosting) | Grátis          | Alta       | ✅ Recomendado |
| **Render** (free tier)           | Não           | Grátis*         | Média      | Alternativa |
| **Roboflow Inference API**       | Sim, integrado| Grátis (limitado)| Alta      | Para Fase 2 |
| AWS Rekognition Custom Labels    | Sim           | $$$             | Média      | Produção   |
| Azure Custom Vision              | Sim           | $$              | Alta       | Produção   |
| GCP Vertex AI                    | Sim           | $$$             | Baixa      | Escala    |

\* Render free tier adormece após inatividade; primeira requisição é
lenta.

## Recomendação: Hugging Face Spaces (Docker)

Vantagens:

- Grátis para imagens públicas.
- Suporta Dockerfile nativamente — reaproveitamos `backend/Dockerfile`.
- URL pública HTTPS sem configuração adicional.
- Fácil de citar na documentação científica.

## Passos de deploy

### 1. Preparar o espaço

1. Criar conta em huggingface.co.
2. Criar novo Space → escolher template **Docker**.
3. Clonar o repositório do Space localmente.

### 2. Copiar o backend

```bash
cp -r Baja/backend/* <space-repo>/
```

O Hugging Face Spaces procura `Dockerfile` na raiz do Space.

### 3. Commit e push

```bash
cd <space-repo>
git add .
git commit -m "Initial deploy"
git push
```

Em ~2 minutos o Space estará em
`https://<user>-<space-name>.hf.space`.

### 4. Apontar o frontend

Em `frontend/.env.local` (ou variáveis do provedor onde o frontend for
hospedado):

```bash
NEXT_PUBLIC_API_URL=https://<user>-<space-name>.hf.space
```

## Deploy alternativo: Render

1. Conectar repositório GitHub.
2. Tipo de serviço: **Web Service**.
3. Build command: `pip install .` · Start command:
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Plano: Free.

## Deploy do frontend

Vercel é o caminho natural para Next.js:

```bash
npx vercel
```

Configure `NEXT_PUBLIC_API_URL` no painel da Vercel apontando para a
URL do Space.

## CORS

O backend já libera `http://localhost:3000` por padrão. Em produção
defina a variável:

```bash
BAJA_ALLOWED_ORIGINS=https://seu-dominio.vercel.app,http://localhost:3000
```
