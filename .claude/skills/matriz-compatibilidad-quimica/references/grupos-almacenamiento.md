# Grupos de almacenamiento (G1–G15)

Cada producto del inventario se asigna a **un solo grupo**. La asignación se hace
leyendo la Sección 2 (clasificación GHS) de la SDS y aplicando las reglas de
desempate de abajo.

| Grupo | Nombre | Clases GHS / indicios típicos | Ejemplos |
|-------|--------|-------------------------------|----------|
| G1  | Explosivos y pirotécnicos | Unstable Expl., Expl. 1.1–1.6; H200–H205 | Detonadores, mecha |
| G2  | Gases inflamables | Flam. Gas 1/2; H220, H221 | GLP, acetileno, propano |
| G3  | Gases comprimidos inertes | Press. Gas sin otra clase; H280 | Nitrógeno, argón, CO2, aire |
| G4  | Gases oxidantes | Ox. Gas 1; H270 | Oxígeno, cloro gas |
| G5  | Líquidos inflamables y combustibles | Flam. Liq. 1–4; H224–H227 | Diésel, gasolina, thinner, alcohol, acetona |
| G6  | Sólidos inflamables, pirofóricos y autorreactivos | Flam. Sol., Self-react., Pyr. Sol/Liq, Self-heat; H228, H240–H252 | Azufre, fósforo, nitrocelulosa |
| G7  | Reactivos con agua | Water-react. 1–3; H260, H261 | Sodio metálico, carburo de calcio, hidruros |
| G8  | Oxidantes (sólidos y líquidos) | Ox. Liq./Sol. 1–3; H271, H272 | Hipoclorito de sodio, permanganato, nitratos, peróxido de hidrógeno |
| G9  | Peróxidos orgánicos | Org. Perox. A–F; H240–H242 | MEKP, peróxido de benzoílo |
| G10 | Tóxicos agudos y plaguicidas | Acute Tox. 1–3; H300, H310, H330, H301, H311, H331 | Plaguicidas, fungicidas, biocidas concentrados |
| G11 | Ácidos inorgánicos no oxidantes | Skin Corr. 1 + inorgánico sin carácter oxidante; H314 | Ácido clorhídrico, fosfórico, sulfámico |
| G12 | Ácidos oxidantes fuertes | Skin Corr. 1 + Ox.; H314 + H271/H272 | Ácido nítrico, sulfúrico concentrado, perclórico |
| G13 | Ácidos orgánicos | Skin Corr./Irrit. + orgánico; H314, H315 | Acético, fórmico, cítrico, peracético* |
| G14 | Bases y álcalis | Skin Corr. 1, carácter alcalino; H314 | Sosa cáustica, hidróxido de potasio, amoníaco, cal |
| G15 | Misceláneos, peligro ambiental o no peligrosos | Aquatic Acute/Chronic solos, Skin/Eye Irrit. leves, o sin clasificación | Detergentes neutros, aceites lubricantes, pinturas base agua |

\* El ácido peracético es ácido **y** oxidante fuerte: clasifíquelo en G12, no en G13.

## Reglas de desempate (en orden)

1. **G1 manda sobre todo.** Explosivo es explosivo.
2. **Oxidante gana a corrosivo.** Si la SDS declara Ox. Liq./Ox. Sol. **y** Skin Corr.,
   va a G12 (si es ácido) o G8 (si no lo es). Caso típico: hipoclorito de sodio →
   G8, no G14, aunque su pH sea alcalino.
3. **Reactivo con agua gana a inflamable.** H260/H261 → G7 aunque también sea Flam. Sol.
4. **Tóxico agudo gana a corrosivo e irritante**, pero no a oxidante ni a inflamable.
   Un plaguicida en solvente inflamable (Flam. Liq. 3 + Acute Tox. 3) va a **G5**
   con la observación de toxicidad, porque el riesgo de almacenamiento dominante
   es el incendio.
5. **Gas gana a todo lo demás** salvo G1: cualquier producto en cilindro a presión
   va a G2, G3 o G4 según su clase.
6. Si no cae en ninguno, va a **G15**.

## Campo obligatorio: `incompat_sds`

Independientemente del grupo, se transcribe literal la **Sección 10.5** de la SDS
("Materiales incompatibles"). Ese texto sobrescribe la matriz por grupos cuando
es más restrictivo. Nunca al revés: la SDS puede volver roja una celda verde,
pero jamás vuelve verde una celda roja.
