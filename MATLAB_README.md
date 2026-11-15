# Implementación MATLAB — IEEE-118 y escenario 1

Los métodos numéricos son propios; MATPOWER no participa en `main` ni en la GUI. La evidencia incluida usa **MATLAB R2025a Update 1**, tablas Excel y `uifigure` para la interfaz, sin toolboxes adicionales identificados.

## Entrada, ejecución y salida

Desde la raíz, preparar una copia con el único cambio exigido:

```bash
python -m pip install openpyxl
python tools/prepare_scenario1.py
```

`data/IEEE118.xlsx` permanece intacto. En `data/IEEE118_escenario1.xlsx`, `branch!K39` (rama 38, 26–30 de 345 kV) cambia `STATUS=1` a `0`, con resaltado. El preparador verifica una copia existente y rechaza cambios adicionales; `--force` la recrea explícitamente. No es un editor genérico de escenarios.

```matlab
cd('C:/repos/Potencia_proyecto');
addpath('matlab');
study = run_video_project(false);
```

El pipeline exige la copia preparada, valida la salida de línea y la conectividad, corre los tres métodos en ambos casos y genera:

- `resultados_IEEE118_matlab.xlsx`.
- `resultados_IEEE118_escenario1_matlab.xlsx`.
- `comparacion_escenario1.xlsx`.
- Figuras y registro de ejecución en `escenario1_assets/`.

Son **cinco Excel principales**: dos entradas y tres salidas; cada libro de resultados incluye los tres métodos en hojas separadas. Los libros de otros casos y de validación son auxiliares. Los libros de salida se reemplazan: cerrarlos en Excel y preservar cualquier corrida anterior que interese. El pipeline no prepara ni reescribe la entrada por sí mismo.

### Contrato `main(input, output, makePlots, options)`

```matlab
opts = struct('tolerance',1e-8,'maxIterations',1000, ...
    'relaxation',1.5,'enforceQLimits',false,'verbose',true);
r = main('data/IEEE118.xlsx','resultados_IEEE118_matlab.xlsx',false,opts);
```

El cuarto argumento es opcional. `main` usa `verbose=true` por defecto y muestra mismatch máximo en cada iteración; `solve_power_flow` usa `verbose=false` por defecto para pruebas y llamadas directas. La tolerancia es de potencia en pu, no de tensión. Máximo IEEE-118: 1000; relajación GS: 1,5. Los límites Q están desactivados en la evidencia.

La inicialización usa VM/VA del Excel y VG de generadores activos en PV/Slack, **no perfil plano**. `VG` impone la consigna regulada; `VM` solo es condición inicial de PQ. Consignas incompatibles se rechazan. PV sin unidades activas se resuelve como PQ; Slack debe conservar generación activa.

Los tres métodos se ejecutan secuencialmente en una sola llamada, y el Excel se exporta después. El tiempo medido abarca solver, ensamblado y consola si verbose está activo; excluye importación, exportación y gráficas. No comparar tiempos como benchmark controlado.

`main;` carga IEEE-118. Si se omite la salida, se deriva de la entrada. Para demostrar tamaño variable, usar brevemente IEEE-14:

```matlab
r14 = main('data/IEEE14.xlsx','resultados_IEEE14_matlab.xlsx',false);
```

IEEE-300 es opcional fuera del video. Para más de 118 barras se amplía el máximo de iteraciones sin relajar la tolerancia.

## Interfaz: caso base → retirar línea → comparar

```matlab
addpath('matlab'); app_flows
```

- Inicialmente **Retirar línea 26–30** está deshabilitado. Ejecutar el IEEE-118 original con **Todos**, tolerancia ≤`1e-8` y límites Q desactivados; los tres métodos deben converger. Se exporta la base y se habilita la opción.
- Pulsar **Retirar línea 26–30** verifica la copia preparada, resuelve con las mismas opciones y exporta base (snapshot), escenario y comparación. No vuelve a resolver la base ni modifica sus entradas.
- **Base vs. salida 26–30** presenta tabla y perfiles; **Cambios de flujo**, rankings. La fila retirada y STATUS se resaltan. **Volver al caso base** restaura tablas y resultados guardados.
- Cualquier edición/cambio de parámetros, método o archivo invalida el snapshot y la comparación. Los controles se bloquean durante el cálculo; también hay validación al pulsar para rechazar estados obsoletos.
- `app_flows(carpetaSalida)` aísla los Excel. Sin argumento se reemplazan los tres libros de resultados de la raíz. La copia de entrada es `data/IEEE118_escenario1.xlsx`, ya incluida; si falta, se prepara con Python.
- La fila **Abrir Excel** abre **Entrada actual**, **Entrada 26–30**, **Resultados base**, **Resultados 26–30** y **Comparación** en la aplicación predeterminada de Windows. Solo se habilitan los archivos existentes, se respeta la carpeta de salida y no se guardan las ediciones de la GUI al abrirlos. Cerrar los resultados en Excel antes de recalcular.
- **Reset resultados** pide confirmación (predeterminado: **Cancelar**) y borra solo los seis Excel de salida conocidos de la carpeta configurada: resultados IEEE-14/118/118 escenario/300, comparación y validación MATPOWER. Limpia vistas y snapshots de resultados sin cambiar entradas ni parámetros; si estabas en el escenario, selecciona IEEE-118 para empezar desde la base. Protege cualquier libro usado como entrada y avisa de archivos bloqueados que no pudo borrar; cerrar Excel y reintentar. Se deshabilita mientras se calcula.
- `test_app_flows` ejerce el flujo completo, sus bloqueos, las rutas de apertura y el reset (cancelación, borrado, repetición y protección de entradas) usando una carpeta temporal, un abridor y un confirmador simulados; comprueba que las entradas y resultados del proyecto no cambien, incluso cuando las salidas aún no existen.

## Módulos para explicar en pantalla

| Responsabilidad | Archivo MATLAB |
| --- | --- |
| Importación y validación Excel | `load_case_excel.m`, `validate_case.m` |
| Tipos efectivos y consignas | `bus_sets.m`, `voltage_setpoints.m`, `initial_voltage.m` |
| Modelo π, tap/desfase y derivaciones GS/BS | `build_ybus.m` |
| Potencia especificada y residual común | `specified_power.m`, `power_mismatch.m` |
| Newton-Raphson / GS / FDLF | `solve_newton_raphson.m`, `solve_gauss_seidel.m`, `solve_fast_decoupled.m` |
| Matrices aproximadas FDLF | `fast_decoupled_matrices.m` |
| Límites Q agregados PV→PQ | `apply_q_limits.m`, `solve_power_flow.m` |
| Flujos y pérdidas / resultados | `calculate_branch_flows.m`, `assemble_result.m` |
| Exportación / GUI | `export_results_excel.m`, `app_flows.m` |
| Contingencia y comparación | `validate_line_outage.m`, `compare_scenario1.m`, `run_video_project.m` |

La entrada requiere `bus`, `gen`, `branch`, con compensación nodal **GS/BS en `bus`**, no una hoja ficticia de capacitores. `config` define baseMVA=100. Los Excel IEEE-118 nuevos exportan `entrada_bus/gen/branch`, `config`, `parametros`, `comparacion` y hojas `NR/GS/FDLF_bus/branch/conv`. `comparacion` añade `P_slack_MW` y `Q_slack_MVAr` a las columnas originales.

## Contrato de comparación del escenario

Auditoría de los archivos guardados: `python tools/check_video_evidence.py --materials`.
Pruebas de preparación y de detección de evidencia alterada: `python -m unittest discover -s tests -v`.

`comparacion_escenario1.xlsx` conserva:

- `comparacion`: Variable, Caso_base, Escenario, Diferencia **numéricos**; identificadores de barras extremas en filas separadas.
- `base_top5_bajas`, `escenario_top5_bajas`: cinco filas completas por barra.
- `base_top5_flujos`, `escenario_top5_flujos`: ramas completas más `S_max_MVA`.
- `cambios_top5_total`: cinco mayores cambios globales, incluida la línea retirada (−100 %); ranking literal de la guía.
- `cambios_ramas`, `cambios_top5`: Rama, Desde, Hasta, S_base_MVA, S_escenario_MVA, Delta_MVA, Delta_pct, Abs_delta_MVA y estados.
- `fuera_base`, `fuera_escenario`: filas completas de barras fuera del intervalo guía.
- `linea_retirada`: flujos P/Q/S base en ambos extremos de 26–30.
- `base_metodos`, `escenario_metodos`: comparación de los tres solvers.
- `definiciones`: convenciones.

S máxima es el máximo aparente de ambos extremos. El top5 global se ordena por |ΔS| e incluye la retirada; el complemento activo la excluye. Ambos conservan el signo de Δ. Los límites guía 0,95–1,05 no son VMIN/VMAX=0,94/1,06; RATE_A=0 no acredita margen térmico. Q neta de ramas puede ser negativa por capacitancia.

## Pruebas y referencia independiente

```matlab
addpath('matlab');
test_powerflow;
test_scenario1;
test_plot_convergence;
% test_app_flows; % Abre la interfaz.
```

Estos son comandos de reproducción, no una afirmación de haberlos ejecutado durante la generación documental. El informe verifica de manera adicional los archivos guardados sin lanzar MATLAB.

```bash
python tools/setup_matpower.py
```

```matlab
validate_against_matpower('C:/ruta/mostrada/matpower8.1');
```

La referencia publicada es MATPOWER 8.1 con `case118.m` oficial y NR a 1e-10 pu. Se exportan errores VM/VA, flujos, pérdidas P/Q y P/Q Slack en `validacion_MATPOWER.xlsx/json`. El generador marca pendientes si las columnas adicionales aún no están presentes. La validación base no certifica externamente el escenario. Fuentes/umbrales: `VALIDACION_EXTERNA.md`.

## Generación documental compatible

Python 3.10+, Typst en PATH y estas dependencias:

```bash
python -m pip install openpyxl numpy matplotlib PyMuPDF python-docx Pillow
python tools/build_report.py
# O bien: python tools/build_video_report.py
```

El builder anterior delega al nuevo y no pierde el escenario. Se conserva el desarrollo técnico completo (~60 KB originales) y se añaden tablas, unifilar y análisis del escenario. Salidas: `INFORME_PROYECTO_MATLAB.md`, `.pdf`, **`.docx` Word real**; `.typ` es la plantilla PDF. No se ejecutan MATLAB ni generadores de presentación. El Word conserva texto y tablas editables; las ecuaciones se renderizan con Typst como imágenes. No requiere Word/COM ni python-pptx. Evidencia y hashes: `informe_assets/manifest_video.json`.

Nombres de integrantes, MP4 1080p de 30–40 min, voces identificadas, grabación continua y entrega siguen pendientes humanos. La ejecución automatizada no sustituye el video. Ver `CUMPLIMIENTO_GUIA_VIDEO.md`.
