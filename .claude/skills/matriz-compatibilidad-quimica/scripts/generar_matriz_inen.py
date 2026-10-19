#!/usr/bin/env python3
"""Matriz de compatibilidad segun NTE INEN 2266:2013 (Anexo K + clausula 6.1.7.10 b).

Uso:
    python3 generar_matriz_inen.py inventario.csv salida.html --empresa "Plantabal S.A."

Columnas del inventario: codigo, producto, clase_onu, subgrupo, ubicacion.
Opcionales: onu, riesgo_sec, uso, clasificacion_sga, pictogramas, concentracion,
incompat_sds, fecha_sds, idioma_sds, observaciones.

clase_onu admite las 14 clases y divisiones de la Seccion 4, mas NR para los
productos que su Seccion 14 declara no regulados durante el transporte.
"""

import argparse
import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plantilla
from plantilla import CLASES
from reglas_inen import evaluar, SUBGRUPOS, normaliza

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")


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
                           f"'{p.get('clase_onu')}' invalida. Use una clase de la "
                           f"Seccion 4, o NR si la Seccion 14 dice no regulado.")
        for s in [x.strip() for x in (p.get("subgrupo") or "").lower().split(";") if x.strip()]:
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
                out.append((a, b, codigo, motivos, ua if misma else f"{ua} / {ub}"))
    out.sort(key=lambda h: {"R": 0, "A": 1}.get(h[2], 2))
    return out


def vacios(productos):
    """Vacios agrupados por tipo: una linea por hallazgo, no por producto."""
    hoy = date.today()
    grupos = []

    def grupo(titulo, cumplen, accion):
        if cumplen:
            grupos.append(f"<b>{titulo}</b> &mdash; {', '.join(cumplen)}. {accion}")

    grupo("Sección 10.5 sin datos utilizables",
          [p["producto"] for p in productos
           if not p.get("incompat_sds")
           or normaliza(p["incompat_sds"]).startswith("sin dato")],
          "Solicitar SDS actualizada al proveedor.")

    grupo("Fuera del alcance del Anexo K",
          [p["producto"] for p in productos if p.get("clase_onu") == "NR"],
          "Su Sección 14 los declara no regulados durante el transporte, por lo que no "
          "tienen clase ONU. Su compatibilidad se sostiene solo en la Sección 10.5 de la "
          "SDS y en las cláusulas 6.1.7.x, no en el Anexo K.")

    grupo("Sin clasificación SGA registrada (Sección 2)",
          [p["producto"] for p in productos if not p.get("clasificacion_sga")],
          "La SDS no está en formato SGA o no declara clasificación. Exigir al proveedor "
          "la Ficha de Datos de Seguridad conforme al SGA.")

    viejas = []
    for p in productos:
        f = p.get("fecha_sds", "")
        try:
            anios = hoy.year - int(f[-4:])
        except (ValueError, IndexError):
            continue
        if anios >= 3:
            viejas.append(f"{p['producto']} ({f}, {anios} años)")
    grupo("SDS con tres años o más desde su revisión", viejas,
          "La clasificación SGA cambia entre revisiones. Solicitar la vigente.")

    grupo("SDS solo en inglés",
          [p["producto"] for p in productos
           if (p.get("idioma_sds") or "").lower().startswith("ing")],
          "El personal de bodega debe disponer de la versión en español.")

    grupo("Sin ubicación real de almacenamiento",
          [p["producto"] for p in productos
           if not p.get("ubicacion") or "confirmar" in normaliza(p.get("ubicacion", ""))],
          "Sin este dato la matriz describe compatibilidades teóricas pero no detecta "
          "ningún incumplimiento en bodega.")

    return grupos


NOTAS = [
    "<b>Orden de precedencia aplicado:</b> Sección 10.5 de la SDS del producto &gt; "
    "cláusulas 6.1.7.5 y 6.1.7.10 b) de la NTE INEN 2266:2013 &gt; Anexo K. Ninguna "
    "fuente relaja a la anterior; solo puede endurecerla.",
    "<b>El Anexo K no basta por sí solo.</b> Opera por clase ONU: ácidos y bases son "
    "ambos Clase 8 y su celda es amarilla, pero la cláusula 6.1.7.10 b.7 los prohíbe "
    "expresamente. Lo mismo ocurre con Clase 3 × Clase 8, que es verde en el Anexo K y "
    "queda prohibida por b.2, b.4 y b.8 cuando el corrosivo es además comburente.",
    "<b>La norma no tiene Sección 10.</b> Llega hasta la Sección 6. La cláusula de "
    "almacenamiento es 6.1.7.10 y la de apilamiento 6.1.7.5. La Sección 10 que aparece "
    "numerada en el documento pertenece al formato de MSDS del Anexo B.",
    "<b>Requisitos de bodega de 6.1.7.4:</b> envases sobre plataformas o paletas, nunca "
    "directamente en el piso; líquidos con las tapas hacia arriba; apilado respetando la "
    "resistencia del envase y la clase de peligro.",
    "<b>Alcance.</b> Esta matriz cubre almacenamiento conjunto. No dimensiona cantidades "
    "máximas por área ni distancias por carga de fuego, no evalúa compatibilidad de "
    "materiales de envase y no decide sobre reacciones de proceso.",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inventario")
    ap.add_argument("salida")
    ap.add_argument("--empresa", default="")
    ap.add_argument("--area", default="")
    ap.add_argument("--anexo-k", default=os.path.join(BASE, "matriz-anexo-k.csv"))
    args = ap.parse_args()

    k = cargar_anexo_k(args.anexo_k)
    productos = cargar_inventario(args.inventario)
    meta = [("Base normativa", "NTE INEN 2266:2013, segunda revisión")]
    if args.area:
        meta.insert(0, ("Área", args.area))

    html = plantilla.pagina(
        productos, k, lambda a, b: evaluar(a, b, k), args.empresa,
        hallazgos(productos, k), vacios(productos), NOTAS, meta)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(html)

    hs = hallazgos(productos, k)
    print(f"Matriz generada: {args.salida}\nProductos: {len(productos)}  "
          f"Hallazgos: {len(hs)}  Vacios: {len(vacios(productos))}")
    for a, b, c, m, s in hs:
        print(f"  [{c}] {a['producto']} / {b['producto']} -> {s}\n       {'; '.join(m)}")


if __name__ == "__main__":
    main()
