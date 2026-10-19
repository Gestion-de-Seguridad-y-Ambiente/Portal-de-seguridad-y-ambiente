---
name: matriz-compatibilidad-quimica
description: Construye matrices de compatibilidad para almacenamiento de productos quimicos a partir de las SDS (Hojas de Datos de Seguridad). Usala cuando el usuario adjunte SDS/FDS/MSDS, pida una matriz de compatibilidad o incompatibilidad quimica, quiera revisar la segregacion de una bodega de quimicos, o pregunte si dos productos pueden almacenarse juntos. Clasifica cada producto en grupos de almacenamiento usando el GHS/SGA, aplica la matriz base de segregacion y la Seccion 10.5 de cada SDS, y emite la matriz en HTML con los hallazgos de la bodega.
---

# Matriz de compatibilidad quimica

## El principio que no se negocia

El **GHS/SGA clasifica peligros; no define compatibilidad de almacenamiento.** Dos
productos con el mismo pictograma pueden ser perfectamente compatibles o matar a
alguien si se mezclan. Hipoclorito de sodio y sosa caustica son ambos GHS05 y
conviven; hipoclorito y acido clorhidrico son ambos GHS05 y liberan cloro gaseoso.

Por eso el GHS entra como **capa de entrada** (clasificar en grupos) y la segregacion
sale de la matriz base + la Seccion 10.5 de cada SDS. Si el usuario pide una matriz
"segun el GHS", explicale esto una vez, con un ejemplo de su propio inventario, y
sigue adelante con el metodo correcto. No construyas una matriz solo con clases GHS.

## Flujo de trabajo

### 1. Recibir e inventariar las SDS

Lee cada SDS adjunta. Extrae los campos segun `references/extraccion-sds.md`
(secciones 1, 2, 3, 7, 10 y 14). Rechaza documentos que no sean SDS de 16 secciones:
una ficha tecnica o una etiqueta no sirve, pidele la SDS real al usuario.

Transcribe la Seccion 10.5 **literal**. No la resumas ni la interpretes todavia.

### 2. Asignar grupo de almacenamiento

Aplica `references/grupos-almacenamiento.md`: 15 grupos, G1 a G15, con reglas de
desempate explicitas para productos multiclase. La concentracion importa: acido
sulfurico 98 % es G12 y al 10 % es G11.

Cuando un producto tenga mas de una clase GHS relevante, **di en voz alta que regla
de desempate aplicaste y por que**. Es el punto donde mas se equivoca la matriz.

### 3. Confirmar con el usuario antes de emitir

Antes de generar nada, muestra una tabla corta: producto - grupo - regla aplicada -
texto de la Seccion 10.5. Pide confirmacion de:
- los grupos asignados,
- los productos con `SIN DATO` en la Seccion 10.5,
- la **ubicacion real actual** de cada producto en bodega (el usuario la sabe, la SDS no).

Sin ubicaciones reales, la matriz es un ejercicio teorico y no detecta nada.

### 4. Armar el inventario CSV

Escribe el inventario con el formato de `ejemplos/inventario-ejemplo.csv`. Columnas
obligatorias: `codigo`, `producto`, `grupo`, `ubicacion`. El resto suma trazabilidad.

Un consejo util: la `ubicacion` se escribe como `Zona - Detalle`
(`Bodega A - Estante 3`). El script compara la zona para las incompatibilidades X
y la ubicacion exacta para las S.

### 5. Generar la matriz

```bash
python3 scripts/generar_matriz.py inventario.csv matriz-compatibilidad.html \
    --empresa "Plantabal S.A."
```

Solo usa la libreria estandar de Python. Produce un HTML con la matriz NxN
coloreada, la leyenda, los **hallazgos de segregacion** (pares incompatibles que hoy
comparten zona o ubicacion) y los **vacios de informacion** por cerrar.

El script endurece automaticamente una celda a X cuando la Seccion 10.5 de alguna de
las dos SDS menciona al otro tipo de producto; esas celdas se marcan con asterisco.
Nunca relaja una celda.

### 6. Entregar y cerrar

En la respuesta al usuario, siempre:
1. **Los hallazgos primero.** Si hay un par X compartiendo bodega, esa es la primera
   linea de tu respuesta, no un anexo. Nombra los dos productos y la consecuencia
   concreta ("liberan cloro gaseoso", "incendio sin fuente de ignicion externa").
2. Las acciones correctivas, en orden de urgencia y con el criterio de la columna
   "Codigo" de `references/criterios-matriz.md`.
3. Los vacios de informacion (SDS faltantes, vencidas o sin Seccion 10.5).

Publica el HTML como artefacto cuando el usuario lo vaya a compartir o imprimir.

## Lo que esta habilidad no hace

- **No reemplaza al responsable de seguridad.** La matriz es una herramienta de
  decision; la firma es humana.
- **No calcula cantidades maximas por area** ni distancias segun carga de fuego
  (eso es NFPA 400 / INEN 2266 capitulo de bodegas, dimensionamiento aparte).
- **No evalua compatibilidad de materiales de envase** (Seccion 10.5 a veces lo
  mezcla; sepáralo en observaciones).
- **No decide sobre reacciones de proceso**, solo almacenamiento conjunto.
- Si una SDS no declara incompatibilidades, **no se asume que no las tiene**.

## Archivos

- `references/grupos-almacenamiento.md` - los 15 grupos, mapeo GHS y reglas de desempate.
- `references/matriz-base.csv` - matriz 15x15 con codigos C / S / X.
- `references/criterios-matriz.md` - que exige cada codigo en bodega, justificacion
  de las celdas criticas y respaldo normativo.
- `references/extraccion-sds.md` - que leer de cada SDS y como manejar SDS incompletas.
- `scripts/generar_matriz.py` - generador del HTML.
- `ejemplos/inventario-ejemplo.csv` - plantilla del inventario.
