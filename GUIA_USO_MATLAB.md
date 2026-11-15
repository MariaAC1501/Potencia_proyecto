# Guía de uso del repositorio en MATLAB

Esta guía explica cómo ejecutar y aprovechar el repositorio de flujos de potencia IEEE-118 en MATLAB. **El escenario elegido para el video es el 1: salida de la línea 26–30.** El procedimiento completo está en la sección 18; los requisitos audiovisuales aún pendientes están en `CUMPLIMIENTO_GUIA_VIDEO.md`.

## 1. ¿Qué contiene el repositorio?

- `data/IEEE118.xlsx`: caso de prueba IEEE de 118 barras en formato Excel.
- `data/case118.m`: caso IEEE-118 en formato MATPOWER, usado solo para validación opcional.
- `matlab/`: funciones MATLAB del proyecto.
- `matlab/main.m`: script/función principal que ejecuta los métodos numéricos.
- `matlab/app_flows.m`: interfaz gráfica para cargar, editar y resolver casos.
- `resultados_IEEE118_matlab.xlsx`: archivo de resultados generado.
- `README.md` y `MATLAB_README.md`: documentación breve del proyecto.

El proyecto implementa tres métodos:

1. Newton-Raphson.
2. Gauss-Seidel con relajación.
3. Desacoplado rápido.

No se necesita MATPOWER para ejecutar el proyecto principal.

## 2. Requisitos

La evidencia incluida se obtuvo con **MATLAB R2025a Update 1**. Se requiere una versión reciente con soporte para (otras versiones no se certifican aquí):

- `readtable` / `writetable` para archivos Excel.
- `sheetnames`.
- `uifigure`, si se quiere usar la interfaz gráfica.

No se requieren toolboxes especiales para la ejecución principal.

## 3. Abrir el repositorio en MATLAB

1. Abre MATLAB.
2. Cambia la carpeta actual al repositorio:

```matlab
cd('C:/repos/Potencia_proyecto')
```

También puedes hacerlo desde el explorador de carpetas de MATLAB seleccionando la carpeta del proyecto.

3. Agrega la carpeta `matlab` al path:

```matlab
addpath('matlab')
```

## 4. Ejecución rápida del caso IEEE-118

Desde la raíz del proyecto ejecuta:

```matlab
addpath('matlab')
results = main;
```

Esto hace lo siguiente:

1. Lee el archivo `data/IEEE118.xlsx`.
2. Ejecuta los tres métodos:
   - Newton-Raphson.
   - Gauss-Seidel.
   - Desacoplado rápido.
3. Muestra en consola si cada método convergió, el número de iteraciones, el error final, el tiempo y las pérdidas activas.
4. Genera el archivo:

```text
resultados_IEEE118_matlab.xlsx
```

5. Abre gráficas de convergencia, perfil de tensión, ángulos y comparación de iteraciones/pérdidas.

## 5. Ejecutar indicando archivos manualmente

Puedes especificar el archivo de entrada, el archivo de salida, si quieres generar gráficas y un cuarto argumento opcional `options`:

```matlab
results = main('data/IEEE118.xlsx', 'mis_resultados.xlsx', true);
```

Si no quieres gráficas:

```matlab
results = main('data/IEEE118.xlsx', 'mis_resultados.xlsx', false);
```

## 6. Revisar los resultados en MATLAB

La variable `results` es un arreglo de estructuras. Cada elemento corresponde a un método.

Ejemplo:

```matlab
results(1)
```

Campos importantes:

- `results(k).method`: nombre del método.
- `results(k).converged`: indica si convergió.
- `results(k).iterations`: número de iteraciones.
- `results(k).maxMismatch`: error final en pu.
- `results(k).elapsedSeconds`: tiempo de ejecución.
- `results(k).V`: vector complejo de tensiones.
- `results(k).mismatchHistory`: historial del error por iteración.
- `results(k).busResults`: tabla de resultados por barra.
- `results(k).branchResults`: tabla de flujos por rama.
- `results(k).summary`: resumen general del caso.

Ejemplos de consulta:

```matlab
% Ver resumen del método Newton-Raphson
results(1).summary

% Ver tabla de barras del primer método
results(1).busResults

% Ver tensiones en pu
results(1).busResults(:, {'BUS_I','VM_pu','VA_deg'})

% Ver pérdidas por rama
results(1).branchResults(:, {'Rama','Desde','Hasta','P_loss_MW','Q_loss_MVAr'})
```

## 7. Revisar el archivo Excel de salida

El archivo de salida incluye varias hojas:

- `entrada_bus`: datos de barras usados como entrada.
- `entrada_gen`: datos de generadores usados como entrada.
- `entrada_branch`: datos de ramas usados como entrada.
- `comparacion`: resumen de los métodos; en las salidas IEEE-118 nuevas incluye `P_slack_MW` y `Q_slack_MVAr`, además de iteraciones, tiempo, mismatch y pérdidas P/Q.
- `config`: `baseMVA` en las nuevas salidas IEEE-118.
- `parametros`: tolerancia, máximo, relajación, límites Q, inicialización y alcance del tiempo. Los libros complementarios antiguos pueden no contener estas dos hojas.
- `NR_bus`: resultados por barra de Newton-Raphson.
- `NR_branch`: flujos por rama de Newton-Raphson.
- `NR_conv`: convergencia de Newton-Raphson.
- `GS_bus`: resultados por barra de Gauss-Seidel.
- `GS_branch`: flujos por rama de Gauss-Seidel.
- `GS_conv`: convergencia de Gauss-Seidel.
- `FDLF_bus`: resultados por barra del desacoplado rápido.
- `FDLF_branch`: flujos por rama del desacoplado rápido.
- `FDLF_conv`: convergencia del desacoplado rápido.

## 8. Usar la interfaz gráfica

Para abrir la GUI:

```matlab
addpath('matlab')
app_flows
```

La interfaz permite:

1. Elegir **IEEE-14**, **IEEE-118** o **IEEE-300** en **Caso visualizado** para cargar y calcular ese caso automáticamente.
2. También seleccionar y cargar un Excel propio; aparecerá como **Personalizado** y se limpiarán las gráficas anteriores hasta ejecutar el cálculo.
3. Consultar y editar tablas de barras, generadores y ramas.
4. Elegir el método:
   - Todos.
   - Newton-Raphson.
   - Gauss-Seidel.
   - Desacoplado rápido.
5. Cambiar tolerancia, máximo de iteraciones y relajación de Gauss-Seidel.
6. Activar o desactivar límites de potencia reactiva.
7. Ejecutar el cálculo.
8. Visualizar comparación, convergencia, tensiones y ángulos.
9. Después de resolver IEEE-118 con **Todos**, retirar la línea **26–30**, comparar y volver al caso base.
10. Abrir los libros desde la fila **Abrir Excel**: **Entrada actual**, **Entrada 26–30**, **Resultados base**, **Resultados 26–30** y **Comparación**. Se abren con Excel o la aplicación predeterminada de Windows. El primer botón sigue el caso cargado; los otros corresponden al estudio IEEE-118. Las salidas respetan la carpeta indicada en `app_flows(carpetaSalida)`.

11. Usar **Reset resultados** para eliminar, previa confirmación, los Excel de salida de la carpeta configurada: resultados IEEE-14, IEEE-118 base, IEEE-118 escenario, IEEE-300, comparación del escenario y validación MATPOWER. **Cancelar** es la opción predeterminada. No se borran entradas ni otros archivos; también se limpian las gráficas, tablas de resultados y la referencia base de la interfaz, conservando los datos de entrada y parámetros actuales. Si estabas en el escenario, continúa cargado ese escenario: selecciona **IEEE-118** para volver a empezar desde la base.

Si un resultado está abierto o bloqueado y no puede borrarse, se informa qué archivos quedaron pendientes; ciérralos en Excel y repite el reset. Una entrada propia que tenga el nombre de una salida se protege: hay que cargar otro caso antes de intentar borrarla. El reset se deshabilita durante los cálculos.

Los botones de archivos inexistentes quedan deshabilitados y se habilitan cuando se generan las salidas. La ruta completa aparece al pasar el cursor. Abren el archivo guardado, que puede corresponder a una ejecución anterior; no guardan cambios hechos en las tablas de la interfaz. Cierra los resultados en Excel antes de volver a calcular para evitar bloqueos de escritura.

### 8.1. Flujo interactivo del escenario 1

1. Al abrir, **Retirar línea 26–30** está deshabilitado. Deja **IEEE-118**, **Todos**, tolerancia `1e-8` y límites Q desactivados; pulsa **Ejecutar métodos**.
2. Si los tres métodos convergen con desajuste ≤`1e-8`, se exporta `resultados_IEEE118_matlab.xlsx` y se habilita **Retirar línea 26–30**. Con un método solo, otra red, datos editados, tolerancia mayor o límites Q activados no se habilita.
3. Pulsa **Retirar línea 26–30**. La aplicación verifica la copia resaltada incluida, pone fuera la única rama, conserva el snapshot base y ejecuta los tres métodos con exactamente los mismos parámetros. No modifica el Excel base.
4. Se exportan `resultados_IEEE118_escenario1_matlab.xlsx` y `comparacion_escenario1.xlsx`. Se abre **Base vs. salida 26–30**, con tabla obligatoria y perfiles NR superpuestos. **Cambios de flujo** muestra los rankings global y activo.
5. En **Ramas**, la fila 38 y `STATUS=0` quedan resaltados. La ruta visualizada corresponde al Excel modificado; el selector indica **Personalizado**.
6. **Volver al caso base** recupera la red con la línea activa y los resultados guardados, sin otra corrida. La comparación conserva la referencia de esas mismas dos ejecuciones.

Cambiar datos, método, tolerancia, máximo, relajación, límites Q o ruta invalida los resultados y la comparación; hay que cargar/ejecutar de nuevo el caso base. La aplicación también verifica el estado al pulsar para rechazar resultados obsoletos. Los botones y controles se bloquean durante el cálculo.

Para este estudio son **cinco Excel principales**: dos entradas (`IEEE118.xlsx` y `IEEE118_escenario1.xlsx`) y tres salidas (resultados base, resultados escenario y comparación). Los tres métodos se guardan en hojas dentro de cada resultado; los libros IEEE-14/300 y de validación son auxiliares.

Las salidas se guardan por defecto en la raíz y se reemplazan: ciérralas antes en Excel. Para aislar otra ejecución, usa `app_flows('C:/ruta/carpeta_salida')`. La entrada modificada ya está incluida; si falta, ejecuta `python tools/prepare_scenario1.py`. La GUI muestra el mismatch por iteración en la consola MATLAB; graba desde antes de pulsar cada botón hasta la exportación, sin cortes ni acelerado.

## 9. Ejecutar un solo método desde código

Si quieres más control, puedes llamar las funciones directamente:

```matlab
addpath('matlab')

caseData = load_case_excel('data/IEEE118.xlsx');

options = struct();
options.tolerance = 1e-8;
options.maxIterations = 1000;
options.relaxation = 1.5;
options.enforceQLimits = false;
options.verbose = true; % Mismatch en cada iteración para la grabación.

resultNR = solve_power_flow(caseData, 'Newton-Raphson', options);
resultGS = solve_power_flow(caseData, 'Gauss-Seidel', options);
resultFD = solve_power_flow(caseData, 'Desacoplado rápido', options);
```

También puedes usar alias:

```matlab
resultFD = solve_power_flow(caseData, 'fdlf', options);
```

## 10. Cambiar parámetros de solución

Los parámetros principales están en la estructura `options`:

```matlab
options = struct( ...
    'tolerance', 1e-8, ...
    'maxIterations', 1000, ...
    'relaxation', 1.5, ...
    'enforceQLimits', false, ...
    'verbose', true);
```

Significado:

- `tolerance`: tolerancia de convergencia en pu.
- `maxIterations`: máximo número de iteraciones. En casos de más de 118 barras, si este valor es bajo, el programa lo aumenta automáticamente para permitir la convergencia de Gauss-Seidel sin relajar la tolerancia.
- `relaxation`: factor de relajación para Gauss-Seidel.
- `enforceQLimits`: si es `true`, intenta aplicar límites reactivos agregados convirtiendo PV a PQ; no limita la Slack ni garantiza reparto individual. La evidencia base/escenario mantiene `false`.
- `verbose`: muestra mismatch máximo inicial y por iteración. Predeterminado `true` en `main` y en la GUI, `false` en llamadas directas a `solve_power_flow` sin esa opción. Su impresión forma parte del tiempo medido.

Ejemplo con tolerancia más relajada:

```matlab
options.tolerance = 1e-6;
result = solve_power_flow(caseData, 'Newton-Raphson', options);
```

## 11. Formato del archivo Excel de entrada

El archivo Excel debe tener al menos estas hojas:

- `bus`
- `gen`
- `branch`

Opcionalmente puede tener:

- `config`, para definir `baseMVA`.

### Hoja `config`

Debe contener el valor de la base de potencia. Por ejemplo:

| baseMVA |
|---:|
| 100 |

Si no existe esta hoja, el programa usa `baseMVA = 100`.

### Hoja `bus`

Columnas mínimas obligatorias:

| Columna | Significado |
|---|---|
| `BUS_I` | Número de barra |
| `TYPE` | Tipo de barra: `1` PQ, `2` PV, `3` Slack |
| `PD` | Demanda activa MW |
| `QD` | Demanda reactiva MVAr |

Columnas opcionales con valor por defecto:

| Columna | Valor por defecto |
|---|---:|
| `GS` | 0 |
| `BS` | 0 |
| `AREA` | 1 |
| `VM` | 1 |
| `VA` | 0 |
| `BASE_KV` | 0 |
| `ZONE` | 1 |
| `VMAX` | 1.10 |
| `VMIN` | 0.90 |

### Hoja `gen`

Columnas mínimas obligatorias:

| Columna | Significado |
|---|---|
| `GEN_BUS` | Barra donde está conectado el generador |
| `PG` | Potencia activa generada MW |
| `QG` | Potencia reactiva generada MVAr |

Columnas opcionales con valor por defecto:

| Columna | Valor por defecto |
|---|---:|
| `QMAX` | `inf` |
| `QMIN` | `-inf` |
| `VG` | `VM` de la barra asociada, si se omite la columna |
| `MBASE` | `baseMVA` |
| `STATUS` | 1 |
| `PMAX` | `inf` |
| `PMIN` | `-inf` |

### Hoja `branch`

Columnas mínimas obligatorias:

| Columna | Significado |
|---|---|
| `F_BUS` | Barra de origen |
| `T_BUS` | Barra de destino |
| `BR_R` | Resistencia en pu |
| `BR_X` | Reactancia en pu |

Columnas opcionales con valor por defecto:

| Columna | Valor por defecto |
|---|---:|
| `BR_B` | 0 |
| `RATE_A` | 0 |
| `RATE_B` | 0 |
| `RATE_C` | 0 |
| `TAP` | 1 |
| `SHIFT` | 0 |
| `STATUS` | 1 |
| `ANGMIN` | -360 |
| `ANGMAX` | 360 |

Las unidades activas fijan mediante `VG` la magnitud en barras PV y Slack; editar solo `VM` en esas barras no cambia la consigna si existe `VG`. En barras PQ, `VM` es una condición inicial. Si hay varias unidades activas en una misma barra regulada, deben tener consignas compatibles. Una PV sin unidades activas pasa a calcularse como PQ; la Slack necesita un generador activo.

## 12. Reglas importantes del caso

El validador exige que:

- `baseMVA` sea mayor que cero.
- Exista al menos una barra y una rama.
- Los identificadores `BUS_I` sean únicos.
- Exista exactamente una barra Slack, es decir, una barra con `TYPE = 3`.
- Solo se usen tipos de barra `1`, `2` y `3`.
- No existan ramas con reactancia `BR_X = 0`.
- Todas las ramas referencien barras existentes.
- Todos los generadores referencien barras existentes.

## 13. Crear y correr un caso propio

1. Copia `data/IEEE118.xlsx` con otro nombre, por ejemplo:

```text
data/mi_caso.xlsx
```

2. Edita las hojas `bus`, `gen` y `branch` en Excel.
3. Guarda el archivo.
4. Ejecuta en MATLAB:

```matlab
addpath('matlab')
results = main('data/mi_caso.xlsx', 'resultados_mi_caso.xlsx', true);
```

## 14. Ejecutar pruebas del proyecto

Para verificar que todo está funcionando:

```matlab
addpath('matlab')
test_powerflow
test_scenario1
```

Estos son comandos para repetir las pruebas, no evidencia audiovisual. Si todo está correcto, MATLAB mostrará:

```text
test_powerflow: todas las pruebas pasaron.
```

## 15. Validación opcional con MATPOWER

La solución principal no necesita MATPOWER. La validación independiente compara los tres métodos propios en IEEE-14, IEEE-118 e IEEE-300, incluyendo tensiones, ángulos, flujos en ambos extremos y pérdidas. Las nueve comparaciones realizadas con MATPOWER 8.1 aprobaron; las entradas IEEE-118 coinciden con su caso oficial.

Para descargar la versión fijada ejecuta `python tools/setup_matpower.py` en una terminal. El procedimiento, los umbrales y las fuentes IEEE están en `VALIDACION_EXTERNA.md`.

Ejemplo:

```matlab
addpath('matlab')
validate_against_matpower('C:/ruta/a/matpower')
```

La validación actualizada conserva en `resumen` diferencias de pérdidas P y Q neta de ramas, y P/Q Slack, con sus valores de referencia. La referencia publicada IEEE-118 es el `case118.m` oficial de MATPOWER 8.1, no un acuerdo entre métodos propios. Consultar la tabla 9.9 del informe; si una columna aún falta, el builder la marca pendiente sin inventarla. Esta validación del caso base no certifica externamente el escenario.

Si MATPOWER ya está en el path:

```matlab
validate_against_matpower
```

Se generan `validacion_MATPOWER.xlsx` y `validacion_MATPOWER.json`. La función lanza un error si falla un criterio de aceptación y no modifica de forma permanente el path de MATLAB.

## 16. Problemas comunes

### MATLAB no encuentra `main`

Asegúrate de estar en la raíz del proyecto y de haber agregado la carpeta `matlab`:

```matlab
cd('C:/repos/Potencia_proyecto')
addpath('matlab')
```

### Error: no existe el archivo Excel

Verifica la ruta:

```matlab
isfile('data/IEEE118.xlsx')
```

Debe devolver `1`.

### Error: falta una hoja `bus`, `gen` o `branch`

El Excel de entrada debe incluir esas hojas. También se aceptan algunos nombres equivalentes, por ejemplo `barras`, `generadores` o `ramas`.

### Error: debe existir exactamente una barra Slack

En la hoja `bus` debe haber una sola fila con:

```text
TYPE = 3
```

### Gauss-Seidel tarda más que Newton-Raphson

Es normal. Gauss-Seidel suele requerir más iteraciones. Para casos de más de 118 barras el programa sube automáticamente el máximo de iteraciones. Si lo llamas manualmente, también puedes ajustar:

```matlab
options.relaxation = 1.5;  % por ejemplo
options.maxIterations = 30000;
```

### No quiero que se abran gráficas

Ejecuta:

```matlab
results = main('data/IEEE118.xlsx', 'resultados_IEEE118_matlab.xlsx', false);
```

## 17. Flujo básico de trabajo (sin escenario)

Para cumplir la guía del video debe añadirse el procedimiento de la sección 18, no quedarse en esta corrida base.

Para una corrida normal:

```matlab
cd('C:/repos/Potencia_proyecto')
addpath('matlab')
results = main;
```

Para estudiar resultados:

```matlab
results(1).summary
results(1).busResults
results(1).branchResults
```

Para usar la interfaz gráfica:

```matlab
app_flows
```

## 18. Procedimiento completo para la guía del video — escenario 1

### 18.1. Preparar y comprobar el único cambio

En una terminal desde `C:/repos/Potencia_proyecto`:

```bash
python -m pip install openpyxl
python tools/prepare_scenario1.py
```

La copia `data/IEEE118_escenario1.xlsx` conserva todas las hojas y valores del original salvo **`branch!K39`**, `STATUS` de la rama 38 entre 26 y 30: **1→0**. La celda y la fila quedan resaltadas. Mostrar ambas entradas en Excel; no eliminar la fila ni modificar cargas, generación o BS. El preparador verifica una copia existente y falla si tiene cambios adicionales; `--force` la recrea deliberadamente. El pipeline MATLAB requiere esta preparación y no la reescribe automáticamente.

### 18.2. Generar toda la evidencia computacional

Con los Excel de salida cerrados:

```matlab
cd('C:/repos/Potencia_proyecto');
addpath('matlab');
study = run_video_project(false);
```

Produce las corridas completas base y escenario, `comparacion_escenario1.xlsx`, perfiles y redistribución en `escenario1_assets/`, con metadatos y log cuando se conserva la consola. `false` evita mostrar las figuras, pero sí las guarda. No es una grabación del video humano.

Para registrar un log deliberadamente en otra ejecución:

```matlab
diary('mi_corrida_video.log');
study = run_video_project(false);
diary off;
```

El log tampoco sustituye la captura audiovisual continua. Evitar generar un archivo nuevo si no se necesita; las salidas existentes se reemplazan.

### 18.3. Corridas para mostrar en pantalla

Es posible grabar una llamada de `main` por caso, con los tres métodos secuenciales y exportación al final:

```matlab
opts = struct('tolerance',1e-8,'maxIterations',1000, ...
    'relaxation',1.5,'enforceQLimits',false,'verbose',true);
base = main('data/IEEE118.xlsx','resultados_IEEE118_matlab.xlsx',false,opts);
```

Sin detener/acelerar la captura desde el lanzamiento hasta abrir la salida exportada. Para el escenario, comenzar otra toma continua:

```matlab
escenario = main('data/IEEE118_escenario1.xlsx', ...
    'resultados_IEEE118_escenario1_matlab.xlsx',false,opts);
```

La guía exige los tres métodos en base y al menos NR/GS en escenario; esta llamada incluye también FDLF. Mostrar mismatch por iteración, tablas VM/VA, flujos P/Q en ambos extremos, pérdidas y Slack. **Si se usan corridas separadas, regenerar/verificar la comparación antes de presentarla; no mezclar resultados de ejecuciones distintas.** Usar directamente `run_video_project(false)` en captura continua es la opción que mantiene automáticamente unidos los tres libros.

Los tiempos del solver no son duración de captura ni de video; incluyen consola con verbose activo. IEEE-14 sirve para mostrar tamaño variable en menos de un minuto de demostración, idealmente:

```matlab
r14 = main('data/IEEE14.xlsx','resultados_IEEE14_matlab.xlsx',false);
```

IEEE-300 no ocupa tiempo en el video: se mantiene como apéndice técnico opcional.

### 18.4. Qué abrir para las comparaciones obligatorias

En `comparacion_escenario1.xlsx`, `cambios_top5_total` es el ranking global exigido por la guía, incluyendo 26–30 con −100 %. `cambios_top5` es el complemento de cinco ramas activas para explicar redistribución; no reemplaza el global.

| Hoja | Qué mostrar |
| --- | --- |
| `comparacion` | V mínima/máxima y barras en filas separadas, conteo fuera de rango, P/Q Slack, pérdidas P, iteraciones NR/GS; valores numéricos base/escenario/diferencia |
| `base_metodos`, `escenario_metodos` | Iteraciones, tiempo, mismatch, P Slack, pérdidas P/Q de los tres métodos |
| `base_top5_bajas`, `escenario_top5_bajas` | Las cinco tensiones más bajas con sus datos completos |
| `base_top5_flujos`, `escenario_top5_flujos` | Cinco ramas de mayor S máxima de ambos extremos |
| `cambios_top5` | Cinco cambios por valor absoluto en ramas que permanecen activas, ΔMVA y Δ% con signo |
| `cambios_ramas` | Todas las 186 ramas, incluida la retirada para trazabilidad |
| `linea_retirada` | Flujos base de 26–30; retirada se presenta aparte del top5 |
| `fuera_base`, `fuera_escenario` | Barras fuera de 0,95–1,05 pu, con tolerancia de borde 1e-8 pu |

No interpretar Desde–Hasta como sentido del flujo: revisar signos P/Q. No sumar magnitudes MVA como un balance de potencia activa. RATE_A=0 es un límite no disponible, no una prueba de ausencia de sobrecarga.

### 18.5. Respuestas de referencia para interpretar los resultados

- **Redistribución:** 26–25 aumenta 223,362016 MVA (+240,606 %); 23–25, 135,984080 MVA (+79,440 %); 25–27, 87,077145 MVA (+59,382 %); 32–113, 50,278581 MVA (+275,223 %). 30–17 disminuye 120,114746 MVA (−48,204 %). Se usa el máximo de ambos extremos.
- **Tensión:** base fuera de guía: 53, 76, 118. Escenario: 20, 21, 22, 53, 76, 118. Mínima: 0,943000 pu (76)→0,940040 pu (21). El criterio guía 0,95–1,05 es distinto de VMIN/VMAX 0,94/1,06 del Excel; ambos casos cumplen estos límites más amplios.
- **Pérdidas:** 132,862872→165,897686 MW: +33,034814 MW (+24,864 %). La carga y PG no Slack no cambian; el incremento Slack coincide por balance. La redistribución eleva pérdidas I²R en otros caminos aunque desaparezca la pérdida propia de 26–30. Q neta de ramas negativa refleja capacitancia, no disipación resistiva negativa; al retirar la rama también se elimina su BR_B, sin modificar los BS de barras.
- **Diagnóstico:** no aceptable respecto al rango de tensión de la guía, sin colapso demostrado ni sobrecarga acreditada. Convergencia y límites Q desactivados no prueban factibilidad operativa. Estudiar restitución del corredor, soporte reactivo/redespacho y límites reales antes de dimensionar medidas.

Fuente exacta: Excel actuales e informe, sección 9. El unifilar publicado es `escenario1_assets/IEEE118_unifilar_UW.png` (UW/R. Christie, mayo 1993); el recorte ubica **26 Tanners Creek y 30 Sorenson**, verificados contra el CDF original UW. La identificación inicial de 26 como W. Kamm era errónea; no repetirla en el video. El recorte `_anotado.png` añade etiquetas propias al original publicado. Fuente, TIFF original y hash están junto a la imagen. El caso tiene 118 barras, 186 ramas, 54 generadores activos, 99 barras con carga, Slack 69, base 100 MVA, carga 4242 MW/1438 MVAr y PG programada 4377,4 MW. Además de 138/345 kV, el archivo incluye 161 kV en la barra 87.

### 18.6. Regenerar el Word y PDF reales desde evidencia existente

Requiere Python 3.10+ y Typst disponible en PATH:

```bash
python -m pip install openpyxl numpy matplotlib PyMuPDF python-docx Pillow
typst --version
python tools/build_report.py
# Equivalente: python tools/build_video_report.py
```

Genera `INFORME_PROYECTO_MATLAB.md`, `.pdf` y **`.docx` real**, preservando todo el desarrollo técnico y actualizando tablas/figuras. El Word contiene texto/tablas editables y ecuaciones como imágenes Typst. No requiere Word instalado, COM ni python-pptx. No ejecuta MATLAB, no modifica Excel y no genera presentaciones. No editar solo el Word: regenerarlo desde Markdown y evidencia. Nombres reales deben completarse también en las fuentes/plantillas antes de cerrar la entrega.

`informe_assets/manifest_video.json` conserva huellas, controles, estructura del Word y revisión del PDF. El builder valida el cambio único, entradas exportadas, top5, porcentajes, Slack, pérdidas, historiales y tabla obligatoria. Si falta evidencia externa adicional la marca pendiente; volver a generar después de repetir MATPOWER.

### 18.7. Guía del video y entrega (pendiente humana)

Mantener el orden 0 presentación, 1 configuración, 2 red base, 3 corrida base/validación, 4 escenario, 5 conclusiones. Una distribución objetivo compatible es **1:30 + 9:00 + 3:30 + 7:30 + 11:45 + 2:30 = 35:45**, sincronizada con `PRESENTACION.md`, a comprobar en ensayo y metadatos del MP4, no una duración ya alcanzada.

Faltan completar/confirmar: nombres e identificación por voz de todos, MP4 1080p de 30–40 min, audio claro sin música que tape voces, código/consola/entradas/salidas visibles y corridas sin cortes/acelerado. Entregar video, programa, informe Word, PowerPoint y cuatro Excel por TEC Digital **un día antes**; incluir comparación y, si es necesario, enlace institucional con permiso para el profesor. La notificación al profesor del escenario elegido también requiere confirmación humana.

La presentación tiene 32 diapositivas con el formato anterior: fondo blanco, títulos azul oscuro, tablas y listas. Antes de cada una de las tres respuestas se muestra la pregunta completa en una diapositiva propia (15 s previstos cada una). Las explicaciones extensas permanecen en notas y guion; las tablas obligatorias se conservan.

Consultar el checklist granular `CUMPLIMIENTO_GUIA_VIDEO.md`. Ni este documento ni `ejecucion.json`, logs, capturas o pruebas computacionales certifican que el video esté grabado o entregado.
