#!/bin/bash
# Gera o relatório ABNT em duas passagens (a 2ª preenche os números de página).
set -e
cd "$(dirname "$0")"
SOFFICE=${SOFFICE:-soffice}
node gerar_relatorio.js
$SOFFICE --headless --convert-to pdf Relatorio_ScanParts_ABNT.docx >/dev/null 2>&1
python3 paginas.py Relatorio_ScanParts_ABNT.pdf chaves.json paginas.json
node gerar_relatorio.js paginas.json
zip -d Relatorio_ScanParts_ABNT.docx '*/' >/dev/null 2>&1 || true
$SOFFICE --headless --convert-to pdf Relatorio_ScanParts_ABNT.docx >/dev/null 2>&1
python3 paginas.py Relatorio_ScanParts_ABNT.pdf chaves.json paginas_verif.json
cmp -s <(python3 -c "import json;print(json.load(open('paginas.json')))") <(python3 -c "import json;print(json.load(open('paginas_verif.json')))") && echo "Sumário confere com o PDF final" || echo "ATENÇÃO: páginas mudaram na 2ª passagem"
rm -f chaves.json paginas_verif.json
