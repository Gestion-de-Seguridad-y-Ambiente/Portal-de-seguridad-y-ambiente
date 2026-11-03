# Contratistas Plantabal — App Android

App React Native (Expo) para verificar contratistas en campo.

## Configuración antes de compilar

Edita `app.json` y reemplaza los valores en `extra`:

```json
"extra": {
  "sheetCsvUrl": "https://docs.google.com/spreadsheets/d/e/TU_URL/pub?output=csv",
  "geminiApiKey": "TU_API_KEY_DE_GEMINI"
}
```

**Cómo obtener la API Key de Gemini (gratis):**
1. Ve a https://aistudio.google.com/app/apikey
2. Clic en "Create API Key"
3. Copia la clave y pégala en `geminiApiKey`

## Compilar el APK (sin costo)

### Requisitos
- Cuenta gratuita en https://expo.dev
- Node.js instalado

### Pasos

```bash
npm install -g eas-cli
npm install
eas login          # iniciar sesión en Expo
eas build -p android --profile preview
```

Cuando termine (~10 min) descarga el APK desde expo.dev y compártelo por WhatsApp.

## Funcionalidades

- **Búsqueda** por nombre, apellido o cédula
- **Filtro por empresa** (detecta todas las del consolidado)
- **Chips de filtro**: Con acceso / IESS vigente / Inducción vigente
- **Tarjeta de detalle**: todos los documentos del trabajador
- **Asistente IA** (Gemini): pregunta en lenguaje natural
  - "Trabajadores de Empresa X con certificado en alturas"
  - "¿Quiénes de Don Quiño tienen IESS vencido?"
  - "Fernández tiene certificado médico?"
