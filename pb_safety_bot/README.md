# Pb_safety_bot — Verificador de Contratistas Plantabal

Bot de Telegram que consulta el Consolidado de Contratistas en tiempo real.

## Variables de entorno requeridas

| Variable | Descripción |
|---|---|
| `BOT_TOKEN` | Token del bot (obtenido de @BotFather) |
| `SHEET_CSV_URL` | URL del Google Sheet publicado como CSV |

## Cómo obtener la URL del Google Sheet

1. Abre el Google Sheet con el consolidado
2. Archivo → Compartir → Publicar en la web
3. Selecciona la hoja "CONSOLIDADO" → formato CSV → Publicar
4. Copia el enlace generado y ponlo en `SHEET_CSV_URL`

## Deploy en Railway

1. Ve a railway.app → New Project → Deploy from GitHub repo
2. Selecciona este repositorio, carpeta `pb_safety_bot`
3. En Variables agrega `BOT_TOKEN` y `SHEET_CSV_URL`
4. Railway detecta el Procfile y lanza el bot automáticamente

## Uso

**Por persona** — escribe nombre, apellido o cédula:
- `Martinez` · `Kevin Martinez` · `0912345678`

**Por empresa** — el bot detecta el nombre de empresa del consolidado:
- `trabajadores de Frank Meta`
- `empresa Tecnólogo sin Valla con acceso`

**Encadenado** — filtra sobre el listado anterior:
- `de ellos, cuáles tienen inducción`
- `de esos, cuáles tienen certificado médico`
- `y cuáles tienen IESS al día`

**El bot detecta automáticamente las columnas** del consolidado (inducción,
cert. médico, aptitud, y cualquier columna adicional que tenga el sheet).

**Comandos:** `/start` · `/ayuda` · `/refrescar` (recarga el consolidado ahora)
