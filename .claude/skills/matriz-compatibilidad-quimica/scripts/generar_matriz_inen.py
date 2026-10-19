#!/usr/bin/env python3
"""Matriz de compatibilidad segun NTE INEN 2266:2013 (Anexo K + clausula 6.1.7.10 b).

Uso:
    python3 generar_matriz_inen.py inventario.csv salida.html --empresa "Plantabal S.A."

Columnas del inventario: codigo, producto, clase_onu, onu (numero ONU), subgrupo,
ubicacion. Opcionales: riesgo_sec, concentracion, incompat_sds, observaciones.
"""

import argparse
import csv
import html
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reglas_inen import evaluar, SUBGRUPOS

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")

CLASES = {
    "1": "Explosivos", "2.1": "Gases inflamables",
    "2.2": "Gases no inflamables, no toxicos", "2.3": "Gases toxicos",
    "3": "Liquidos inflamables", "4.1": "Solidos inflamables",
    "4.2": "Combustion espontanea", "4.3": "Desprenden gases inflamables con agua",
    "5.1": "Comburentes", "5.2": "Peroxidos organicos",
    "6": "Toxicas e infecciosas", "7": "Material radioactivo",
    "8": "Corrosivas", "9": "Peligrosos varios",
}

ETIQUETA = {
    "V": "Pueden almacenarse y transportarse juntos",
    "A": "Precaucion. Revisar incompatibilidades individuales",
    "R": "Son incompatibles. Pueden requerir almacenamiento y transporte separados",
}


def normaliza(t):
    t = t.lower()
    for a, b in zip("aeiouun", "áéíóúüñ"):
        t = t.replace(b, a)
    return t


def cargar_anexo_k(ruta):
    m = {}
    with open(ruta, encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            for col, val in fila.items():
                if col != "clase":
                    m[(fila["clase"], col)] = val.strip()
    return m


def cargar_inventario(ruta):
    with open(ruta, encoding="utf-8-sig") as fh:
        productos = [{k: (v or "").strip() for k, v in f.items() if k}
                     for f in csv.DictReader(fh)]
    errores = []
    for i, p in enumerate(productos, start=2):
        if not p.get("producto"):
            errores.append(f"Fila {i}: falta el nombre del producto.")
        if p.get("clase_onu") not in CLASES:
            errores.append(f"Fila {i} ({p.get('producto','?')}): clase_onu "
                           f"'{p.get('clase_onu')}' invalida (Seccion 4 de la norma).")
        sub = (p.get("subgrupo") or "").lower()
        for s in [x.strip() for x in sub.split(";") if x.strip()]:
            if s not in SUBGRUPOS:
                errores.append(f"Fila {i} ({p.get('producto','?')}): subgrupo '{s}' "
                               f"desconocido. Validos: {', '.join(SUBGRUPOS)}.")
    if errores:
        raise SystemExit("Inventario con errores:\n  - " + "\n  - ".join(errores))
    return productos


def zona(u):
    return normaliza(u.split("-")[0]).strip()


def hallazgos(productos, k):
    out = []
    for i, a in enumerate(productos):
        for b in productos[i + 1:]:
            ua, ub = a.get("ubicacion", ""), b.get("ubicacion", "")
            if not ua or not ub or zona(ua) != zona(ub):
                continue
            codigo, motivos = evaluar(a, b, k)
            misma = normaliza(ua) == normaliza(ub)
            if codigo == "R" or (codigo == "A" and misma):
                sitio = ua if misma else f"{ua} / {ub}"
                out.append((a, b, codigo, motivos, sitio))
    out.sort(key=lambda h: {"R": 0, "A": 1}.get(h[2], 2))
    return out


def render(productos, k, empresa):
    e = html.escape
    hoy = date.today().strftime("%d/%m/%Y")

    filas = []
    for a in productos:
        celdas = []
        for b in productos:
            if a is b:
                celdas.append('<td class="self">&mdash;</td>')
                continue
            codigo, motivos = evaluar(a, b, k)
            forzado = any(m.startswith("6.1.7") for m in motivos)
            t = f"{a['producto']} (clase {a['clase_onu']}) / {b['producto']} " \
                f"(clase {b['clase_onu']}): {ETIQUETA[codigo]} — {'; '.join(motivos)}"
            celdas.append(f'<td class="c-{codigo.lower()}" title="{e(t)}">'
                          f'{codigo}{"&dagger;" if forzado else ""}</td>')
        filas.append(
            f'<tr><th class="rowh"><span class="cod">{e(a.get("codigo",""))}</span>'
            f'{e(a["producto"])}<span class="grp">clase {e(a["clase_onu"])}'
            + (f' + {e(a["riesgo_sec"])}' if a.get("riesgo_sec") else "")
            + "</span></th>" + "".join(celdas) + "</tr>")

    cols = "".join(f'<th class="colh"><div>{e(p.get("codigo") or p["producto"][:18])}'
                   f"</div></th>" for p in productos)

    hs = hallazgos(productos, k)
    if hs:
        bloque = ('<table class="lista"><thead><tr><th>Ubicacion</th><th>Producto A</th>'
                  '<th>Producto B</th><th></th><th>Fundamento</th></tr></thead><tbody>'
                  + "".join(f'<tr><td>{e(s)}</td><td>{e(a["producto"])}</td>'
                            f'<td>{e(b["producto"])}</td><td class="c-{c.lower()}">{c}</td>'
                            f'<td>{e("; ".join(m))}</td></tr>'
                            for a, b, c, m, s in hs) + "</tbody></table>")
    else:
        bloque = '<p class="ok">Ningun par conflictivo comparte zona declarada.</p>'

    usadas = sorted({p["clase_onu"] for p in productos},
                    key=lambda c: [float(x) for x in c.split(".")])
    leyenda = "".join(f"<li><b>Clase {c}</b> &mdash; {e(CLASES[c])}</li>" for c in usadas)

    inv = "".join(
        f'<tr><td>{e(p.get("codigo",""))}</td><td>{e(p["producto"])}</td>'
        f'<td>{e(p.get("onu",""))}</td><td>{e(p["clase_onu"])}'
        + (f' + {e(p["riesgo_sec"])}' if p.get("riesgo_sec") else "")
        + f'</td><td>{e(p.get("concentracion",""))}</td>'
          f'<td>{e(p.get("ubicacion",""))}</td></tr>' for p in productos)

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matriz INEN 2266</title>
<style>
 :root {{ --bg:#f6f7f9; --fg:#1b1f24; --card:#fff; --line:#d9dde3; --mut:#7b838f;
   --v:#1e7f4f; --vbg:#d8f0e2; --a:#a06a00; --abg:#fdeec8; --r:#a31d1d; --rbg:#fadcdc; }}
 @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
   --bg:#14171c; --fg:#e7eaee; --card:#1c2026; --line:#333a44; --mut:#8d96a3;
   --vbg:#153324; --v:#6fd79e; --abg:#3a2d0c; --a:#f0c04a; --rbg:#3c1618; --r:#f08a8a; }} }}
 :root[data-theme="dark"] {{ --bg:#14171c; --fg:#e7eaee; --card:#1c2026; --line:#333a44;
   --mut:#8d96a3; --vbg:#153324; --v:#6fd79e; --abg:#3a2d0c; --a:#f0c04a;
   --rbg:#3c1618; --r:#f08a8a; }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; padding:24px 16px 64px; background:var(--bg); color:var(--fg);
   font:15px/1.5 "Segoe UI", system-ui, -apple-system, sans-serif; }}
 .wrap {{ max-width:1200px; margin:0 auto; }}
 h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:-.01em; }}
 .meta {{ color:var(--mut); font-size:13px; margin-bottom:20px; }}
 section {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
   padding:18px; margin-bottom:18px; }}
 h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.06em; margin:0 0 12px;
   color:var(--mut); }}
 .scroll {{ overflow:auto; }}
 table.m {{ border-collapse:collapse; font-size:12px; }}
 table.m th, table.m td {{ border:1px solid var(--line); }}
 table.m td {{ width:34px; height:30px; text-align:center; font-weight:700; }}
 th.colh {{ height:150px; vertical-align:bottom; padding:4px; width:34px; }}
 th.colh div {{ writing-mode:vertical-rl; transform:rotate(180deg); white-space:nowrap;
   font-weight:600; font-size:11px; }}
 th.rowh {{ text-align:left; padding:4px 10px; font-weight:600; white-space:nowrap;
   position:sticky; left:0; background:var(--card); }}
 th.rowh .cod {{ color:var(--mut); font-weight:500; margin-right:8px; }}
 th.rowh .grp {{ color:var(--mut); font-weight:500; margin-left:8px; font-size:11px; }}
 .c-v {{ background:var(--vbg); color:var(--v); }}
 .c-a {{ background:var(--abg); color:var(--a); }}
 .c-r {{ background:var(--rbg); color:var(--r); }}
 td.self {{ background:var(--line); color:var(--mut); }}
 .leyenda {{ display:flex; gap:18px; flex-wrap:wrap; margin-top:14px; font-size:13px; }}
 .leyenda span b {{ display:inline-block; width:22px; text-align:center; border-radius:4px;
   margin-right:6px; }}
 ul {{ margin:0; padding-left:20px; font-size:13px; }}
 table.lista {{ width:100%; border-collapse:collapse; font-size:13px; }}
 table.lista th, table.lista td {{ border-bottom:1px solid var(--line); padding:7px 8px;
   text-align:left; vertical-align:top; }}
 table.lista th {{ color:var(--mut); font-weight:600; font-size:12px;
   text-transform:uppercase; }}
 .ok {{ color:var(--v); font-size:13px; margin:0; }}
 .nota {{ font-size:12px; color:var(--mut); margin-top:12px; }}
 @media (max-width:640px) {{ body {{ padding:16px; }} }}
</style></head><body><div class="wrap">
<h1>Matriz de incompatibilidades quimicas</h1>
<div class="meta">{e(empresa)} &middot; {len(productos)} productos &middot; Emitida el {hoy}<br>
Base normativa: NTE INEN 2266:2013 (Segunda revision) &mdash; Seccion 4 Clasificacion,
Anexo K Matriz de incompatibilidades quimicas, clausulas 6.1.7.5 y 6.1.7.10 b)</div>

<section><h2>Inventario clasificado</h2>
<table class="lista"><thead><tr><th>Codigo</th><th>Producto</th><th>ONU</th>
<th>Clase (Seccion 4)</th><th>Concentracion</th><th>Ubicacion</th></tr></thead>
<tbody>{inv}</tbody></table></section>

<section><h2>Matriz</h2><div class="scroll"><table class="m">
<thead><tr><th class="rowh"></th>{cols}</tr></thead><tbody>{''.join(filas)}</tbody>
</table></div>
<div class="leyenda">
 <span><b class="c-v">V</b>{ETIQUETA['V']}</span>
 <span><b class="c-a">A</b>{ETIQUETA['A']}</span>
 <span><b class="c-r">R</b>{ETIQUETA['R']}</span>
 <span><b>&dagger;</b>Endurecido por clausula 6.1.7.10 b) sobre el Anexo K</span>
</div>
<p class="nota">Leyenda literal del Anexo K. Pase el cursor sobre cada celda para ver
el fundamento del par. Orden de precedencia aplicado: Seccion 10.5 de la SDS &gt;
clausulas 6.1.7.5 y 6.1.7.10 b) &gt; Anexo K.</p></section>

<section><h2>Hallazgos de segregacion</h2>{bloque}</section>

<section><h2>Clases presentes (Seccion 4)</h2><ul>{leyenda}</ul>
<p class="nota">Nota 1 de la norma: el orden numerico de las clases y divisiones no
corresponde a su grado de peligro. La celda 4.2 x 8 del Anexo K impreso es asimetrica
(roja por la fila 4.2, amarilla por la fila 8); aqui se adopta el criterio mas
restrictivo.</p></section>
</div></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inventario")
    ap.add_argument("salida")
    ap.add_argument("--empresa", default="")
    ap.add_argument("--anexo-k", default=os.path.join(BASE, "matriz-anexo-k.csv"))
    args = ap.parse_args()

    k = cargar_anexo_k(args.anexo_k)
    productos = cargar_inventario(args.inventario)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(render(productos, k, args.empresa))

    hs = hallazgos(productos, k)
    print(f"Matriz generada: {args.salida}\nProductos: {len(productos)}")
    print(f"Hallazgos: {len(hs)}")
    for a, b, c, m, s in hs:
        print(f"  [{c}] {a['producto']} / {b['producto']} -> {s}\n       {'; '.join(m)}")


if __name__ == "__main__":
    main()
