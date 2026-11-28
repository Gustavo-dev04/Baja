"""ScanParts – linha de comando.

  python3 -m scanparts tabuleiro --saida tabuleiro.pdf
  python3 -m scanparts capturar --saida foto.jpg                      (no Jetson, câmera CSI)
  python3 -m scanparts calibrar --fotos "calib/*.jpg" --referencia prato.jpg --saida calibracao.json
  python3 -m scanparts medir foto.jpg --calibracao calibracao.json --espessura 3 --saida resultado/
  python3 -m scanparts simular --saida demo_sintetica/                (gera fotos de teste sem a bancada)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2


def cmd_tabuleiro(a):
    from .calibracao import gerar_pdf_tabuleiro
    gerar_pdf_tabuleiro(Path(a.saida))
    print(f"Tabuleiro salvo em {a.saida}. Imprima em 100% e confira a régua de 50 mm.")


def cmd_capturar(a):
    from .captura import capturar
    img = capturar(a.sensor, a.largura, a.altura, a.exposicao_us, a.ganho)
    cv2.imwrite(a.saida, img)
    print(f"Foto salva em {a.saida} ({img.shape[1]}x{img.shape[0]})")


def cmd_calibrar(a):
    from . import calibracao as cb
    fotos = cb.expandir(a.fotos)
    print(f"{len(fotos)} fotos do tabuleiro")
    cal = cb.calibrar(fotos, a.referencia, racional=a.racional)
    cb.salvar(cal, Path(a.saida))
    print(f"Calibração salva em {a.saida}")


def cmd_medir(a):
    from . import calibracao as cb
    from .exportar import exportar_dxf, exportar_fusion
    from .medicao import Medidor, alinhar
    t0 = time.time()
    img = cv2.imread(a.foto)
    if img is None:
        sys.exit(f"Não consegui abrir {a.foto}")
    med = Medidor(cb.carregar(a.calibracao))
    res = med.medir(img, a.espessura, arredondar_furos=not a.sem_norma)
    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    conf_img = med.sobreposicao(img, res)
    if a.ia:                      # etapa "Localização": YOLO confere os furos medidos
        from . import ia
        r = ia.conferir_furos(a.ia, img, med, res)
        ia.desenhar(conf_img, r)
        print(f"IA: {r['furos_confirmados']}/{r['furos_medidos']} furos confirmados pelo YOLO"
              + (f", {len(r['ia_sem_medida'])} caixa(s) sem furo medido – confira a foto" if r["ia_sem_medida"] else ""))
    cv2.imwrite(str(out / "conferencia.jpg"), conf_img)
    if not a.sem_alinhar:
        res = alinhar(res)        # CAD: maior aresta na horizontal, canto inferior esquerdo na origem
    exportar_dxf(out / "peca.dxf", res["contorno"], res["furos"], a.espessura)
    exportar_fusion(out / "peca_fusion.py", res["contorno"], res["furos"], a.espessura)
    relatorio = {k: v for k, v in res.items() if k not in ("contorno", "contorno_pontos_mm")}
    relatorio["contorno"] = [e.__dict__ for e in res["contorno"]]
    (out / "relatorio.json").write_text(json.dumps(relatorio, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    d = res["dimensoes_mm"]
    print(f"Peça {d['largura']:.2f} x {d['altura']:.2f} mm, espessura {a.espessura} mm, contorno: {res['contorno_info']}")
    for k, f in enumerate(res["furos"], 1):
        alt = f["interpretacao"].get("alternativas")
        print(f"  furo {k}: Ø{f['diametro_medido']:.2f} mm em ({f['centro'][0]:.2f}; {f['centro'][1]:.2f}) -> "
              f"{f['interpretacao']['texto']}" + (f"  (ou: {', '.join(alt)})" if alt else ""))
    print(f"Arquivos em {out}/ (conferencia.jpg, peca.dxf, peca_fusion.py, relatorio.json) – {time.time() - t0:.1f} s")


def cmd_simular(a):
    import math
    from . import calibracao as cb
    from . import simulador as sm
    out = Path(a.saida)
    (out / "calibracao").mkdir(parents=True, exist_ok=True)
    cam = sm.Camera.imx219()
    for i, (R, t) in enumerate(sm.poses_calibracao(a.fotos_calibracao)):
        cv2.imwrite(str(out / "calibracao" / f"tabuleiro_{i:02d}.jpg"), sm.renderizar_tabuleiro(cam, R, t, seed=i))
    R, t = sm.pose_tabuleiro_plano()
    cv2.imwrite(str(out / "referencia_prato.jpg"), sm.renderizar_tabuleiro(cam, R, t, seed=99))
    peca = sm.PECAS[a.peca]()
    img, _ = sm.renderizar_peca(cam, peca, a.espessura, math.radians(a.angulo), 0, 0, seed=1)
    cv2.imwrite(str(out / f"{a.peca}.jpg"), img)
    print(f"Fotos sintéticas em {out}/. Próximo passo:\n"
          f"  python3 -m scanparts calibrar --fotos \"{out}/calibracao/*.jpg\" --referencia {out}/referencia_prato.jpg --saida {out}/calibracao.json\n"
          f"  python3 -m scanparts medir {out}/{a.peca}.jpg --calibracao {out}/calibracao.json --espessura {a.espessura} --saida {out}/resultado")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scanparts", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tabuleiro", help="gera o PDF do tabuleiro de calibração")
    p.add_argument("--saida", default="tabuleiro_scanparts.pdf")
    p.set_defaults(f=cmd_tabuleiro)
    p = sub.add_parser("capturar", help="tira uma foto com a IMX219 (Jetson)")
    p.add_argument("--saida", default="foto.jpg")
    p.add_argument("--sensor", type=int, default=0)
    p.add_argument("--largura", type=int, default=3280)
    p.add_argument("--altura", type=int, default=2464)
    p.add_argument("--exposicao-us", type=int, default=None, help="exposição fixa em µs (sem automático)")
    p.add_argument("--ganho", type=float, default=None)
    p.set_defaults(f=cmd_capturar)
    p = sub.add_parser("calibrar", help="calibra a lente e o prato")
    p.add_argument("--fotos", required=True, help='padrão das fotos do tabuleiro, ex.: "calib/*.jpg"')
    p.add_argument("--referencia", required=True, help="foto do tabuleiro deitado no centro do prato")
    p.add_argument("--saida", default="calibracao.json")
    p.add_argument("--racional", action="store_true", help="modelo de distorção com 8 coeficientes (lentes muito abertas)")
    p.set_defaults(f=cmd_calibrar)
    p = sub.add_parser("medir", help="mede a peça e gera DXF + script do Fusion")
    p.add_argument("foto")
    p.add_argument("--calibracao", default="calibracao.json")
    p.add_argument("--espessura", type=float, required=True, help="espessura da chapa em mm (paquímetro)")
    p.add_argument("--saida", default="resultado")
    p.add_argument("--sem-norma", action="store_true", help="não arredonda os furos para a medida de norma")
    p.add_argument("--sem-alinhar", action="store_true", help="mantém a posição da peça no prato (não alinha ao eixo X)")
    p.add_argument("--ia", default=None, help="modelo YOLO (.pt/.engine) que confere os furos medidos, ex.: ia/modelos/furos_v1.pt")
    p.set_defaults(f=cmd_medir)
    p = sub.add_parser("simular", help="gera fotos sintéticas da bancada para testar sem hardware")
    p.add_argument("--saida", default="demo_sintetica")
    p.add_argument("--peca", default="suporte_retangular", choices=["suporte_retangular", "suporte_L", "flange"])
    p.add_argument("--espessura", type=float, default=3.0)
    p.add_argument("--angulo", type=float, default=20.0)
    p.add_argument("--fotos-calibracao", type=int, default=15)
    p.set_defaults(f=cmd_simular)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
