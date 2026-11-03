"""
Pb_safety_bot — Verificador de contratistas Plantabal
Lee el consolidado desde un Google Sheet publicado como CSV.
"""
import os, csv, io, unicodedata, logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN        = os.environ["BOT_TOKEN"]
SHEET_CSV    = os.environ["SHEET_CSV_URL"]  # URL pública del Google Sheet en formato CSV

# ── Columnas del consolidado (índices, empieza en 0) ──────────────────────────
# A=0 N°  B=1 Apellido  C=2 Nombres  D=3 Empresa  E=4 Cédula
# F=5 Ind.Fecha  G=6 Vigente Ind.  H=7 IESS  I=8 CertMéd.Fecha
# J=9 Vigente Med.  K=10 Aptitud  L=11 ACCESO
COL = {
    "apellido": 1,
    "nombres":  2,
    "empresa":  3,
    "cedula":   4,
    "ind_fecha":    5,
    "ind_vigente":  6,
    "iess":         7,
    "med_fecha":    8,
    "med_vigente":  9,
    "aptitud":      10,
    "acceso":       11,
}

def normalizar(texto: str) -> str:
    """Quita tildes y pasa a minúsculas para búsqueda tolerante."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )

def cargar_datos() -> list[dict]:
    """Descarga el CSV del Google Sheet y retorna lista de filas."""
    resp = requests.get(SHEET_CSV, timeout=10)
    resp.raise_for_status()
    reader = csv.reader(io.StringIO(resp.text))
    filas = []
    for i, row in enumerate(reader):
        if i < 5:  # Las primeras 5 filas son encabezados/títulos del consolidado
            continue
        if len(row) < 12 or not row[COL["apellido"]].strip():
            continue
        filas.append(row)
    return filas

def buscar_trabajador(query: str, filas: list) -> list:
    """Busca por nombre (apellido o nombres) o cédula."""
    q = normalizar(query.strip())
    resultados = []
    for row in filas:
        apellido = normalizar(row[COL["apellido"]])
        nombres  = normalizar(row[COL["nombres"]])
        cedula   = row[COL["cedula"]].strip()
        if q in apellido or q in nombres or q == cedula:
            resultados.append(row)
    return resultados

def formatear_resultado(row: list) -> str:
    """Convierte una fila en un mensaje legible para Telegram."""
    acceso   = row[COL["acceso"]].strip()
    nombre   = f"{row[COL['apellido']].strip()} {row[COL['nombres']].strip()}"
    empresa  = row[COL["empresa"]].strip()
    cedula   = row[COL["cedula"]].strip()

    if "PERMITIDO" in acceso:
        encabezado = "✅ *ACCESO PERMITIDO*"
    else:
        encabezado = "🚫 *SIN ACCESO*"

    ind  = row[COL["ind_vigente"]].strip()
    iess = row[COL["iess"]].strip()
    med  = row[COL["med_vigente"]].strip()
    apt  = row[COL["aptitud"]].strip()

    def icono(val, ok_text="✔"):
        return "✅" if ok_text in val else "❌"

    lineas = [
        encabezado,
        f"",
        f"👤 *{nombre}*",
        f"🏭 Empresa: {empresa}",
        f"🪪 Cédula: {cedula}",
        f"",
        f"{icono(ind)} Inducción: {ind}",
        f"{icono(iess, 'IESS') if iess else '❌'} IESS: {iess or 'Sin dato'}",
        f"{icono(med)} Cert. Médico: {med}",
        f"{icono(apt, 'APTO')} Aptitud: {apt}",
    ]
    return "\n".join(lineas)

# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👷 *Verificador de Contratistas — Plantabal*\n\n"
        "Escribe el *apellido*, *nombre* o *número de cédula* del trabajador "
        "y te digo si tiene acceso a planta.\n\n"
        "_Ejemplo:_ `Martinez` o `0912345678`",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Comandos disponibles:*\n\n"
        "/start — Mensaje de bienvenida\n"
        "/ayuda — Esta ayuda\n\n"
        "O simplemente escribe el nombre o cédula del trabajador.",
        parse_mode="Markdown"
    )

async def consultar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if len(query) < 3:
        await update.message.reply_text("⚠️ Escribe al menos 3 caracteres para buscar.")
        return

    await update.message.reply_text("🔍 Buscando...")

    try:
        filas = cargar_datos()
    except Exception as e:
        await update.message.reply_text(
            "⚠️ No pude cargar los datos del consolidado. Verifica que el Google Sheet esté publicado."
        )
        logging.error(f"Error cargando datos: {e}")
        return

    resultados = buscar_trabajador(query, filas)

    if not resultados:
        await update.message.reply_text(
            f"❓ No encontré a nadie con *{query}* en el consolidado.\n"
            f"Verifica la ortografía o busca por cédula.",
            parse_mode="Markdown"
        )
        return

    for row in resultados[:3]:  # máximo 3 resultados
        msg = formatear_resultado(row)
        await update.message.reply_text(msg, parse_mode="Markdown")

    if len(resultados) > 3:
        await update.message.reply_text(
            f"_(Se encontraron {len(resultados)} coincidencias. Mostrando las primeras 3. "
            f"Sé más específico si necesitas otro resultado.)_",
            parse_mode="Markdown"
        )

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar))
    app.run_polling()

if __name__ == "__main__":
    main()
