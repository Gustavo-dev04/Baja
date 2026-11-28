"""Exportação: DXF (mm) e script Python do Autodesk Fusion que recria a peça por extrusão."""
from __future__ import annotations

import math
from pathlib import Path

from .geometria import angulos_arco


def exportar_dxf(caminho: Path, contorno, furos, espessura_mm: float):
    import ezdxf
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.layers.add("CONTORNO", color=7)
    doc.layers.add("FUROS", color=1)
    doc.layers.add("TEXTO", color=8)
    msp = doc.modelspace()
    for e in contorno:
        _dxf_entidade(msp, e, "CONTORNO")
    for f in furos:
        if f.get("redondo", True):
            msp.add_circle(f["centro"], f["raio_cad"], dxfattribs={"layer": "FUROS"})
        else:
            msp.add_lwpolyline(f["contorno_mm"], close=True, dxfattribs={"layer": "FUROS"})
    msp.add_text(f"ScanParts - espessura {espessura_mm:.2f} mm", height=2.5,
                 dxfattribs={"layer": "TEXTO"}).set_placement(_canto_texto(contorno))
    doc.saveas(caminho)


def _dxf_entidade(msp, e, layer):
    if e.tipo == "linha":
        msp.add_line(e.p0, e.p1, dxfattribs={"layer": layer})
    elif e.tipo == "circulo":
        msp.add_circle(e.centro, e.raio, dxfattribs={"layer": layer})
    elif e.tipo == "arco":
        a0, a1 = angulos_arco(e)
        ini, fim = (a0, a1) if a1 > a0 else (a1, a0)   # DXF: sempre anti-horário
        msp.add_arc(e.centro, e.raio, math.degrees(ini), math.degrees(fim), dxfattribs={"layer": layer})
    elif e.tipo == "polilinha":
        msp.add_lwpolyline(e.pontos, dxfattribs={"layer": layer})


def _canto_texto(contorno):
    xs, ys = [], []
    for e in contorno:
        for k in ("p0", "p1", "centro"):
            if hasattr(e, k):
                xs.append(getattr(e, k)[0]); ys.append(getattr(e, k)[1])
        if e.tipo == "polilinha":
            xs += [p[0] for p in e.pontos]; ys += [p[1] for p in e.pontos]
    return (min(xs), min(ys) - 8) if xs else (0, -8)


SCRIPT_FUSION = '''"""Gerado pelo ScanParts – recria a peça no Autodesk Fusion.

Como rodar: Utilitários > Suplementos > Scripts e suplementos > Criar (Python),
abra o arquivo .py criado, cole este conteúdo no lugar e clique em Executar.
Unidades: o código trabalha em mm e converte para cm (unidade interna da API do Fusion).
"""
import adsk.core, adsk.fusion, traceback

ESPESSURA_MM = {espessura}
LINHAS = {linhas}        # [(x0, y0, x1, y1), ...]
ARCOS = {arcos}          # [(x_ini, y_ini, x_meio, y_meio, x_fim, y_fim), ...]
POLILINHAS = {polis}     # [[(x, y), ...], ...]
CIRCULOS_CONTORNO = {circulos}  # [(cx, cy, r), ...]
FUROS = {furos}          # [(cx, cy, diametro, "descrição"), ...]


def P(x, y):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, 0)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Abra um design (Arquivo > Novo design) antes de rodar o script.")
            return
        root = design.rootComponent
        params = design.userParameters
        if params.itemByName("espessura") is None:
            params.add("espessura", adsk.core.ValueInput.createByString("%.3f mm" % ESPESSURA_MM), "mm",
                       "Espessura medida pelo ScanParts")

        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = "ScanParts - contorno"
        linhas = sk.sketchCurves.sketchLines
        arcos = sk.sketchCurves.sketchArcs
        circulos = sk.sketchCurves.sketchCircles
        pontas = []   # (SketchPoint) de todas as curvas do contorno, para ligar as pontas

        for x0, y0, x1, y1 in LINHAS:
            ln = linhas.addByTwoPoints(P(x0, y0), P(x1, y1))
            pontas += [ln.startSketchPoint, ln.endSketchPoint]
        for xa, ya, xm, ym, xb, yb in ARCOS:
            ar = arcos.addByThreePoints(P(xa, ya), P(xm, ym), P(xb, yb))
            pontas += [ar.startSketchPoint, ar.endSketchPoint]
        for pts in POLILINHAS:
            for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
                ln = linhas.addByTwoPoints(P(xa, ya), P(xb, yb))
                pontas += [ln.startSketchPoint, ln.endSketchPoint]
        for cx, cy, r in CIRCULOS_CONTORNO:
            circulos.addByCenterRadius(P(cx, cy), r / 10.0)

        # liga pontas coincidentes (fecha o contorno para o Fusion achar o perfil)
        restr = sk.geometricConstraints
        usados = set()
        for i, a in enumerate(pontas):
            if i in usados:
                continue
            for j in range(i + 1, len(pontas)):
                if j in usados:
                    continue
                b = pontas[j]
                if a.geometry.distanceTo(b.geometry) < 0.002:   # 0,02 mm
                    try:
                        restr.addCoincident(a, b)
                    except Exception:
                        pass
                    usados.update((i, j))
                    break

        # furos com cota de diâmetro editável
        for cx, cy, d, desc in FUROS:
            c = circulos.addByCenterRadius(P(cx, cy), d / 20.0)
            try:
                sk.sketchDimensions.addDiameterDimension(c, P(cx + d * 0.8, cy + d * 0.8))
            except Exception:
                pass

        # extruda o perfil maior (a chapa, já descontando os furos)
        perfis = [sk.profiles.item(i) for i in range(sk.profiles.count)]
        if not perfis:
            ui.messageBox("Não foi possível fechar o contorno (nenhum perfil encontrado).")
            return
        acc = adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy
        chapa = max(perfis, key=lambda p: p.areaProperties(acc).area)
        ext = root.features.extrudeFeatures.addSimple(
            chapa, adsk.core.ValueInput.createByString("espessura"),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext.bodies.item(0).name = "Peca ScanParts"
        ui.messageBox("Peça criada pelo ScanParts.\\n%d furos, espessura %.2f mm (parâmetro 'espessura')."
                      % (len(FUROS), ESPESSURA_MM))
    except Exception:
        if ui:
            ui.messageBox("Falha:\\n{{}}".format(traceback.format_exc()))
'''


def exportar_fusion(caminho: Path, contorno, furos, espessura_mm: float):
    r = lambda v: round(float(v), 4)
    linhas, arcos, polis, circs = [], [], [], []
    for e in contorno:
        if e.tipo == "linha":
            linhas.append((r(e.p0[0]), r(e.p0[1]), r(e.p1[0]), r(e.p1[1])))
        elif e.tipo == "arco":
            arcos.append((r(e.p0[0]), r(e.p0[1]), r(e.meio[0]), r(e.meio[1]), r(e.p1[0]), r(e.p1[1])))
        elif e.tipo == "polilinha":
            pts = [(r(x), r(y)) for x, y in e.pontos]
            if pts[0] != pts[-1] and len(contorno) == 1:
                pts.append(pts[0])
            polis.append(pts)
        elif e.tipo == "circulo":
            circs.append((r(e.centro[0]), r(e.centro[1]), r(e.raio)))
    fur = [(r(f["centro"][0]), r(f["centro"][1]), r(f["diametro_cad"]), f["interpretacao"]["texto"])
           for f in furos if f.get("redondo", True)]
    for f in furos:          # furos não redondos (oblongos/irregulares) entram como polilinha fechada
        if not f.get("redondo", True):
            pts = [(r(x), r(y)) for x, y in f["contorno_mm"]]
            polis.append(pts + [pts[0]])
    caminho.write_text(SCRIPT_FUSION.format(espessura=r(espessura_mm), linhas=repr(linhas), arcos=repr(arcos),
                                            polis=repr(polis), circulos=repr(circs), furos=repr(fur)), encoding="utf-8")
