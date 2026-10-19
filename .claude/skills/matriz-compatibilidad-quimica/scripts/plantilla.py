"""Plantilla HTML de la matriz de compatibilidad. Autocontenida y para imprimir."""

import html
from datetime import date

from simbolos import rombo, pictograma

CLASES = {
    "1": "Explosivos", "2.1": "Gases inflamables",
    "2.2": "Gases no inflamables, no tóxicos", "2.3": "Gases tóxicos",
    "3": "Líquidos inflamables", "4.1": "Sólidos inflamables",
    "4.2": "Combustión espontánea", "4.3": "Desprenden gases inflamables con agua",
    "5.1": "Comburentes", "5.2": "Peróxidos orgánicos",
    "6": "Tóxicas e infecciosas", "7": "Material radioactivo",
    "8": "Corrosivas", "9": "Peligrosos varios",
    "NR": "No regulado para transporte",
}
ORDEN = ["1", "2.1", "2.2", "2.3", "3", "4.1", "4.2", "4.3",
         "5.1", "5.2", "6", "7", "8", "9"]

CONVENCIONES = [
    ("v", "V", "Pueden almacenarse y transportarse juntos",
     "Comparten estantería y cubeto. Prácticas normales: envase cerrado, rotulado, ventilación."),
    ("a", "A", "Precaución. Revisar incompatibilidades individuales",
     "Distinto cubeto de contención y separación mínima de 3 m, o barrera incombustible. "
     "Si no puede garantizarla, trátelo como incompatible."),
    ("r", "R", "Son incompatibles. Pueden requerir almacenamiento y transporte separados",
     "Áreas separadas, sin drenaje ni contención compartida. Un derrame simultáneo no debe "
     "poder encontrarse en el piso."),
]

CSS = """
/* Documento técnico de bodega: una columna, matrices desplazables, listo para imprimir. */
:root{
  --bg:#f1f3f6; --sup:#ffffff; --fg:#161b22; --mut:#5f6a78; --line:#d3d9e1;
  --acc:#0d6a78; --acc-sup:#e3f0f2;
  --v:#17723f; --v-bg:#d2ecdb; --a:#8f6100; --a-bg:#faeac0; --r:#9e1f1c; --r-bg:#f8d6d3;
  --disp:"Barlow Condensed", "Arial Narrow", sans-serif;
  --body:"IBM Plex Sans", system-ui, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e1216; --sup:#161c23; --fg:#e4e9ef; --mut:#8c97a5; --line:#28313b;
  --acc:#52c2d2; --acc-sup:#103035;
  --v:#63d191; --v-bg:#12331f; --a:#e9bb4e; --a-bg:#36290a; --r:#ef8a85; --r-bg:#3a1413;
  color-scheme:dark;}}
:root[data-theme="dark"]{
  --bg:#0e1216; --sup:#161c23; --fg:#e4e9ef; --mut:#8c97a5; --line:#28313b;
  --acc:#52c2d2; --acc-sup:#103035;
  --v:#63d191; --v-bg:#12331f; --a:#e9bb4e; --a-bg:#36290a; --r:#ef8a85; --r-bg:#3a1413;
  color-scheme:dark;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);
  font-size:15px;line-height:1.55;-webkit-text-size-adjust:100%}
.hoja{max-width:1080px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:28px 72px}

/* Encabezado */
.cab{border-top:4px solid var(--acc);padding-top:18px;margin-bottom:30px}
.eyebrow{font-family:var(--disp);text-transform:uppercase;letter-spacing:.14em;
  font-size:13px;font-weight:600;color:var(--acc);margin:0 0 6px}
h1{font-family:var(--disp);font-size:clamp(28px,5vw,40px);line-height:1.05;margin:0 0 10px;
  font-weight:700;letter-spacing:-.01em;text-wrap:balance}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:2px 20px;
  border-top:1px solid var(--line);padding-top:12px;margin-top:14px}
.ficha div{padding:5px 0}
.ficha dt{font-family:var(--disp);text-transform:uppercase;letter-spacing:.09em;
  font-size:12px;color:var(--mut);font-weight:600}
.ficha dd{margin:1px 0 0;font-size:14px}

/* Secciones */
section{margin-top:40px}
h2{font-family:var(--disp);font-size:22px;font-weight:700;margin:0 0 4px;letter-spacing:.01em}
.sub{color:var(--mut);font-size:13.5px;margin:0 0 16px;max-width:68ch}
h3{font-family:var(--disp);font-size:16px;text-transform:uppercase;letter-spacing:.08em;
  margin:26px 0 10px;color:var(--mut);font-weight:600}

/* Avisos */
.aviso{border-left:4px solid var(--r);background:var(--r-bg);color:var(--fg);
  padding:14px 16px;margin:0 0 14px;border-radius:0 6px 6px 0}
.aviso.ok{border-color:var(--v);background:var(--v-bg)}
.aviso.ojo{border-color:var(--a);background:var(--a-bg)}
.aviso p{margin:0}
.aviso p+p{margin-top:8px}
.aviso strong{font-weight:600}

/* Matrices */
.desliz{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--sup)}
table.mx{border-collapse:collapse;font-size:13px;min-width:100%}
table.mx th,table.mx td{border:1px solid var(--line);text-align:center}
table.mx td.celda{width:40px;height:38px;font-weight:700;font-family:var(--mono);font-size:13px}
table.mx thead th{background:var(--sup);padding:7px 4px;vertical-align:bottom}
.rot{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;
  font-family:var(--disp);font-size:12.5px;font-weight:600;letter-spacing:.03em;
  max-height:150px;padding:4px 0}
th.fila{text-align:left;padding:5px 10px;white-space:nowrap;position:sticky;left:0;
  background:var(--sup);font-weight:500;font-size:13px;z-index:1}
th.fila .nom{font-weight:600}
th.fila .tag{font-family:var(--mono);font-size:11px;color:var(--mut);margin-right:9px}
th.fila .cls{color:var(--mut);font-size:11.5px;margin-left:8px;font-family:var(--disp);
  text-transform:uppercase;letter-spacing:.05em}
.v{background:var(--v-bg);color:var(--v)}
.a{background:var(--a-bg);color:var(--a)}
.r{background:var(--r-bg);color:var(--r)}
.nd{background:repeating-linear-gradient(45deg,transparent,transparent 5px,
  var(--line) 5px,var(--line) 6px);color:var(--mut)}
td.diag{background:var(--line);color:var(--mut)}
.marca{font-size:10px;vertical-align:super;font-weight:700}
.rombo,.picto{display:block;margin:0 auto}
.pictos{display:flex;gap:4px;flex-wrap:wrap;min-width:84px}
.pictos .picto{margin:0}

/* Convenciones */
.conv{display:grid;gap:10px}
.conv .fila-conv{display:grid;grid-template-columns:52px 1fr;gap:14px;align-items:start;
  border:1px solid var(--line);border-radius:7px;background:var(--sup);padding:11px 13px}
.chip{height:34px;display:grid;place-items:center;border-radius:5px;font-weight:700;
  font-family:var(--mono);font-size:15px}
.conv b{display:block;font-size:14px;margin-bottom:2px}
.conv span{font-size:13px;color:var(--mut)}

/* Tablas de datos */
.tabla{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--sup)}
.tabla th,.tabla td{border-bottom:1px solid var(--line);padding:9px 10px;
  text-align:left;vertical-align:top}
.tabla thead th{font-family:var(--disp);text-transform:uppercase;letter-spacing:.07em;
  font-size:12px;color:var(--mut);font-weight:600;border-bottom:2px solid var(--line)}
.tabla tbody tr:last-child td{border-bottom:none}
.tabla .cod{font-family:var(--mono);font-size:12px;color:var(--mut);white-space:nowrap}
.envoltura{border:1px solid var(--line);border-radius:8px;overflow:hidden}
.pill{display:inline-block;font-family:var(--mono);font-size:11.5px;font-weight:700;
  padding:2px 7px;border-radius:4px;white-space:nowrap}
.listado{margin:0;padding-left:18px;font-size:13.5px}
.listado li{margin-bottom:5px}
.listado li:last-child{margin-bottom:0}
.nota{font-size:12.5px;color:var(--mut);margin:12px 0 0;max-width:72ch}
.firma{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:28px;
  margin-top:26px;padding-top:22px;border-top:1px solid var(--line)}
.firma div{border-top:1px solid var(--fg);padding-top:7px;font-size:12.5px;color:var(--mut);
  font-family:var(--disp);text-transform:uppercase;letter-spacing:.07em}
@media print{body{background:#fff}.desliz{overflow:visible}}
"""


def _e(t):
    return html.escape(str(t or ""))


def _cab(empresa, productos, extra_meta):
    hoy = date.today().strftime("%d/%m/%Y")
    filas = [("Empresa", empresa or "—"), ("Productos evaluados", str(len(productos))),
             ("Fecha de emisión", hoy)] + extra_meta
    return (
        '<header class="cab"><p class="eyebrow">Seguridad y Ambiente</p>'
        "<h1>Matriz de compatibilidad de sustancias químicas</h1>"
        '<p class="sub">Compatibilidad para almacenamiento conjunto, evaluada producto a '
        "producto sobre la clasificación de transporte de la Sección 4, el Anexo K y las "
        "cláusulas 6.1.7.5 y 6.1.7.10 b) de la NTE INEN 2266:2013, con la Sección 10.5 de "
        "cada Ficha de Datos de Seguridad por encima de la matriz.</p>"
        '<dl class="ficha">'
        + "".join(f"<div><dt>{_e(k)}</dt><dd>{_e(v)}</dd></div>" for k, v in filas)
        + "</dl></header>"
    )


def _matriz_productos(productos, evaluar):
    enc = "".join(
        f'<th><div class="rot">{_e(p.get("codigo") or p["producto"])}</div></th>'
        for p in productos)
    filas = []
    for a in productos:
        celdas = []
        for b in productos:
            if a is b:
                celdas.append('<td class="celda diag">—</td>')
                continue
            codigo, motivos = evaluar(a, b)
            forzado = any(m.startswith("6.1.7") or m.startswith("Sección 10.5")
                          or m.startswith("Seccion 10.5") for m in motivos)
            fuera = any(m.startswith("Fuera del alcance") for m in motivos)
            clase = "nd" if (fuera and codigo == "V") else codigo.lower()
            texto = codigo if not (fuera and codigo == "V") else "s/d"
            tip = (f'{a["producto"]} / {b["producto"]} — ' + "; ".join(motivos))
            celdas.append(f'<td class="celda {clase}" title="{_e(tip)}">{texto}'
                          + ('<span class="marca">†</span>' if forzado else "") + "</td>")
        cls = a.get("clase_onu", "")
        filas.append(
            f'<tr><th class="fila"><span class="tag">{_e(a.get("codigo",""))}</span>'
            f'<span class="nom">{_e(a["producto"])}</span>'
            f'<span class="cls">{"no regulado" if cls == "NR" else "clase " + _e(cls)}'
            + (f' + {_e(a["riesgo_sec"])}' if a.get("riesgo_sec") else "")
            + "</span></th>" + "".join(celdas) + "</tr>")
    return ('<div class="desliz"><table class="mx"><thead><tr><th class="fila"></th>'
            + enc + "</tr></thead><tbody>" + "".join(filas) + "</tbody></table></div>")


def _matriz_clases(anexo_k, presentes):
    enc = "".join(f"<th>{rombo(c, 28)}</th>" for c in ORDEN)
    filas = []
    for a in ORDEN:
        celdas = []
        for b in ORDEN:
            v = anexo_k.get((a, b), "A")
            destaca = ' style="outline:2px solid var(--acc);outline-offset:-2px"' \
                if a in presentes and b in presentes else ""
            celdas.append(f'<td class="celda {v.lower()}"{destaca} '
                          f'title="Clase {a} x clase {b}">{v}</td>')
        filas.append(f'<tr><th class="fila">{rombo(a, 24)}</th>'
                     f'<th class="fila"><span class="nom">Clase {_e(a)}</span>'
                     f'<span class="cls">{_e(CLASES[a])}</span></th>'
                     + "".join(celdas) + "</tr>")
    return ('<div class="desliz"><table class="mx"><thead><tr><th class="fila"></th>'
            '<th class="fila"></th>' + enc + "</tr></thead><tbody>"
            + "".join(filas) + "</tbody></table></div>")


def _convenciones():
    return '<div class="conv">' + "".join(
        f'<div class="fila-conv"><div class="chip {c}">{s}</div>'
        f"<div><b>{_e(t)}</b><span>{_e(d)}</span></div></div>"
        for c, s, t, d in CONVENCIONES) + (
        '<div class="fila-conv"><div class="chip nd">s/d</div><div>'
        "<b>Fuera del alcance del Anexo K</b><span>Al menos uno de los dos productos no "
        "está regulado para transporte y no tiene clase ONU. El par se evalúa solo con la "
        "Sección 10.5 de las SDS y las cláusulas 6.1.7.x.</span></div></div>"
        '<div class="fila-conv"><div class="chip" style="background:var(--acc-sup);'
        'color:var(--acc)">†</div><div><b>Endurecido sobre el Anexo K</b>'
        "<span>La celda subió de categoría por una cláusula expresa de la norma o por la "
        "Sección 10.5 de una SDS. Pase el cursor sobre la celda para ver cuál.</span>"
        "</div></div></div>")


def _inventario(productos):
    filas = []
    for p in productos:
        pics = "".join(pictograma(c.strip()) for c in
                       (p.get("pictogramas") or "").split(";") if c.strip())
        cls = p.get("clase_onu", "")
        etiqueta = ("No regulado" if cls == "NR" else f"Clase {cls}"
                    + (f" + {p['riesgo_sec']}" if p.get("riesgo_sec") else ""))
        filas.append(
            f'<tr><td class="cod">{_e(p.get("codigo",""))}</td>'
            f'<td><b>{_e(p["producto"])}</b><br><span style="color:var(--mut);'
            f'font-size:12.5px">{_e(p.get("uso",""))}</span></td>'
            f'<td><div class="pictos">{pics or "<span style=\'color:var(--mut)\'>—</span>"}'
            f"</div></td>"
            f'<td style="font-size:12.5px">{_e(p.get("clasificacion_sga",""))}</td>'
            f'<td class="cod">{_e(p.get("onu","—"))}<br>{_e(etiqueta)}</td>'
            f'<td style="font-size:12.5px">{_e(p.get("incompat_sds",""))}</td>'
            f'<td class="cod">{_e(p.get("ubicacion",""))}</td></tr>')
    return ('<div class="envoltura"><table class="tabla"><thead><tr>'
            "<th>Código</th><th>Producto</th><th>SGA</th><th>Clasificación SGA</th>"
            "<th>ONU / Clase</th><th>Incompatibles (Sección 10.5)</th><th>Ubicación</th>"
            "</tr></thead><tbody>" + "".join(filas) + "</tbody></table></div>")


def _lista(items, clase="listado"):
    return f'<ul class="{clase}">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def pagina(productos, anexo_k, evaluar, empresa, hallazgos, vacios, notas, extra_meta):
    presentes = {p.get("clase_onu") for p in productos}

    if hallazgos:
        filas = "".join(
            f'<tr><td class="cod">{_e(s)}</td><td>{_e(a["producto"])}</td>'
            f'<td>{_e(b["producto"])}</td>'
            f'<td><span class="pill {c.lower()}">{c}</span></td>'
            f'<td style="font-size:12.5px">{_e("; ".join(m))}</td></tr>'
            for a, b, c, m, s in hallazgos)
        bloque_h = ('<div class="envoltura"><table class="tabla"><thead><tr>'
                    "<th>Ubicación</th><th>Producto A</th><th>Producto B</th><th></th>"
                    "<th>Fundamento</th></tr></thead><tbody>" + filas
                    + "</tbody></table></div>")
    else:
        bloque_h = ('<div class="aviso ok"><p>Ningún par incompatible comparte zona de '
                    "almacenamiento declarada.</p></div>")

    bloque_v = (f'<div class="aviso ojo">{_lista(vacios)}</div>' if vacios
                else '<div class="aviso ok"><p>Sin vacíos de información.</p></div>')

    return f"""<title>Matriz de compatibilidad química</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>
<div class="hoja">
{_cab(empresa, productos, extra_meta)}

<section>
  <h2>Hallazgos</h2>
  <p class="sub">Pares que comparten zona de almacenamiento y no son compatibles, o que
  requieren precaución estando en la misma ubicación exacta.</p>
  {bloque_h}
</section>

<section>
  <h2>Matriz por producto</h2>
  <p class="sub">La matriz operativa: dice qué hacer con los envases que usted tiene.
  Pase el cursor sobre cualquier celda para ver el fundamento del par.</p>
  {_matriz_productos(productos, evaluar)}
</section>

<section>
  <h2>Convenciones</h2>
  <p class="sub">Leyenda literal del Anexo K, con el criterio operativo que exige cada
  categoría en bodega.</p>
  {_convenciones()}
</section>

<section>
  <h2>Inventario clasificado</h2>
  <p class="sub">Clasificación SGA de la Sección 2 e incompatibilidades de la Sección 10.5,
  transcritas de cada Ficha de Datos de Seguridad.</p>
  {_inventario(productos)}
</section>

<section>
  <h2>Anexo K de la NTE INEN 2266:2013</h2>
  <p class="sub">Matriz de incompatibilidades químicas por clase y división ONU, según la
  Sección 4 de la norma. Recuadradas en color de acento, las clases presentes en este
  inventario. Fuente declarada por la norma: Código Marítimo Internacional de Mercancías
  Peligrosas (IMDG).</p>
  {_matriz_clases(anexo_k, presentes)}
  <p class="nota">La celda 4.2 × 8 del Anexo K impreso es asimétrica: roja leyendo por la
  fila 4.2 y amarilla leyendo por la fila 8. Aquí se adopta el valor más restrictivo.
  Nota 1 de la norma: el orden numérico de las clases y divisiones no corresponde a su
  grado de peligro.</p>
</section>

<section>
  <h2>Vacíos de información por cerrar</h2>
  <p class="sub">Esta matriz solo es válida mientras estos puntos sigan abiertos y
  documentados. Ciérrelos con el proveedor.</p>
  {bloque_v}
</section>

<section>
  <h2>Criterio aplicado</h2>
  {_lista(notas)}
  <div class="firma">
    <div>Elaborado por</div><div>Revisado por</div><div>Aprobado por</div>
  </div>
</section>
</div>
"""
