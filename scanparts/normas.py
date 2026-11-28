"""Interpretação de medidas por norma (recupera a intenção de projeto).

Furos passantes: ISO 273 (séries fina, média e grossa).
Pré-furos para rosca métrica grossa: tabela usual de brocas.
"""
from __future__ import annotations

# ISO 273 – furos passantes para parafusos (mm)
ISO273 = {
    #       fina   média  grossa
    "M2":   (2.2,  2.4,   2.6),
    "M2.5": (2.7,  2.9,   3.1),
    "M3":   (3.2,  3.4,   3.6),
    "M4":   (4.3,  4.5,   4.8),
    "M5":   (5.3,  5.5,   5.8),
    "M6":   (6.4,  6.6,   7.0),
    "M8":   (8.4,  9.0,  10.0),
    "M10":  (10.5, 11.0,  12.0),
    "M12":  (13.0, 13.5,  14.5),
    "M16":  (17.0, 17.5,  18.5),
}
SERIES = ("fina", "média", "grossa")

# pré-furo (broca) para rosca métrica grossa
PRE_FURO = {"M2": 1.6, "M2.5": 2.05, "M3": 2.5, "M4": 3.3, "M5": 4.2, "M6": 5.0,
            "M8": 6.8, "M10": 8.5, "M12": 10.2, "M16": 14.0}


def interpretar_furo(diametro_mm: float, tolerancia_mm: float = 0.25) -> dict:
    """Devolve a interpretação mais provável de um furo medido.

    Ex.: 9,02 mm -> {'nominal': 9.0, 'texto': 'Passante para M8 (ISO 273, série média)', ...}"""
    candidatos = []
    for rosca, valores in ISO273.items():
        for serie, d in zip(SERIES, valores):
            candidatos.append((abs(diametro_mm - d), d, f"Passante para {rosca} (ISO 273, série {serie})", rosca, "passante"))
    for rosca, d in PRE_FURO.items():
        candidatos.append((abs(diametro_mm - d), d, f"Pré-furo para rosca {rosca}", rosca, "pre_furo"))
    candidatos.sort(key=lambda c: (c[0], 0 if "média" in c[2] else 1))
    erro, d, texto, rosca, tipo = candidatos[0]
    if erro <= tolerancia_mm:
        # alternativas quase tão prováveis (ex.: 3,3 = pré-furo M4 × 3,4 = passante M3)
        alt = [c[2] for c in candidatos[1:] if c[1] != d and c[0] <= erro + 0.06 and c[0] <= tolerancia_mm]
        return {"nominal": d, "texto": texto, "rosca": rosca, "tipo": tipo, "diferenca_mm": round(diametro_mm - d, 3),
                "alternativas": alt[:2]}
    # sem correspondência: arredonda para o décimo de mm (broca comum)
    nominal = round(diametro_mm * 10) / 10
    return {"nominal": nominal, "texto": f"Furo Ø{nominal:.1f} mm (sem correspondência em norma)",
            "rosca": None, "tipo": "livre", "diferenca_mm": round(diametro_mm - nominal, 3)}
