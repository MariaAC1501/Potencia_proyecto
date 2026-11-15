# Flujos de potencia IEEE-118 — MATLAB · escenario 1

Proyecto MI-5215, II semestre 2026. Métodos propios **Newton-Raphson, Gauss-Seidel y desacoplado rápido**, con Excel como entrada/salida; MATPOWER solo se utiliza como referencia independiente.

**Escenario elegido: salida de la línea 26–30 de 345 kV.** La prioridad del video es IEEE-118 base y modificado. IEEE-14 demuestra versatilidad en una corrida breve; IEEE-300 es respaldo opcional, no parte del recorrido de exposición.

> Los Excel, logs y pruebas son evidencia computacional, **no un video grabado**. Faltan nombres reales, voces identificadas de todos los integrantes, MP4 mínimo 1080p de 30–40 minutos, captura continua de las corridas y entrega institucional. El checklist trazable está en [CUMPLIMIENTO_GUIA_VIDEO.md](CUMPLIMIENTO_GUIA_VIDEO.md).

## Ejecución reproducible

Probado en la evidencia incluida con **MATLAB R2025a Update 1**. Requiere tablas Excel (`readtable`, `writetable`, `sheetnames`); la GUI necesita `uifigure`. No se requieren toolboxes adicionales ni MATPOWER para resolver los casos.

Desde una terminal en la raíz:

```bash
python -m pip install openpyxl
python tools/prepare_scenario1.py
```

La preparación crea o verifica `data/IEEE118_escenario1.xlsx`. **Solo cambia `branch!K39`, STATUS de la rama 38 (26–30), de 1 a 0**, y resalta el dato. Nunca modifica el caso base. Si existe una copia con cambios adicionales, falla; `--force` recrea deliberadamente la copia, no el original.

En MATLAB:

```matlab
cd('C:/repos/Potencia_proyecto');
addpath('matlab');
study = run_video_project(false);
```

El pipeline valida el cambio único y la conectividad, ejecuta los tres métodos en ambos casos, exporta los dos libros completos, la comparación y las figuras en `escenario1_assets/`. No regenera la entrada si ya existe: debe prepararse antes con Python. `false` evita mostrar ventanas de gráficas, pero conserva las figuras guardadas.

### Desde la interfaz: primero base, después retirar la línea

```matlab
addpath('matlab');
app_flows
```

1. Deja **IEEE-118**, **Todos**, tolerancia `1e-8` y **Aplicar límites Q** desmarcado. Pulsa **Ejecutar métodos**: corre primero con todas las líneas activas y exporta el caso base.
2. Se habilita **Retirar línea 26–30**. Al pulsarlo ejecuta la copia modificada con los mismos parámetros, conserva los resultados base y exporta escenario y comparación.
3. Consulta **Base vs. salida 26–30** y **Cambios de flujo**. La rama retirada queda resaltada con `STATUS=0` en **Ramas**.
4. **Volver al caso base** recupera la red original y sus resultados sin recalcular. Cambiar datos, parámetros o archivo invalida la referencia y obliga a ejecutar de nuevo el caso base.

Las salidas usan los tres nombres indicados arriba, en la raíz; cierra esos Excel antes de ejecutar porque se reemplazan. La copia resaltada ya viene incluida; si falta, créala con `python tools/prepare_scenario1.py`. `app_flows(carpetaSalida)` permite usar otra carpeta sin reemplazar los resultados incluidos.

Para grabar por consola corridas separadas desde su lanzamiento hasta la exportación, sin cortes ni acelerado:

```matlab
opts = struct('tolerance',1e-8,'maxIterations',1000, ...
    'relaxation',1.5,'enforceQLimits',false,'verbose',true);
base = main('data/IEEE118.xlsx','resultados_IEEE118_matlab.xlsx',false,opts);
% Detener la grabación solo después de la exportación y revisión del libro.
escenario = main('data/IEEE118_escenario1.xlsx', ...
    'resultados_IEEE118_escenario1_matlab.xlsx',false,opts);
```

`main` muestra el mismatch en cada iteración (`verbose=true` por defecto). Ejecuta los métodos secuencialmente y exporta al terminar los tres. Abrir los Excel de entrada antes y los de salida después permite conservar una captura continua. Cerrar las salidas en Excel antes de ejecutar: **se reemplazan**. Para actualizar también la comparación, usar `run_video_project(false)`; no mezclar salidas nuevas con una comparación antigua.

Versatilidad, fuera del bloque central:

```matlab
r14 = main('data/IEEE14.xlsx','resultados_IEEE14_matlab.xlsx',false);
```

La demostración de IEEE-14 debe durar idealmente menos de un minuto; no se garantiza su duración audiovisual a partir del tiempo de solver.

## Evidencia y resultados del escenario

| Magnitud (NR) | Base | Salida 26–30 |
| --- | ---: | ---: |
| V mínima (pu) | 0,943000 (76) | 0,940040 (21) |
| Barras fuera de 0,95–1,05 pu | 3 | 6 |
| P Slack 69 (MW) | 513,862872 | 546,897686 |
| Pérdidas activas (MW) | 132,862872 | 165,897686 |
| Iteraciones NR / GS / FDLF | 3 / 757 / 9 | 4 / 909 / 11 |

El flujo máximo aparente de 26–25 pasa de 92,833255 a 316,195271 MVA (+240,606 %). Las pérdidas aumentan **33,034814 MW (+24,864 %)**. El informe contiene la tabla obligatoria completa, top5, potencia retirada y respuestas a las tres preguntas. `cambios_top5_total` muestra los cinco mayores cambios globales, incluida 26–30 (−100 %); `cambios_top5` añade las cinco ramas activas con mayor redistribución.

**Cautelas:** 0,95–1,05 pu es el intervalo de la guía; el Excel usa VMIN/VMAX=0,94/1,06. Q neta negativa de ramas refleja compensación capacitiva, no pérdidas resistivas negativas. RATE_A=0 no permite afirmar ausencia de sobrecargas. Convergencia no demuestra estabilidad ni factibilidad con límites Q, que están desactivados. El escenario no cumple el criterio de tensión de la guía, sin colapso demostrado ni sobrecarga acreditada.

## Archivos para revisión y entrega

El estudio IEEE-118 usa **cinco Excel principales: dos de entrada y tres de salida** (base, escenario y comparación). Los casos IEEE-14/300 y la validación tienen libros auxiliares aparte.

- `data/IEEE118.xlsx` / `data/IEEE118_escenario1.xlsx`: entradas base y modificada.
- `resultados_IEEE118_matlab.xlsx` / `resultados_IEEE118_escenario1_matlab.xlsx`: resultados completos de los tres métodos, Slack P/Q, `config` y `parametros`.
- `comparacion_escenario1.xlsx`: tabla obligatoria numérica, top5 de tensiones y flujos de ambos casos, cambios en MVA/%, barras fuera de rango, flujo retirado y métodos.
- `escenario1_assets/`: figuras MATLAB, log y manifiesto de ejecución; **no contiene evidencia suficiente de video humano**.
- `escenario1_assets/IEEE118_unifilar_UW.png`: **unifilar publicado** por R. Christie, University of Washington, archivo IEEE-118 (mayo de 1993), sistema AEP de diciembre de 1962. [Página de la fuente](https://labs.ece.uw.edu/pstca/pf118/pg_tca118bus.htm), [TIFF original](https://labs.ece.uw.edu/pstca/pf118/118bus6.tif). Cita/hash en `escenario1_assets/README_FUENTES.md` y `fuente_unifilar.json`; el recorte `unifilar_region_26_30.png` ubica **26 Tanners Creek y 30 Sorenson**, identificación verificada contra el CDF original UW; no confundir 26 con W. Kamm. La versión `_anotado.png` añade resaltado propio sobre el recorte publicado. No confundirlo con una topología propia generada.
- **`INFORME_PROYECTO_MATLAB.docx`**: informe Word real exigido por la guía. También se incluyen el Markdown editable, PDF y fuente Typst del informe técnico completo, no un resumen sustitutivo.
- `informe_assets/manifest_video.json`: comprobaciones de coherencia, huellas completas y pendientes humanos; `datos_informe.json` conserva diagnósticos de los casos complementarios.
- `CUMPLIMIENTO_GUIA_VIDEO.md`: correspondencia granular guía → evidencia/comando → estado.
- `GUIA_USO_MATLAB.md` / `MATLAB_README.md`: uso detallado y contrato técnico/dependencias.
- `matlab/`: programa; `PRESENTACION.pptx` y `GUION_PARA_EXPONER.md/pdf`: material audiovisual mantenido por separado, cuya revisión y ensayo son necesarios antes de grabar.

## Regenerar el informe, sin ejecutar MATLAB

Python 3.10+ y Typst en PATH (`typst --version`). Dependencias del generador:

```bash
python -m pip install openpyxl numpy matplotlib PyMuPDF python-docx Pillow
# Entorno completo fijado (Python 3.11+): pip install -r requirements-materiales.txt
python tools/build_report.py
# Equivalente:
python tools/build_video_report.py
```

Ambas entradas conservan el informe técnico original y actualizan el escenario desde Excel; generan **MD, PDF y DOCX**. El Word lleva texto/tablas editables y ecuaciones como imágenes renderizadas con Typst. No requiere Word, COM ni `python-pptx`. No modifica entradas/resultados ni inicia MATLAB, capturas o generadores de presentación. Repetirlo si cambia la validación externa.

## Regenerar presentación y guion

```bash
python tools/build_presentation.py
python tools/render_presentation.py
python tools/build_oral_script.py
```

El recorrido tiene **32 diapositivas, 35 min 45 s previstos** y seis secciones en el orden de la guía. Se restauró el **formato anterior: fondo blanco, títulos azul oscuro, tablas y listas**. Cada una de las tres preguntas conserva una diapositiva antes de su respuesta. Las explicaciones completas permanecen en las notas y el guion. La fuente común es `tools/presentation_story.py`; los comandos actualizan PPTX, PDF y discurso, sin ejecutar MATLAB. El render requiere PowerPoint y pywin32; el guion requiere Typst. Dependencias completas en `requirements-materiales.txt`. Nombres y ensayo siguen pendientes.

## Pruebas y validación externa

```bash
python -m unittest discover -s tests -v
python tools/check_video_evidence.py --materials
```

El verificador contrasta entradas, historiales, balances P/Q, Slack, diferencias y rankings con las salidas actuales, y vincula tensiones/ángulos/pérdidas con la evidencia MATPOWER. Rechaza modificaciones inconsistentes; no certifica el MP4.


```matlab
addpath('matlab');
test_powerflow;
test_scenario1;
test_plot_convergence;
% test_app_flows; % Abre GUI; ejecutar solo en una sesión destinada a ello.
```

Para repetir la comparación independiente con **MATPOWER 8.1**:

```bash
python tools/setup_matpower.py
```

```matlab
validate_against_matpower('C:/ruta/mostrada/matpower8.1');
```

Referencia IEEE-118: `case118.m` oficial, entradas cotejadas. `validacion_MATPOWER.xlsx` y `.json` contienen errores de tensión, ángulo, flujos, pérdidas P/Q y potencia P/Q de la Slack. El informe marca cualquier columna adicional ausente como pendiente, sin inventar cifras. Ver `VALIDACION_EXTERNA.md` para fuentes y umbrales. La validación base no certifica externamente el escenario.

## Entrega humana pendiente

La guía exige **MP4 ≥1080p, 30–40 min**, audio claro sin música que tape las voces, participación identificada de todos, y corridas continuas sin cortes/acelerado. Entregar por evaluaciones del **TEC Digital un día antes** de la exposición: video, programa, **Word**, **PowerPoint** y los cuatro Excel de entrada/salida; incluir también la comparación. Si excede el límite, compartir carpeta institucional Drive/OneDrive con acceso probado para el profesor. No declarar entregado o grabado sin comprobarlo.
