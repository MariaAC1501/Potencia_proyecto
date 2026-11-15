"""Read-only evidence -> complete technical report in MD, PDF and real Word.

Run: python tools/build_video_report.py (or the compatible tools/build_report.py).
Requires openpyxl, numpy, matplotlib, PyMuPDF, python-docx and Typst on PATH.
Never runs MATLAB, rewrites Excel, captures a desktop or builds presentations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from PIL import Image

import pymupdf
from openpyxl import load_workbook
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import build_report as legacy
from presentation_data import ROOT, METHODS, NAMES, method_code, rows, fingerprint

ASSETS = ROOT / 'informe_assets'
SOURCE = ROOT / 'INFORME_PROYECTO_MATLAB.md'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b, message, tolerance=1e-6):
    require(isinstance(a, (int, float)) and not isinstance(a, bool)
            and math.isfinite(a) and math.isclose(a, b, abs_tol=tolerance, rel_tol=1e-10), message)


def book_data(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return {name: rows(book, name) for name in book.sheetnames}
    finally:
        book.close()


def method_table(records):
    records = {method_code(r['Metodo']): r for r in records}
    require(set(records) == set(METHODS), 'Se requieren tres métodos únicos.')
    return legacy.table(
        ['Método', 'Iter.', 'Tiempo (s)', 'Mismatch (pu)', 'P slack (MW)', 'P ramas (MW)', 'Q ramas (MVAr)'],
        [[NAMES[m], r['Iteraciones'], f"{r['Tiempo_s']:.6f}", f"{r['Error_final_pu']:.3e}",
          f"{r['P_slack_MW']:.6f}", f"{r['Perdidas_P_MW']:.6f}", f"{r['Perdidas_Q_MVAr']:.6f}"]
         for m in METHODS for r in [records[m]]])


def smax(row):
    return max(row['S_from_MVA'], row['S_to_MVA'])


def analyze_evidence():
    paths = [ROOT / name for name in (
        'data/IEEE118.xlsx', 'data/IEEE118_escenario1.xlsx',
        'resultados_IEEE118_matlab.xlsx', 'resultados_IEEE118_escenario1_matlab.xlsx',
        'comparacion_escenario1.xlsx', 'validacion_MATPOWER.xlsx', 'validacion_MATPOWER.json',
        'escenario1_assets/ejecucion.json', 'escenario1_assets/entrada_escenario1.json',
        'escenario1_assets/fuente_unifilar.json', 'escenario1_assets/README_FUENTES.md',
        'escenario1_assets/IEEE118_unifilar_UW.png', 'escenario1_assets/IEEE118_unifilar_UW.tif',
        'escenario1_assets/unifilar_region_26_30.png',
        'escenario1_assets/perfil_escenario1.png', 'escenario1_assets/redistribucion_escenario1.png',
        'escenario1_assets/unifilar_region_26_30_anotado.png',
        'escenario1_assets/gui_caso_base.png', 'escenario1_assets/gui_salida_26_30.png',
        'escenario1_assets/captura_GUI_escenario1.json')]
    files = [fingerprint(path) for path in paths]
    base_input, scenario_input = [book_data(p) for p in paths[:2]]
    require(base_input.keys() == scenario_input.keys(), 'Hojas de entrada diferentes.')
    changes = []
    for name in base_input:
        require(len(base_input[name]) == len(scenario_input[name]), 'Cantidad de filas distinta.')
        for i, (a, b) in enumerate(zip(base_input[name], scenario_input[name]), 1):
            require(a.keys() == b.keys(), 'Encabezados de entrada diferentes.')
            changes.extend((name, i, col, a[col], b[col]) for col in a if a[col] != b[col])
    require(changes == [('branch', 38, 'STATUS', 1, 0)], f'No es un cambio único: {changes}')
    require({base_input['branch'][37]['F_BUS'], base_input['branch'][37]['T_BUS']} == {26, 30},
            'Rama retirada incorrecta.')
    styled = load_workbook(paths[1], read_only=False, data_only=True)
    try:
        require(styled['branch']['K39'].fill.fill_type == 'solid', 'STATUS no está resaltado.')
    finally:
        styled.close()
    base, scenario, comparison, validation = [book_data(p) for p in paths[2:6]]
    required = {'comparacion', 'base_top5_bajas', 'escenario_top5_bajas', 'base_top5_flujos',
                'escenario_top5_flujos', 'cambios_top5', 'cambios_top5_total', 'cambios_ramas', 'fuera_base',
                'fuera_escenario', 'linea_retirada', 'base_metodos', 'escenario_metodos'}
    require(required.issubset(comparison), 'Faltan hojas de comparación del escenario.')
    for data, input_data, prefix in ((base, base_input, 'base'), (scenario, scenario_input, 'escenario')):
        for name in ('bus', 'gen', 'branch'):
            # MATLAB normalizes optional column names such as RAMP_AGC -> RAMPAGC.
            canonical = lambda records: [{key.replace('_', '').upper(): value
                                         for key, value in row.items()} for row in records]
            require(canonical(data['entrada_' + name]) == canonical(input_data[name]),
                    'La salida no corresponde a su entrada.')
        require(data['config'] == input_data['config'], 'Base MVA no preservada.')
        require(data['comparacion'] == comparison[prefix + '_metodos'], 'Tabla de métodos desactualizada.')
        require(len(data['NR_bus']) == 118 and len(data['NR_branch']) == 186, 'Dimensiones incorrectas.')
        methods = {method_code(r['Metodo']): r for r in data['comparacion']}
        require(set(methods) == set(METHODS), 'Faltan métodos.')
        for method, record in methods.items():
            require(record['Convergio'] is True and 0 <= record['Error_final_pu'] <= 1e-8,
                    'Método no convergente.')
            history = data[method + '_conv']
            require([r['Iteracion'] for r in history] == list(range(record['Iteraciones'] + 1)),
                    'Historial incompleto.')
            close(history[-1]['Error_max_pu'], record['Error_final_pu'], 'Residual final inconsistente.', 1e-14)
            bus = data[method + '_bus']
            slack = next(r for r in bus if r['BUS_I'] == 69)
            for key, column in [('P_slack_MW', 'P_gen_calculada_MW'), ('Q_slack_MVAr', 'Q_gen_calculada_MVAr')]:
                close(record[key], slack[column], 'Slack inconsistente.')
            for key, column in [('Perdidas_P_MW', 'P_loss_MW'), ('Perdidas_Q_MVAr', 'Q_loss_MVAr')]:
                close(record[key], sum(r[column] for r in data[method + '_branch']), 'Pérdidas inconsistentes.')
        voltage = data['NR_bus']
        low = sorted(voltage, key=lambda r: (r['VM_pu'], r['BUS_I']))[:5]
        require([r['BUS_I'] for r in low] == [r['BUS_I'] for r in comparison[prefix + '_top5_bajas']],
                'Top5 de tensión incorrecto.')
        outside = [r for r in voltage if r['VM_pu'] < .95 - 1e-8 or r['VM_pu'] > 1.05 + 1e-8]
        require(outside == comparison['fuera_' + prefix], 'Lista fuera de rango incorrecta.')
        require(low == comparison[prefix + '_top5_bajas'], 'Valores top5 de tensión incorrectos.')
        topflows = sorted(data['NR_branch'], key=smax, reverse=True)[:5]
        require([r['Rama'] for r in topflows] == [r['Rama'] for r in comparison[prefix + '_top5_flujos']],
                'Top5 de flujos incorrecto.')
        for actual, record in zip(topflows, comparison[prefix + '_top5_flujos']):
            require(all(record.get(key) == value for key, value in actual.items()),
                    'Datos de rama en top5 diferentes de la salida.')
            close(record['S_max_MVA'], smax(record), 'No se usó máximo de ambos extremos.')
    bf, sf = [{r['Rama']: r for r in data['NR_branch']} for data in (base, scenario)]
    require(len(comparison['cambios_ramas']) == 186, 'Faltan cambios de ramas.')
    for key in ('P_from_MW', 'Q_from_MVAr', 'S_from_MVA', 'P_to_MW', 'Q_to_MVAr', 'S_to_MVA'):
        close(sf[38][key], 0, 'Flujo no nulo en línea retirada.', 1e-12)
    for r in comparison['cambios_ramas']:
        close(r['S_base_MVA'], smax(bf[r['Rama']]), 'S base incorrecta.')
        close(r['S_escenario_MVA'], smax(sf[r['Rama']]), 'S escenario incorrecta.')
        close(r['Delta_MVA'], r['S_escenario_MVA'] - r['S_base_MVA'], 'Delta incorrecto.')
        close(r['Abs_delta_MVA'], abs(r['Delta_MVA']), 'Valor absoluto incorrecto.')
        if r['S_base_MVA'] > 1e-9:
            close(r['Delta_pct'], 100 * r['Delta_MVA'] / r['S_base_MVA'], 'Porcentaje incorrecto.')
    top = sorted([r for r in comparison['cambios_ramas'] if r['Rama'] != 38],
                 key=lambda r: r['Abs_delta_MVA'], reverse=True)[:5]
    require(top == comparison['cambios_top5'], 'Top5 activo no excluye retirada o tiene orden incorrecto.')
    global_top = sorted(comparison['cambios_ramas'],key=lambda r:(-r['Abs_delta_MVA'],r['Rama']))[:5]
    require(global_top == comparison['cambios_top5_total'], 'Top5 global incorrecto: debe incluir la retirada.')
    require(comparison['linea_retirada'][0]['Rama'] == 38, 'Flujo retirado incorrecto.')
    for key in bf[38]:
        if isinstance(bf[38][key], (int, float)):
            close(comparison['linea_retirada'][0][key], bf[38][key], 'Flujo de línea retirada distinto.')
    bnr, snr = [next(r for r in d['comparacion'] if method_code(r['Metodo']) == 'NR') for d in (base, scenario)]
    numeric_rows = []
    for d, record, prefix in ((base, bnr, 'base'), (scenario, snr, 'escenario')):
        v = d['NR_bus']; low = min(v, key=lambda r: r['VM_pu']); high = max(v, key=lambda r: r['VM_pu'])
        methods = {method_code(r['Metodo']): r for r in d['comparacion']}
        numeric_rows.append([low['VM_pu'], low['BUS_I'], high['VM_pu'], high['BUS_I'],
                             len(comparison['fuera_' + prefix]), record['P_slack_MW'], record['Q_slack_MVAr'],
                             record['Perdidas_P_MW'], methods['NR']['Iteraciones'], methods['GS']['Iteraciones'],
                             record['Perdidas_Q_MVAr']])
    require(len(comparison['comparacion']) == len(numeric_rows[0]), 'Contrato de tabla obligatoria cambió.')
    for i, row in enumerate(comparison['comparacion']):
        close(row['Caso_base'], numeric_rows[0][i], 'Tabla: base inconsistente.')
        close(row['Escenario'], numeric_rows[1][i], 'Tabla: escenario inconsistente.')
        if i not in (1, 3):
            close(row['Diferencia'], numeric_rows[1][i] - numeric_rows[0][i], 'Tabla: diferencia inconsistente.')
    external = [r for r in validation['resumen'] if str(r['Case']).replace('-', '') == 'IEEE118']
    require(len(external) == 3 and all(r['Passed'] for r in external), 'Validación IEEE118 no aprobada.')
    # The added reference columns are optional until the external validator is rerun.
    optional = ('AbsQLossError_MVAr', 'AbsSlackPError_MW', 'AbsSlackQError_MVAr')
    missing = [key for key in optional if any(r.get(key) is None for r in external)]
    own_methods = {method_code(r['Metodo']): r for r in base['comparacion']}
    for reference in external:
        own = own_methods[method_code(reference['Method'])]
        for error, ref, col in (
            ('AbsPLossError_MW', 'ReferencePLoss_MW', 'Perdidas_P_MW'),
            ('AbsQLossError_MVAr', 'ReferenceQLoss_MVAr', 'Perdidas_Q_MVAr'),
            ('AbsSlackPError_MW', 'ReferenceSlackP_MW', 'P_slack_MW'),
            ('AbsSlackQError_MVAr', 'ReferenceSlackQ_MVAr', 'Q_slack_MVAr')):
            if reference.get(error) is not None and reference.get(ref) is not None:
                close(reference[error], abs(own[col] - reference[ref]), 'Error externo no corresponde a la salida.', 1e-9)
                require(0 <= reference[error] <= 1e-4, 'Diferencia externa fuera del umbral.')
    capture = json.loads((ROOT/'escenario1_assets/captura_GUI_escenario1.json').read_text(encoding='utf-8'))
    require(capture['temporaryExportsOnly'], 'Las capturas GUI deben aislar sus exportaciones.')
    for captured, stored in ((capture['base'],base['comparacion']), (capture['scenario'],scenario['comparacion'])):
        require(len(captured) == len(stored) == 3, 'Captura GUI incompleta.')
        for a,b in zip(captured,stored):
            require(a['Iteraciones'] == b['Iteraciones'], 'Captura GUI de otra solución.')
            close(a['PerdidasPMW'],b['Perdidas_P_MW'],'La captura GUI no corresponde al caso documentado.')
    source = json.loads(paths[9].read_text(encoding='utf-8'))
    require(hashlib.sha256(paths[12].read_bytes()).hexdigest() == source['sha256_tif'], 'Unifilar original alterado.')
    for original, path in zip(files, paths):
        require(original == fingerprint(path), f'La evidencia cambió durante la lectura: {path.name}')
    return {'base': base, 'scenario': scenario, 'input': base_input, 'comparison': comparison,
            'external': external, 'missing_external': missing, 'numeric_rows': numeric_rows,
            'files': files, 'changes': changes, 'checks': [
                'Único cambio de entrada branch!K39: STATUS 1 -> 0; resaltado verificado',
                'Entradas exportadas y base MVA coinciden con sus libros originales',
                'Tres métodos convergentes por caso; historiales completos y slack verificada',
                'Sumas de pérdidas P/Q contrastadas con todas las ramas',
                'Tabla obligatoria contrastada con las salidas NR y contadores NR/GS',
                'Top5 de tensiones, flujos, cambios y listas fuera de rango recalculados',
                'S máxima de ambos extremos; retirada separada; porcentajes contrastados',
                'SHA256 del TIFF publicado coincide con fuente_unifilar.json']}


def scenario_section(e):
    b, s, c, inp = e['base'], e['scenario'], e['comparison'], e['input']
    nv = e['numeric_rows']; top = c['cambios_top5']; removed = c['linea_retirada'][0]
    labels = ['Tensión mínima (pu) y barra', 'Tensión máxima (pu) y barra', 'Barras fuera de 0,95–1,05 pu',
              'P de la barra slack 69 (MW)', 'Q de la barra slack 69 (MVAr)', 'Pérdidas totales (MW)',
              'Iteraciones Newton-Raphson', 'Iteraciones Gauss-Seidel']
    table_rows = [[labels[0], f'{nv[0][0]:.6f} (barra {nv[0][1]})', f'{nv[1][0]:.6f} (barra {nv[1][1]})', f'{nv[1][0]-nv[0][0]:+.6f} pu; 76 → 21'],
                  [labels[1], f'{nv[0][2]:.6f} (barra {nv[0][3]})', f'{nv[1][2]:.6f} (barra {nv[1][3]})', '0,000000 pu; misma barra']]
    for label, i in zip(labels[2:], (4, 5, 6, 7, 8, 9)):
        fmt = (lambda x: str(int(x))) if i in (4, 8, 9) else (lambda x: f'{x:.6f}')
        table_rows.append([label, fmt(nv[0][i]), fmt(nv[1][i]), f'{nv[1][i]-nv[0][i]:+d}' if i in (4, 8, 9) else f'{nv[1][i]-nv[0][i]:+.6f}'])
    low_table = lambda prefix: legacy.table(['Barra', 'Tensión (pu)', 'Ángulo (°)'], [
        [r['BUS_I'], f"{r['VM_pu']:.6f}", f"{r['VA_deg']:.6f}"] for r in c[prefix + '_top5_bajas']])
    flow_table = lambda prefix: legacy.table(['Rama', 'Desde–Hasta', 'S desde (MVA)', 'S hasta (MVA)', 'S máxima (MVA)'], [
        [r['Rama'], f"{r['Desde']}–{r['Hasta']}", f"{r['S_from_MVA']:.6f}", f"{r['S_to_MVA']:.6f}", f"{r['S_max_MVA']:.6f}"]
        for r in c[prefix + '_top5_flujos']])
    change_table = lambda records: legacy.table(['Rama', 'Desde–Hasta', 'Base (MVA)', 'Escenario (MVA)', 'Δ MVA', 'Δ %'], [
        [r['Rama'], f"{r['Desde']}–{r['Hasta']}", f"{r['S_base_MVA']:.6f}", f"{r['S_escenario_MVA']:.6f}",
         f"{r['Delta_MVA']:+.6f}", f"{r['Delta_pct']:+.3f}"] for r in records])
    outside_table = legacy.table(['Caso', 'Barra', 'VM (pu)', 'Desviación respecto a 0,95 (pu)'], [
        [title, r['BUS_I'], f"{r['VM_pu']:.6f}", f"{r['VM_pu']-.95:+.6f}"]
        for prefix, title in [('base', 'Base'), ('escenario', 'Escenario 1')] for r in c['fuera_' + prefix]])
    errors = ('MaxAbsVMError_pu', 'MaxAbsVAError_deg', 'AbsPLossError_MW')
    headers = ['Método', 'Error VM (pu)', 'Error VA (°)', 'Error P pérdidas (MW)']
    for key, title in [('AbsQLossError_MVAr', 'Error Q ramas (MVAr)'), ('AbsSlackPError_MW', 'Error P slack (MW)'), ('AbsSlackQError_MVAr', 'Error Q slack (MVAr)')]:
        if key not in e['missing_external']:
            errors += (key,); headers.append(title)
    external = legacy.table(headers, [[NAMES[method_code(r['Method'])]] + [f'{r[k]:.3e}' for k in errors] for r in e['external']])
    reference_keys = ('ReferencePLoss_MW', 'ReferenceQLoss_MVAr', 'ReferenceSlackP_MW', 'ReferenceSlackQ_MVAr')
    reference_nr = next(r for r in e['external'] if method_code(r['Method']) == 'NR')
    absolute_reference = ''
    if all(isinstance(reference_nr.get(key), (int, float)) for key in reference_keys):
        absolute_reference = legacy.table(['Magnitud base', 'Propia NR', 'MATPOWER NR'], [
            [label, f'{nv[0][i]:.9f}', f'{reference_nr[key]:.9f}']
            for label, i, key in zip(('P pérdidas (MW)', 'Q neta ramas (MVAr)', 'P Slack 69 (MW)', 'Q Slack 69 (MVAr)'),
                                     (7, 10, 5, 6), reference_keys)])
    external_note = ('**PENDIENTE de evidencia externa:** el resumen guardado aún no contiene ' + ', '.join('`'+k+'`' for k in e['missing_external']) + '. No se inventan esas diferencias: repetir la validación y regenerar el informe antes de declarar completa esa parte de la guía.'
                     if e['missing_external'] else 'Las diferencias de Q neta de ramas y P/Q de la slack están presentes en la validación externa y se muestran en la tabla. Las referencias absolutas se conservan en el resumen del Excel de validación.')
    delta_loss = nv[1][7] - nv[0][7]
    buses = inp['bus']; gen = [r for r in inp['gen'] if r['STATUS'] != 0]
    load_count = sum(r['PD'] != 0 or r['QD'] != 0 for r in buses)
    nonunity = sum(r['TAP'] not in (0, 1) for r in inp['branch'])
    lines = [
        '## 9. Escenario 1 de la guía: salida de la línea 26–30',
        '### 9.1. Caso base, fuente publicada y localización',
        f'La entrada es `data/IEEE118.xlsx`, cotejada con `data/case118.m` oficial de MATPOWER 8.1. Son {len(buses)} barras, {len(inp["branch"])} ramas ({nonunity} con tap no unitario y {len(inp["branch"])-nonunity} restantes), {len(gen)} registros de generadores activos y {load_count} barras con PD o QD no nulos. La Slack es la barra 69 y la base es 100 MVA. Carga total: {sum(r["PD"] for r in buses):.3f} MW y {sum(r["QD"] for r in buses):.3f} MVAr. Generación programada de entrada: {sum(r["PG"] for r in gen):.3f} MW y {sum(r["QG"] for r in gen):.3f} MVAr; QG=0 de entrada no impone Q=0 en PV/Slack. PG programada incluye 516,4 MW en la Slack; su generación resuelta es distinta porque cierra el balance.',
        'Los niveles nominales leídos son **138, 161 y 345 kV**: la barra 87 es de 161 kV. La guía destaca 138/345 kV, pero no debe ocultarse el nivel adicional presente en el archivo oficial. Las barras 26 y 30 sí son ambas de 345 kV.',
        '![Unifilar publicado por R. Christie, University of Washington, archivo IEEE-118, mayo de 1993; sistema AEP de diciembre de 1962. Fuente [5], escaneo original 118bus6.tif, no topología generada por el proyecto.](escenario1_assets/IEEE118_unifilar_UW.png)',
        '![Recorte del unifilar publicado con resaltado y etiquetas propios: barra 26 Tanners Creek y barra 30 Sorenson, ambas de 345 kV. Identificación verificada contra el CDF original UW; 26 no es W. Kamm. Se conservan TIFF original, recorte sin anotaciones, cita y hash en escenario1_assets.](escenario1_assets/unifilar_region_26_30_anotado.png)',
        'Fuente directa: https://labs.ece.uw.edu/pstca/pf118/118bus6.tif. Procedencia y advertencias: `escenario1_assets/README_FUENTES.md` y `fuente_unifilar.json`.',
        '### 9.2. Única modificación y opciones comunes',
        'Se conserva intacto el caso base. En `data/IEEE118_escenario1.xlsx`, hoja `branch`, **K39 (STATUS de la rama 38, 26–30) cambia de 1 a 0**, con resaltado amarillo/naranja. Ningún otro valor de ninguna hoja cambia; conservar la fila mantiene la identidad de las 186 ramas y deja 185 activas. No se retira generación, no se cambia carga ni se anulan capacitores de barras.',
        'La rama tiene R=0,00799 pu, X=0,086 pu y BR_B=0,908 pu. Ponerla fuera de servicio elimina tanto la admitancia serie como su carga capacitiva. No equivale a mantener su capacitor conectado.',
        'Ambos casos usan tolerancia 1e-8 pu, máximo 1000 iteraciones, relajación GS=1,5, inicialización VM/VA del Excel y VG activa (no perfil plano), límites Q desactivados. `main` muestra el mismatch de cada iteración con `verbose=true`. La evidencia de cálculo se conserva en `escenario1_assets/ejecucion.json` y su log; esa ejecución automatizada **no acredita una grabación continua ni voces del grupo**.',
        '### 9.3. Tres métodos: tabla exigida del caso base', method_table(c['base_metodos']),
        '### 9.4. Tres métodos en el escenario modificado', method_table(c['escenario_metodos']),
        'Los tiempos son observaciones guardadas, incluyen solución, ensamblado y escritura de consola cuando verbose está activo, y excluyen lectura/exportación Excel y gráficas. Sin repeticiones ni control del calentamiento no permiten afirmar que la contingencia sea más rápida por observar un tiempo NR menor.',
        '### 9.5. Tabla obligatoria base–escenario',
        legacy.table(['Variable', 'Caso base', 'Escenario 1', 'Diferencia'], table_rows, left=(0, 1, 2, 3)),
        'Referencia eléctrica: NR convergente; GS y FDLF sirven como contraste interno. El Excel `comparacion_escenario1.xlsx`, hoja `comparacion`, conserva valores numéricos y separa las barras de los extremos en filas propias: no se resta un identificador de barra como si fuera una magnitud física.',
        '### 9.6. Cinco barras de menor tensión y cinco ramas de mayor flujo',
        '**Cinco tensiones más bajas del caso base:**', low_table('base'),
        '**Cinco tensiones más bajas del escenario:**', low_table('escenario'),
        '**Cinco ramas de mayor potencia aparente del caso base:**', flow_table('base'),
        '**Cinco ramas de mayor potencia aparente del escenario:**', flow_table('escenario'),
        'Se usa **S máxima = max(S desde, S hasta)**, no solo el extremo de origen. MVA es magnitud aparente, no transferencia activa MW. `Loading_percent` del libro no es un criterio de ordenación para estas tablas; RATE_A=0 significa capacidad no disponible, no una capacidad física nula.',
        '### 9.7. Flujo de la línea retirada y cinco mayores cambios',
        legacy.table(['Extremo de la rama 26–30', 'P (MW)', 'Q (MVAr)', 'S (MVA)'], [
            ['Desde 26', f'{removed["P_from_MW"]:.6f}', f'{removed["Q_from_MVAr"]:.6f}', f'{removed["S_from_MVA"]:.6f}'],
            ['Desde 30', f'{removed["P_to_MW"]:.6f}', f'{removed["Q_to_MVAr"]:.6f}', f'{removed["S_to_MVA"]:.6f}']]),
        f'En el caso base transfiere {removed["P_from_MW"]:.6f} MW desde 26 y entrega {-removed["P_to_MW"]:.6f} MW a 30, con {removed["P_loss_MW"]:.6f} MW de pérdida propia y {removed["Q_loss_MVAr"]:.6f} MVAr netos. En el escenario todos sus flujos son cero (reducción de S máxima: −100 %). Se muestra aparte: no ocupa un puesto entre las cinco ramas activas con mayor cambio.',
        '**Cinco mayores cambios globales exigidos por la guía (incluida la línea retirada):**',
        change_table(c['cambios_top5_total']),
        'El ranking global corresponde a `cambios_top5_total`: 26–30, 26–25, 23–25, 30–17 y 25–27. La retirada encabeza el cambio absoluto (−224,004254 MVA, −100 %). No se la excluye del ranking solicitado.',
        '**Complemento: cinco ramas activas para estudiar la redistribución:**',
        change_table(top),
        'Las cinco filas complementarias se ordenan por |ΔS| en ramas activas en ambos casos; ΔS=S escenario−S base y Δ%=100·ΔS/S base. La reducción 30–17 forma parte del top5 por magnitud absoluta, aunque no es un aumento. Los porcentajes grandes sobre bases pequeñas no implican sobrecarga. Las sumas de MVA de estas ramas no son un balance conservativo de MW: cambian reactiva, pérdidas, signos y flujos de malla.',
        '![Perfil comparado base y salida de línea, con intervalo 0,95–1,05 pu de la guía.](escenario1_assets/perfil_escenario1.png)',
        '![Redistribución del flujo aparente: cinco ramas activas con mayor cambio, retirada separada.](escenario1_assets/redistribucion_escenario1.png)',
        '### 9.8. Respuestas numéricas a las tres preguntas del escenario',
        '**1. ¿Hacia qué líneas se redistribuyó la potencia y cuánto aumentó su flujo?** La salida elimina el camino 26–30. El enlace 26–25 (transformador con tap 0,96) aumenta de 92,833255 a 316,195271 MVA: **+223,362016 MVA (+240,606 %)**. Las ramas 23–25, 25–27 y 32–113 aumentan respectivamente **135,984080 MVA (+79,440 %)**, **87,077145 MVA (+59,382 %)** y **50,278581 MVA (+275,223 %)**. La rama 30–17 disminuye **120,114746 MVA (−48,204 %)**. Los flujos P/Q firmados de `NR_branch` permiten seguir el sentido real; las etiquetas Desde–Hasta no indican por sí solas dirección de transferencia.',
        '**2. ¿Alguna barra quedó fuera de 0,95–1,05 pu?** Sí. En base son **53, 76 y 118**; en escenario son **20, 21, 22, 53, 76 y 118**: tres adicionales y ninguna por encima de 1,05 pu. La mínima pasa de **0,943000 pu en 76** a **0,940040 pu en 21**. La barra 76 es PV con consigna 0,943 pu, de modo que su subtensión frente a la guía ya estaba programada; no todo incumplimiento lo produce la contingencia.',
        outside_table,
        'El conteo usa margen numérico 1e-8 pu en los bordes. No debe confundirse con VMIN=0,94 y VMAX=1,06 del Excel: ambos casos permanecen dentro de esos límites más amplios. Cumplir VMIN/VMAX no elimina los seis incumplimientos del intervalo exigido por la guía.',
        f'**3. ¿Aumentaron o disminuyeron las pérdidas y por qué?** Aumentan de **{nv[0][7]:.6f} a {nv[1][7]:.6f} MW**, esto es **+{delta_loss:.6f} MW (+{100*delta_loss/nv[0][7]:.3f} %)**. Aunque desaparecen los 3,978115 MW de pérdida propia de 26–30, la redistribución aumenta corrientes en otros caminos; las pérdidas resistivas dependen de I²R y del nuevo estado AC, no solo del número de líneas. La carga total y PG no Slack no cambian, y GS nodal es cero: por balance, el aumento de P Slack **+{nv[1][5]-nv[0][5]:.6f} MW** coincide con el aumento de pérdidas.',
        f'La suma Q neta de ramas cambia de **{nv[0][10]:.6f} a {nv[1][10]:.6f} MVAr** (Δ=+{nv[1][10]-nv[0][10]:.6f} MVAr). Es absorción inductiva menos aporte capacitivo de líneas, no disipación resistiva negativa. Al retirar la línea se pierde también su aporte capacitivo. Los BS de barras no cambian, pero sus aportes dependen de V²; la diferencia Q no se atribuye exclusivamente al capacitor retirado. La Slack pasa de {nv[0][6]:.6f} a {nv[1][6]:.6f} MVAr: sigue absorbiendo reactiva, aunque menos.',
        '### 9.9. Validación externa publicada del caso base',
        'Referencia independiente: solución AC NR de **MATPOWER 8.1, case118.m oficial**, con tolerancia 1e-10 pu y límites Q desactivados. No es una tabla publicada de tensiones copiada ni una comparación entre métodos propios: MATPOWER es el software publicado [1, 4] y su caso oficial la referencia reproducible. Los detalles barra por barra VM/VA se conservan en `validacion_MATPOWER.xlsx`.',
        external, absolute_reference, external_note,
        'Esta tabla valida el **caso base**, no certifica externamente el escenario: su contraste NR/GS/FDLF es interno. La validación completa y los umbrales se desarrollan en la sección 11 y `VALIDACION_EXTERNA.md`.',
        '### 9.10. Conclusiones, diagnóstico y recomendación',
        'Los tres métodos convergen en ambos estados con residual menor que 1e-8 pu. NR pasa de **3 a 4** iteraciones, GS de **757 a 909** y FDLF de **9 a 11**: la contingencia exige más pasos en los tres, pero esto solo demuestra robustez en esta perturbación e inicialización. Las tablas 9.3–9.4 documentan precisión y tiempos sin convertir iteraciones de distinto coste en unidades equivalentes.',
        'El escenario es **no aceptable respecto al criterio de tensión de la guía**: seis barras por debajo de 0,95 pu, mínima 0,940040 pu, y pérdidas +24,864 %. No se demuestra colapso de tensión, estabilidad dinámica ni sobrecarga térmica. RATE_A=0 en las ramas impide acreditar un margen térmico y los límites Q están desactivados; convergencia no equivale a factibilidad operativa.',
        'Recomendación: priorizar la restitución del corredor 26–30 cuando sea viable y estudiar regulación/soporte reactivo y redespacho en la zona 20–22. Antes de recomendar un tamaño de capacitor o declarar seguridad N-1, repetir con límites Q/P efectivos, capacidades térmicas válidas y análisis de estabilidad. Este estudio no dimensiona equipos ni calcula márgenes de colapso.',
        '### 9.11. Reproducción y frontera de la evidencia',
        'Desde una terminal: `python tools/prepare_scenario1.py`. En MATLAB, después de `addpath(\'matlab\')`: `study = run_video_project(false);`. Para regenerar solo los documentos, sin ejecutar MATLAB: `python tools/build_report.py` o `python tools/build_video_report.py`. Dependencias y comandos completos: `GUIA_USO_MATLAB.md` y `MATLAB_README.md`.',
        'Para el video se debe mostrar el código, ambos Excel de entrada y salida, y grabar cada corrida sin cortes ni aceleración desde el lanzamiento hasta la exportación. Las capturas, logs y pruebas automáticas no satisfacen ese requisito audiovisual. Nombres de integrantes, voces identificadas, MP4 1080p de 30–40 minutos y entrega al TEC Digital un día antes siguen **PENDIENTES humanos**, trazados individualmente en `CUMPLIMIENTO_GUIA_VIDEO.md`.'
    ]
    return '\n\n'.join(lines)


def render_equations(markdown):
    formulas = re.findall(r'^```math\s*\n(.*?)^```', markdown, flags=re.M | re.S)
    mathdir = ASSETS / 'ecuaciones'; mathdir.mkdir(exist_ok=True)
    typst = shutil.which('typst')
    require(typst is not None, 'Typst no está en PATH.')
    source = '#set page(width: 17cm, height: auto, margin: 8pt)\n#set text(size: 11pt)\n'
    source += '\n#pagebreak()\n'.join('$ ' + f.strip() + ' $' for f in formulas)
    template = mathdir / 'ecuaciones.typ'; template.write_text(source, encoding='utf-8')
    pdf = mathdir / 'ecuaciones.pdf'
    subprocess.run([typst, 'compile', str(template), str(pdf)], cwd=ROOT, check=True)
    images = []
    with pymupdf.open(pdf) as doc:
        require(len(doc) == len(formulas), 'No se renderizó una página por ecuación.')
        for i, page in enumerate(doc):
            path = mathdir / f'ecuacion_{i+1:02d}.png'
            page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(path)
            images.append((path, page.rect.width, page.rect.height))
    return images


def add_inline(paragraph, text):
    cursor = 0
    for match in re.finditer(r'`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*', text):
        paragraph.add_run(text[cursor:match.start()])
        run = paragraph.add_run(next(v for v in match.groups() if v is not None))
        if match.group(1) is not None:
            run.font.name = 'Consolas'; run.font.size = Pt(8)
        elif match.group(2) is not None:
            run.bold = True
        else:
            run.italic = True
        cursor = match.end()
    paragraph.add_run(text[cursor:])


def build_word(markdown):
    equations = iter(render_equations(markdown))
    doc = Document(); section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(2)
    normal = doc.styles['Normal']; normal.font.name = 'Calibri'; normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(6)
    section.header.paragraphs[0].text = 'MI-5215 · IEEE-118 · Caso base y escenario 1'
    footer = section.footer.paragraphs[0]; footer.alignment = 1
    footer.add_run('Página ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    doc.core_properties.title = 'Flujos de potencia IEEE-118 — caso base y escenario 1'
    doc.core_properties.author = 'Integrantes: PENDIENTE completar nombres reales'
    doc.add_heading('Flujos de potencia IEEE-118', 0)
    doc.add_paragraph('Caso base y escenario 1: salida de la línea 26–30 de 345 kV', 'Subtitle')
    doc.add_paragraph('MI-5215 · Análisis de Sistemas Eléctricos de Potencia · II semestre de 2026')
    doc.add_paragraph('Integrantes: PENDIENTE completar nombres reales.')
    doc.add_paragraph('Informe técnico completo. Los cálculos y documentos no constituyen el video exigido. MP4 1080p, participación del grupo, captura continua y entrega: PENDIENTES humanos.')
    doc.add_paragraph('Las ecuaciones se incluyen como imágenes renderizadas desde Typst; el resto del texto y las tablas son editables en Word.')
    doc.add_page_break()
    lines = markdown.splitlines(); i = 0; headings = []; image_count = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('<!--'):
            i += 1; continue
        if line.startswith('```'):
            language = line[3:].strip(); content = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                content.append(lines[i]); i += 1
            if language == 'math':
                path, width, height = next(equations)
                paragraph = doc.add_paragraph(); paragraph.alignment = 1
                paragraph.add_run().add_picture(str(path), width=Cm(17))
            else:
                for code_line in content:
                    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
                    run = p.add_run(code_line); run.font.name = 'Consolas'; run.font.size = Pt(8)
            i += 1; continue
        match = re.fullmatch(r'!\[(.*)\]\((.*)\)', line)
        if match:
            path = ROOT / match.group(2)
            # Fit tall scans on A4 rather than overflowing the printable area.
            with Image.open(path) as image:
                width, height = image.size
            w = min(17, 20 * width / height)
            doc.add_picture(str(path), width=Cm(w))
            add_inline(doc.add_paragraph(style='Caption'), match.group(1))
            image_count += 1; i += 1; continue
        if line.startswith('|'):
            cells = lambda value: [c.strip() for c in value.strip().strip('|').split('|')]
            header = cells(line); table = doc.add_table(rows=1, cols=len(header)); table.style = 'Light Shading Accent 1'
            for cell, value in zip(table.rows[0].cells, header):
                add_inline(cell.paragraphs[0], value)
            repeat = OxmlElement('w:tblHeader'); table.rows[0]._tr.get_or_add_trPr().append(repeat)
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                values = cells(lines[i]); require(len(values) == len(header), 'Tabla Word inconsistente.')
                for cell, value in zip(table.add_row().cells, values):
                    add_inline(cell.paragraphs[0], value)
                i += 1
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.size = Pt(7.5 if len(header) >= 6 else 8)
            doc.add_paragraph(); continue
        match = re.match(r'^(#{1,6}) (.+)$', line)
        if match:
            depth = len(match.group(1))
            if depth > 1:
                title = match.group(2); headings.append(title)
                add_inline(doc.add_heading(level=min(depth - 1, 4)), title)
            i += 1; continue
        match = re.match(r'^(?:- |\d+\. )(.+)$', line)
        p = doc.add_paragraph(style=('List Bullet' if line.startswith('- ') else 'List Number') if match else None)
        add_inline(p, match.group(1) if match else line)
        i += 1
    output = ROOT / 'INFORME_PROYECTO_MATLAB.docx'; doc.save(output)
    reopened = Document(output)
    text = '\n'.join(p.text for p in reopened.paragraphs)
    for title in headings:
        require(title in text, f'Falta encabezado Word: {title}')
    require(len(reopened.tables) >= 25, 'Se perdieron tablas del informe Word.')
    table_text = '\n'.join(cell.text for table in reopened.tables for row in table.rows for cell in row.cells)
    for value in ('165.897686', '546.897686', '0.940040', '223.362016'):
        require(value in table_text, f'Falta cifra del escenario en tablas Word: {value}')
    require(len(reopened.inline_shapes) == image_count + len(re.findall(r'^```math', markdown, re.M)),
            'Faltan imágenes o ecuaciones en Word.')
    with zipfile.ZipFile(output) as archive:
        require(archive.testzip() is None and 'word/document.xml' in archive.namelist(), 'DOCX no válido.')
    return {'tables': len(reopened.tables), 'headings': len(headings),
            'figures': image_count, 'equations': len(re.findall(r'^```math', markdown, re.M))}


def main():
    ASSETS.mkdir(exist_ok=True)
    evidence = analyze_evidence()
    legacy.refresh_tables(SOURCE, {'escenario1': scenario_section(evidence)})
    # Reorder only the two existing complementary sections, retaining all text.
    text = SOURCE.read_text(encoding='utf-8')
    start = text.index('### 8.2. IEEE-14'); middle = text.index('### 8.1. IEEE-118'); end = text.index('### 8.3. IEEE-300')
    if start < middle:
        text = text[:start] + text[middle:end] + text[start:middle] + text[end:]
        SOURCE.write_text(text, encoding='utf-8')
    legacy.refresh_legacy_report()
    markdown = SOURCE.read_text(encoding='utf-8')
    word_info = build_word(markdown)
    with pymupdf.open(ROOT / 'INFORME_PROYECTO_MATLAB.pdf') as pdf:
        text = '\n'.join(page.get_text() for page in pdf)
        for value in ('165.897686', '546.897686', '0.940040', '223.362016', 'PENDIENTE'):
            require(value in text, f'Falta evidencia del escenario en PDF: {value}')
        for index, page in enumerate(pdf, 1):
            for block in page.get_text('blocks'):
                require(block[1] >= 25 and block[3] <= page.rect.height - 25,
                        f'Desbordamiento vertical en página PDF {index}.')
        pdf_info = {'pages': len(pdf), 'bookmarks': len(pdf.get_toc()), 'vertical_bounds_verified': True}
    for record in evidence['files']:
        require(record == fingerprint(Path(record['path'])),
                f"Una entrada cambió durante la compilación: {record['path']}. Repita el comando.")
    record = {'built_at_utc': datetime.now(timezone.utc).isoformat(),
              'description': 'Lectura y contraste de evidencia guardada; no se ejecutó MATLAB ni se grabó video.',
              'files': evidence['files'], 'input_changes': evidence['changes'], 'checks': evidence['checks'],
              'supporting_logs': [fingerprint(ROOT / name) for name in
                                  ('escenario1_assets/pruebas_escenario1.log',
                                   'escenario1_assets/auditoria_evidencia.json') if (ROOT / name).is_file()],
              'missing_external_columns': evidence['missing_external'], 'word': word_info, 'pdf': pdf_info,
              'human_pending': ['Nombres reales de integrantes', 'Voces identificadas de todos',
                                'MP4 >=1080p, 30–40 min, audio claro', 'Captura continua de cada corrida hasta exportación',
                                'Notificar escenario al profesor y entregar paquete en TEC Digital un día antes'],
              'outputs': [fingerprint(ROOT / f'INFORME_PROYECTO_MATLAB.{ext}') for ext in ('md', 'typ', 'pdf', 'docx')],
              'generators': [fingerprint(Path(__file__)), fingerprint(ROOT / 'tools/build_report.py')]}
    (ASSETS / 'manifest_video.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Word real:', ROOT / 'INFORME_PROYECTO_MATLAB.docx', word_info)
    print('Validación externa adicional pendiente:', evidence['missing_external'] or 'ninguna columna')
    print('Video/miembros/entrega: PENDIENTES humanos.')


if __name__ == '__main__':
    main()
