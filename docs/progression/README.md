# Magnus — Progression reports

Snapshots PDF auto-suficientes de cada versão do modelo, destinados a um
projeto externo de tracking de progressão (outro Claude Code).

## Versões registradas

| Versão | Arquivo | Modelo | Classes | mAP@50 | Data |
|---|---|---|---|---|---|
| **v0** | [`magnus_v0_snapshot.pdf`](./magnus_v0_snapshot.pdf) | YOLOv8n (3M) | 4 | 0,989 | 2026-05-19 |
| v1 | (a gerar após fine-tuning) | YOLO11s (9M) | 8 | — | — |

## Como regenerar

Cada versão tem um script `generate_<v>_pdf.py` ao lado do PDF. Tudo é
estático (dados embutidos no script) — basta rodar:

```bash
pip install reportlab
python docs/progression/generate_v0_pdf.py
```

## Quando criar o snapshot da v1

Após o treino do v2 (em `training/v2/`) concluir e o `best.pt` estar
publicado no Hugging Face Hub:

1. Copiar `generate_v0_pdf.py` para `generate_v1_pdf.py`.
2. Atualizar tabelas de métricas com os números reais do treino
   (Ultralytics imprime no fim do `yolo.train()`).
3. Atualizar o cabeçalho ("v0 baseline" → "v1 fine-tuned"), datas, e a
   seção "9. O que muda em v1" para descrever a próxima meta (v2).
4. Rodar `python docs/progression/generate_v1_pdf.py`.
5. Commit do PDF + script + atualizar esta tabela.

## Estrutura do PDF

Cada snapshot é auto-contido (não precisa de contexto externo):

1. Resumo executivo
2. Arquitetura
3. Detalhes técnicos do modelo
4. Métricas com leitura honesta das limitações
5. Stack tecnológica
6. Dataset usado
7. Endpoints da API
8. Limitações conhecidas
9. O que muda na próxima versão
10. Referências de código (commits-âncora)
