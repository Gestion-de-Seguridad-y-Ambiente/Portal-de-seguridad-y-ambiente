# Qué se extrae de cada SDS

Se leen **cinco** secciones. Las demás no aportan a la matriz.

| Sección | Qué se saca | Campo del inventario |
|---------|-------------|----------------------|
| 1 | Nombre comercial, proveedor, usos | `producto`, `proveedor` |
| 2 | Clasificación GHS: clases, códigos H, pictogramas, palabra de advertencia | `clases_ghs`, `codigos_h`, `pictogramas` |
| 3 | Componente principal y su CAS; concentración | `cas`, `concentracion` |
| 7 | Condiciones de almacenamiento seguro y materiales incompatibles mencionados ahí | `cond_almacenamiento` |
| 10 | 10.3 Posibilidad de reacciones peligrosas, 10.5 Materiales incompatibles, 10.6 Productos de descomposición peligrosos | `incompat_sds`, `descomposicion` |
| 14 | Clase de peligro para transporte (ONU), si existe | `onu` |

## Reglas de extracción

- **Transcribir, no interpretar.** `incompat_sds` lleva el texto literal de la 10.5,
  en el idioma de la SDS. La interpretación ocurre después, al asignar grupo.
- **SDS sin Sección 10.5 útil** ("ninguno conocido", "no aplica", casilla vacía):
  marcar `incompat_sds = SIN DATO` y anotarlo en el informe de vacíos. No se asume
  que no tiene incompatibilidades; se aplica la matriz por grupo y se solicita SDS
  actualizada al proveedor.
- **SDS con más de 3 años** desde su fecha de revisión (Sección 16): marcar en el
  informe de vacíos. La clasificación GHS cambia entre revisiones.
- **SDS que no es SDS**: fichas técnicas, hojas de producto y etiquetas no sirven.
  Si el documento no tiene las 16 secciones, se rechaza y se pide la SDS real.
- **Mezclas**: si un producto es mezcla, el grupo lo fija el componente de mayor
  peligro de almacenamiento, no el de mayor concentración.
- **Concentración importa**: ácido sulfúrico al 98 % es G12; al 10 % es G11. Peróxido
  de hidrógeno al 50 % es G8; al 3 % es G15. Registrar siempre `concentracion`.

## Verificación obligatoria antes de emitir la matriz

Para cada producto, confirmar en voz alta con el usuario:
1. Grupo asignado y la regla de desempate que se aplicó, si hubo más de una clase.
2. Cualquier producto donde la Sección 10.5 obligue a una restricción **más dura**
   que la matriz por grupos.
3. Productos con `SIN DATO`.

Nunca emitir una matriz sin esa confirmación. Una celda verde equivocada es un
incidente, no un error de formato.
