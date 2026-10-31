# Skill: Generador de Instructivos Plantabal

Activa este skill cuando el usuario pida crear o actualizar un instructivo del sistema GE-SO de Plantabal (GE-SO-I, GE-SO-R, GE-SO-D o cualquier documento de gestión con la plantilla corporativa).

## Template y script

- **Plantilla Word**: `/root/.claude/uploads/873d328e-e6e2-50a6-bb43-ebf160679516/f16cdbf7-GE-SO-DXX_Plantilla_Instructivo.docx`
- **Script generador**: `/home/user/kewei/scripts/instructivos/build_instructivo.py`
- **Ejemplo de config**: `/home/user/kewei/scripts/instructivos/config_ejemplo_GE-SO-I002.json`
- **Salida**: `/home/user/kewei/<CODIGO>_<titulo_slug>_v<version>.docx`

## Convención de códigos

| Tipo     | Código      | Descripción                          |
|----------|-------------|--------------------------------------|
| I — Instructivo | GE-SO-I### | Pasos detallados de un proceso       |
| R — Registro    | GE-SO-R### | Formulario/registro de datos         |
| D — Documento   | GE-SO-D### | Documento normativo/procedimiento    |
| P — Procedimiento | GE-SO-P### | Procedimiento operativo estándar    |

## Workflow (siempre seguir este orden)

### 1. Recopilar información
Pregunta o extrae del contexto:
- `codigo` — ej. "GE-SO-I003", "GE-SO-R036"
- `titulo` — nombre completo del documento
- `version` — "01" para emisión inicial, "02" para segunda revisión, etc.
- `objetivo` — 2-3 oraciones: qué busca lograr el documento
- `alcance` — a quién aplica
- `definiciones` — lista de términos clave con sus definiciones
- `responsabilidades` — por cargo: qué le corresponde hacer
- `desarrollo` — fases y actividades (la parte más importante)
- `documentos_referencia` — códigos y nombres de otros docs relacionados

### 2. Crear el JSON de configuración
Genera el archivo JSON siguiendo exactamente la estructura del ejemplo en:
`/home/user/kewei/scripts/instructivos/config_ejemplo_GE-SO-I002.json`

Guárdalo en: `/tmp/claude-0/-home-user-kewei/873d328e-e6e2-50a6-bb43-ebf160679516/scratchpad/config_<CODIGO>.json`

### 3. Ejecutar el generador
```bash
python3 /home/user/kewei/scripts/instructivos/build_instructivo.py \
  /tmp/claude-0/-home-user-kewei/873d328e-e6e2-50a6-bb43-ebf160679516/scratchpad/config_<CODIGO>.json
```

### 4. Verificar visualmente
```bash
python3 /root/.claude/skills/synced/a0e77799-0b6d-46d2-aa0c-91658295909b_a93dcd9b-1f6c-4fa0-a611-b5956f26318f/docx/scripts/office/soffice.py \
  --headless --convert-to pdf /home/user/kewei/<archivo>.docx
pdftoppm -jpeg -r 100 /home/user/kewei/<archivo>.pdf /tmp/preview_page
```
Leer las imágenes generadas con Read para verificar que el formato sea correcto.

### 5. Comprometer y enviar
```bash
cd /home/user/kewei
git add <archivo>.docx scripts/instructivos/
git commit -m "Add <CODIGO>: <titulo>"
git push -u origin claude/serene-einstein-jriq3d
```
Enviar el archivo `.docx` al usuario con SendUserFile.

## Estructura JSON — referencia rápida

```json
{
  "codigo":        "GE-SO-I003",
  "titulo":        "Nombre completo del instructivo",
  "version":       "01",
  "fecha":         "2024-11",
  "elaborado_por": "Pasante de Seguridad y Ambiente",
  "revisado_por":  "Jefe de Seguridad y Ambiente",
  "aprobado_por":  "Gerente de Planta",
  "objetivo":      "...",
  "alcance":       "...",
  "definiciones": [
    { "termino": "...", "definicion": "..." }
  ],
  "responsabilidades": [
    { "cargo": "...", "responsabilidad": "..." }
  ],
  "desarrollo": [
    {
      "fase": "FASE 1 — NOMBRE DE LA FASE",
      "actividades": [
        {
          "actividad":   "Descripción detallada de lo que se hace.",
          "responsable": "Cargo o persona",
          "notificar":   "Quién debe ser notificado (puede ser vacío)"
        }
      ]
    }
  ],
  "documentos_referencia": [
    { "codigo": "GE-SO-R34", "nombre": "Nombre del documento", "tipo": "Registro" }
  ],
  "control_cambios": [
    {
      "version":     "01",
      "fecha":       "2024-11",
      "descripcion": "Emisión inicial",
      "elabora":     "...",
      "revisa":      "...",
      "aprueba":     "..."
    }
  ]
}
```

## Notas importantes

- El script reutiliza la plantilla con logo, colores corporativos y estructura ya aprobada.
- El encabezado (header1.xml) se actualiza automáticamente con el nuevo código y título.
- Los espacios vacíos entre tablas se comprimen automáticamente para evitar saltos de página innecesarios.
- Para TAR (Trabajos de Alto Riesgo) siempre mencionar: trabajo en caliente, eléctrico, altura, confinado, excavación, izaje.
- La tabla de Desarrollo tiene 4 columnas: #, Actividad, Responsable, Notificar.
- El formato condicional (rojo/amarillo/verde) del Consolidado de Contratistas es independiente de este workflow.
