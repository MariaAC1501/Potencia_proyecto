# Validación independiente del flujo de potencia

## Alcance y evidencia

Se compararon Newton-Raphson, Gauss-Seidel y desacoplado rápido propios con **MATPOWER 8.1**, software de referencia descrito en un artículo de *IEEE Transactions on Power Systems* [1]. Se verificaron IEEE-14, IEEE-118 e IEEE-300: **9 de 9 comparaciones aprobaron**.

La evidencia numérica reproducible está en:

- `validacion_MATPOWER.xlsx`: resumen, metadatos y diferencias de cada barra y rama para los nueve cálculos.
- `validacion_MATPOWER.json`: versiones, fecha UTC, umbrales, comprobación del caso oficial y resultados de aceptación.
- `resultados_IEEE14_matlab.xlsx`, `resultados_IEEE118_matlab.xlsx` y `resultados_IEEE300_matlab.xlsx`: resultados propios regenerados después de corregir las consignas `VG`.
- `matlab/validate_against_matpower.m`: procedimiento que vuelve a calcular las referencias, comprueba los errores y falla si algún criterio no se cumple.
- `verificacion_MATLAB.log`: registro de la suite ampliada y de las comprobaciones de consola, exportación, gráficas y ejecución de la GUI. Estas pruebas técnicas no constituyen un ensayo oral cronometrado.

Esto es una validación contra un solucionador independiente respaldado por literatura IEEE y datos estándar, no una afirmación de que las cifras de este repositorio se copiaron de una tabla de un artículo. No se ha realizado validación de una red regional real ni de todas las condiciones operativas posibles.

## 1. Fuentes del caso base y de los métodos

El caso principal tiene 118 barras, 186 ramas y 54 registros de generación, con base de 100 MVA. Representa una aproximación de una parte del sistema American Electric Power de diciembre de 1962, archivada por la Universidad de Washington [5]. Los límites MVA de ese archivo no son límites históricos verificados; no deben interpretarse como datos operativos de una red real actual.

La entrada `data/IEEE118.xlsx` se cotejó numéricamente con el **`data/case118.m` distribuido en MATPOWER 8.1**, no únicamente con una copia local del proyecto. Coincidieron la base MVA, las 13 columnas de barras, las primeras 10 columnas de generadores utilizadas por el flujo y las 13 columnas de ramas. La diferencia máxima fue cero. Los taps 0 y 1 se consideran equivalentes cuando ambos representan relación unitaria.

Para IEEE-14 e IEEE-300 se suministraron al solucionador independiente exactamente los datos importados de sus Excel. No se afirma que esos dos libros coincidan en todos sus campos con otras variantes publicadas de `case14` o `case300`. La comparación de la entrada oficial se exige expresamente para IEEE-118.

La formulación de Newton-Raphson se relaciona con [2]; el fundamento del desacoplamiento rápido, con [3]. Estas fuentes no implican que nuestra variante de matrices B' y B'' o sus iteraciones sean idénticas a las de MATPOWER. Se contrasta el estado eléctrico final y los flujos, no la igualdad del número de iteraciones entre implementaciones.

## 2. Condiciones comunes

| Parámetro | Implementación propia | Referencia MATPOWER |
|---|---|---|
| Algoritmo | Los tres métodos propios | Newton-Raphson AC |
| Tolerancia de desbalance | `1e-8 pu` | `1e-10 pu` |
| Inicialización | `VM` y `VA`; `VG` en PV/Slack con unidades activas | Datos equivalentes y consignas `VG` |
| Límites Q | Desactivados | Desactivados |
| Máximo de iteraciones | 1000; 30000 para IEEE-300 | 30 |
| Base de potencia | 100 MVA en los tres casos | La misma |

Se utilizó MATLAB R2025a Update 1. La versión exacta y la fecha UTC de cada ejecución se guardan en el JSON. MATPOWER se incorpora al path solo durante la validación y se restaura el path original al terminar; no interviene en `main` ni en `app_flows`.

## 3. Criterios de aceptación

Los siguientes son criterios numéricos elegidos para este proyecto, no tolerancias impuestas por el enunciado ni una norma IEEE:

| Magnitud | Máximo error absoluto permitido |
|---|---:|
| Magnitud de tensión | `1e-7 pu` |
| Ángulo de tensión | `1e-5 grados` |
| Potencia activa por rama, en ambos extremos | `1e-4 MW` |
| Potencia reactiva por rama, en ambos extremos | `1e-4 MVAr` |
| Suma de pérdidas activas de ramas | `1e-4 MW` |
| Suma neta de potencia reactiva de ramas | `1e-4 MVAr` |
| Potencia activa de la Slack | `1e-4 MW` |
| Potencia reactiva de la Slack | `1e-4 MVAr` |

Además, cada método propio debe declarar convergencia y un desbalance final no mayor que `1e-8 pu`; MATPOWER debe declarar éxito. Los ángulos se comparan módulo 360 grados. Las barras se emparejan por identificador, y se comprueban los extremos y el orden de las ramas.

## 4. Resultados obtenidos

| Caso | Método | Error VM (pu) | Error VA (grados) | Error P de rama (MW) | Error Q de rama (MVAr) | Estado |
|---|---|---:|---:|---:|---:|---|
| IEEE-14 | Newton-Raphson | `5.480e-12` | `2.620e-10` | `3.275e-09` | `5.223e-09` | Aprobado |
| IEEE-14 | Gauss-Seidel | `2.957e-10` | `1.604e-07` | `1.863e-06` | `7.512e-07` | Aprobado |
| IEEE-14 | Desacoplado rápido | `1.175e-09` | `1.616e-08` | `5.434e-07` | `3.610e-07` | Aprobado |
| IEEE-118 | Newton-Raphson | `8.882e-16` | `8.527e-14` | `3.922e-12` | `2.736e-12` | Aprobado |
| IEEE-118 | Gauss-Seidel | `9.893e-11` | `3.472e-07` | `3.201e-06` | `5.450e-07` | Aprobado |
| IEEE-118 | Desacoplado rápido | `5.034e-11` | `6.887e-09` | `1.844e-07` | `1.351e-08` | Aprobado |
| IEEE-300 | Newton-Raphson | `5.218e-15` | `1.194e-12` | `1.953e-11` | `8.481e-11` | Aprobado |
| IEEE-300 | Gauss-Seidel | `2.182e-10` | `3.144e-07` | `5.924e-06` | `8.171e-07` | Aprobado |
| IEEE-300 | Desacoplado rápido | `3.094e-10` | `1.709e-08` | `6.649e-07` | `5.565e-08` | Aprobado |

Todos los errores de pérdida activa fueron menores que `5.8e-7 MW`. Las pérdidas propias de Newton-Raphson fueron 13.393272 MW, **132.862872 MW** y 408.985541 MW para IEEE-14, IEEE-118 e IEEE-300, respectivamente. Los valores completos sin redondeo están en el Excel y el JSON; diferencias de últimos dígitos entre ejecuciones pueden depender de la plataforma.

### Validación adicional exigida por la guía del video

La validación regenerada incluye pérdidas netas Q y potencia P/Q de la Slack, no solamente tensión y flujos. Para IEEE-118, MATPOWER obtiene P Slack **513.862872 MW**, Q Slack **−82.424057 MVAr**, pérdidas activas **132.862872 MW** y suma neta Q de ramas **−557.947423 MVAr**. El signo negativo de esta última incluye el aporte capacitivo de líneas y no representa una disipación reactiva negativa.

| Método IEEE-118 | Error pérdidas P (MW) | Error Q neta (MVAr) | Error P Slack (MW) | Error Q Slack (MVAr) |
|---|---:|---:|---:|---:|
| Newton-Raphson | `6.281e-12` | `4.775e-12` | `3.524e-12` | `2.558e-13` |
| Gauss-Seidel | `4.581e-7` | `2.978e-6` | `6.367e-6` | `3.915e-7` |
| Desacoplado rápido | `2.568e-9` | `7.105e-9` | `4.808e-8` | `2.344e-9` |

Los valores completos y referencias se exportan en las columnas `AbsQLossError_MVAr`, `AbsSlackPError_MW`, `AbsSlackQError_MVAr` y `Reference*` de la hoja `resumen` y del JSON. Estos criterios forman parte de la aceptación automática de las nueve comparaciones.

El estudio de salida de la línea 26–30 está separado en `comparacion_escenario1.xlsx`: no se atribuyen sus números a la validación del caso base. `test_scenario1` comprueba el único cambio de estado, la eliminación completa de la admitancia serie y carga de línea, los flujos nulos de la rama retirada, el acuerdo entre métodos, los rankings y la exportación. La evidencia automatizada sigue sin sustituir la grabación continua requerida.

## 5. Correcciones que motivaron esta validación

Antes de esta actualización, los métodos fijaban las magnitudes PV a `bus.VM` y no a `gen.VG`. En IEEE-118 esos campos difieren en las barras 19, 32, 34, 92 y 103. La coincidencia anterior entre los tres métodos era una comprobación interna de un mismo modelo con consignas equivocadas, no una validación independiente.

Ahora los tres métodos respetan `VG` de generadores activos en PV y Slack. La pérdida IEEE-118 pasa de aproximadamente 132.4778 MW a **132.8629 MW**, y Gauss-Seidel pasa de 760 a **757 iteraciones**. Los resultados anteriores de IEEE-118 quedan sustituidos por los libros regenerados.

También se corrigió la selección por defecto: `main` utiliza IEEE-118 y deriva el nombre del Excel de salida del archivo de entrada. `resultados_IEEE118_matlab.xlsx` vuelve a contener 118 barras; IEEE-300 se guarda en su propio archivo. Si se omite `VG` en el libro, se utiliza `VM` de la barra como respaldo documentado, no una consigna arbitraria de 1 pu.

## 6. Cómo reproducir

Desde una terminal en la raíz del proyecto:

```bash
python tools/setup_matpower.py
```

El instalador descarga el ZIP oficial de **MATPOWER 8.1** y verifica su SHA-256 antes de extraerlo. Por defecto usa una carpeta temporal y muestra su ruta. Si esa carpeta se elimina, vuelve a ejecutar el instalador. También puedes elegir una ruta persistente:

```bash
python tools/setup_matpower.py --destination C:/herramientas/matpower8.1
```

En MATLAB, desde la raíz del proyecto:

```matlab
addpath('matlab');
test_powerflow;
test_scenario1;
validate_against_matpower('C:/herramientas/matpower8.1');
```

Ajusta la ruta a la mostrada por el instalador. Las pruebas no requieren MATPOWER; `validate_against_matpower` sí. Para regenerar los resultados propios sin gráficas:

```matlab
for name = {'IEEE14', 'IEEE118', 'IEEE300'}
    main(fullfile('data', [name{1}, '.xlsx']), [], false);
end
```

Los Excel de salida existentes se reemplazan, por lo que deben cerrarse antes de ejecutar. La comparación escribe primero un libro temporal y luego reemplaza el destino, evitando mezclar hojas de ejecuciones distintas.

Salida de aceptación esperada:

```text
Validación externa: 9/9 comparaciones aprobadas.
```

La ruta del libro se añade al mensaje real. Si un umbral no se cumple, se produce un error y debe revisarse la evidencia; no debe declararse aprobada una corrida fallida.

### Descarga fijada

- URL: https://github.com/MATPOWER/matpower/releases/download/8.1/matpower8.1.zip
- Tamaño verificado: 47268554 bytes.
- SHA-256: `7f13b1441669a64e312d14a60e564cd91977ff1676ff77d25538e94ff313dd56`.
- DOI de la versión 8.1: https://doi.org/10.5281/zenodo.15871662.

## 7. Referencias verificadas

[1] R. D. Zimmerman, C. E. Murillo-Sánchez y R. J. Thomas, “MATPOWER: Steady-State Operations, Planning, and Analysis Tools for Power Systems Research and Education”, *IEEE Transactions on Power Systems*, vol. 26, n.º 1, pp. 12–19, febrero de 2011. DOI: https://doi.org/10.1109/TPWRS.2010.2051168. Sustenta la elección del software de referencia; la referencia numérica se calculó con la versión 8.1, no se atribuye a una tabla del artículo.

[2] W. F. Tinney y C. E. Hart, “Power Flow Solution by Newton's Method”, *IEEE Transactions on Power Apparatus and Systems*, vol. PAS-86, n.º 11, pp. 1449–1460, noviembre de 1967. DOI: https://doi.org/10.1109/TPAS.1967.291823. Los datos bibliográficos se verificaron mediante los metadatos del DOI.

[3] B. Stott y O. Alsac, “Fast Decoupled Load Flow”, *IEEE Transactions on Power Apparatus and Systems*, vol. PAS-93, n.º 3, pp. 859–869, mayo de 1974. DOI: https://doi.org/10.1109/TPAS.1974.293985.

[4] R. D. Zimmerman y C. E. Murillo-Sánchez, *MATPOWER*, versión 8.1, 2025, software. DOI: https://doi.org/10.5281/zenodo.15871662. Política oficial de citas: https://matpower.org/citing.

[5] R. Christie, Universidad de Washington, *Power Systems Test Case Archive: 118 Bus Power Flow Test Case*, mayo de 1993. https://labs.ece.uw.edu/pstca/pf118/pg_tca118bus.htm. Procedencia y advertencias del caso base.

Las consultas y extracciones de apoyo se conservaron en `.searches/` y `.web-content/`. Citar un artículo no sustituye la comparación numérica: ambas evidencias se presentan separadamente.
