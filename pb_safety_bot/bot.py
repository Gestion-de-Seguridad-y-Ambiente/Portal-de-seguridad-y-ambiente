"""
Pb_safety_bot — Verificador de contratistas Plantabal
NLP basado en reglas: detecta empresa, columnas dinámicas y consultas encadenadas.
Sin costos externos — todo procesado localmente.
"""
import os, csv, io, unicodedata, logging, re, time
from datetime import date
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN     = os.environ["BOT_TOKEN"]
SHEET_CSV = os.environ["SHEET_CSV_URL"]

# Columnas fijas
COL_APELLIDO = 1
COL_NOMBRES  = 2
COL_EMPRESA  = 3
COL_CEDULA   = 4
COL_ACCESO   = 11

# Cache del sheet (se recarga cada 5 minutos)
_cache = {"ts": 0, "encabezados": [], "empresas": set(), "filas": []}
CACHE_TTL = 300  # segundos

# Palabras que indican "aplicar sobre los resultados anteriores"
PALABRAS_PREVIOS = {
    "de ellos", "de esos", "de esas", "de los", "de las",
    "entre ellos", "entre esos", "de ese listado", "de esa lista",
    "y cuales", "y cuáles", "filtrar", "de anteriores", "ahora cuales",
    "ahora cuáles", "cuales tienen", "cuáles tienen",
}

# Palabras que indican filtro por acceso permitido
PALABRAS_ACCESO = {
    "acceso", "con acceso", "pueden entrar", "permitido",
    "habilitados", "aprobados", "autorizados",
}

# Palabras que indican filtro por IESS
PALABRAS_IESS = {"iess", "seguro", "afiliacion", "afiliación"}

# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )

def iess_vigente(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        return ""
    try:
        partes = valor.replace("-", "/").split("/")
        if len(partes) == 3:
            d, m, a = int(partes[0]), int(partes[1]), int(partes[2])
            if a < 100:
                a += 2000
            hoy = date.today()
            limite = date(
                hoy.year if hoy.month > 1 else hoy.year - 1,
                hoy.month - 1 if hoy.month > 1 else 12,
                1,
            )
            return "Vigente" if date(a, m, 1) >= limite else "Vencido"
    except Exception:
        pass
    return valor

# ---------------------------------------------------------------------------

def cargar_todo(forzar: bool = False) -> tuple:
    """Retorna (encabezados, empresas, filas) con caché de 5 min."""
    global _cache
    if not forzar and time.time() - _cache["ts"] < CACHE_TTL and _cache["filas"]:
        return _cache["encabezados"], _cache["empresas"], _cache["filas"]

    resp = requests.get(SHEET_CSV, timeout=10)
    resp.raise_for_status()
    reader = csv.reader(io.StringIO(resp.text))

    encabezados = []
    filas = []
    empresas = set()

    for i, row in enumerate(reader):
        if i == 3:
            encabezados = [c.strip() for c in row]
        if i < 5:
            continue
        if not (len(row) > COL_APELLIDO and row[COL_APELLIDO].strip()):
            continue
        filas.append(row)
        if len(row) > COL_EMPRESA and row[COL_EMPRESA].strip():
            empresas.add(row[COL_EMPRESA].strip())

    _cache = {"ts": time.time(), "encabezados": encabezados,
              "empresas": empresas, "filas": filas}
    return encabezados, empresas, filas

# ---------------------------------------------------------------------------

def detectar_empresa(msg_n: str, empresas: set) -> str | None:
    """Retorna la empresa cuyo nombre normalizado aparece mejor en el mensaje."""
    mejor, mejor_len = None, 0
    for emp in empresas:
        emp_n = normalizar(emp)
        tokens = [t for t in emp_n.split() if len(t) >= 3]
        if not tokens:
            continue
        if all(t in msg_n for t in tokens) and len(emp_n) > mejor_len:
            mejor, mejor_len = emp, len(emp_n)
    return mejor


def detectar_columna(msg_n: str, encabezados: list) -> tuple:
    """
    Busca la columna del sheet que mejor coincide con palabras del mensaje.
    Retorna (índice, encabezado) o (None, None).
    Excluye columnas de control (apellido, nombres, empresa, cédula, acceso).
    """
    EXCLUIR = {COL_APELLIDO, COL_NOMBRES, COL_EMPRESA, COL_CEDULA, COL_ACCESO}
    mejor_idx, mejor_nombre, mejor_score = None, None, 0

    for idx, header in enumerate(encabezados):
        if idx in EXCLUIR or not header:
            continue
        h_n = normalizar(header)
        tokens = [t for t in h_n.split() if len(t) >= 4]
        if not tokens:
            continue
        matches = sum(1 for t in tokens if t in msg_n)
        score = matches / len(tokens)
        if score >= 0.4 and matches > mejor_score:
            mejor_score, mejor_idx, mejor_nombre = matches, idx, header

    return mejor_idx, mejor_nombre


def detectar_intencion(mensaje: str, encabezados: list, empresas: set,
                        hay_previos: bool) -> dict:
    msg_n = normalizar(mensaje)

    usar_previos = hay_previos and any(p in msg_n for p in PALABRAS_PREVIOS)
    filtro_acceso = any(p in msg_n for p in PALABRAS_ACCESO)
    filtro_iess   = any(p in msg_n for p in PALABRAS_IESS)
    empresa       = detectar_empresa(msg_n, empresas)
    col_idx, col_nombre = detectar_columna(msg_n, encabezados)

    cedula_m = re.search(r'\b\d{10}\b', mensaje)
    cedula   = cedula_m.group() if cedula_m else None

    # Es búsqueda de persona si no hay empresa ni filtros de grupo
    es_persona = not empresa and not usar_previos and not filtro_acceso \
                 and col_idx is None and not filtro_iess

    return {
        "usar_previos": usar_previos,
        "empresa":      empresa,
        "filtro_acceso": filtro_acceso,
        "filtro_iess":  filtro_iess,
        "col_filtro":   col_idx,
        "col_nombre":   col_nombre,
        "es_persona":   es_persona,
        "nombre":       mensaje.strip() if es_persona and not cedula else None,
        "cedula":       cedula,
    }

# ---------------------------------------------------------------------------

def aplicar_filtros(filas: list, intencion: dict) -> list:
    resultado = []
    for row in filas:
        # empresa
        if intencion["empresa"]:
            emp = row[COL_EMPRESA].strip() if len(row) > COL_EMPRESA else ""
            if normalizar(intencion["empresa"]) not in normalizar(emp):
                continue

        # acceso
        if intencion["filtro_acceso"]:
            acc = row[COL_ACCESO].strip() if len(row) > COL_ACCESO else ""
            if "PERMITIDO" not in acc.upper():
                continue

        # IESS vigente
        if intencion["filtro_iess"]:
            raw = row[7].strip() if len(row) > 7 else ""
            if iess_vigente(raw) != "Vigente":
                continue

        # columna dinámica (ej: inducción, cert médico, trabajo en caliente…)
        if intencion["col_filtro"] is not None:
            try:
                cel = row[intencion["col_filtro"]].strip() if len(row) > intencion["col_filtro"] else ""
                cel_n = normalizar(cel)
                # Se considera positivo si dice VIGENTE, APTO, SI, o tiene contenido
                # y NO dice VENCIDO, NO, SIN
                positivo = cel and not any(neg in cel_n for neg in ("vencido", " no ", "sin "))
                if not positivo:
                    continue
            except IndexError:
                continue

        resultado.append(row)
    return resultado


def buscar_por_nombre(query: str, filas: list) -> list:
    q = normalizar(query.strip())
    tokens = q.split()
    resultado = []
    for row in filas:
        apellido = normalizar(row[COL_APELLIDO] if len(row) > COL_APELLIDO else "")
        nombres  = normalizar(row[COL_NOMBRES]  if len(row) > COL_NOMBRES  else "")
        cedula   = row[COL_CEDULA].strip()       if len(row) > COL_CEDULA   else ""
        nc = apellido + " " + nombres
        if q == cedula or all(t in nc for t in tokens):
            resultado.append(row)
    return resultado

# ---------------------------------------------------------------------------

def formatear_detalle(row: list) -> str:
    acceso  = row[COL_ACCESO].strip() if len(row) > COL_ACCESO else ""
    nombre  = f"{row[COL_APELLIDO].strip()} {row[COL_NOMBRES].strip()}"
    empresa = row[COL_EMPRESA].strip() if len(row) > COL_EMPRESA else ""
    cedula  = row[COL_CEDULA].strip()  if len(row) > COL_CEDULA  else ""

    enc = "✅ *ACCESO PERMITIDO*" if "PERMITIDO" in acceso else "🚫 *SIN ACCESO*"
    ind  = row[6].strip()  if len(row) > 6  else ""
    iess = iess_vigente(row[7].strip() if len(row) > 7 else "")
    med  = row[9].strip()  if len(row) > 9  else ""
    apt  = row[10].strip() if len(row) > 10 else ""

    def ico(val, palabra="VIGENTE"):
        return "✅" if palabra.upper() in val.upper() else "❌"

    return "\n".join([
        enc, "",
        f"👤 *{nombre}*",
        f"🏭 {empresa}",
        f"🪪 {cedula}", "",
        f"{ico(ind)} Inducción: {ind}",
        f"{'✅' if iess == 'Vigente' else '❌'} IESS: {iess or 'Sin dato'}",
        f"{ico(med)} Cert. Médico: {med}",
        f"{'✅' if 'APTO' in apt.upper() else '❌'} Aptitud: {apt}",
    ])


def formatear_lista(filas: list, titulo: str = "") -> str:
    lineas = [f"*{titulo}*\n"] if titulo else []
    for row in filas:
        nombre = f"{row[COL_APELLIDO].strip()} {row[COL_NOMBRES].strip()}"
        emp    = row[COL_EMPRESA].strip() if len(row) > COL_EMPRESA else ""
        acceso = row[COL_ACCESO].strip()  if len(row) > COL_ACCESO  else ""
        ico    = "✅" if "PERMITIDO" in acceso else "🚫"
        lineas.append(f"{ico} {nombre} — _{emp}_")
    return "\n".join(lineas)

# ---------------------------------------------------------------------------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👷 *Verificador de Contratistas — Plantabal*\n\n"
        "Puedes preguntarme de forma natural:\n\n"
        "• `Martinez` — busca por apellido\n"
        "• `0912345678` — busca por cédula\n"
        "• `trabajadores de Frank Meta` — lista empresa\n"
        "• `de Frank Meta con acceso` — filtra por acceso\n"
        "• `de ellos, cuáles tienen inducción` — encadena filtros\n\n"
        "_Escribe /ayuda para más ejemplos._",
        parse_mode="Markdown",
    )


async def ayuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Ejemplos de consultas:*\n\n"
        "*Por persona:*\n"
        "`Martinez` · `Kevin Martinez` · `0912345678`\n\n"
        "*Por empresa:*\n"
        "`trabajadores de Tecnólogo sin Valla`\n"
        "`empresa Frank Meta con acceso`\n\n"
        "*Encadenadas (sobre el listado anterior):*\n"
        "`de ellos, cuáles tienen inducción vigente`\n"
        "`de esos, cuáles tienen certificado médico`\n"
        "`y cuáles tienen IESS al día`\n\n"
        "*Comandos:*\n"
        "/start · /ayuda · /refrescar",
        parse_mode="Markdown",
    )


async def refrescar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Recargando datos del consolidado...")
    try:
        _, empresas, filas = cargar_todo(forzar=True)
        await update.message.reply_text(
            f"✅ Datos actualizados: *{len(filas)} trabajadores* de *{len(empresas)} empresas*.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Error recargando: {e}")
        await update.message.reply_text("⚠️ No pude recargar. Verifica que el Google Sheet esté publicado.")


async def consultar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message.text.strip()
    if len(mensaje) < 2:
        return

    try:
        encabezados, empresas, filas = cargar_todo()
    except Exception as e:
        logging.error(f"Error cargando datos: {e}")
        await update.message.reply_text(
            "⚠️ No pude conectar con el consolidado. Verifica que el Google Sheet esté publicado."
        )
        return

    previos: list = ctx.user_data.get("ultimos", [])
    intencion = detectar_intencion(mensaje, encabezados, empresas, bool(previos))

    # ── Búsqueda por persona ───────────────────────────────────────────────
    if intencion["es_persona"] or intencion["cedula"]:
        query = intencion["cedula"] or intencion["nombre"] or mensaje
        resultados = buscar_por_nombre(query, filas)

        if not resultados:
            await update.message.reply_text(
                f"❓ No encontré a nadie con *{query}* en el consolidado.\n"
                "Verifica ortografía o busca por cédula.",
                parse_mode="Markdown",
            )
            return

        ctx.user_data["ultimos"] = resultados

        for row in resultados[:3]:
            await update.message.reply_text(formatear_detalle(row), parse_mode="Markdown")

        if len(resultados) > 3:
            await update.message.reply_text(
                f"_(Se encontraron {len(resultados)} coincidencias. Mostrando las primeras 3.)_",
                parse_mode="Markdown",
            )
        return

    # ── Filtro de grupo ────────────────────────────────────────────────────
    base = previos if intencion["usar_previos"] else filas
    resultados = aplicar_filtros(base, intencion)

    if not resultados:
        contexto = "ese filtro" if intencion["usar_previos"] else "esos criterios"
        detalle = []
        if intencion["empresa"]:
            detalle.append(f"empresa *{intencion['empresa']}*")
        if intencion["filtro_acceso"]:
            detalle.append("con acceso permitido")
        if intencion["col_nombre"]:
            detalle.append(f"con {intencion['col_nombre']} vigente")
        if intencion["filtro_iess"]:
            detalle.append("con IESS vigente")
        desc = ", ".join(detalle) if detalle else contexto
        await update.message.reply_text(
            f"❓ No encontré trabajadores con {desc}.",
            parse_mode="Markdown",
        )
        ctx.user_data["ultimos"] = []
        return

    ctx.user_data["ultimos"] = resultados

    # Título del listado
    partes = []
    if intencion["empresa"]:
        partes.append(intencion["empresa"])
    if intencion["filtro_acceso"]:
        partes.append("con acceso")
    if intencion["col_nombre"]:
        partes.append(f"con {intencion['col_nombre']} vigente")
    if intencion["filtro_iess"]:
        partes.append("con IESS vigente")
    if intencion["usar_previos"] and partes:
        titulo = f"Filtro: {' · '.join(partes)} ({len(resultados)} trabajadores)"
    else:
        titulo = f"{' · '.join(partes)} — {len(resultados)} trabajador{'es' if len(resultados) != 1 else ''}"

    # Dividir en bloques de 30 para no exceder límite de Telegram
    BLOQUE = 30
    for inicio in range(0, len(resultados), BLOQUE):
        bloque = resultados[inicio: inicio + BLOQUE]
        es_primero = inicio == 0
        t = titulo if es_primero else f"_(continuación {inicio + 1}–{inicio + len(bloque)})_"
        await update.message.reply_text(
            formatear_lista(bloque, t),
            parse_mode="Markdown",
        )

    await update.message.reply_text(
        "_Puedes seguir filtrando: escribe por ejemplo_ `de ellos, cuáles tienen inducción`",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("ayuda",     ayuda))
    app.add_handler(CommandHandler("refrescar", refrescar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar))
    app.run_polling()


if __name__ == "__main__":
    main()
