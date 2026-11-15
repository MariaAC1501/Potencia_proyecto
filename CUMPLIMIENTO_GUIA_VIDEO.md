# Cumplimiento trazable de la guía del video — IEEE-118, escenario 1

Referencia: `Guía_para_el_video_de_exposición_—_Proyecto_de_Flujos_de_Potencia_IEEE_118_barra.md` (10 de noviembre de 2026). **Escenario elegido: salida de la línea 26–30 de 345 kV.**

**No se declara cumplida la entrega audiovisual.** Hay programa, cálculos, entradas/salidas, comparación, unifilar publicado e informe Word real. No hay evidencia suficiente de MP4 final, nombres/participación, corridas grabadas continuas ni entrega institucional.

Estados: **V** = verificado en evidencia computacional/documental; **D** = explicado o comando disponible, requiere demostración en el video; **H** = pendiente humano; **R** = revisión/ensayo audiovisual pendiente. V no equivale a video grabado. Los hashes y comprobaciones están en `informe_assets/manifest_video.json`; `escenario1_assets/auditoria_evidencia.json` y `pruebas_escenario1.log` conservan la auditoría numérica y la prueba MATLAB del responsable del código.

## A. Formato, participación y entrega

| ID | Requisito de la guía | Archivo, evidencia o acción comprobable | Estado |
| --- | --- | --- | --- |
| F01 | Video de 30–40 min | Revisar duración real del MP4 final; plan 35:45 en `PRESENTACION.md` y `GUIA_USO_MATLAB.md` §18.7, no duración certificada | H |
| F02 | Formato MP4 | Generar/reproducir archivo final; no confundir PDF/PPT con video | H |
| F03 | Resolución mínima 1080p | Comprobar propiedades de la pista de video final (mínimo 1920×1080) | H |
| F04 | Audio claro | Escuchar de principio a fin con voces inteligibles y nivel consistente | H |
| F05 | Sin música que tape la voz | Revisar mezcla de audio final; preferir sin música | H |
| F06 | Todos los integrantes con voz | Completar nombres reales, reparto y participación efectiva; no se inventan miembros | H |
| F07 | Cada integrante se identifica al iniciar | Confirmar nombre pronunciado al comenzar su sección | H |
| F08 | Cámara preferible | Decisión del grupo y prueba audiovisual; recomendación, no obligación de la guía | H |
| F09 | Corridas continuas, sin cortes ni acelerado | Grabar cada toma desde lanzamiento hasta exportación; logs/capturas no prueban continuidad | H |
| F10 | Se permite editar entre secciones, no dentro de corrida | Revisar línea de tiempo de edición y MP4 completo | H |
| F11 | Código visible | Mostrar módulos listados en `MATLAB_README.md`; verificar legibilidad en 1080p | R |
| F12 | Consola o interfaz visible | `main(...,false,opts)` con `verbose=true`; revisar legibilidad de mismatch | R |
| F13 | Excel de entrada y salida visibles | Abrir las cuatro entradas/salidas IEEE-118 durante las tomas correspondientes | R |
| E01 | Avisar al profesor el escenario | Confirmar notificación de elección **1, línea 26–30** | H |
| E02 | Entrega por evaluaciones TEC Digital | Confirmación real de subida en el apartado del proyecto | H |
| E03 | Un día antes de la exposición | Confirmar fecha asignada y fecha límite; no se inventa calendario | H |
| E04 | Video adjunto | MP4 final no acreditado en esta revisión | H |
| E05 | Programa adjunto | `matlab/`, `tools/prepare_scenario1.py`, instrucciones y datos; empaquetar y probar rutas | V / H subir |
| E06 | Informe **Word** adjunto | `INFORME_PROYECTO_MATLAB.docx`: OOXML real, texto/tablas editables; no PDF renombrado | V / H subir |
| E07 | Presentación **PowerPoint** adjunta | `PRESENTACION.pptx`; revisar versión del escenario, notas y legibilidad antes de subir | R / H subir |
| E08 | Excel entrada base | `data/IEEE118.xlsx` intacto | V / H subir |
| E09 | Excel entrada modificada | `data/IEEE118_escenario1.xlsx`, STATUS resaltado | V / H subir |
| E10 | Excel salida base | `resultados_IEEE118_matlab.xlsx`, tres métodos y Slack P/Q | V / H subir |
| E11 | Excel salida escenario | `resultados_IEEE118_escenario1_matlab.xlsx`, tres métodos y Slack P/Q | V / H subir |
| E12 | Si excede límite, enlace institucional accesible | Drive/OneDrive institucional y prueba del permiso del profesor | H si aplica |
| E13 | Paquete íntegro, sin resultados mezclados | Cinco Excel principales: dos entradas, dos resultados y `comparacion_escenario1.xlsx`; añadir fuentes y manifiestos, abrir desde carpeta de entrega. Los libros auxiliares son aparte | V estructura / H subir |

## B. Orden y tiempo de las seis secciones

| ID | Requisito | Evidencia o plan | Estado |
| --- | --- | --- | --- |
| O00 | Presentación: curso, proyecto, integrantes, escenario | Portadas del informe y material audiovisual; nombres siguen pendientes | D / H |
| O01 | Configuración, 8–10 min sugeridos | `MATLAB_README.md`, informe §§4–7; objetivo 9:00 | D / R |
| O02 | Descripción base, 3–4 min | Informe §9.1; objetivo 3:30 | D / R |
| O03 | Corrida base/validación, 6–8 min | Informe §§9.3, 9.6, 9.9; objetivo 7:30 | D / H grabar |
| O04 | Escenario, 10–12 min | Informe §§9.2, 9.4–9.8; objetivo 11:45, incluidas tres preguntas previas de 15 s | D / H grabar |
| O05 | Conclusiones, 2–3 min | Informe §9.10; objetivo 2:30 | D / R |
| O06 | Orden 0→1→2→3→4→5 y total 30–40 min | Propuesta: 1:30+9:00+3:30+7:30+11:45+2:30=35:45; comprobar en ensayo y MP4 | H |
| O07 | Prioridad IEEE-118 + escenario | README e informe; IEEE-14 solo demostración breve; IEEE-300 fuera de exposición, opcional de respaldo | D / R |

## C. Sección 1: configuración del programa

| ID | Punto de la guía | Archivo o comando para mostrar | Estado |
| --- | --- | --- | --- |
| C01 | Lenguaje y organización de módulos | MATLAB R2025a; `MATLAB_README.md`, informe §6.1; `main.m` y `solve_power_flow.m` | V / D |
| C02 | Hojas de barras, ramas y generadores | `data/IEEE118.xlsx`: `bus`, `branch`, `gen` | V / D |
| C03 | Compensación en derivación | `bus.GS/BS`, no hoja de capacitores ficticia; informe §§4.2, 10.3 | V / D |
| C04 | Columnas, unidades y base 100 MVA | `config`, informe §§4.1, 15.1; `GUIA_USO_MATLAB.md` §11 | V / D |
| C05 | Identificación Slack, PV, PQ | `bus_sets.m`, `voltage_setpoints.m`; TYPE 3/2/1 y generación activa | V / D |
| C06 | Modelo π y construcción Ybus | `build_ybus.m`, informe §4.2; mostrar acumulación serie y BR_B/2 | V / D |
| C07 | Tap y desfase | `build_ybus.m`; t=τ·exp(jφ), términos de ambos extremos | V / D |
| C08 | GS/BS en diagonal Ybus | `build_ybus.m`; dividir por baseMVA, distinguir capacitor de carga | V / D |
| C09 | Tamaño definido por entrada, no fijo a 118 | `load_case_excel.m`; correr `main('data/IEEE14.xlsx','resultados_IEEE14_matlab.xlsx',false)` | V / H demostrar |
| C10 | IEEE-14 en menos de 1 min recomendado | Ensayar la demostración completa, no confundir solver con tiempo de explicación | H |
| C11 | Newton-Raphson obligatorio: ecuaciones/estado | `solve_newton_raphson.m`, informe §5.1; Jacobiano y ángulos/magnitudes PQ | V / D |
| C12 | Gauss-Seidel obligatorio: ecuaciones/estado | `solve_gauss_seidel.m`, informe §5.2; barrido, reactiva PV y proyección VG | V / D |
| C13 | Tercer método: desacoplado rápido | `solve_fast_decoupled.m`, `fast_decoupled_matrices.m`, informe §5.3 | V / D |
| C14 | Tolerancia pu y máximo de iteraciones | `parametros` en salidas: 1e-8 pu y 1000 para IEEE-118 | V / D |
| C15 | Valores iniciales | VM/VA del Excel y VG activa, **no perfil plano**; `initial_voltage.m` | V / D |
| C16 | Aceleración GS | Relajación 1,5; `parametros`, informe §5.2 | V / D |
| C17 | Límites Q / PV→PQ si implementado | `apply_q_limits.m`; agregado por barra, no Slack; **desactivado en estas corridas** | V / D |
| C18 | Flujos P/Q de rama y pérdidas | `calculate_branch_flows.m`, `assemble_result.m`; signos de entrada a rama | V / D |
| C19 | P/Q de Slack | `NR_bus` barra 69 y `comparacion.P_slack_MW/Q_slack_MVAr` | V / D |
| C20 | Exportación y hojas de resultados | `export_results_excel.m`; entrada_*, config, parametros, comparacion, NR/GS/FDLF_bus/branch/conv. La GUI también exporta base, escenario y comparación al usar el flujo de contingencia | V / D |

## D. Secciones 2–3: red base, corrida y validación

| ID | Punto de la guía | Evidencia concreta | Estado |
| --- | --- | --- | --- |
| B01 | Fuente exacta y versión | `data/case118.m`, MATPOWER 8.1; cotejo oficial en `validacion_MATPOWER.json`; procedencia UW, informe §9.1 | V / D |
| B02 | Barras, ramas y generadores del archivo | 118 barras, 186 ramas, 54 generadores activos; 9 ramas con tap no unitario | V / D |
| B03 | Barras con carga, criterio explícito | 99 con PD o QD no nulos; 91 con PD distinto de cero. No confundir los conteos | V / D |
| B04 | Referencia y niveles de tensión | Slack 69; 138/345 kV y también 161 kV (barra 87) presentes en Excel | V / D |
| B05 | Carga total | 4242 MW y 1438 MVAr, hoja `bus`; informe §9.1 | V / D |
| B06 | Generación programada total | 4377,4 MW, incluye PG Slack 516,4; QG entrada 0 no fija Q en PV/Slack | V / D |
| B07 | Unifilar **publicado y citado** | `escenario1_assets/IEEE118_unifilar_UW.png/.tif`, UW/R. Christie mayo 1993; `README_FUENTES.md`, hash JSON | V / D |
| B08 | Localizar 26 y 30 correctamente | Recorte y `_anotado.png`: **26 Tanners Creek**, **30 Sorenson**, según CDF UW; 26 NO es W. Kamm | V / D |
| B09 | Abrir entrada y lanzar NR, mismatch cada paso | `main(...,false,opts)` con verbose=true; consola conservada en `ejecucion_MATLAB.log` | V cálculo / H toma continua |
| B10 | Repetir GS y tercer método | La misma llamada ejecuta NR→GS→FDLF y exporta al final | V cálculo / H toma continua |
| B11 | Mostrar VM/VA, flujos P/Q, pérdidas y Slack en salida | `resultados_IEEE118_matlab.xlsx`, hojas `*_bus`, `*_branch`, `comparacion` | V / H mostrar |
| B12 | Tabla comparativa de 7 columnas de la guía | Informe §9.3: método, iteraciones, tiempo, mismatch, P Slack, pérdidas P/Q | V / D |
| B13 | Referencia independiente publicada | MATPOWER 8.1 NR, caso oficial, tolerancia 1e-10 pu; informe §9.9 y `VALIDACION_EXTERNA.md` | V / D |
| B14 | Error máximo VM y VA | `validacion_MATPOWER.xlsx`: resumen y `IEEE118_*_bus`; informe §9.9 | V / D |
| B15 | Diferencias pérdidas totales P y Q | Resumen: AbsPLossError_MW, AbsQLossError_MVAr y referencias | V / D |
| B16 | Diferencias potencia Slack P y Q | Resumen: AbsSlackPError_MW, AbsSlackQError_MVAr y referencias | V / D |
| B17 | Explicar diferencias apreciables | Errores dentro de umbrales, mismas consignas VG y límites Q desactivados; no exigir mismas iteraciones | V / D |
| B18 | 5 barras de menor tensión base | `base_top5_bajas`; informe §9.6: 76, 53, 118, 55, 107 | V / D |
| B19 | 5 ramas de mayor S base | `base_top5_flujos`; máximo de ambos extremos: 9–10, 8–9, 8–5, 38–37, 30–17 | V / D |

## E. Sección 4: escenario 1 y preguntas obligatorias

| ID | Punto de la guía | Evidencia concreta | Estado |
| --- | --- | --- | --- |
| S01 | Un solo cambio: retirar 26–30 | `branch!K39`, rama 38, STATUS 1→0, copia resaltada y base intacta | V / H mostrar |
| S02 | Ubicar línea en unifilar | Unifilar publicado y recorte anotado; enlace vertical Tanners Creek–Sorenson de 345 kV | V / D |
| S03 | NR y GS del escenario, corrida continua | GUI: primero **Ejecutar métodos**, luego **Retirar línea 26–30**, que se habilita tras base válida. También `main('data/IEEE118_escenario1.xlsx',...,false,opts)` o pipeline; corre FDLF adicional | V cálculo / H toma continua |
| S04 | Flujo previo de línea retirada | `linea_retirada`: P desde 223,710922 MW; P hasta −219,732807 MW; S máxima 224,004254 MVA | V / D |
| S05 | Tabla obligatoria: V mínima y barra | 0,943000 (76)→0,940040 (21), Δ−0,002960 pu; informe §9.5 | V / D |
| S06 | Tabla obligatoria: V máxima y barra | 1,050000 (10)→1,050000 (10), Δ0 | V / D |
| S07 | Tabla obligatoria: fuera de 0,95–1,05 | 3→6, Δ+3; filas completas `fuera_base/fuera_escenario` | V / D |
| S08 | Tabla obligatoria: P Slack 69 | 513,862872→546,897686 MW, Δ+33,034814 | V / D |
| S09 | Tabla obligatoria: Q Slack 69 | −82,424057→−79,013080 MVAr, Δ+3,410977; absorbe menos Q | V / D |
| S10 | Tabla obligatoria: pérdidas MW | 132,862872→165,897686, Δ+33,034814 (+24,864 %) | V / D |
| S11 | Tabla obligatoria: iteraciones NR | 3→4, Δ+1 | V / D |
| S12 | Tabla obligatoria: iteraciones GS | 757→909, Δ+152 | V / D |
| S13 | Comparación numérica exportable | `comparacion`, valores numéricos, barras en filas separadas; no restar identificadores como magnitudes | V |
| S14 | 5 mayores cambios en MVA y % | `cambios_top5_total`, informe §9.7 y diapositiva25: ranking global **incluye retirada** (26–30, 26–25, 23–25, 30–17, 25–27). `cambios_top5` añade cinco activas para redistribución | V / D |
| S15 | Pregunta 1: por dónde y cuánto aumenta | Informe §9.8: 26–25 +223,362016 MVA; 23–25 +135,984080; 25–27 +87,077145; 32–113 +50,278581; 30–17 −120,114746 | V / D |
| S16 | Pregunta 2: barras fuera de rango | Base 53/76/118; escenario 20/21/22/53/76/118; informe §9.8 | V / D |
| S17 | Pregunta 3: pérdidas y explicación | +33,034814 MW; nuevas corrientes/rutas y pérdidas I²R, a pesar de retirar pérdida propia 3,978115 MW | V / D |
| S18 | Cautelas de interpretación | Intervalo guía ≠ VMIN/VMAX; máximo ambos extremos; MVA ≠ MW; Q neta incluye carga capacitiva | V / D |
| S19 | No afirmar seguridad térmica | RATE_A=0 no informa capacidad; no acreditar sobrecarga ni ausencia de ella | V / D |
| S20 | Prueba del escenario | `test_scenario1.m` y `test_app_flows.m`; logs `escenario1_assets/pruebas_escenario1.log` y `pruebas_GUI_escenario1.log`. La GUI comprueba base→salida→volver, invalidación y exportación temporal, sin modificar evidencia incluida | V |
| S21 | Pregunta antes de cada respuesta | Diapositivas 24/25, 26/27 y 28/29: pregunta completa → respuesta correspondiente, manteniendo el formato anterior. `test_presentation_story.py` comprueba texto, orden y tiempos; notas conservan las explicaciones | V / D |

## F. Sección 5: conclusiones y cierre

| ID | Punto de la guía | Evidencia o acción | Estado |
| --- | --- | --- | --- |
| K01 | Precisión de tres métodos, base y escenario | Informes §§9.3–9.4: seis soluciones con mismatch ≤1e-8 pu | V / D |
| K02 | Iteraciones y tiempo, base y escenario | NR 3→4, GS 757→909, FDLF 9→11; tiempos medidos en tablas, sin benchmark controlado | V / D |
| K03 | Robustez con alcance correcto | Los tres convergen en esta contingencia/inicialización; no afirmar robustez general | V / D |
| K04 | Diagnóstico aceptable/emergencia/colapso y razón | No aceptable respecto a tensión guía (6 bajas); no colapso demostrado, no sobrecarga acreditada; informe §9.10 | V / D |
| K05 | Recomendación técnica principal | Estudiar restitución del corredor, soporte reactivo y redespacho en 20–22 con límites reales; no dimensionar capacitor sin estudio | V / D |
| K06 | Cada conclusión con un número | 0,940040 pu; seis bajas; +33,034814 MW; +223,362016 MVA; repetir en cierre audiovisual | D / R |

## G. Reproducibilidad documental y controles realizados

```bash
python -m pip install openpyxl numpy matplotlib PyMuPDF python-docx Pillow
typst --version
python tools/build_report.py
# La entrada nueva equivalente es: python tools/build_video_report.py
```

| Control | Resultado y evidencia |
| --- | --- |
| No ejecutar MATLAB ni alterar resultados al compilar documentos | Los builders leen Excel/JSON y solo escriben documentos/`informe_assets`; no llaman solver ni capturador |
| Preservar informe técnico existente | Desarrollo de modelo, métodos, arquitectura, resultados, validación y bibliografía conservado; sección 9 completa añadida; IEEE-118 primero |
| Presentación y guion sincronizados con la GUI | PPTX/notas, PDF y guion describen Ejecutar métodos → Retirar línea 26–30 → comparación → Volver al caso base; fuentes y capturas actuales se verifican con hashes |
| Compatibilidad builder anterior | `tools/build_report.py` delega al nuevo; ambas entradas producen MD/PDF/DOCX sin perder escenario |
| Cambio único y resaltado | Comparación entre todas las hojas de entrada; STATUS 1→0 en K39; relleno sólido comprobado |
| Salidas correspondientes a sus entradas | Compara tablas exportadas, normalizando solo nombres de columnas opcionales que MATLAB normaliza |
| Seis convergencias e historiales | Iteraciones 0…N, residual final, tolerancia, sumas P/Q y Slack contrastados |
| Tabla y rankings reproducibles | Recalcula extremos, conteos, diferencias, top5 de tensiones/flujos/cambios y porcentajes; máximo ambos extremos, ranking global incluye retirada y complemento activo la separa |
| Validación externa adicional completa | Columnas de errores Q ramas y P/Q Slack presentes; `missing_external_columns=[]` en manifiesto |
| Unifilar publicado | Hash del TIFF original verificado contra `fuente_unifilar.json`; ubicación de barras según fuente corregida |
| PDF completo | Revisión automática de todos los capítulos, cifras clave, páginas no vacías y límites horizontales/verticales; detalle en manifiestos |
| Word real completo | DOCX OOXML reabierto con python-docx, ZIP íntegro, todos los encabezados, cifras, tablas/figuras y 35 ecuaciones como imágenes. También abierto/exportado en Microsoft Word: `informe_assets/revision_word.pdf`; revisión visual de tablas, validación y unifilar. Este control adicional usa Word/pywin32, no es requisito del builder |
| Verificador independiente y pruebas negativas | `python -m unittest discover -s tests -v`: incluye pruebas numéricas, de manipulación de evidencia y de pregunta→respuesta, tiempos y notas. Rechaza diferencias, ángulos, pérdidas Q y rankings alterados. `python tools/check_video_evidence.py --materials` comprueba evidencia y presencia/estructura de entregables, no video |
| Dependencias explícitas | `requirements-materiales.txt` fija el entorno probado (Python 3.11+); generadores sin fijar versiones admiten Python 3.10+, openpyxl/numpy/matplotlib/PyMuPDF/python-docx/Pillow; Typst en PATH. No requiere Word/COM para generar |
| Evidencia no equivale a video | La aprobación numérica no cambia los pendientes F01–F13/E01–E13 ni certifica tomas continuas |

**Cierre obligatorio humano:** completar nombres también en las fuentes/portadas antes de regenerar; revisar material audiovisual actualizado; ensayar con cronómetro; grabar y comprobar MP4; verificar continuidad de cada corrida; preparar paquete y confirmar entrega/permisos. No marcar esos pasos como realizados solo porque existe este checklist.
