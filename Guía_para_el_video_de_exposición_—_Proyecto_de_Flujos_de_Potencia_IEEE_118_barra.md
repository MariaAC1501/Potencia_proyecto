# Guía para el video de exposición — Proyecto de Flujos de Potencia IEEE 118 barras

MI-5215 Análisis de Sistemas Eléctricos de Potencia · II Semestre 2026 · Nov 10, 2026 · @Greivin

## Propósito y formato del video

La exposición del proyecto se sustituye por un video grabado por cada grupo. Las secciones 1 a 3 del video son iguales para todos los grupos; en la sección 4 cada grupo desarrolla, a su elección, uno de cinco escenarios sencillos de modificación de la red IEEE de 118 barras.

**Requisitos del video**

- Duración: entre 30 y 40 minutos, igual que la exposición presencial establecida en la rúbrica.
- Formato: MP4, resolución mínima 1080p, audio claro y sin música de fondo que tape la voz.
- Participación: todos los integrantes deben aparecer con voz (y preferiblemente cámara) explicando al menos una sección. Cada integrante se identifica por nombre al iniciar su parte.
- Corridas: las ejecuciones del programa se graban en pantalla de forma continua, sin cortes ni acelerado, desde que se lanza el programa hasta que se exporta el Excel. Se permite editar entre secciones, no dentro de una corrida.
- Evidencia: la pantalla debe mostrar el código, la consola o interfaz, el archivo Excel de entrada y el de salida.

**Entrega**

- El video se sube por evaluaciones del TEC Digital, en el apartado del proyecto, junto con el programa, el informe en Word y la presentación en PowerPoint, un día antes de la fecha programada para la exposición.
- Si el archivo excede el límite de la plataforma, se sube a una carpeta compartida (Drive u OneDrive institucional) y se entrega el enlace con acceso para el profesor.
- Se entregan también los archivos Excel de entrada y salida del caso base y del escenario elegido.

## Estructura del video

El video sigue seis secciones en este orden; los tiempos son una guía y la suma debe quedar entre 30 y 40 minutos.

| Sección | Contenido | Tiempo sugerido | Común o por grupo |
| --- | --- | --- | --- |
| 0. Presentación | Curso, nombre del proyecto, integrantes y escenario elegido | 1–2 min | Común |
| 1. Configuración del programa | Arquitectura, datos de entrada, métodos implementados | 8–10 min | Común |
| 2. Caso base IEEE 118 barras | Descripción de la red y de los datos usados | 3–4 min | Común |
| 3. Corrida del caso base | Ejecución de los tres métodos, resultados y validación | 6–8 min | Común |
| 4. Escenario modificado | Modificación de los datos base, corrida y análisis | 10–12 min | Elegido por el grupo |
| 5. Conclusiones y cierre | Conclusiones del método y del escenario | 2–3 min | Común |

## Sección 1 (común): configuración del programa

El objetivo es que quien vea el video entienda cómo el programa pasa de un Excel con datos de red a un Excel con resultados de flujo de potencia. Muestren el código en pantalla mientras explican cada punto.

1. **Lenguaje y organización.** Lenguaje o herramienta usada (MATLAB, Python, otro), archivos o módulos que componen el programa y la función de cada uno.
2. **Datos de entrada desde Excel.** Mostrar el libro de entrada: hojas de barras, ramas (líneas y transformadores), generadores y compensación en derivación. Explicar las columnas, las unidades y la base de potencia (100 MVA).
3. **Clasificación de barras.** Cómo el programa identifica la barra de referencia (slack), las barras PV y las PQ a partir de los datos.
4. **Construcción de la matriz Ybus.** Modelo π de líneas, tratamiento de transformadores con relación de transformación (tap) y ángulo de desfase, y elementos en derivación. Mostrar el fragmento de código correspondiente.
5. **Versatilidad.** Demostrar que el número de barras se define por los datos de entrada y no está fijo en el código. Recomendado: una corrida rápida (menos de 1 minuto) con IEEE 9 o 14 barras.
6. **Métodos numéricos implementados.** Para cada uno de los tres métodos (Newton-Raphson y Gauss-Seidel obligatorios, más el tercero elegido):
    - Ecuaciones que resuelve y variables de estado.
    - Criterio de convergencia (tolerancia en pu) y número máximo de iteraciones.
    - Valores iniciales (perfil plano u otro) y, en Gauss-Seidel, factor de aceleración si se usó.
    - Tratamiento de los límites de potencia reactiva de los generadores (conversión PV a PQ), si se implementó.
7. **Cálculo de resultados.** Cómo se obtienen flujos de potencia por rama, pérdidas por rama y totales, y potencia de la barra slack.
8. **Exportación a Excel.** Hojas del libro de salida y qué contiene cada una.

## Secciones 2 y 3 (comunes): caso base IEEE 118 barras y su corrida

El caso base es la red IEEE de 118 barras en la versión de datos que el grupo descargó (MATPOWER case118 u otra fuente indicada en el enunciado). Todos los resultados del escenario de la sección 4 se comparan contra esta corrida.

**Sección 2 — Descripción del caso base**

- Fuente exacta de los datos y versión.
- Número de barras, ramas (líneas y transformadores), generadores y barras con carga, tal como aparecen en su archivo.
- Barra de referencia (barra 69 en la versión de MATPOWER) y niveles de tensión de la red (138 kV y 345 kV).
- Carga total (MW y MVAr) y generación programada total.
- Un diagrama unifilar de la red, tomado de la literatura y citado, en el que se pueda ubicar las barras del escenario elegido.

**Sección 3 — Corrida del caso base (grabación continua)**

1. Abrir el Excel de entrada y lanzar el programa con Newton-Raphson; mostrar las iteraciones y el desajuste (mismatch) máximo en cada una.
2. Repetir con Gauss-Seidel y con el tercer método.
3. Abrir el Excel de salida y mostrar: tensiones y ángulos por barra, flujos P y Q por rama, pérdidas totales y potencia de la barra slack.
4. Presentar la tabla comparativa de los tres métodos:

| Método | Iteraciones | Tiempo de cómputo (s) | Mismatch final (pu) | P slack (MW) | Pérdidas P (MW) | Pérdidas Q (MVAr) |
| --- | --- | --- | --- | --- | --- | --- |
| Newton-Raphson |  |  |  |  |  |  |
| Gauss-Seidel |  |  |  |  |  |  |
| Tercer método |  |  |  |  |  |  |

5. **Validación contra la referencia publicada.** Comparar con la solución de referencia (MATPOWER o artículo IEEE citado): error máximo de tensión en pu, error máximo de ángulo en grados, diferencia en pérdidas totales y en potencia de la slack. Explicar cualquier diferencia apreciable.
6. Señalar en el caso base las 5 barras de menor tensión y las 5 ramas con mayor flujo de potencia aparente. Estos valores son la referencia para el escenario.

## Sección 4: escenario elegido por el grupo

Cada grupo elige uno de los cinco escenarios siguientes y le informa al profesor cuál escogió. Todos los escenarios consisten en un solo cambio a los datos base y se analizan con el mismo procedimiento.

**Procedimiento en el video**

1. Explicar el cambio y ubicar en el diagrama unifilar la barra, línea o generador involucrado.
2. Mostrar en una copia del Excel de entrada el dato modificado, resaltado en color.
3. Correr el escenario con Newton-Raphson y con Gauss-Seidel, en grabación continua.
4. Comparar los resultados con el caso base usando la tabla de abajo.
5. Responder las tres preguntas del escenario elegido.

**Tabla de comparación (obligatoria en el video)**

| Variable | Caso base | Escenario | Diferencia |
| --- | --- | --- | --- |
| Tensión mínima (pu) y barra |  |  |  |
| Tensión máxima (pu) y barra |  |  |  |
| Barras fuera de 0,95–1,05 pu |  |  |  |
| P de la barra slack 69 (MW) |  |  |  |
| Q de la barra slack 69 (MVAr) |  |  |  |
| Pérdidas totales (MW) |  |  |  |
| Iteraciones Newton-Raphson |  |  |  |
| Iteraciones Gauss-Seidel |  |  |  |

Además de la tabla, mostrar las 5 ramas cuyo flujo cambió más respecto al caso base (en MVA y en %).

## Los cinco escenarios para elegir

| Escenario | Cambio a los datos base | Corridas |
| --- | --- | --- |
| 1. Salida de una línea | Retirar la línea 26–30 | 1 |
| 2. Salida de un generador | Retirar el generador de la barra 25 | 1 |
| 3. Crecimiento de la demanda | Aumentar todas las cargas en 10 % y en 20 % | 2 |
| 4. Nueva carga en una barra | Agregar 100 MW y 50 MVAr en la barra 118 | 1 |
| 5. Retiro de capacitores | Poner en cero los capacitores en derivación | 1 |

### Escenario 1: salida de una línea de transmisión

**Cambio en el Excel:** poner fuera de servicio la línea 26–30 de 345 kV (estado en 0 o eliminar su fila).

**Qué mostrar:** el flujo que llevaba la línea en el caso base y las ramas que ahora transportan esa potencia.

**Preguntas**

1. ¿Hacia qué líneas se redistribuyó la potencia y cuánto aumentó su flujo?
2. ¿Alguna barra quedó fuera del rango de 0,95–1,05 pu?
3. ¿Aumentaron o disminuyeron las pérdidas? ¿Por qué?

### Escenario 2: salida de un generador

**Cambio en el Excel:** poner fuera de servicio el generador de la barra 25 (alrededor de 220 MW en la versión de MATPOWER). La barra 25 pasa de PV a PQ y la barra slack asume la potencia faltante.

**Qué mostrar:** la potencia de la slack antes y después, y las tensiones en la zona de la barra 25 (barras 23 a 32).

**Preguntas**

1. ¿Cuánto aumentó la generación de la slack? ¿Es igual a la potencia perdida o hay una diferencia? ¿A qué se debe?
2. ¿Qué pasó con la tensión de la barra 25 al perder el control de tensión del generador?
3. ¿La slack queda dentro de su potencia máxima (Pmax del archivo)?

### Escenario 3: crecimiento de la demanda

**Cambio en el Excel:** multiplicar la potencia activa y reactiva de todas las cargas por 1,10 (corrida A) y por 1,20 (corrida B). La generación de las demás unidades no se cambia: la slack asume el aumento.

**Qué mostrar:** la tabla de comparación con tres columnas (base, +10 %, +20 %) y el perfil de tensiones de las tres corridas en un mismo gráfico.

**Preguntas**

1. ¿Cómo cambian la tensión mínima y las pérdidas al aumentar la carga? ¿Crecen en la misma proporción que la demanda?
2. ¿En cuál corrida aparecen barras fuera de rango, si aparecen?
3. ¿Puede la slack asumir sola el aumento de demanda, según su Pmax? ¿Qué harían en un sistema real?

### Escenario 4: conexión de una carga nueva

**Cambio en el Excel:** sumar 100 MW y 50 MVAr a la carga existente de la barra 118, como si se conectara una planta industrial.

**Qué mostrar:** la tensión de la barra 118 y de sus vecinas (75, 76, 77) y el flujo por las líneas que la alimentan (75–118 y 76–118).

**Preguntas**

1. ¿Cuánto bajó la tensión en la barra 118 y en las barras cercanas? ¿Y en barras lejanas?
2. ¿Por cuáles líneas llega la nueva potencia y cuánto aumentaron sus flujos?
3. ¿Qué recomendarían para mejorar la tensión en esa barra (por ejemplo, un capacitor)?

### Escenario 5: retiro de los capacitores en derivación

**Cambio en el Excel:** en los datos de barras, poner en cero la susceptancia en derivación (Bs) de todas las barras donde sea positiva (capacitores). Los valores negativos (reactores) se dejan igual.

**Qué mostrar:** la lista de barras con capacitores y su valor en MVAr, y el perfil de tensiones antes y después.

**Preguntas**

1. ¿En qué barras bajó más la tensión y cuántas quedaron fuera de rango?
2. ¿Cómo cambió la potencia reactiva de la slack y de los generadores?
3. ¿Qué función cumplen los capacitores en derivación en una red de transmisión?

Los números de barras y ramas corresponden a la versión de MATPOWER del caso de 118 barras; si el grupo usa otra fuente, debe verificarlos en su archivo.

## Sección 5 (común): conclusiones y lista de verificación

El video cierra con conclusiones derivadas de los datos obtenidos, no con generalidades: cada conclusión debe citar un número de sus resultados.

**Conclusiones mínimas**

- Comparación de los tres métodos: precisión, iteraciones, tiempo y robustez, en el caso base y en el escenario.
- Diagnóstico de la red en el escenario elegido: operación aceptable, emergencia o colapso, y por qué.
- Recomendación técnica principal para el escenario.

**Antes de entregar, verificar que el video:**

- ☐ Dura entre 30 y 40 minutos e incluye a todos los integrantes.
- ☐ Muestra el código y explica la construcción de la Ybus y los tres métodos.
- ☐ Incluye la corrida continua del caso base con los tres métodos y la tabla comparativa.
- ☐ Valida el caso base contra la referencia publicada.
- ☐ Muestra en el Excel los datos modificados del escenario elegido.
- ☐ Incluye la corrida continua del escenario y responde todas sus preguntas.
- ☐ Presenta conclusiones con números.
- ☐ Se entrega junto con el programa, el informe, el PowerPoint y los Excel de entrada y salida.

**Correspondencia con la rúbrica:** el rubro “Exposición y corrida del programa” (25 %) se evalúa con este video; la “corrida en vivo” se sustituye por las corridas grabadas de forma continua del caso base y del escenario.
