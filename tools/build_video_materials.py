#!/usr/bin/env python3
"""Build the guide-aligned IEEE118 / line 26–30 deck and shared oral source.

Read-only evidence consumer. Never executes MATLAB, edits Excel, or fabricates video.
python tools/build_presentation.py
python tools/render_presentation.py
python tools/build_oral_script.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

from presentation_story import (make_story, SECTION_NAMES, SMALL_COMMAND, BASE_COMMAND,
                                SCENARIO_COMMAND, COMPARE_COMMAND, GUI_COMMAND,
                                QUESTION_PROMPTS, SECTION_SECONDS, PLANNED_SECONDS, EXPECTED_SLIDES)

ROOT = Path(__file__).resolve().parents[1]
NAVY, INK, TEAL, BLUE, ORANGE, PALE, MUTED = ('10263F', '20364C', '007E74', '2463A4', 'B34F16', 'EFF4F8', '52667C')
METHODS = ['NR', 'GS', 'FDLF']
SOURCE_FILES = ['data/IEEE118.xlsx', 'data/IEEE118_escenario1.xlsx',
                'resultados_IEEE118_matlab.xlsx', 'resultados_IEEE118_escenario1_matlab.xlsx',
                'comparacion_escenario1.xlsx', 'validacion_MATPOWER.xlsx',
                'data/case118.m', 'escenario1_assets/IEEE118_unifilar_UW.png',
                'escenario1_assets/unifilar_region_26_30.png',
                'escenario1_assets/unifilar_region_26_30_anotado.png',
                'escenario1_assets/fuente_unifilar.json', 'escenario1_assets/README_FUENTES.md',
                'matlab/main.m', 'matlab/build_ybus.m', 'matlab/solve_newton_raphson.m',
                'matlab/solve_gauss_seidel.m', 'matlab/solve_fast_decoupled.m',
                'matlab/solve_power_flow.m', 'matlab/export_results_excel.m',
                'matlab/app_flows.m', 'matlab/test_app_flows.m',
                'escenario1_assets/gui_caso_base.png', 'escenario1_assets/gui_salida_26_30.png',
                'escenario1_assets/captura_GUI_escenario1.json',
                'tools/presentation_story.py', 'tools/build_video_materials.py',
                'tools/video_classic.py']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tables(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    result = {}
    for sheet in workbook:
        values = iter(sheet.values)
        head = next(values)
        result[sheet.title] = [dict(zip(head, row)) for row in values if any(x is not None for x in row)]
    workbook.close()
    return result


def close(a, b, tol=1e-7):
    assert math.isclose(a, b, abs_tol=tol, rel_tol=1e-10), (a, b)


def load_evidence(root):
    for source in SOURCE_FILES:
        if not (root/source).is_file():
            raise FileNotFoundError(f'Falta evidencia; no se generan cifras estimadas: {source}')
    base_input = tables(root/'data/IEEE118.xlsx')
    scenario_input = tables(root/'data/IEEE118_escenario1.xlsx')
    differences = [(sheet, i+2, key, row[key], other[key])
                   for sheet, rows in base_input.items()
                   for i, (row, other) in enumerate(zip(rows, scenario_input[sheet]))
                   for key in row if row[key] != other[key]]
    assert all(len(base_input[k]) == len(scenario_input[k]) for k in base_input)
    assert differences == [('branch', 39, 'STATUS', 1, 0)], differences
    assert base_input['branch'][37]['F_BUS'] == 26 and base_input['branch'][37]['T_BUS'] == 30
    highlight_book = load_workbook(root/'data/IEEE118_escenario1.xlsx')
    assert highlight_book['branch']['K39'].fill.patternType == 'solid', 'Falta resaltado del cambio.'
    highlight_book.close()
    base = tables(root/'resultados_IEEE118_matlab.xlsx')
    scenario = tables(root/'resultados_IEEE118_escenario1_matlab.xlsx')
    comp = tables(root/'comparacion_escenario1.xlsx')
    validation = tables(root/'validacion_MATPOWER.xlsx')
    for result, input_case in ((base, base_input), (scenario, scenario_input)):
        assert result['entrada_bus'] == input_case['bus']
        assert result['entrada_branch'] == input_case['branch']
        normalize = lambda rows: [{k.replace('_',''): v for k,v in row.items()} for row in rows]
        assert normalize(result['entrada_gen']) == normalize(input_case['gen'])
        assert len(result['comparacion']) == 3
        for index, method in enumerate(METHODS):
            row = result['comparacion'][index]
            assert row['Convergio'] and row['Error_final_pu'] <= 1e-8
            assert isinstance(row['P_slack_MW'], (float, int))
            assert len(result[method+'_conv']) == row['Iteraciones']+1
            close(result[method+'_conv'][-1]['Error_max_pu'], row['Error_final_pu'])
    assert len(base_input['bus']) == 118 and len(base_input['branch']) == 186
    assert all(r['RATE_A'] == 0 for r in base_input['branch'])
    assert [r['BUS_I'] for r in comp['fuera_base']] == [53, 76, 118]
    assert [r['BUS_I'] for r in comp['fuera_escenario']] == [20, 21, 22, 53, 76, 118]
    assert [r['Rama'] for r in comp['cambios_top5_total']] == [38,32,31,36,33]
    assert comp['cambios_top5_total'][0]['Delta_pct'] == -100
    for row in comp['cambios_top5']:
        assert row['Rama'] != 38 and row['Activa_base'] and row['Activa_escenario']
        close(row['Delta_MVA'], row['S_escenario_MVA']-row['S_base_MVA'])
        close(row['Delta_pct'], 100*row['Delta_MVA']/row['S_base_MVA'])
    validation118 = [r for r in validation['resumen'] if r['Case'] == 'IEEE118']
    assert len(validation118) == 3 and all(r['Passed'] for r in validation118)
    slack = next(r for r in base_input['bus'] if r['BUS_I'] == 69)
    # Reference branch powers include branch charging. Shunt at bus69 is zero.
    assert slack['GS'] == 0 and slack['BS'] == 0
    reference_p, reference_q = slack['PD'], slack['QD']
    for row in validation['IEEE118_NR_branch']:
        if row['Desde'] == 69:
            reference_p += row['Ref_Pfrom_MW']; reference_q += row['Ref_Qfrom_MVAr']
        if row['Hasta'] == 69:
            reference_p += row['Ref_Pto_MW']; reference_q += row['Ref_Qto_MVAr']
    close(reference_p, base['comparacion'][0]['P_slack_MW'])
    close(reference_q, base['comparacion'][0]['Q_slack_MVAr'])
    close(base['comparacion'][0]['Perdidas_P_MW'] + 4242,
          sum(r['P_gen_calculada_MW'] for r in base['NR_bus']))
    removed = comp['linea_retirada'][0]
    close(removed['S_max_MVA'], max(removed['S_from_MVA'], removed['S_to_MVA']))
    capture=json.loads((root/'escenario1_assets/captura_GUI_escenario1.json').read_text(encoding='utf-8'))
    assert capture['temporaryExportsOnly']
    for captured, recorded in ((capture['base'],base['comparacion']), (capture['scenario'],scenario['comparacion'])):
        assert len(captured)==len(recorded)==3
        for a,b in zip(captured,recorded):
            assert a['Iteraciones']==b['Iteraciones']
            close(a['PerdidasPMW'],b['Perdidas_P_MW'])
    return dict(base=base, scenario=scenario, base_input=base_input,
                scenario_input=scenario_input, comparison=comp, validation=validation118,
                reference_voltage=validation['IEEE118_NR_bus'],
                base_methods=base['comparacion'], scenario_methods=scenario['comparacion'],
                reference_slack_p=reference_p, reference_slack_q=reference_q,
                slack_reconstruction='Sumar Ref_Pfrom/Ref_Qfrom cuando Desde=69 y Ref_Pto/Ref_Qto cuando Hasta=69, más PD/QD de barra69. GS=BS=0 en esa barra.',
                input_difference=differences,
                published_source=json.loads((root/'escenario1_assets/fuente_unifilar.json').read_text(encoding='utf-8')))


def make_charts(e, assets, root):
    from video_classic import make_charts as classic_charts
    return classic_charts(e, assets, root)


class Deck:
    """The earlier white/navy title, table and list layout."""
    def __new__(cls, assets, count):
        from video_classic import ClassicDeck
        return ClassicDeck(assets, count)


def f(number,places=3):
    return f'{number:.{places}f}'.replace('.',',')


def method_table(d,s,rows):
    body=[[m,str(r['Iteraciones']),f(r['Tiempo_s'],4),f"{r['Error_final_pu']:.2e}",f(r['P_slack_MW']),f(r['Perdidas_P_MW']),f(r['Perdidas_Q_MVAr'])]
          for m,r in zip(METHODS,rows)]
    d.table(s,['Método','Iter.','Tiempo\n[s]','Mismatch\n[pu]','P slack\n[MW]','Pérdidas P\n[MW]','Pérdidas Q\n[MVAr]'],body,[1.3,.8,1.5,1.7,2.0,2.25,2.4],y=2,size=20,row_h=.8)
    d.text(s,'NR: Newton-Raphson · GS: Gauss-Seidel · FDLF: desacoplado rápido',.75,5.43,11.9,.45,18,TEAL,True)
    d.text(s,'Una corrida. Tiempo: solución + ensamblado + consola; sin Excel ni gráficas.',.75,6.0,11.9,.5,18,MUTED)


def build_deck(e,story,charts,root,assets):
    from video_classic import build_deck as classic_deck
    return classic_deck(e, story, charts, root, assets)


def clock(seconds):
    return f'{seconds//60:02d}:{seconds%60:02d}'


def write_guides(root,story):
    lines=['# Presentación para el video — IEEE118, escenario 1','',
           '**Estado:** PPTX con notas y PDF son apoyos estáticos. El MP4 real con voces y corridas continuas está pendiente.',
           '**Identidades:** completar todos los nombres reales y asignar cada sección. Un mismo integrante puede cubrir varias; todos deben tener voz e identificarse antes de su parte.',
           '', f'## Orden y presupuesto ({clock(PLANNED_SECONDS)}; ensayo y duración real pendientes)', '',
           '| Sección | Tiempo previsto | Ventana guía |','|---|---:|---:|']
    for section,window in [(0,'1–2 min'),(1,'8–10 min'),(2,'3–4 min'),(3,'6–8 min'),(4,'10–12 min'),(5,'2–3 min')]:
        lines.append(f"| {SECTION_NAMES[section]} | {clock(sum(s['seconds'] for s in story if s['section_number']==section))} | {window} |")
    lines+=['','Los tiempos incluyen mostrar código, operar Excel, observar iteraciones y exportar. No son una narración ya cronometrada; ensayar sin acelerar las corridas. Las ejecuciones suelen durar mucho menos que el bloque completo porque Excel y la explicación también requieren tiempo.',
            '', '## Recorrido sincronizado con notas y guion', '', '| N.º | Diapositiva | Tiempo | Tramo | Voz pendiente |','|---:|---|---:|---|---|']
    elapsed=0
    oral=['# Guion oral — IEEE118, escenario 1: retiro de línea 26–30','',
          f'Fuente común: `tools/presentation_story.py`. Editar allí y reconstruir. {EXPECTED_SLIDES} diapositivas con el formato anterior (fondo blanco, títulos azul oscuro, tablas y listas), con una pregunta antes de cada respuesta. El presupuesto {clock(PLANNED_SECONDS)} incluye acciones en pantalla; ensayar para confirmar 30–40 minutos.',
          '', '**Completar antes de grabar:** lista de TODOS los nombres reales: [PENDIENTE]. Asignar sección0 [NOMBRE], sección1 [NOMBRE], sección2 [NOMBRE], sección3 [NOMBRE], sección4 [NOMBRE], sección5 [NOMBRE]. Esto no supone seis personas: repetir nombres o subdividir partes según el equipo real. Cada nueva voz se identifica por nombre antes de hablar.',
          '', '**Honestidad de evidencia:** PDF, imágenes, miniaturas y logs son apoyos o registros técnicos, NO grabación. El video real está pendiente. No cortar ni acelerar dentro de una corrida.', '']
    for i,s in enumerate(story,1):
        lines.append(f"| {i} | {s['title']} | {clock(s['seconds'])} | {clock(elapsed)}–{clock(elapsed+s['seconds'])} | {s['voice']} |")
        elapsed+=s['seconds']
        oral += [f"## {i}. {s['title']}",'','### Discurso','','\n\n'.join(s['speech']),
                 '', '### Apoyo visual','',f"Voz asignada: {s['voice']}. Tiempo previsto {clock(s['seconds'])}. "+s['cue'],'']
        if s['code']:oral+=['### Comandos','','```matlab',s['code'],'```','']
    lines += ['','## Preparación concreta de la grabación', '',
              '1. Completar nombres reales en el relato y reconstruir; repartir voces para incluir a todos. Si cambia la persona dentro de una sección, añadir su identificación antes de su parte. Ensayar 30–40min con reloj.',
              '2. Configurar OBS u otro grabador a 1920×1080 o superior, MP4, audio inteligible y sin música de fondo. Probar micrófono, encuadre y espacio en disco. Cámara preferida. Preparar MATLAB abierto, consola legible y ruta raíz `C:/repos/Potencia_proyecto`.',
              '3. Tener visibles código y Excel de entrada. Cerrar los libros de SALIDA antes de ejecutar. Guardar los archivos antes de iniciar la toma; no sobrescribir la entrada. El escenario ya está preparado y resaltado.',
              '4. En cada corrida iniciar la captura ANTES de pulsar Ejecutar métodos o Retirar línea 26–30; mostrar la acción, todos los mismatch por iteración y la exportación. Mantener sin cortes ni acelerado hasta el mensaje de exportación y la apertura del Excel nuevo. Se permite cambiar ventanas y desplazarse sin detener captura. No reemplazar tramos por logs, capturas o PDFs.',
              '5. Si falla una ejecución: explicar el fallo, corregirlo y repetir la toma COMPLETA. No empalmar una ejecución antigua. Se permite edición entre secciones, nunca dentro de la corrida.',
              f'6. Revisar hojas de resultados, editar solamente transiciones entre secciones y verificar que el archivo final realmente conserve las tomas continuas. Escuchar todas las voces y medir duración real; el plan de {clock(PLANNED_SECONDS)} no prueba ese requisito.',
              '7. En la parte del escenario, mostrar primero cada tarjeta con la pregunta completa, hacer una pausa breve y avanzar a su respuesta correspondiente. Las explicaciones extensas están en notas y guion, no en bloques de texto en pantalla.',
              '', '## Comandos reales (MATLAB, desde la raíz)', '', '### Sección1: versatilidad IEEE14 (<1min real)', '', '```matlab',SMALL_COMMAND,'```',
              '', '### Sección3: caso base desde la interfaz','', '```matlab',GUI_COMMAND,'```',
              '', 'Dejar IEEE-118, Todos, tol1e−8, máximo1000, GS1,5 y límitesQ desactivados. Grabar desde antes de **Ejecutar métodos** hasta exportar y abrir el Excel base. Solo después se habilita **Retirar línea 26–30**; no pulsarlo hasta la sección4.',
              '', '### Sección4: retirar desde la misma interfaz', '',
              'Sin cambiar datos ni parámetros, grabar desde antes de pulsar **Retirar línea 26–30** hasta la exportación y apertura del escenario y comparación. Se conservan los resultados base. Mostrar **Base vs. salida 26–30**, **Cambios de flujo** y STATUS=0 resaltado; **Volver al caso base** restaura la referencia sin recalcular. Una edición invalida la referencia y obliga a ejecutar de nuevo la base.',
              '', '### Cinco Excel del estudio principal', '',
              'Dos entradas: `data/IEEE118.xlsx` y `data/IEEE118_escenario1.xlsx`. Tres salidas: `resultados_IEEE118_matlab.xlsx`, `resultados_IEEE118_escenario1_matlab.xlsx` y `comparacion_escenario1.xlsx`. Los tres métodos van en hojas dentro de cada resultado. Los libros de versatilidad y validación son auxiliares.',
              '', '### Alternativa por consola (no mezclar con la toma GUI)','', '```matlab',BASE_COMMAND,'```',
              '', '```matlab',SCENARIO_COMMAND,'```',
              '', 'SOLO para la alternativa por consola, conservar `base` y `esc` y comparar esas MISMAS corridas. En la GUI esto se hace automáticamente y no hay que ejecutar este comando:', '', '```matlab',COMPARE_COMMAND,'```',
              '', 'Alternativa de reproducción técnica completa (corre ambos casos y comparación):', '', '```matlab',"addpath('matlab'); study = run_video_project(false);",'```',
              '', '`main(input,output,false)` también exporta los tres métodos y usa verbose=true por defecto. El cuarto argumento lo deja explícito; `false` desactiva gráficas, NO Excel. El pipeline técnico o un diary NO constituyen un video.',
              '', 'Si se vuelven a ejecutar los casos, los tiempos pueden cambiar. Regenerar estos materiales después de actualizar Excel; no mantener cifras temporales antiguas ni alegar que representan exactamente una nueva toma.',
              '', '## Código que debe verse en pantalla', '',
              '- Arquitectura e importación: `matlab/app_flows.m` (run_case, run_outage, restore_base), `matlab/main.m`, `load_case_excel.m`, `validate_case.m`, `solve_power_flow.m`.',
              '- Tipos y arranque: `bus_sets.m`, `specified_power.m`, `voltage_setpoints.m`, `initial_voltage.m` (dentro de `matlab/`).',
              '- Ybus: `matlab/build_ybus.m`: tamaño desde ids, shunts, STATUS, π, tap complejo, Yff/Yft/Ytf/Ytt.',
              '- Métodos: `matlab/solve_newton_raphson.m` (Jacobiano, J\\mis), `solve_gauss_seidel.m` (candidate, α, PV), `fast_decoupled_matrices.m` y `solve_fast_decoupled.m` (B′/B″, reevaluación Q).',
              '- Tolerancia y log: `matlab/power_mismatch.m`, `log_powerflow_iteration.m`; límites Q opcionales: `apply_q_limits.m`.',
              '- Flujos/slack/Excel: `matlab/calculate_branch_flows.m`, `assemble_result.m`, `result_comparison.m`, `export_results_excel.m`.',
              '', '## Trazabilidad y alcances', '',
              '- Datos: `data/IEEE118.xlsx`; copia `data/IEEE118_escenario1.xlsx`. Único cambio: `branch!K39`, STATUS 1→0, rama38 26–30, resaltado. No se modifican cargas, generación, parámetros ni otras ramas.',
              '- Métodos: `resultados_IEEE118_matlab.xlsx` y `resultados_IEEE118_escenario1_matlab.xlsx`, hoja `comparacion` con P/Q slack. Parámetros e historiales en sus hojas; arranque VM/VA del Excel y VG activa, no plano; tol1e−8, máximo1000, GS1,5, límitesQ off.',
              '- Rankings, tabla obligatoria y línea retirada: `comparacion_escenario1.xlsx`. S_máx=max módulos de ambos extremos. Cambios ordenados por |ΔMVA|, con signo y Δ%=100Δ/Sbase. `cambios_top5_total` es el ranking global exigido, incluida retirada; `cambios_top5` es complemento de redistribución en ramas activas. Identificadores de extremos en filas separadas, sin restarlos.',
              '- Fuera de rango: 0,95–1,05 pu inclusivo con margen1e−8. Es distinto de 0,94–1,06 del archivo. Hay tres violaciones base y seis escenario. RATE_A=0: no se puede certificar factibilidad térmica. Convergencia no demuestra cumplimiento Q, seguridad N−1 ni estabilidad dinámica.',
              '- Validación externa conservada: `validacion_MATPOWER.xlsx`, `resumen` IEEE118 y `metadatos`, MATPOWER8.1 NR tol1e−10 Q off. P/Q slack referencia se reconstruyen de flujos incidentes de `IEEE118_NR_branch` más carga barra69 (GS=BS=0); cálculo numérico en `presentacion_assets/evidencia_video.json`. Esta validación es BASE, no escenario.',
              '- Los tiempos son de una corrida técnica e incluyen solución, ensamblado y consola si verbose; excluyen Excel y gráficas. No representan un benchmark ni la duración de la toma.',
              '- Capturas GUI actuales: `escenario1_assets/gui_caso_base.png` y `gui_salida_26_30.png`; realizadas en una carpeta temporal. Son referencias estáticas, no video; sus tiempos no sustituyen los tabulados en los libros de evidencia. Procedencia: `captura_GUI_escenario1.json`.',
              '', '## Unifilar y referencias', '',
              '- R. Christie, University of Washington, *Power Systems Test Case Archive: 118 Bus Power Flow Test Case*, mayo1993; diagrama AEP diciembre1962. Página: https://labs.ece.uw.edu/pstca/pf118/pg_tca118bus.htm ; original: https://labs.ece.uw.edu/pstca/pf118/118bus6.tif . Archivos originales y cita: `escenario1_assets/README_FUENTES.md`, `fuente_unifilar.json`, `.tif` y `.png`.',
              '- `presentacion_assets/video_unifilar_region_anotada.png`: copia del recorte corregido `escenario1_assets/unifilar_region_26_30_anotado.png`, con resaltado y etiquetas PROPIOS, no atribuidos al original. Barra26=Tanners Creek345kV; barra30=Sorenson345kV, identificadas contra CDF UW y case118. NO confundir26 con W.Kamm. Manifiesto de procedencia y hashes junto al archivo. No se etiqueta una topología propia como publicada.',
              '- Datos MATPOWER8.1 `data/case118.m`, formato2; encabezado: conversión CDF 15-Oct-2014, correcciones de transformadores 15-Feb-2019. https://matpower.org/ .',
              '- W. F. Tinney y C. E. Hart, 1967, *Power Flow Solution by Newton’s Method*, DOI: 10.1109/TPAS.1967.291823.',
              '- B. Stott y O. Alsac, 1974, *Fast Decoupled Load Flow*, DOI: 10.1109/TPAS.1974.293985.',
              '- R. D. Zimmerman, C. E. Murillo-Sánchez y R. J. Thomas, 2011, MATPOWER, DOI: 10.1109/TPWRS.2010.2051168.',
              '', '## Reconstrucción de materiales (sin ejecutar MATLAB)', '', '```bash',
              'python tools/build_presentation.py','python tools/render_presentation.py','python tools/build_oral_script.py','```',
              '', '`build_presentation.py` redirige exclusivamente a `build_video_materials.py`; `presentation_story.py` es la fuente común para notas y discurso. El renderer exporta con PowerPoint y comprueba desbordamientos. El guion se compila con Typst. No ejecutar el antiguo capturador de demostraciones para reconstruir este video: las capturas no son requisito ni una grabación continua.',
              '', '## Pendientes reales de entrega', '',
              '- [ ] Completar lista real de integrantes y reparto; cada voz se identifica.',
              '- [ ] Ensayo y medición real 30–40 minutos; IEEE14 menor de1min.',
              '- [ ] Grabar MP4 real mínimo1080p con audio y corridas continuas; PDFs/logs no lo sustituyen.',
              '- [ ] Verificar informe en Word, programa, PowerPoint y Excel base/escenario de entrada/salida.',
              '- [ ] Subir a TEC Digital un día antes de exposición; si excede límite, enlace institucional accesible al profesor. No afirmar entrega realizada.', '']
    (root/'PRESENTACION.md').write_text('\n'.join(lines),encoding='utf-8')
    (root/'GUION_PARA_EXPONER.md').write_text('\n'.join(oral),encoding='utf-8')


def text_metrics(presentation):
    """Editable text only: labels embedded in chart images are not counted."""
    records=[]
    for index,slide in enumerate(presentation.slides,1):
        body=[]; all_text=[]
        for shape in slide.shapes:
            fragments=[]
            if shape.has_text_frame: fragments.append(shape.text)
            if shape.has_table:
                fragments.extend(cell.text for row in shape.table.rows for cell in row.cells)
            all_text.extend(fragments)
            if shape.top < Inches(6.65): body.extend(fragments)
        count=lambda pieces:len(re.findall(r'\S+',' '.join(pieces)))
        records.append({'slide':index,'editable_body_words':count(body),'editable_words':count(all_text)})
    return {'editable_body_words':sum(r['editable_body_words'] for r in records),
            'editable_words':sum(r['editable_words'] for r in records),
            'max_editable_body_words':max(r['editable_body_words'] for r in records),
            'includes_image_labels':False,'slides':records}


def verify(path,story):
    p=Presentation(path)
    assert len(p.slides)==len(story)==EXPECTED_SLIDES
    assert sum(s['seconds'] for s in story)==PLANNED_SECONDS
    assert tuple(sum(s['seconds'] for s in story if s['section_number']==k) for k in range(6))==SECTION_SECONDS
    questions=[(i,s) for i,s in enumerate(story) if s['kind']=='question']
    assert [s['question_number'] for _,s in questions]==[1,2,3]
    answer_kinds={1:'branch_changes',2:'voltage_change',3:'loss_change'}
    for i,spec in questions:
        number=spec['question_number']
        assert spec['question']==QUESTION_PROMPTS[number]
        assert story[i+1]['kind']==answer_kinds[number]
        assert story[i+1]['question_number']==number
        shown=' '.join(shape.text for shape in p.slides[i].shapes if shape.has_text_frame)
        assert ' '.join(QUESTION_PROMPTS[number].split()) in ' '.join(shown.split()), 'La pregunta debe verse completa, antes de su respuesta.'
    for i,(slide,spec) in enumerate(zip(p.slides,story),1):
        assert slide.has_notes_slide and spec['voice'] in slide.notes_slide.notes_text_frame.text
        assert all(paragraph in slide.notes_slide.notes_text_frame.text for paragraph in spec['speech'])
        for shape in slide.shapes:
            assert shape.left>=0 and shape.top>=0 and shape.left+shape.width<=p.slide_width+100 and shape.top+shape.height<=p.slide_height+100, (i,shape.name)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    all_text=' '.join(shape.text for slide in p.slides for shape in slide.shapes if shape.has_text_frame)
    assert 'IEEE300' not in all_text and 'IEEE-300' not in all_text
    for slide,spec in zip(p.slides,story):
        if spec['kind'] in ('base_methods','scenario_comparison'):
            assert any(shape.has_table for shape in slide.shapes), 'Conservar las dos tablas obligatorias de la guía.'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    before={source:digest(root/source) for source in SOURCE_FILES}
    e=load_evidence(root);story=make_story(e)
    if args.check_only:
        manifest=json.loads((root/'presentacion_assets/manifest.json').read_text(encoding='utf-8'))
        assert {r['path']:r['sha256'] for r in manifest['inputs']}==before, 'Fuentes cambiadas: reconstruya la presentación y el guion.'
        verify(root/'PRESENTACION.pptx',story);print('Evidencia y estructura IEEE118 escenario1 comprobadas.');return
    assets=root/'presentacion_assets';assets.mkdir(exist_ok=True)
    charts=make_charts(e,assets,root);prs=build_deck(e,story,charts,root,assets)
    output=root/'PRESENTACION.pptx';prs.save(output);verify(output,story);write_guides(root,story)
    (assets/'evidencia_video.json').write_text(json.dumps({
        'base_methods':e['base_methods'],'scenario_methods':e['scenario_methods'],
        'comparison':e['comparison'], 'validation_IEEE118':e['validation'],
        'reference_slack_P_MW':e['reference_slack_p'],'reference_slack_Q_MVAr':e['reference_slack_q'],
        'slack_reconstruction':e['slack_reconstruction'],'input_difference':e['input_difference'],
        'recording_status':'PENDIENTE: video real con voces; esta evidencia es técnica y estática.'
    },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert before=={source:digest(root/source) for source in SOURCE_FILES}, 'La evidencia debe permanecer intacta.'
    manifest={'built_at_utc':datetime.now(timezone.utc).isoformat(),'project':'IEEE118_escenario1_video',
              'inputs':[{'path':source,'sha256':sha} for source,sha in before.items()],
              'outputs':[{'path':str(p.relative_to(root)),'sha256':digest(p)} for p in [output,root/'PRESENTACION.md',root/'GUION_PARA_EXPONER.md']],
              'checks':{'slides':len(story),'main_slides':len(story),'backup_slides':0,'speaker_notes':len(story),
                        'planned_seconds':PLANNED_SECONDS,'evidence_unchanged':True,'structural_check':'OK',
                        'question_slides':3,'question_before_each_answer':True,
                        'presentation_style':'classic',
                        'visual_style':'Formato anterior: fondo blanco, títulos azul oscuro, tablas y listas'}, 
              'text_metrics':text_metrics(prs),
              'section_seconds':{str(k):sum(s['seconds'] for s in story if s['section_number']==k) for k in range(6)},
              'slides':[dict(number=i,layout=s['kind'],**s) for i,s in enumerate(story,1)],
              'charts':{k:str(v.relative_to(root)) for k,v in charts.items()},
              'recording_status':'PENDIENTE: MP4 continuo 1080p, nombres reales, voces y ensayo.',
              'source_story':'tools/presentation_story.py'}
    (assets/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PowerPoint: {output}\n{len(story)} diapositivas en formato anterior con notas · {clock(PLANNED_SECONDS)} previstos · evidencia Excel intacta.')
    print('Pendiente: renderizar PDF, compilar guion y grabar video real con identidades completas.')


if __name__=='__main__':main()
