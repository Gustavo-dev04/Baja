"""2ª passagem: acha a página impressa de cada seção/legenda no PDF da 1ª passagem."""
import json, subprocess, sys, re
pdf, chaves_json, saida = sys.argv[1], sys.argv[2], sys.argv[3]
chaves = json.load(open(chaves_json))
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
txt = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
linhas = [[re.sub(r"\s+", " ", l).strip() for l in t.splitlines()] for t in txt]
# primeira página textual: contém "1 INTRODUÇÃO" e não é o sumário
ini = next(i for i, t in enumerate(txt) if "1 INTRODUÇÃO" in t and "SUMÁRIO" not in t)
res, falta = {}, []
cursor = {"h": ini, "Figura": ini, "Quadro": ini, "Tabela": ini}
for c in chaves:
    tipo = "h" if c.startswith("h:") else c.split()[0]
    alvo = re.sub(r"\s+", " ", c[2:] if tipo == "h" else c)
    achou = None
    for i in range(cursor[tipo], n):
        if any(l.startswith(alvo[:40]) for l in linhas[i]):
            achou = i
            break
    if achou is None:
        falta.append(c); continue
    cursor[tipo] = achou
    res[c] = achou  # índice físico 0-based = número impresso (capa não é contada)
json.dump(res, open(saida, "w"), ensure_ascii=False, indent=1)
print(f"{len(res)}/{len(chaves)} localizadas; total {n} páginas; textual começa na pág. impressa {ini}")
if falta: print("NÃO ACHADAS:", falta)
