"""Rombos de clase ONU y pictogramas SGA como SVG en linea.

Nada de imagenes externas: el HTML tiene que abrirse sin conexion y sin
dependencias, porque termina en una bodega o impreso en una carpeta.
"""

# Colores de fondo de cada rombo de clase, segun el etiquetado de transporte.
ROMBOS = {
    "1":   ("#e8820c", "#000", "1",   "bomba"),
    "2.1": ("#d0202a", "#fff", "2",   "llama"),
    "2.2": ("#1f8a4c", "#fff", "2",   "cilindro"),
    "2.3": ("#ffffff", "#000", "2",   "calavera"),
    "3":   ("#d0202a", "#fff", "3",   "llama"),
    "4.1": ("#ffffff", "#000", "4",   "llama"),
    "4.2": ("#ffffff", "#000", "4",   "llama"),
    "4.3": ("#1457a8", "#fff", "4",   "llama"),
    "5.1": ("#f2c500", "#000", "5.1", "comburente"),
    "5.2": ("#f2c500", "#000", "5.2", "comburente"),
    "6":   ("#ffffff", "#000", "6",   "calavera"),
    "7":   ("#f2c500", "#000", "7",   "radiactivo"),
    "8":   ("#ffffff", "#000", "8",   "corrosion"),
    "9":   ("#ffffff", "#000", "9",   "franjas"),
    "NR":  ("#eceff3", "#5b6472", "NR", "ninguno"),
}

_SIMBOLO = {
    "llama": '<path d="M50 24c3 9-2 12-6 16-5 5-9 9-9 16 0 9 7 16 15 16s15-7 15-16c0-5-2-9-5-13-1 4-3 6-5 6 2-9-2-19-5-25z"/>',
    "calavera": ('<path d="M50 24c-11 0-19 8-19 18 0 6 3 10 6 13v6h26v-6c3-3 6-7 6-13 0-10-8-18-19-18z'
                 'm-7 17a4 4 0 110 8 4 4 0 010-8zm14 0a4 4 0 110 8 4 4 0 010-8zm-10 14h6l-3 6z"/>'
                 '<rect x="38" y="64" width="24" height="4" rx="2"/>'),
    "cilindro": '<rect x="42" y="26" width="16" height="40" rx="7"/><rect x="46" y="20" width="8" height="8"/>',
    "comburente": ('<circle cx="50" cy="56" r="15" fill="none" stroke="currentColor" stroke-width="5"/>'
                   '<path d="M50 14c3 9-2 12-6 16-4 4-7 7-7 12h26c0-7-10-16-13-28z"/>'),
    "bomba": ('<circle cx="47" cy="58" r="15"/><rect x="52" y="34" width="5" height="14" '
              'transform="rotate(35 54 41)"/><path d="M62 30l10-8-4 11 10-4-8 9"/>'),
    "radiactivo": ('<circle cx="50" cy="50" r="5"/>'
                   '<path d="M50 20a30 30 0 0126 15l-17 10a10 10 0 00-9-5z"/>'
                   '<path d="M76 65a30 30 0 01-26 15v-20a10 10 0 009-5z"/>'
                   '<path d="M24 65a30 30 0 0026 15v-20a10 10 0 01-9-5z" transform="scale(-1,1) translate(-100,0)"/>'),
    "corrosion": ('<path d="M26 30h12v14c0 4 4 7 9 9l-3 5H24z"/>'
                  '<path d="M60 30h12v14c0 4 4 7 9 9l-3 5H58z"/>'
                  '<rect x="20" y="66" width="60" height="5"/>'
                  '<path d="M44 72l4 8M56 72l4 8" stroke="currentColor" stroke-width="4"/>'),
    "franjas": '<rect x="18" y="20" width="64" height="4"/><rect x="18" y="28" width="64" height="4"/><rect x="18" y="36" width="64" height="4"/>',
    "ninguno": "",
}


def rombo(clase, px=30):
    """Rombo de clase ONU, estilo etiqueta de transporte."""
    fondo, tinta, numero, simbolo = ROMBOS.get(clase, ROMBOS["NR"])
    cuerpo = _SIMBOLO.get(simbolo, "")
    # Las clases 4.1, 4.2 y 9 llevan franjas caracteristicas en la mitad superior.
    extra = ""
    if clase == "4.1":
        extra = ('<g clip-path="url(#c)">' + "".join(
            f'<rect x="{x}" y="0" width="7" height="100" fill="#d0202a"/>' for x in range(4, 100, 16)
        ) + "</g>")
    elif clase == "4.2":
        extra = '<path d="M0 50h100v50H0z" fill="#d0202a" clip-path="url(#c)"/>'
    elif clase == "8":
        extra = '<path d="M0 50h100v50H0z" fill="#2b3038" clip-path="url(#c)"/>'
    elif clase == "7":
        extra = '<path d="M0 50h100v50H0z" fill="#ffffff" clip-path="url(#c)"/>'
    elif clase == "9":
        extra = ('<g clip-path="url(#c)">' + "".join(
            f'<rect x="0" y="{y}" width="100" height="5" fill="#2b3038"/>' for y in range(2, 50, 10)
        ) + "</g>")

    tinta_num = "#fff" if clase == "8" else tinta
    return (
        f'<svg class="rombo" viewBox="0 0 100 100" width="{px}" height="{px}" role="img" '
        f'aria-label="Clase {clase}"><defs><clipPath id="c">'
        f'<path d="M50 2 98 50 50 98 2 50z"/></clipPath></defs>'
        f'<path d="M50 2 98 50 50 98 2 50z" fill="{fondo}"/>{extra}'
        f'<path d="M50 2 98 50 50 98 2 50z" fill="none" stroke="#2b3038" stroke-width="3"/>'
        f'<g fill="{tinta}" color="{tinta}" transform="translate(0,-8) scale(0.74) translate(17,10)">{cuerpo}</g>'
        f'<text x="50" y="86" text-anchor="middle" font-size="19" font-weight="700" '
        f'fill="{tinta_num}" font-family="system-ui, sans-serif">{numero}</text></svg>'
    )


# Pictogramas SGA: rombo rojo sobre blanco.
_SGA = {
    "GHS01": ("Explosivo", _SIMBOLO["bomba"]),
    "GHS02": ("Inflamable", _SIMBOLO["llama"]),
    "GHS03": ("Comburente", _SIMBOLO["comburente"]),
    "GHS04": ("Gas a presion", _SIMBOLO["cilindro"]),
    "GHS05": ("Corrosivo", _SIMBOLO["corrosion"]),
    "GHS06": ("Toxicidad aguda", _SIMBOLO["calavera"]),
    "GHS07": ("Atencion", '<path d="M50 22l5 36h-10zM50 68a6 6 0 110 12 6 6 0 010-12z"/>'),
    "GHS08": ("Peligro para la salud",
              '<path d="M50 20a30 30 0 100 60 30 30 0 000-60zm0 9a21 21 0 110 42 21 21 0 010-42z"/>'
              '<path d="M50 34l5 12 12-4-8 10 8 10-12-4-5 12-5-12-12 4 8-10-8-10 12 4z"/>'),
    "GHS09": ("Peligro ambiental",
              '<path d="M14 70h72l-8 12H22z"/><path d="M34 26c10 6 14 16 12 30-10-2-16-12-12-30z"/>'
              '<path d="M58 40l18 6-18 10 6-8z"/><circle cx="68" cy="42" r="3"/>'),
}


def pictograma(codigo, px=26):
    nombre, cuerpo = _SGA.get(codigo, ("", ""))
    if not cuerpo:
        return ""
    return (
        f'<svg class="picto" viewBox="0 0 100 100" width="{px}" height="{px}" role="img" '
        f'aria-label="{nombre}"><title>{nombre}</title>'
        f'<path d="M50 3 97 50 50 97 3 50z" fill="#fff"/>'
        f'<path d="M50 3 97 50 50 97 3 50z" fill="none" stroke="#d0202a" stroke-width="8"/>'
        f'<g fill="#111" color="#111" transform="translate(50,50) scale(0.62) translate(-50,-50)">'
        f'{cuerpo}</g></svg>'
    )
