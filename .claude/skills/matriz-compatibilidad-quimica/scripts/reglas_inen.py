"""Clausulas 6.1.7.5 y 6.1.7.10 b) de la NTE INEN 2266:2013.

El Anexo K opera por clase ONU, demasiado grueso para decidir almacenamiento:
acidos y bases son ambos Clase 8 y su celda es amarilla, pero la clausula b.7 los
prohibe. Estas reglas endurecen la matriz; nunca la relajan.
"""

# Vocabulario controlado de la columna `subgrupo` del inventario.
SUBGRUPOS = [
    "acido", "base", "comburente", "reductor", "combustible", "inflamable",
    "toxico", "alimento", "radiactivo", "infeccioso", "explosivo", "detonador",
]

# (subgrupo_a, subgrupo_b, clausula, texto literal de la norma)
PROHIBICIONES = [
    ("toxico", "alimento", "6.1.7.10 b.1",
     "Materiales toxicos con alimentos o semillas o cultivos agricolas comestibles"),
    ("combustible", "comburente", "6.1.7.10 b.2", "Combustibles con comburentes"),
    ("explosivo", "detonador", "6.1.7.10 b.3", "Explosivos con fulminantes o detonadores"),
    ("inflamable", "comburente", "6.1.7.10 b.4", "Liquidos inflamables con comburentes"),
    ("acido", "base", "6.1.7.10 b.7", "Acidos con bases"),
    ("comburente", "reductor", "6.1.7.10 b.8", "Oxidantes (comburentes) con reductores"),
]

# Subgrupos que la norma aisla de todo lo demas.
AISLAN_DE_TODO = [
    ("radiactivo", "6.1.7.10 b.5", "Material radioactivo con otro cualquiera"),
    ("infeccioso", "6.1.7.10 b.6", "Sustancias infecciosas con ninguna otra"),
]

GRAVEDAD = {"V": 0, "A": 1, "R": 2}


def peor(*codigos):
    return max(codigos, key=lambda c: GRAVEDAD.get(c, 0))


def subgrupos_de(producto):
    crudo = (producto.get("subgrupo") or "").lower()
    return {s for s in SUBGRUPOS if s in crudo}


def clases_de(producto):
    """Clase ONU principal mas el riesgo secundario, si lo declara."""
    clases = [producto.get("clase_onu", "").strip()]
    sec = (producto.get("riesgo_sec") or "").strip()
    if sec:
        clases.append(sec)
    return [c for c in clases if c]


def evaluar(a, b, anexo_k):
    """Devuelve (codigo, lista_de_motivos) para el par a-b segun la INEN 2266."""
    motivos = []

    # 1. Anexo K, considerando tambien los riesgos secundarios de ambos productos.
    codigo = "V"
    for ca in clases_de(a):
        for cb in clases_de(b):
            celda = anexo_k.get((ca, cb), "A")
            if GRAVEDAD.get(celda, 0) > GRAVEDAD[codigo]:
                codigo = celda
                etiqueta = f"Anexo K, {ca} x {cb}"
                if ca != a.get("clase_onu") or cb != b.get("clase_onu"):
                    etiqueta += " (por riesgo secundario)"
                motivos = [etiqueta]
            elif celda == codigo and not motivos:
                motivos = [f"Anexo K, {ca} x {cb}"]

    # 2. Clausulas expresas: endurecen a R.
    sa, sb = subgrupos_de(a), subgrupos_de(b)
    for uno, otro, clausula, texto in PROHIBICIONES:
        if (uno in sa and otro in sb) or (otro in sa and uno in sb):
            codigo = "R"
            motivos.append(f"{clausula}: {texto}")
    for sub, clausula, texto in AISLAN_DE_TODO:
        if sub in sa or sub in sb:
            codigo = "R"
            motivos.append(f"{clausula}: {texto}")

    return codigo, motivos
