"""Relato único del video IEEE118, escenario 1. Cifras: evidencia Excel, nunca estimadas.

Los tiempos incluyen mostrar código, operar Excel y grabar las corridas sin cortes.
Los campos de identidad se completan con personas reales antes de grabar.
"""
from __future__ import annotations

SECTION_NAMES = {
    0: '0 · Presentación', 1: '1 · Configuración', 2: '2 · Red IEEE118',
    3: '3 · Corrida base', 4: '4 · Salida de línea 26–30', 5: '5 · Conclusiones',
}
QUESTION_PROMPTS = {
    1: '¿Hacia qué líneas se redistribuyó la potencia y cuánto aumentó su flujo?',
    2: '¿Alguna barra quedó fuera del rango de 0,95–1,05 pu?',
    3: '¿Aumentaron o disminuyeron las pérdidas? ¿Por qué?',
}
SECTION_SECONDS = (90, 540, 210, 450, 705, 150)
PLANNED_SECONDS = sum(SECTION_SECONDS)
EXPECTED_SLIDES = 32

SMALL_COMMAND = """addpath('matlab');
options = struct('verbose',true);
r14 = main('data/IEEE14.xlsx','resultados_IEEE14_matlab.xlsx',false,options);"""
BASE_COMMAND = """addpath('matlab');
options = struct('verbose',true);
base = main('data/IEEE118.xlsx','resultados_IEEE118_matlab.xlsx',false,options);"""
SCENARIO_COMMAND = """options = struct('verbose',true);
esc = main('data/IEEE118_escenario1.xlsx', ...
    'resultados_IEEE118_escenario1_matlab.xlsx',false,options);"""
COMPARE_COMMAND = """b = load_case_excel('data/IEEE118.xlsx');
e = load_case_excel('data/IEEE118_escenario1.xlsx');
a = compare_scenario1(b,e,base,esc,'comparacion_escenario1.xlsx');"""
GUI_COMMAND = """addpath('matlab');
app_flows"""


def make_story(e):
    b, s = e['base_methods'], e['scenario_methods']
    loss_b, loss_s = b[0]['Perdidas_P_MW'], s[0]['Perdidas_P_MW']
    loss_delta = loss_s-loss_b
    changes = e['comparison']['cambios_top5']
    outside_b = ', '.join(str(int(r['BUS_I'])) for r in e['comparison']['fuera_base'])
    outside_s = ', '.join(str(int(r['BUS_I'])) for r in e['comparison']['fuera_escenario'])
    slack_error = abs(b[0]['P_slack_MW']-e['reference_slack_p'])
    v = e['validation'][0]
    stories = []

    def add(title, section, kind, seconds, speech, cue, code='', **content):
        voice = f'[NOMBRE REAL — VOZ SECCIÓN {section}]'
        if not stories or stories[-1]['section_number'] != section:
            speech = [f'Soy {voice}. '+speech[0], *speech[1:]]
        stories.append(dict(title=title, section=SECTION_NAMES[section], section_number=section,
                            kind=kind, seconds=seconds, speech=speech, cue=cue, code=code,
                            voice=voice, appendix=False, case_number=118, **content))

    def ask(number, topic):
        add(f'Pregunta {number}: {topic}', 4, 'question', 15,
            [QUESTION_PROMPTS[number]],
            'Leer la pregunta completa, hacer una pausa y avanzar a la respuesta. No adelantar resultados.',
            question_number=number, question=QUESTION_PROMPTS[number])

    add('IEEE118 · Escenario 1: salida de la línea 26–30', 0, 'cover', 90, [
        'Presentamos el proyecto de flujos de potencia de MI-5215, segundo semestre de 2026. El equipo está integrado por [COMPLETAR TODOS LOS NOMBRES REALES]. Elegimos el escenario uno: retirar únicamente la línea 26–30 y comparar contra la red original.',
        'Vamos a explicar la configuración, describir IEEE118, ejecutar los tres métodos en el caso base, retirar la línea y cerrar con conclusiones numéricas. El programa usa MATLAB y exporta resultados a Excel. Cada integrante se identificará antes de explicar su parte; el reparto final de las voces todavía debe completarse con nuestros nombres.',
        'Las diapositivas y los PDF son apoyos estáticos. No son una grabación de las corridas. En el video mostraremos las ejecuciones completas, sin cortes ni acelerado, desde pulsar el botón o lanzar el comando hasta la exportación y la revisión del archivo generado.'
    ], 'Completar nombres y asignar secciones a TODOS los integrantes. Una persona puede cubrir varias secciones. Mostrar curso, proyecto y escenario; no inventar identidades.')

    add('Arquitectura: del Excel al Excel', 1, 'architecture', 60, [
        'Podemos entrar por app_flows.m, la interfaz gráfica, o por main.m, la consola. Ambos usan solve_power_flow y los mismos métodos propios: Newton-Raphson, Gauss-Seidel y desacoplado rápido. La interfaz añade el control de caso base, retirada de línea y comparación; no implementa otro solucionador.',
        'load_case_excel reconoce las hojas y columnas, obtiene nBus de la altura de la tabla y verifica los identificadores. build_ybus arma el modelo eléctrico. Cada solucionador es propio: MATPOWER solo se usa como referencia externa, no resuelve dentro de nuestros métodos.',
        'Para el video utilizamos la interfaz: primero Ejecutar métodos con toda la red y después Retirar línea 26–30. Dejamos visible también la consola MATLAB, donde se imprime el desajuste de cada iteración. Mostramos app_flows.m, los métodos compartidos y export_results_excel; main sigue disponible como alternativa reproducible por comandos.'
    ], 'Mostrar matlab/app_flows.m: run_case, run_outage y restore_base; luego load_case_excel.m, solve_power_flow.m y export_results_excel. No sustituir el código por capturas antiguas.')

    add('Entradas y unidades: cuatro hojas, base 100 MVA', 1, 'inputs', 75, [
        'Hay dos libros de entrada: IEEE118.xlsx para el caso base e IEEE118_escenario1.xlsx para la copia sin la línea. Cada uno tiene cuatro hojas. config contiene baseMVA igual a cien; bus incluye identificador, TYPE, PD, QD, VM, VA, tensión nominal y compensación GS y BS. No hay una hoja independiente de compensación: está incorporada en bus.',
        'gen relaciona cada unidad con su barra e incluye PG, QG, VG, límites de reactiva, límites de activa y STATUS. branch identifica los dos extremos, resistencia, reactancia, carga capacitiva, tap, desfase y estado. Las potencias se ingresan en MW y MVAr; resistencia, reactancia y susceptancia de rama están en pu; VA y SHIFT están en grados.',
        'GS representa MW consumidos y BS MVAr inyectados a tensión de uno pu; el programa los divide por baseMVA al construir admitancias. TAP igual a cero significa relación unitaria. RATE_A igual a cero significa que no tenemos un límite térmico utilizable, no que la línea admita cualquier flujo.'
    ], 'Abrir config, bus, gen y branch en Excel. Señalar GS/BS en bus, VG/QMIN/QMAX en gen y STATUS/RATE_A/TAP/SHIFT en branch.')

    add('Clasificación y variables de estado', 1, 'bus_types', 45, [
        'TYPE igual a uno identifica PQ: conocemos P y Q y calculamos magnitud y ángulo. TYPE dos identifica PV: conocemos P y magnitud, y calculamos reactiva y ángulo. TYPE tres es la slack: fija magnitud y ángulo y ajusta P y Q para cerrar el balance.',
        'En este archivo tenemos 64 PQ, 53 PV y una slack, la barra 69. Los ángulos desconocidos están en las 117 barras no slack y las magnitudes desconocidas en las 64 PQ. La reactiva PV y las potencias de la slack no son ecuaciones de desajuste impuestas.',
        'Mostramos bus_sets.m y voltage_setpoints.m: las consignas de las barras reguladas vienen de VG de generadores activos. Los identificadores se mapean a posiciones internas; no se usa el número de barra como dimensión fija de la red.'
    ], 'Abrir matlab/bus_sets.m y voltage_setpoints.m. Identificar TYPE=3 en la fila de barra69, sin confundir fila Excel con identificador.')

    add('Ybus: modelo π, transformadores y shunts', 1, 'ybus', 90, [
        'En build_ybus.m se crea una matriz compleja de tamaño n, donde n es el número de identificadores leídos. Primero se suma GS más j BS, dividido entre la base, a cada diagonal. Después se recorren las ramas y se omiten las que tienen STATUS cero.',
        'Para cada rama, la admitancia serie es uno dividido entre R más j X. La susceptancia de carga se reparte en dos mitades, una a cada extremo del modelo pi. El tap complejo es su magnitud por la exponencial del desfase; si TAP es cero se reemplaza por uno.',
        'Las cuatro contribuciones son Yff, Yft, Ytf y Ytt. La diagonal de origen lleva el módulo del tap al cuadrado; los términos cruzados usan el tap conjugado o sin conjugar según el sentido. Estas cuatro entradas se acumulan en Ybus. No se borra ninguna barra al retirar una línea: basta con excluir su contribución de rama.',
        'Mostramos exactamente ese bloque y lo relacionamos con el cálculo de corrientes. Así verificamos que líneas, transformadores, desfase y compensación se incorporan al mismo modelo nodal.'
    ], 'En matlab/build_ybus.m mostrar desde ids/n hasta las cuatro sumas Ybus(i,i), Ybus(i,j), Ybus(j,i), Ybus(j,j). Detenerse en STATUS==0, charging y tap.')

    add('Newton-Raphson: corregir ángulos y magnitudes', 1, 'newton', 60, [
        'Los tres métodos buscan resolver S igual a V por el conjugado de Ybus V. El vector de desajustes contiene P especificada menos calculada en barras no slack y Q especificada menos calculada en PQ. Se acepta cuando su norma infinito es menor o igual a diez a la menos ocho pu.',
        'Newton-Raphson construye el Jacobiano completo con los bloques de sensibilidad de P y Q respecto de ángulos y magnitudes. Resuelve J por corrección igual a desajuste usando la barra invertida de MATLAB; no calcula una inversa explícita.',
        'Se actualizan los ángulos no slack y las magnitudes PQ, se recalcula el modelo AC y se repite hasta cumplir la tolerancia o alcanzar mil iteraciones. La slack y las magnitudes reguladas no se actualizan como incógnitas. El código también detecta errores no finitos o magnitudes no positivas; pocas iteraciones no garantizan convergencia desde cualquier arranque.'
    ], 'Abrir matlab/power_mismatch.m y solve_newton_raphson.m. Mostrar J, correction = J\\mis, actualizaciones y log_powerflow_iteration.')

    add('Gauss-Seidel: barrido con relajación 1,5', 1, 'gauss', 60, [
        'Gauss-Seidel calcula una tensión por vez usando los valores más recientes disponibles. En una barra PQ usa P y Q especificadas; en una PV estima Q a partir del estado actual y después restituye la magnitud VG. La barra slack permanece fija.',
        'El candidato se obtiene de la ecuación nodal despejando la tensión. Aplicamos relajación: valor anterior más uno coma cinco veces la diferencia entre candidato y anterior. Ese valor nuevo queda inmediatamente disponible para las siguientes barras del barrido.',
        'Después de un barrido completo se calcula el mismo desajuste AC que en Newton. No basta con que la tensión cambie poco. Usamos tolerancia de diez a la menos ocho y máximo mil barridos para estos casos. La consola muestra también el estado inicial, iteración cero, que no se cuenta como corrección. Este método hace operaciones más sencillas por paso, pero puede requerir muchos más pasos.'
    ], 'Abrir matlab/solve_gauss_seidel.m: q_i, sumOther, candidate, updated, normalización PV, cálculo err y registro de cada barrido.')

    add('Desacoplado rápido: dos sistemas secuenciales', 1, 'decoupled', 50, [
        'El tercer método es desacoplado rápido. Aproxima la relación entre potencia activa y ángulo con B prima, y entre reactiva y magnitud con B doble prima. Las matrices se forman antes del bucle y se reducen a las variables que realmente cambian.',
        'Primero resuelve la corrección de ángulo a partir de delta P dividido entre magnitud. Con el ángulo nuevo vuelve a calcular Q y obtiene la corrección de magnitud PQ. No son dos flujos independientes ni se utiliza el Jacobiano completo de Newton.',
        'La aceptación final se verifica con las ecuaciones AC completas y la misma tolerancia. La aproximación puede ser eficiente en transmisión, pero no garantiza buen comportamiento en cualquier red. En pantalla abrimos la formación de las matrices y luego las dos correcciones, para distinguir la aproximación del criterio de convergencia.'
    ], 'Mostrar matlab/fast_decoupled_matrices.m y solve_fast_decoupled.m: Bprime, Bdouble, dTheta, reevaluación Q, dVm y error final.')

    add('Parámetros comunes y alcance de los límites Q', 1, 'options', 45, [
        'main fija tolerancia uno por diez a la menos ocho, máximo mil iteraciones, relajación de Gauss-Seidel uno coma cinco y verbose verdadero. La condición inicial no es perfil plano: usa VM y VA del Excel, con VG de unidades activas en PV y slack.',
        'Existe una opción para aplicar límites Q. solve_power_flow puede resolver, evaluar Q y convertir una PV en PQ fijando la reactiva al límite; esto está implementado en apply_q_limits.m. En las corridas presentadas enforceQLimits es falso, igual que en la referencia de validación.',
        'Por tanto, no vamos a afirmar cumplimiento de límites reactivos. Tampoco la convergencia demuestra estabilidad dinámica o seguridad térmica. Mantenemos los mismos parámetros y el mismo arranque de datos entre base y escenario para que el efecto principal sea el retiro de la línea.'
    ], 'Mostrar matlab/main.m, initial_voltage.m y apply_q_limits.m. En resultados abrir parametros; distinguir función implementada de opción activada.')

    add('Resultados: flujos, pérdidas y potencia slack', 1, 'result_math', 25, [
        'calculate_branch_flows reutiliza el modelo de cada extremo: S desde es V desde por conjugado de I desde, multiplicado por baseMVA. La suma de las potencias de ambos extremos da la pérdida neta de rama.',
        'assemble_result reconstruye generación como inyección calculada más carga local; así obtiene P y Q de la slack. export_results_excel guarda entradas, parámetros, comparación, tablas de barras, ramas e historial por método. La pérdida Q neta puede ser negativa por la carga capacitiva: no es una pérdida resistiva negativa.'
    ], 'Localizar matlab/calculate_branch_flows.m, assemble_result.m, result_comparison.m y export_results_excel.m; señalar P_calc + PD y Q_calc + QD.')

    add('Versatilidad: corrida breve IEEE14', 1, 'small_run', 30, [
        'Ahora cambiamos únicamente el archivo a IEEE14. Ejecutamos los tres métodos y dejamos visible la consola hasta que aparece la ruta del Excel exportado. Esta comprobación debe durar menos de un minuto; el objetivo es demostrar que el tamaño lo determina la entrada, no comparar otra red en detalle.',
        'Abrimos la salida recién generada y verificamos catorce barras y las hojas de los tres métodos. Si en este equipo tarda más, no aceleramos la grabación: lo registramos, revisamos la preparación y repetimos la toma completa. IEEE118 sigue siendo el caso principal de toda la exposición.'
    ], 'Grabar desde Enter hasta exportación, sin cortes ni acelerado. Preparar MATLAB abierto, Excel de salida cerrado. No mostrar un log técnico como si fuera video.', SMALL_COMMAND)

    add('Caso base: datos exactos de nuestro archivo', 2, 'network_data', 90, [
        'Nuestra fuente es MATPOWER 8.1, archivo case118.m de formato versión dos, conservado en data/case118.m y convertido a data/IEEE118.xlsx. El encabezado documenta conversión CDF de octubre de 2014 y correcciones de transformadores de febrero de 2019. No se trata de una red operativa actual.',
        'El archivo contiene 118 barras, 186 ramas y 54 registros de generación activos; 99 barras tienen demanda activa o reactiva no nula. Hay once ramas codificadas como transformadores mediante TAP no cero y 175 con TAP cero. La slack es la barra 69.',
        'La demanda suma 4242 MW y 1438 MVAr. La generación activa programada de entrada suma 4377,4 MW, pero la generación resuelta cambia porque la slack cierra el balance. Los niveles principales son 138 y 345 kV; hay además una barra, la 87, de 161 kV. Mostramos esta excepción porque está en los datos que realmente utilizamos.',
        'Los límites de magnitud del archivo son 0,94–1,06 pu, mientras que el análisis exigido por la guía usa 0,95–1,05. Mantendremos separados ambos criterios.'
    ], 'Abrir data/case118.m (encabezado), data/IEEE118.xlsx, filtrar TYPE=3 y BASE_KV=161. Los conteos provienen del archivo, no del diagrama histórico.')

    add('Unifilar publicado: ubicación de las barras 26 y 30', 2, 'published_diagram', 120, [
        'Este sí es un unifilar publicado, no una topología generada por nosotros. La fuente es R. Christie, archivo de casos de prueba de la Universidad de Washington, mayo de 1993. El diagrama histórico corresponde al sistema AEP de diciembre de 1962.',
        'Primero recorremos la red completa y después ampliamos la región: la barra 26 es Tanners Creek y la barra 30 es Sorenson, ambas a 345 kV. No debemos confundir la barra 26 con W. Kamm. La identificación se verificó contra los nombres del CDF y case118. El resaltado y las etiquetas de color son propios, no forman parte del original. Conservamos el TIFF sin anotaciones y la cita con su enlace.',
        'En el Excel confirmamos que la rama 38 conecta F_BUS 26 con T_BUS 30 y que ambas barras están a 345 kV. No inferimos el estado del caso moderno solo por la apariencia del escaneo. El dibujo sirve para ubicar la intervención, mientras que impedancias, estados y tensiones del cálculo vienen del archivo MATPOWER.',
        'Antes de modificar nada, observamos que existen rutas alternativas alrededor de esa conexión. La distribución exacta de flujos se determina resolviendo nuevamente toda la red, no repartiendo aritméticamente el flujo perdido entre líneas vecinas.'
    ], 'Mostrar escenario1_assets/IEEE118_unifilar_UW.png y ampliar unifilar_region_26_30_anotado.png (corregido: 26 Tanners Creek abajo y 30 Sorenson arriba). Cita: README_FUENTES.md y fuente_unifilar.json. Resaltado propio, no original; contrastar contra rama38 y bus_name de case118.')

    add('Caso base: grabar los tres métodos de forma continua', 3, 'base_run', 180, [
        'Abrimos app_flows desde MATLAB. Dejamos IEEE-118, Todos, tolerancia uno por diez a la menos ocho, máximo mil iteraciones, relajación uno coma cinco y límites Q desactivados. Mostramos la entrada con todas las ramas activas. Retirar línea 26–30 está inicialmente deshabilitado.',
        'Iniciamos la grabación antes de pulsar Ejecutar métodos. Se ejecutan Newton-Raphson, Gauss-Seidel y desacoplado rápido; la consola muestra el máximo desajuste inicial y de cada iteración. Mantenemos la toma continua, sin cortes ni acelerado, hasta exportar y abrir el Excel base.',
        'Solo tras converger los tres métodos y exportarse el caso base se habilita Retirar línea 26–30. Todavía no lo pulsamos: primero revisamos los resultados base y su validación. La interfaz conserva ese resultado como referencia y rechaza una comparación si después cambiamos datos o parámetros.',
        'La captura mostrada es un apoyo estático de otra ejecución temporal; no sustituye la toma real. Las tablas siguientes provienen de los Excel de evidencia. Si cambia el tiempo en la nueva grabación, conservamos la medición real y regeneramos los materiales, sin fingir una duración idéntica.'
    ], 'Abrir app_flows, cerrar salidas en Excel e iniciar captura ANTES de pulsar Ejecutar métodos. Mantener hasta exportación y apertura. Mostrar consola con todas las iteraciones y el botón de retirada habilitado al final. No pulsarlo hasta la sección4.', GUI_COMMAND)

    add('Salida base: seguir una barra y una rama', 3, 'base_output', 45, [
        'En comparacion vemos convergencia, iteraciones, tiempo, desajuste final, pérdidas y potencia slack. En NR_bus buscamos la barra 69 y leemos magnitud, ángulo, P_gen_calculada y Q_gen_calculada. Para el caso base la slack entrega aproximadamente 513,863 MW y absorbe 82,424 MVAr: el signo negativo de Q indica absorción.',
        'En NR_branch mostramos P y Q de ambos extremos y sus pérdidas. Repetimos la ubicación de las hojas GS y FDLF y abrimos una hoja conv: allí queda el historial desde iteración cero. La salida preserva además las entradas usadas y los parámetros, lo cual permite rastrear qué se calculó.',
        'La potencia aparente no es potencia activa: usamos su módulo para ordenar ramas, pero las pérdidas activas se calculan sumando P de los dos extremos. Esta distinción será importante al explicar la redistribución.'
    ], 'Abrir resultados_IEEE118_matlab.xlsx: comparacion, parametros, NR_bus barra69, NR_branch rama38, GS_conv y FDLF_conv. No confundir VM inicial con VM_pu calculada.')

    add('Caso base: tabla comparativa de los tres métodos', 3, 'base_methods', 75, [
        f"Newton-Raphson convergió en {b[0]['Iteraciones']} correcciones, Gauss-Seidel en {b[1]['Iteraciones']} barridos y desacoplado rápido en {b[2]['Iteraciones']} pasos. Los tres desajustes finales son menores que uno por diez a la menos ocho pu; la tabla muestra también P slack y pérdidas activas y reactivas.",
        f"En esta ejecución los tiempos fueron {b[0]['Tiempo_s']:.4f}, {b[1]['Tiempo_s']:.4f} y {b[2]['Tiempo_s']:.4f} segundos, respectivamente. Son mediciones de una sola corrida: incluyen solución, ensamblado y escritura en consola si verbose está activo, pero excluyen lectura y exportación Excel y gráficas. No equivalen a la duración de la grabación completa.",
        'El desacoplado fue el más rápido en esta medición, aunque Newton necesitó menos iteraciones. El costo por iteración, el calentamiento de MATLAB y la consola influyen. La coincidencia entre métodos es una verificación interna; a continuación la contrastamos con una referencia independiente.'
    ], 'Mostrar todos los campos de la tabla guía. Nombres completos: NR Newton-Raphson; GS Gauss-Seidel; FDLF desacoplado rápido. Fuente: resultados_IEEE118_matlab.xlsx / comparacion.')

    add('Validación externa: MATPOWER, caso base', 3, 'validation', 60, [
        'La validación externa conservada usa MATPOWER 8.1, Newton-Raphson de referencia, tolerancia diez a la menos diez y límites Q desactivados en ambos lados. Se verificaron las entradas de IEEE118 contra case118 oficial. Esta evidencia corresponde al caso base, no a una validación independiente nueva del escenario.',
        f"Para nuestro Newton, el error máximo de magnitud es {v['MaxAbsVMError_pu']:.3e} pu y el de ángulo {v['MaxAbsVAError_deg']:.3e} grados. La diferencia de pérdidas P es {v['AbsPLossError_MW']:.3e} MW. La diferencia actual de P slack frente a la referencia reconstruida es {slack_error:.3e} MW.",
        'Mostramos también los errores de Gauss-Seidel y desacoplado, que pasan los umbrales documentados. El resumen actualizado incluye errores de pérdidas P y Q y potencia P y Q de la slack. Como contraste adicional, reconstruimos la slack sumando flujos de referencia incidentes a barra 69 más su carga local. Los errores pequeños respaldan la solución ensayada, no acreditan límites térmicos o reactivos.'
    ], 'Abrir validacion_MATPOWER.xlsx / resumen (filtrar IEEE118), metadatos e IEEE118_NR_branch. Mostrar reconstrucción slack documentada en presentacion_assets/evidencia_video.json.')

    add('Referencia base: cinco barras de menor tensión', 3, 'base_low', 45, [
        'Estas son las cinco barras de menor tensión del caso base, ordenadas por magnitud calculada y no por VM de entrada. La más baja es la barra 76 con 0,943 pu. Siguen 53, 118, 55 y 107.',
        f'Con el intervalo de la guía, las barras fuera de rango son {outside_b}. Ya había tres antes de retirar la línea: no debemos atribuir todas las violaciones al escenario. Las barras 55 y 107, con 0,952 pu, todavía están por encima de 0,95.',
        'La barra 76 es PV y conserva la consigna de magnitud ingresada. Esto ilustra que converger no corrige automáticamente una consigna inferior al rango de evaluación. Guardamos esta referencia para distinguir problemas previos de los que aparecen después.'
    ], 'Fuente comparacion_escenario1.xlsx / base_top5_bajas y fuera_base. Mostrar tabla completa en Excel si se consulta; la diapositiva selecciona identificador, tipo, tensión y ángulo.')

    add('Referencia base: cinco ramas con mayor flujo aparente', 3, 'base_flows', 45, [
        'Ordenamos las ramas por S máximo, definido como el mayor módulo de potencia aparente entre los dos extremos. Así evitamos depender de la orientación con que se guardó la rama. La mayor es 9–10 con aproximadamente 452,886 MVA; siguen 8–9, 8–5, 38–37 y 30–17.',
        'La tabla muestra los dos módulos y el máximo utilizado. Es un ranking de flujo, no un ranking de porcentaje de carga térmica. Todas las tasas RATE_A del archivo son cero, de modo que no podemos afirmar sobrecarga ni holgura térmica con esta evidencia.',
        'Estas cinco ramas no tienen por qué ser las cinco que más cambian en la contingencia. Un ranking describe el tamaño del flujo base; el otro describirá la magnitud de la variación entre casos.'
    ], 'Fuente comparacion_escenario1.xlsx / base_top5_flujos. Mostrar S_from, S_to y S_max; explicar que Loading_percent vacío no es 0 % de carga.')

    add('Escenario 1: qué transportaba la línea 26–30', 4, 'outage_diagram', 90, [
        'Retiramos una sola línea: la rama 38, entre barras 26 Tanners Creek y 30 Sorenson de 345 kV. Volvemos al recorte corregido del unifilar publicado y localizamos ambos extremos, unidos por el enlace resaltado propio. No retiramos generadores, cargas, compensación de barras ni ninguna otra rama.',
        'En el caso base, desde el extremo 26 circulaban 223,711 MW y menos 11,460 MVAr. En el extremo 30 se registraban menos 219,733 MW y menos 36,572 MVAr, con la convención de inyección desde cada barra hacia la línea. Los módulos son 224,004 y 222,756 MVA.',
        'La diferencia activa entre extremos corresponde a 3,978 MW de pérdidas en esa línea. Al abrirla, sus flujos se vuelven cero; pero eso no significa que las pérdidas totales bajen: la red restante debe encontrar otra distribución y también cambia el soporte capacitivo de la rama.',
        'La potencia no se reparte como una suma escalar de variaciones MVA. Los módulos dependen de P, Q y del estado de tensión; por eso resolvemos nuevamente el flujo AC completo.'
    ], 'Mostrar comparacion_escenario1.xlsx / linea_retirada y el recorte UW. Los signos se refieren a inyección hacia la rama, no a dos demandas independientes.')

    add('Cambio único en Excel: branch!K39, STATUS = 0', 4, 'edit_input', 60, [
        'La copia se llama data/IEEE118_escenario1.xlsx; el archivo base permanece intacto. En branch buscamos F_BUS 26 y T_BUS 30. Es la rama 38, que aparece en la fila 39 porque la primera fila es el encabezado. La columna K es STATUS.',
        'Mostramos la fila resaltada y la celda K39 cambiada de uno a cero. El resto de los valores se conserva, incluidos R, X, BR_B, TAP, generadores y demandas. Mantener la fila facilita rastrear la misma rama entre las dos salidas.',
        'La copia ya está preparada: no editamos el Excel base ni otras celdas. Al pulsar Retirar línea 26–30, la interfaz comprueba que el único cambio sea STATUS y que la red permanezca conectada; la Ybus omite la rama completa, incluida su carga capacitiva. Cerramos ambos Excel de salida antes de pulsar el botón para evitar bloqueos.'
    ], 'Abrir base y copia lado a lado, branch fila39/K39. Mostrar resaltado real. El archivo ya existe: no recrear ni editar otras celdas durante la toma.')

    add('Escenario: corrida continua NR + GS + FDLF', 4, 'scenario_run', 150, [
        'Sin cerrar la interfaz ni cambiar sus parámetros, iniciamos otra toma continua y pulsamos Retirar línea 26–30. Se conserva la solución base y se resuelve la copia con STATUS cero usando NR, GS y desacoplado rápido, con las mismas opciones. La referencia base no se vuelve a calcular.',
        'Mantenemos la grabación desde pulsar el botón hasta la exportación y apertura de los Excel, sin cortar ni acelerar los 909 barridos de Gauss-Seidel. La consola imprime cada desajuste; en la interfaz se resalta la rama retirada y se abre Base vs. salida 26–30.',
        'La aplicación exporta el resultado del escenario y la comparación, y conserva el libro base de esa misma ejecución. En entrada_branch verificamos STATUS cero y en NR_branch el flujo cero de la rama38. Los dos libros de entrada más los dos de resultados y el comparativo suman cinco Excel para este estudio.',
        'Volver al caso base recupera la red con la línea activa y sus resultados guardados sin otra corrida. Cambiar datos, archivo, método o parámetros invalida la referencia y exige resolver otra vez el caso base; así evitamos mezclar ejecuciones. main y run_video_project siguen disponibles como alternativas por consola.'
    ], 'Iniciar captura ANTES de pulsar Retirar línea 26–30. Mantener hasta exportación y apertura; mostrar STATUS=0, pestañas de comparación y cambios de flujo. No ejecutar compare_scenario1 manualmente: la GUI ya exporta la comparación.')

    add('Comparación obligatoria: base frente a escenario', 4, 'scenario_comparison', 90, [
        'La tabla utiliza Newton-Raphson para las magnitudes eléctricas y toma las iteraciones de cada método. La tensión mínima pasa de 0,943 pu en barra 76 a 0,940040 pu en barra 21. La máxima sigue en 1,05 pu en barra 10. Las identificaciones de barra se presentan en filas separadas: restar sus números no tendría significado físico.',
        f'La P slack aumenta de {b[0]["P_slack_MW"]:.3f} a {s[0]["P_slack_MW"]:.3f} MW. Su Q cambia de {b[0]["Q_slack_MVAr"]:.3f} a {s[0]["Q_slack_MVAr"]:.3f} MVAr: continúa absorbiendo reactiva, pero absorbe menos. Las pérdidas activas aumentan {loss_delta:.3f} MW.',
        'Newton pasa de tres a cuatro correcciones y Gauss-Seidel de 757 a 909 barridos. La columna diferencia es escenario menos base. La caída del mínimo global no es la caída de una misma barra: el punto que determina ese mínimo cambió de ubicación.',
        'Las seis barras fuera del intervalo impiden calificar el caso como aceptable según el criterio de tensión de la guía, aunque el flujo converge.'
    ], 'Mostrar Base vs. salida 26–30 en la GUI y comparacion_escenario1.xlsx / comparacion. Leer unidades y Diferencia=Escenario−Base. Volver al caso base restaura el snapshot sin recalcular. No restar identificadores ni mezclar con corridas de consola.')

    ask(1, 'redistribución de potencia')
    add('Respuesta 1: cinco mayores cambios, incluida la retirada', 4, 'branch_changes', 75, [
        f"El mayor aumento aparece en {int(changes[0]['Desde'])}–{int(changes[0]['Hasta'])}: de {changes[0]['S_base_MVA']:.3f} a {changes[0]['S_escenario_MVA']:.3f} MVA, un incremento de {changes[0]['Delta_MVA']:.3f} MVA o {changes[0]['Delta_pct']:.2f} por ciento. También aumentan 23–25 en 135,984 MVA, 25–27 en 87,077 y 32–113 en 50,279 MVA.",
        'En cambio 30–17 baja 120,115 MVA, es decir 48,20 por ciento. La reducción confirma que no todas las ramas reciben más flujo. Estos cambios muestran rutas alternativas alrededor de las barras intervenidas y efectos que se extienden por la red.',
        'El ranking global exigido incluye la línea retirada: 26–30 pasa de 224,004 MVA a cero, un cambio de menos cien por ciento, y encabeza la tabla. Le siguen 26–25, 23–25, 30–17 y 25–27. En otra hoja mostramos cinco ramas que siguen activas para analizar la redistribución, incluida 32–113. Ambos rankings ordenan por el cambio absoluto de máximo módulo entre extremos; el porcentaje usa el flujo base de cada rama.',
        'Esto responde hacia dónde se redistribuyó el esfuerzo de transporte sin confundir variación de módulo aparente con transferencia activa conservada.'
    ], 'Fuente cambios_top5_total (global, incluye retirada), cambios_top5 (complementario, cinco ramas activas) y cambios_ramas. Mostrar MVA y porcentajes con signos; no sumar diferencias MVA como MW.', question_number=1)

    ask(2, 'tensiones fuera de rango')
    add('Respuesta 2: seis barras fuera de 0,95–1,05 pu', 4, 'voltage_change', 60, [
        f'Antes estaban fuera de rango las barras {outside_b}. Después están {outside_s}. Aparecen tres violaciones nuevas: 20, 21 y 22. Todas son por tensión menor que 0,95 pu; la máxima se mantiene en el límite superior, no por encima.',
        'La mínima del escenario es 0,940040 pu en barra 21, apenas por encima del límite inferior de 0,94 del archivo, pero por debajo del criterio de 0,95 de la guía. El gráfico superpone perfiles de ambos casos con la franja de evaluación explícita.',
        'No decimos que hubo colapso: los tres métodos encontraron solución. Tampoco que la operación es aceptable: hay seis incumplimientos del rango solicitado. La barra 76 sigue en su consigna PV baja; no todas las bajas son provocadas por el retiro. El diagnóstico distingue condiciones previas y deterioro adicional.'
    ], 'Mostrar perfil y fuera_base/fuera_escenario completos. Criterio con margen numérico 1e−8 pu, extremos inclusivos; 1,05 pu no se cuenta como violación.', question_number=2)

    ask(3, 'cambio en las pérdidas')
    add('Respuesta 3: aumentan las pérdidas, no disminuyen', 4, 'loss_change', 75, [
        f'Las pérdidas activas suben de {loss_b:.3f} a {loss_s:.3f} MW, un aumento de {loss_delta:.3f} MW o {100*loss_delta/loss_b:.2f} por ciento. Como las cargas y las potencias activas programadas de unidades no slack no cambian y GS es cero, el incremento de P slack coincide con ese incremento de pérdidas.',
        'La línea retirada disipaba 3,978 MW, pero al abrirla cambia la distribución de corriente por otras rutas y desaparece su carga capacitiva. En el modelo las pérdidas resistivas dependen de R por el módulo de corriente al cuadrado. El aumento en las ramas restantes domina el ahorro de esa línea: el total de esas otras ramas crece aproximadamente 37,013 MW.',
        'Esta explicación es consistente con el flujo AC y sus pérdidas; no implica que cada rama aumente ni prueba causalidad aislada de un solo efecto reactivo. La pérdida Q neta continúa negativa por los términos capacitivos, pero se hace menos negativa. No la interpretamos como pérdida activa ni como eficiencia mayor que cien por ciento.'
    ], 'Comparar sumas P_loss de los libros. Mostrar linea_retirada P_loss=3,978115 y el incremento neto de otras ramas. No atribuir todo solo a distancia o solo a BR_B.', question_number=3)

    add('Métodos en escenario: precisión y esfuerzo', 4, 'scenario_methods', 60, [
        f"El escenario converge con Newton en {s[0]['Iteraciones']} pasos, con Gauss-Seidel en {s[1]['Iteraciones']} y con desacoplado en {s[2]['Iteraciones']}. Los tres cumplen el mismo objetivo de desajuste y coinciden en slack y pérdidas a la precisión mostrada.",
        f"Los tiempos medidos son {s[0]['Tiempo_s']:.4f}, {s[1]['Tiempo_s']:.4f} y {s[2]['Tiempo_s']:.4f} segundos. No usamos que Newton sea más rápido aquí que en el caso base para afirmar que la contingencia simplifica el problema: intervienen arranque de MATLAB, caché y salida de consola. Una corrida no es un benchmark estadístico.",
        'Los tres métodos requirieron más iteraciones que en base, especialmente Gauss-Seidel. Esto demuestra convergencia para estas dos condiciones, no robustez universal ante otras salidas ni una evaluación dinámica. La validación externa mostrada sigue siendo la del caso base; la concordancia entre los tres métodos en escenario es un control interno adicional.'
    ], 'Fuente resultados_IEEE118_escenario1_matlab.xlsx / comparacion y escenario_metodos. No reutilizar tiempos antiguos de otros casos.')

    add('Conclusiones numéricas y recomendación', 5, 'conclusions', 90, [
        'Primera conclusión: Newton requiere tres y cuatro pasos; Gauss-Seidel, 757 y 909; desacoplado, nueve y once. Todos cumplen uno por diez a la menos ocho pu. El desacoplado registra el menor tiempo en estas dos mediciones, pero la comparación temporal es descriptiva, no una garantía general.',
        f'Segunda: el retiro de 26–30 aumenta las pérdidas {loss_delta:.3f} MW, aproximadamente {100*loss_delta/loss_b:.2f} por ciento, y eleva la P slack a {s[0]["P_slack_MW"]:.3f} MW. La rama 26–25 incrementa su flujo máximo en 223,362 MVA, un 240,61 por ciento.',
        'Tercera: las barras fuera de 0,95–1,05 pasan de tres a seis y la mínima llega a 0,940040 pu en barra 21. Es un estado convergente pero no aceptable por el criterio de tensión indicado; no observamos colapso numérico y no podemos certificar factibilidad térmica porque RATE_A es cero.',
        'Recomendamos revisar soporte reactivo y consignas en la zona 20–22, estudiar redespacho y rutas alternativas, y repetir el análisis con límites Q activados y capacidades térmicas verificadas. Son estudios recomendados, no soluciones correctivas ya demostradas ni una afirmación de seguridad N menos uno.'
    ], 'Cada conclusión debe conservar su cifra y su alcance. No llamar operación segura al solo hecho de converger. Recomendaciones requieren nuevas corridas no incluidas.')

    add('Cierre: evidencia y entrega del video real', 5, 'closing', 60, [
        'Entregamos el programa, la presentación con notas, las entradas y salidas de los dos casos y el libro de comparación. La referencia externa y la fuente del unifilar quedan identificadas para que el profesor pueda rastrear cada afirmación.',
        'Antes de entregar completaremos los nombres y la participación de todos, ensayaremos la duración y grabaremos el MP4 real en resolución mínima 1080p, con audio claro y sin música que tape las voces. La meta de este recorrido es 35 minutos y 45 segundos, dentro de los 30 a 40 exigidos; todavía no es una duración ensayada ni medida de un video.',
        'Solo editaremos entre secciones, nunca dentro de una corrida. Los PDF, las miniaturas y los logs técnicos no acreditan esa grabación. La entrega también requiere el informe en Word y verificar el acceso si el video se sube a una carpeta institucional. Muchas gracias.'
    ], 'Pendiente real: completar identidades y reparto, ensayo, MP4 continuo 1080p con voces, verificar informe Word y subida un día antes de exposición. Fuentes completas y checklist en PRESENTACION.md. No afirmar que el video ya fue entregado.')

    assert tuple(sum(x['seconds'] for x in stories if x['section_number']==k) for k in range(6)) == SECTION_SECONDS
    assert len(stories) == EXPECTED_SLIDES
    return stories
