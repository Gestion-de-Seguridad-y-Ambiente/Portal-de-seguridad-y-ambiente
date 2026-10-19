#!/usr/bin/env python3
"""Genera la matriz de compatibilidad quimica en HTML a partir de un inventario CSV.

Uso:
    python3 generar_matriz.py inventario.csv salida.html [--empresa "Plantabal S.A."]

El inventario debe traer al menos las columnas: codigo, producto, grupo, ubicacion.
Opcionales: proveedor, cas, concentracion, clases_ghs, codigos_h, cantidad,
incompat_sds, observaciones.
"""

import argparse
import csv
import html
import os
import re
import sys
from datetime import date

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")

GRUPOS = {
    "G1": "Explosivos y pirotecnicos",
    "G2": "Gases inflamables",
    "G3": "Gases comprimidos inertes",
    "G4": "Gases oxidantes",
    "G5": "Liquidos inflamables y combustibles",
    "G6": "Solidos inflamables, pirofóricos y autorreactivos",
    "G7": "Reactivos con agua",
    "G8": "Oxidantes (solidos y liquidos)",
    "G9": "Peroxidos organicos",
    "G10": "Toxicos agudos y plaguicidas",
    "G11": "Acidos inorganicos no oxidantes",
    "G12": "Acidos oxidantes fuertes",
    "G13": "Acidos organicos",
    "G14": "Bases y alcalis",
    "G15": "Miscelaneos / peligro ambiental / no peligrosos",
}

# Palabras que, encontradas en la Seccion 10.5 de una SDS, apuntan a un grupo.
PISTAS_SDS = {
    "G2": ["gas inflamable", "acetileno", "propano", "glp", "hidrogeno"],
    "G4": ["oxigeno", "cloro gas"],
    "G5": ["inflamable", "solvente", "disolvente", "combustible", "hidrocarburo",
            "alcohol", "acetona", "thinner", "diesel", "gasolina"],
    "G6": ["azufre", "fosforo", "material combustible", "pirofor"],
    "G7": ["agua", "humedad", "carburo", "sodio metalico", "hidruro"],
    "G8": ["oxidante", "comburente", "hipoclorito", "permanganato", "nitrato",
            "perox" ,"clorato"],
    "G9": ["peroxido organico"],
    "G10": ["plaguicida", "pesticida", "cianuro", "toxico"],
    "G11": ["acido clorhidrico", "acido fosforico", "acido muriatico", "acido"],
    "G12": ["acido nitrico", "acido sulfurico", "acido perclorico", "oleum"],
    "G13": ["acido acetico", "acido formico", "acido citrico", "acido organico"],
    "G14": ["base", "alcali", "soda caustica", "hidroxido", "amoniaco", "amoniaco",
             "cal viva"],
}

ETIQUETA = {
    "C": "Compatible",
    "S": "Separar (cubeto distinto, min. 3 m o barrera)",
    "X": "Incompatible (bodegas o areas separadas)",
}


def normaliza(texto):
    """Minusculas sin tildes, para comparar texto de SDS."""
    texto = texto.lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        texto = texto.replace(a, b)
    return texto


def cargar_matriz_base(ruta):
    matriz = {}
    with open(ruta, encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            origen = fila["grupo"]
            for destino, codigo in fila.items():
                if destino != "grupo":
                    matriz[(origen, destino)] = codigo.strip()
    return matriz


def cargar_inventario(ruta):
    with open(ruta, encoding="utf-8-sig") as fh:
        productos = [
            {k: (v or "").strip() for k, v in fila.items() if k}
            for fila in csv.DictReader(fh)
        ]
    errores = []
    for i, p in enumerate(productos, start=2):
        if not p.get("producto"):
            errores.append(f"Fila {i}: falta el nombre del producto.")
        grupo = p.get("grupo", "")
        if grupo not in GRUPOS:
            errores.append(
                f"Fila {i} ({p.get('producto', '?')}): grupo '{grupo}' invalido. "
                f"Debe ser uno de G1..G15."
            )
    if errores:
        raise SystemExit("Inventario con errores:\n  - " + "\n  - ".join(errores))
    return productos


def grupos_citados_en_sds(texto):
    """Grupos que la Seccion 10.5 de la SDS menciona como incompatibles."""
    if not texto or normaliza(texto).startswith("sin dato"):
        return set()
    t = normaliza(texto)
    encontrados = set()
    for grupo, pistas in PISTAS_SDS.items():
        if any(pista in t for pista in pistas):
            encontrados.add(grupo)
    return encontrados


def celda(a, b, matriz):
    """Resultado para el par (a, b): codigo, si lo endurecio la SDS, y por que."""
    base = matriz.get((a["grupo"], b["grupo"]), "X")
    if a is b:
        return base, False, ""

    motivos = []
    if b["grupo"] in grupos_citados_en_sds(a.get("incompat_sds", "")):
        motivos.append(f"SDS de {a['producto']} declara incompatible este tipo de producto")
    if a["grupo"] in grupos_citados_en_sds(b.get("incompat_sds", "")):
        motivos.append(f"SDS de {b['producto']} declara incompatible este tipo de producto")

    if motivos and base != "X":
        return "X", True, "; ".join(motivos)
    return base, False, "; ".join(motivos)


def zona(ubicacion):
    """Area mayor de la ubicacion: 'Bodega A - Estante 1' -> 'bodega a'."""
    return normaliza(ubicacion.split("-")[0]).strip()


def conflictos_por_ubicacion(productos, matriz):
    """Pares mal segregados segun lo que hoy declara el inventario.

    X exige areas separadas: basta compartir zona para que sea hallazgo.
    S exige cubeto distinto: solo es hallazgo si comparten la ubicacion exacta.
    """
    hallazgos = []
    for i, a in enumerate(productos):
        for b in productos[i + 1:]:
            ua, ub = a.get("ubicacion", ""), b.get("ubicacion", "")
            if not ua or not ub:
                continue
            misma_ubicacion = normaliza(ua) == normaliza(ub)
            misma_zona = zona(ua) == zona(ub)
            if not misma_zona:
                continue
            codigo, por_sds, motivo = celda(a, b, matriz)
            if codigo == "X":
                alcance = "misma ubicacion" if misma_ubicacion else "misma zona"
                detalle = f"{ua} / {ub}" if not misma_ubicacion else ua
                hallazgos.append((a, b, codigo, por_sds, motivo, f"{detalle} ({alcance})"))
            elif codigo == "S" and misma_ubicacion:
                hallazgos.append((a, b, codigo, por_sds, motivo, f"{ua} (misma ubicacion)"))
    orden = {"X": 0, "S": 1}
    hallazgos.sort(key=lambda h: orden.get(h[2], 2))
    return hallazgos


def vacios(productos):
    pendientes = []
    for p in productos:
        texto = p.get("incompat_sds", "")
        if not texto or normaliza(texto).startswith("sin dato"):
            pendientes.append(
                (p["producto"], "Seccion 10.5 de la SDS sin datos utiles: solicitar SDS actualizada")
            )
        if not p.get("codigos_h"):
            pendientes.append((p["producto"], "Sin codigos H registrados (Seccion 2)"))
        if not p.get("ubicacion"):
            pendientes.append((p["producto"], "Sin ubicacion de almacenamiento declarada"))
    return pendientes


def render(productos, matriz, empresa):
    e = html.escape
    hoy = date.today().strftime("%d/%m/%Y")
    n = len(productos)

    filas = []
    for a in productos:
        celdas = []
        for b in productos:
            if a is b:
                celdas.append('<td class="self">&mdash;</td>')
                continue
            codigo, por_sds, motivo = celda(a, b, matriz)
            marca = "*" if por_sds else ""
            titulo = f"{a['producto']} ({a['grupo']}) / {b['producto']} ({b['grupo']}): {ETIQUETA[codigo]}"
            if motivo:
                titulo += f" — {motivo}"
            celdas.append(
                f'<td class="c-{codigo.lower()}" title="{e(titulo)}">{codigo}{marca}</td>'
            )
        filas.append(
            f'<tr><th class="rowh"><span class="cod">{e(a.get("codigo", ""))}</span>'
            f'{e(a["producto"])}<span class="grp">{e(a["grupo"])}</span></th>'
            + "".join(celdas)
            + "</tr>"
        )

    encabezados = "".join(
        f'<th class="colh"><div>{e(p.get("codigo") or p["producto"][:18])}</div></th>'
        for p in productos
    )

    hallazgos = conflictos_por_ubicacion(productos, matriz)
    if hallazgos:
        filas_conf = "".join(
            f'<tr class="h-{c.lower()}"><td>{e(ub)}</td><td>{e(a["producto"])}</td>'
            f'<td>{e(b["producto"])}</td><td class="c-{c.lower()}">{c}</td>'
            f'<td>{e(motivo or ETIQUETA[c])}</td></tr>'
            for a, b, c, por_sds, motivo, ub in hallazgos
        )
        bloque_conf = (
            '<table class="lista"><thead><tr><th>Ubicacion</th><th>Producto A</th>'
            '<th>Producto B</th><th>Codigo</th><th>Motivo</th></tr></thead>'
            f"<tbody>{filas_conf}</tbody></table>"
        )
    else:
        bloque_conf = '<p class="ok">Ningun par incompatible comparte ubicacion declarada.</p>'

    pendientes = vacios(productos)
    if pendientes:
        bloque_vac = (
            '<table class="lista"><thead><tr><th>Producto</th><th>Pendiente</th></tr></thead><tbody>'
            + "".join(f"<tr><td>{e(p)}</td><td>{e(m)}</td></tr>" for p, m in pendientes)
            + "</tbody></table>"
        )
    else:
        bloque_vac = '<p class="ok">Sin vacios de informacion.</p>'

    usados = sorted({p["grupo"] for p in productos}, key=lambda g: int(g[1:]))
    leyenda_grupos = "".join(
        f"<li><b>{g}</b> &mdash; {e(GRUPOS[g])}</li>" for g in usados
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matriz de compatibilidad quimica</title>
<style>
  :root {{
    --bg:#f6f7f9; --fg:#1b1f24; --card:#fff; --line:#d9dde3;
    --c:#1e7f4f; --cbg:#d8f0e2; --s:#a06a00; --sbg:#fdeec8; --x:#a31d1d; --xbg:#fadcdc;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#14171c; --fg:#e7eaee; --card:#1c2026; --line:#333a44;
      --cbg:#153324; --c:#6fd79e; --sbg:#3a2d0c; --s:#f0c04a; --xbg:#3c1618; --x:#f08a8a;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#14171c; --fg:#e7eaee; --card:#1c2026; --line:#333a44;
    --cbg:#153324; --c:#6fd79e; --sbg:#3a2d0c; --s:#f0c04a; --xbg:#3c1618; --x:#f08a8a;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:24px 16px 64px; background:var(--bg); color:var(--fg);
    font:15px/1.5 "Segoe UI", system-ui, -apple-system, sans-serif; }}
  .wrap {{ max-width:1200px; margin:0 auto; }}
  header {{ margin-bottom:20px; }}
  h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:-.01em; }}
  .meta {{ color:#7b838f; font-size:13px; }}
  section {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:18px; margin-bottom:18px; }}
  h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.06em; margin:0 0 12px;
    color:#7b838f; }}
  .scroll {{ overflow:auto; }}
  table.m {{ border-collapse:collapse; font-size:12px; }}
  table.m th, table.m td {{ border:1px solid var(--line); }}
  table.m td {{ width:34px; height:30px; text-align:center; font-weight:700; }}
  th.colh {{ height:140px; vertical-align:bottom; padding:4px; width:34px; }}
  th.colh div {{ writing-mode:vertical-rl; transform:rotate(180deg); white-space:nowrap;
    font-weight:600; font-size:11px; }}
  th.rowh {{ text-align:left; padding:4px 10px; font-weight:600; white-space:nowrap;
    position:sticky; left:0; background:var(--card); }}
  th.rowh .cod {{ color:#7b838f; font-weight:500; margin-right:8px; }}
  th.rowh .grp {{ color:#7b838f; font-weight:500; margin-left:8px; font-size:11px; }}
  .c-c {{ background:var(--cbg); color:var(--c); }}
  .c-s {{ background:var(--sbg); color:var(--s); }}
  .c-x {{ background:var(--xbg); color:var(--x); }}
  td.self {{ background:var(--line); color:#7b838f; }}
  .leyenda {{ display:flex; gap:20px; flex-wrap:wrap; margin-top:14px; font-size:13px; }}
  .leyenda span b {{ display:inline-block; width:22px; text-align:center; border-radius:4px;
    margin-right:6px; }}
  ul {{ margin:0; padding-left:20px; font-size:13px; }}
  table.lista {{ width:100%; border-collapse:collapse; font-size:13px; }}
  table.lista th, table.lista td {{ border-bottom:1px solid var(--line); padding:7px 8px;
    text-align:left; vertical-align:top; }}
  table.lista th {{ color:#7b838f; font-weight:600; font-size:12px; text-transform:uppercase; }}
  .ok {{ color:var(--c); font-size:13px; margin:0; }}
  .nota {{ font-size:12px; color:#7b838f; margin-top:12px; }}
  @media (max-width:640px) {{ body {{ padding:16px; }} }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Matriz de compatibilidad para almacenamiento de productos quimicos</h1>
  <div class="meta">{e(empresa)} &middot; {n} productos &middot; Emitida el {hoy} &middot;
  Base: GHS/SGA (Seccion 2 SDS) + Seccion 10.5 SDS + NTE INEN 2266</div>
</header>

<section>
  <h2>Matriz</h2>
  <div class="scroll">
  <table class="m">
    <thead><tr><th class="rowh"></th>{encabezados}</tr></thead>
    <tbody>{''.join(filas)}</tbody>
  </table>
  </div>
  <div class="leyenda">
    <span><b class="c-c">C</b>{ETIQUETA['C']}</span>
    <span><b class="c-s">S</b>{ETIQUETA['S']}</span>
    <span><b class="c-x">X</b>{ETIQUETA['X']}</span>
    <span><b>*</b>Endurecido por la Seccion 10.5 de la SDS</span>
  </div>
  <p class="nota">Pase el cursor sobre cada celda para ver el detalle del par.</p>
</section>

<section>
  <h2>Hallazgos: incompatibles que hoy comparten ubicacion</h2>
  {bloque_conf}
</section>

<section>
  <h2>Vacios de informacion por cerrar</h2>
  {bloque_vac}
</section>

<section>
  <h2>Grupos de almacenamiento presentes</h2>
  <ul>{leyenda_grupos}</ul>
  <p class="nota">La Seccion 10.5 de cada SDS prevalece sobre la matriz por grupos
  cuando es mas restrictiva. Nunca al reves.</p>
</section>
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inventario")
    ap.add_argument("salida")
    ap.add_argument("--empresa", default="")
    ap.add_argument("--matriz", default=os.path.join(BASE, "matriz-base.csv"))
    args = ap.parse_args()

    matriz = cargar_matriz_base(args.matriz)
    productos = cargar_inventario(args.inventario)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(render(productos, matriz, args.empresa))

    hallazgos = conflictos_por_ubicacion(productos, matriz)
    print(f"Matriz generada: {args.salida}")
    print(f"Productos: {len(productos)}")
    print(f"Pares no compatibles compartiendo ubicacion: {len(hallazgos)}")
    for a, b, c, _, _, ub in hallazgos:
        print(f"  [{c}] {a['producto']} / {b['producto']} -> {ub}")


if __name__ == "__main__":
    main()
