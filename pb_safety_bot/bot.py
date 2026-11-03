"""
Pb_safety_bot — Verificador de contratistas Plantabal
Lee el consolidado desde un Google Sheet publicado como CSV.
"""
import os, csv, io, unicodedata, logging, re
from datetime import date
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

def iess_vigente(valor: str) -> str:
    """
    El campo IESS contiene la fecha de última afiliación (ej: '1/9/2026').
    Está vigente si el mes/año es >= mes anterior al actual.
    Retorna 'Vigente' o 'Vencido'.
    """
    valor = valor.strip()
    if not valor:
        return ""
    try:
        partes = valor.replace("-", "/").split("/")
        if len(partes) == 3:
            # puede venir d/m/a o m/d/a — asumimos d/m/a como el sheet en español
            d, m, a = int(partes[0]), int(partes[1]), int(partes[2])
            if a < 100:
                a += 2000
            hoy = date.today()
            # vigente si la fecha IESS es del mes anterior o posterior
            limite = date(hoy.year if hoy.month > 1 else hoy.year - 1,
                          hoy.month - 1 if hoy.month > 1 else 12, 1)
            if date(a, m, 1) >= limite:
                return "Vigente"
            else:
                return "Vencido"
    except Exception:
        pass
    return valor  # si no se puede parsear, retorna el valor crudo

def buscar_trabajador(query: str, filas: list) -> list:
    """Busca por nombre (apellido o nombres, soporta 'Martinez Kevin') o cédula."""
    q = normalizar(query.strip())
    tokens = q.split()
    resultados = []
    for row in filas:
        apellido = normalizar(row[COL["apellido"]])
        nombres  = normalizar(row[COL["nombres"]])
        cedula   = row[COL["cedula"]].strip()
        nombre_completo = apellido + " " + nombres
        # cédula exacta
        if q == cedula:
            resultados.append(row)
            continue
        # todos los tokens deben aparecer en el nombre completo
        if all(t in nombre_completo for t in tokens):
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
    iess_raw = row[COL["iess"]].strip()
    iess = iess_vigente(iess_raw)
    med  = row[COL["med_vigente"]].strip()
    apt  = row[COL["aptitud"]].strip()

    def icono(val, ok_text="VIGENTE"):
        return "✅" if ok_text.upper() in val.upper() else "❌"

    lineas = [
        encabezado,
        f"",
        f"👤 *{nombre}*",
        f"🏭 Empresa: {empresa}",
        f"🪪 Cédula: {cedula}",
        f"",
        f"{icono(ind, 'VIGENTE')} Inducción: {ind}",
        f"{'✅' if iess == 'Vigente' else '❌'} IESS: {iess or 'Sin dato'}",
        f"{icono(med, 'VIGENTE')} Cert. Médico: {med}",
        f"{'✅' if 'APTO' in apt.upper() else '❌'} Aptitud: {apt}",
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

PALABRAS_PREGUNTA = {"tiene", "puede", "esta", "está", "es", "cumple", "tiene",
                     "certificado", "apto", "acceso", "vigente", "vencido",
                     "induccion", "inducción", "iess", "medico", "médico",
                     "altura", "riesgo", "riesgos", "laboral", "trabajo"}

def es_pregunta_natural(texto: str) -> bool:
    """Detecta si el mensaje es una pregunta sobre certificados, no un nombre."""
    if texto.endswith("?") or texto.startswith("¿"):
        return True
    tokens = set(normalizar(texto).split())
    return len(tokens & PALABRAS_PREGUNTA) >= 2

async def consultar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if len(query) < 3:
        await update.message.reply_text("⚠️ Escribe al menos 3 caracteres para buscar.")
        return

    if es_pregunta_natural(query):
        await update.message.reply_text(
            "💡 Para consultar el estado de un trabajador, escribe directamente "
            "su *apellido*, *nombre* o *número de cédula*.\n\n"
            "_Ejemplos:_\n`Martinez`\n`Martinez Kevin`\n`0912345678`",
            parse_mode="Markdown"
        )
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
