"""Audit real MATLAB evidence for the video guide; does not certify a recording.

python tools/check_video_evidence.py [--materials]
Checks inputs, histories, balances, guide tables and independent base validation.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from prepare_scenario1 import cell_differences, fingerprint

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('NR', 'GS', 'FDLF')


def rows(book, sheet):
    iterator = iter(book[sheet].values)
    header = next(iterator)
    return [dict(zip(header, values)) for values in iterator if any(v is not None for v in values)]


def near(a, b, tol=1e-7):
    assert math.isclose(a, b, abs_tol=tol, rel_tol=1e-10), (a, b)


def verify_case(path, source):
    book = load_workbook(path, read_only=True, data_only=True)
    input_book = load_workbook(source, read_only=True, data_only=True)
    try:
        for sheet in ('bus', 'gen', 'branch'):
            expected, actual = rows(input_book, sheet), rows(book, 'entrada_' + sheet)
            if sheet == 'bus':
                expected = sorted(expected, key=lambda r: r['BUS_I'])
            # El importador normaliza nombres no usados (p.ej. RAMP_AGC -> RAMPAGC).
            def normalized(records):
                return [{''.join(c for c in str(k).upper() if c.isalnum()):v for k,v in record.items()}
                        for record in records]
            assert normalized(expected) == normalized(actual), f'{path.name}: la entrada exportada no coincide ({sheet}).'
        result = {'comparison': rows(book, 'comparacion'), 'bus': {}, 'branch': {}}
        assert len(result['comparison']) == 3
        for method, comp in zip(METHODS, result['comparison']):
            assert comp['Convergio'] in (True, 1)
            assert 0 <= comp['Error_final_pu'] <= 1e-8
            history = rows(book, method + '_conv')
            assert [r['Iteracion'] for r in history] == list(range(comp['Iteraciones'] + 1))
            near(history[-1]['Error_max_pu'], comp['Error_final_pu'], 1e-14)
            bus, branch = rows(book, method + '_bus'), rows(book, method + '_branch')
            assert len(bus) == 118 and len(branch) == 186
            assert all(math.isfinite(r['VM_pu']) and r['VM_pu'] > 0 for r in bus)
            near(sum(r['P_loss_MW'] for r in branch), comp['Perdidas_P_MW'])
            near(sum(r['Q_loss_MVAr'] for r in branch), comp['Perdidas_Q_MVAr'])
            slack = next(r for r in bus if r['BUS_I'] == 69)
            source_slack = next(r for r in rows(input_book,'bus') if r['TYPE'] == 3)
            near((slack['VA_deg']-source_slack['VA']+180)%360-180,0,1e-9)
            near(slack['P_gen_calculada_MW'], comp['P_slack_MW'])
            near(slack['Q_gen_calculada_MVAr'], comp['Q_slack_MVAr'])
            generation = sum(r['P_gen_calculada_MW'] for r in bus)
            demand = sum(r['PD'] for r in bus)
            shunt = sum(r['GS'] * r['VM_pu'] ** 2 for r in bus)
            near(generation - demand, comp['Perdidas_P_MW'] + shunt, 1e-6)
            q_generation = sum(r['Q_gen_calculada_MVAr'] for r in bus)
            q_demand = sum(r['QD'] for r in bus)
            q_shunt = -sum(r['BS'] * r['VM_pu'] ** 2 for r in bus)
            near(q_generation-q_demand, comp['Perdidas_Q_MVAr']+q_shunt, 1e-6)
            result['bus'][method], result['branch'][method] = bus, branch
        reference = result['bus']['NR']
        for method in METHODS:
            assert max(abs(a['VM_pu']-b['VM_pu']) for a,b in zip(reference,result['bus'][method])) < 1e-7
            assert max(abs((a['VA_deg']-b['VA_deg']+180)%360-180)
                       for a,b in zip(reference,result['bus'][method])) < 1e-5
        return result
    finally:
        book.close()
        input_book.close()


def audit(materials=False):
    base_path, scenario_path = ROOT/'data/IEEE118.xlsx', ROOT/'data/IEEE118_escenario1.xlsx'
    base, scenario = load_workbook(base_path), load_workbook(scenario_path)
    try:
        changes = cell_differences(base, scenario)
        assert changes == [('branch','K39',1,0)], changes
        assert scenario['branch']['K39'].fill.fill_type == 'solid'
    finally:
        base.close(); scenario.close()
    manifest = json.loads((ROOT/'escenario1_assets/entrada_escenario1.json').read_text(encoding='utf-8'))
    assert manifest['source_sha256'] == fingerprint(base_path)
    assert manifest['output_sha256'] == fingerprint(scenario_path)
    b = verify_case(ROOT/'resultados_IEEE118_matlab.xlsx', base_path)
    s = verify_case(ROOT/'resultados_IEEE118_escenario1_matlab.xlsx', scenario_path)
    for method in METHODS:
        removed = s['branch'][method][37]
        assert (removed['Desde'], removed['Hasta']) == (26,30)
        assert all(removed[column] == 0 for column in ('P_from_MW','Q_from_MVAr','P_to_MW','Q_to_MVAr','S_from_MVA','S_to_MVA','P_loss_MW','Q_loss_MVAr'))
    book = load_workbook(ROOT/'comparacion_escenario1.xlsx', read_only=True, data_only=True)
    try:
        comp = {r['Variable']:r for r in rows(book,'comparacion')}
        for field in ('Caso_base','Escenario'):
            case = b if field == 'Caso_base' else s
            bus = case['bus']['NR']; methods = case['comparison']
            near(comp['Tensión mínima (pu)'][field], min(r['VM_pu'] for r in bus))
            near(comp['Tensión máxima (pu)'][field], max(r['VM_pu'] for r in bus))
            near(comp['Barra de tensión mínima'][field], min(bus,key=lambda r:r['VM_pu'])['BUS_I'])
            near(comp['Barra de tensión máxima'][field], max(bus,key=lambda r:r['VM_pu'])['BUS_I'])
            near(comp['Pérdidas totales (MW)'][field],methods[0]['Perdidas_P_MW'])
            near(comp['P de la barra slack 69 (MW)'][field],methods[0]['P_slack_MW'])
            near(comp['Q de la barra slack 69 (MVAr)'][field],methods[0]['Q_slack_MVAr'])
            near(comp['Iteraciones Newton-Raphson'][field],methods[0]['Iteraciones'])
            near(comp['Iteraciones Gauss-Seidel'][field],methods[1]['Iteraciones'])
            outside = [r['BUS_I'] for r in bus if r['VM_pu'] < .95-1e-8 or r['VM_pu'] > 1.05+1e-8]
            near(comp['Barras fuera de 0.95–1.05 pu'][field],len(outside))
            prefix = 'base' if field == 'Caso_base' else 'escenario'
            assert [r['BUS_I'] for r in rows(book,'fuera_'+prefix)] == outside
            expected_low = sorted(bus,key=lambda r:(r['VM_pu'],r['BUS_I']))[:5]
            assert [r['BUS_I'] for r in rows(book,prefix+'_top5_bajas')] == [r['BUS_I'] for r in expected_low]
            expected_flows = sorted(case['branch']['NR'],
                key=lambda r:max(r['S_from_MVA'],r['S_to_MVA']),reverse=True)[:5]
            flow_table = rows(book,prefix+'_top5_flujos')
            assert [r['Rama'] for r in flow_table] == [r['Rama'] for r in expected_flows]
            for actual, expected in zip(flow_table,expected_flows):
                near(actual['S_max_MVA'],max(expected['S_from_MVA'],expected['S_to_MVA']))
        for label, row in comp.items():
            if label.startswith('Barra de tensión'):
                assert row['Diferencia'] is None, 'No restar identificadores de barras.'
            else:
                near(row['Diferencia'],row['Escenario']-row['Caso_base'])
        global_deltas = []
        deltas = []
        for left,right in zip(b['branch']['NR'],s['branch']['NR']):
            sb = max(left['S_from_MVA'],left['S_to_MVA']); ss = max(right['S_from_MVA'],right['S_to_MVA'])
            delta_record = (left['Rama'],ss-sb,100*(ss-sb)/sb if sb > 1e-9 else None)
            global_deltas.append(delta_record)
            if left['Rama'] != 38:
                deltas.append(delta_record)
        global_deltas.sort(key=lambda r:(-abs(r[1]),r[0]))
        global_top = rows(book,'cambios_top5_total')
        assert [r['Rama'] for r in global_top] == [r[0] for r in global_deltas[:5]]
        for actual, expected in zip(global_top, global_deltas):
            near(actual['Delta_MVA'],expected[1]); near(actual['Delta_pct'],expected[2])
        deltas.sort(key=lambda r:(-abs(r[1]),r[0]))
        top = rows(book,'cambios_top5')
        assert [r['Rama'] for r in top] == [r[0] for r in deltas[:5]]
        for actual, expected in zip(top,deltas):
            near(actual['Delta_MVA'],expected[1]); near(actual['Delta_pct'],expected[2])
    finally:
        book.close()
    metadata = json.loads((ROOT/'validacion_MATPOWER.json').read_text(encoding='utf-8'))
    assert metadata['allPassed'] and metadata['officialIEEE118InputCheck']['matches']
    assert len(metadata['comparisons']) == 9 and all(r['Passed'] for r in metadata['comparisons'])
    reference = [r for r in metadata['comparisons'] if r['Case']=='IEEE118']
    validation_book = load_workbook(ROOT/'validacion_MATPOWER.xlsx',read_only=True,data_only=True)
    try:
        for method, validated in zip(METHODS,reference):
            details = rows(validation_book,'IEEE118_'+method+'_bus')
            current = b['bus'][method]
            assert [r['BUS_I'] for r in current] == [r['BUS_I'] for r in details]
            for actual_bus, stored in zip(current,details):
                near(actual_bus['VM_pu'],stored['Own_VM_pu'],1e-10)
                near(actual_bus['VA_deg'],stored['Own_VA_deg'],1e-9)
            vm_error = max(abs(a['VM_pu']-r['Reference_VM_pu']) for a,r in zip(current,details))
            va_error = max(abs((a['VA_deg']-r['Reference_VA_deg']+180)%360-180) for a,r in zip(current,details))
            near(vm_error,validated['MaxAbsVMError_pu'],1e-12)
            near(va_error,validated['MaxAbsVAError_deg'],1e-10)
            assert vm_error <= metadata['thresholds']['VM_pu'] and va_error <= metadata['thresholds']['VA_deg']
    finally:
        validation_book.close()
    for actual, validated in zip(b['comparison'],reference):
        assert actual['Metodo'] == validated['Method']
        near(abs(actual['Perdidas_P_MW']-validated['ReferencePLoss_MW']),validated['AbsPLossError_MW'])
        near(abs(actual['Perdidas_Q_MVAr']-validated['ReferenceQLoss_MVAr']),validated['AbsQLossError_MVAr'])
        near(abs(actual['P_slack_MW']-validated['ReferenceSlackP_MW']),validated['AbsSlackPError_MW'])
        near(abs(actual['Q_slack_MVAr']-validated['ReferenceSlackQ_MVAr']),validated['AbsSlackQError_MVAr'])
        assert validated['AbsPLossError_MW'] <= 1e-4 and validated['AbsQLossError_MVAr'] <= 1e-4
        assert validated['AbsSlackPError_MW'] <= 1e-4 and validated['AbsSlackQError_MVAr'] <= 1e-4
    checked_materials = []
    if materials:
        for name in ('README.md','GUIA_USO_MATLAB.md','MATLAB_README.md','PRESENTACION.md','PRESENTACION.pptx','PRESENTACION.pdf',
                     'GUION_PARA_EXPONER.md','GUION_PARA_EXPONER.pdf','INFORME_PROYECTO_MATLAB.md',
                     'INFORME_PROYECTO_MATLAB.docx','INFORME_PROYECTO_MATLAB.pdf','CUMPLIMIENTO_GUIA_VIDEO.md'):
            path = ROOT/name
            assert path.is_file() and path.stat().st_size > 100, f'Falta {name}'
            checked_materials.append(name)
        with ZipFile(ROOT/'INFORME_PROYECTO_MATLAB.docx') as archive:
            doc = ET.fromstring(archive.read('word/document.xml'))
            text = ''.join(doc.itertext())
            assert '26' in text and '30' in text and '165.897' in text
        from pptx import Presentation
        from presentation_story import EXPECTED_SLIDES, PLANNED_SECONDS, QUESTION_PROMPTS
        deck = Presentation(ROOT/'PRESENTACION.pptx')
        assert len(deck.slides) == EXPECTED_SLIDES
        assert all(slide.has_notes_slide for slide in deck.slides)
        buttons = ('Retirar línea 26–30','Volver al caso base')
        for name in ('README.md','GUIA_USO_MATLAB.md','MATLAB_README.md',
                     'PRESENTACION.md','GUION_PARA_EXPONER.md','INFORME_PROYECTO_MATLAB.md'):
            content = (ROOT/name).read_text(encoding='utf-8')
            assert all(label in content for label in buttons), f'{name}: falta el flujo GUI actual.'
        spoken = ' '.join(slide.notes_slide.notes_text_frame.text for slide in deck.slides)
        assert all(label in spoken for label in buttons), 'Notas PPTX anteriores a la actualización GUI.'
        import pymupdf
        for name in ('PRESENTACION.pdf','GUION_PARA_EXPONER.pdf','INFORME_PROYECTO_MATLAB.pdf'):
            with pymupdf.open(ROOT/name) as pdf:
                content = ' '.join(' '.join(page.get_text().split()) for page in pdf)
                assert all(label in content for label in buttons), f'{name}: PDF desactualizado.'
        presentation_meta = json.loads((ROOT/'presentacion_assets/manifest.json').read_text(encoding='utf-8'))
        assert presentation_meta['checks']['planned_seconds'] == PLANNED_SECONDS
        questions=[(i,s) for i,s in enumerate(presentation_meta['slides']) if s['kind']=='question']
        assert [s['question_number'] for _,s in questions] == [1,2,3]
        answer_kinds={1:'branch_changes',2:'voltage_change',3:'loss_change'}
        with pymupdf.open(ROOT/'PRESENTACION.pdf') as pdf:
            assert len(pdf) == EXPECTED_SLIDES
            for index,question in questions:
                number=question['question_number']
                answer=presentation_meta['slides'][index+1]
                assert answer['kind'] == answer_kinds[number] and answer['question_number'] == number
                assert QUESTION_PROMPTS[number] in ' '.join(pdf[index].get_text().split())
        for record in presentation_meta['inputs'] + presentation_meta['outputs']:
            path = ROOT/record['path']
            assert fingerprint(path) == record['sha256'], f'Presentación desactualizada respecto a {path}'
        report_meta = json.loads((ROOT/'informe_assets/manifest_video.json').read_text(encoding='utf-8'))
        for record in report_meta['outputs']:
            path = ROOT/Path(record['path']).name
            assert fingerprint(path) == record['sha256'], f'Informe desactualizado: {path}'
        code_meta = json.loads((ROOT/'informe_assets/manifest.json').read_text(encoding='utf-8'))
        for record in code_meta['code_files']:
            path = ROOT/'matlab'/Path(record['path']).name
            assert fingerprint(path) == record['sha256'], f'Informe anterior al cambio en {path}'
        speech_meta = json.loads((ROOT/'guion_assets/manifest.json').read_text(encoding='utf-8'))
        assert speech_meta['slides'] == EXPECTED_SLIDES and speech_meta['pages'] == EXPECTED_SLIDES+1
        assert speech_meta['planned_seconds'] == PLANNED_SECONDS
        for name, key in (('PRESENTACION.pptx','presentation_sha256'),
                          ('PRESENTACION.pdf','presentation_pdf_sha256'),
                          ('GUION_PARA_EXPONER.md','speech_source_sha256'),
                          ('GUION_PARA_EXPONER.pdf','pdf_sha256')):
            assert fingerprint(ROOT/name) == speech_meta[key], f'Guion desincronizado: {name}'
    inputs = [base_path,scenario_path,ROOT/'resultados_IEEE118_matlab.xlsx',
              ROOT/'resultados_IEEE118_escenario1_matlab.xlsx',ROOT/'comparacion_escenario1.xlsx',
              ROOT/'validacion_MATPOWER.json']
    return {'passed':True,'checks':['único cambio numérico y resaltado','6 soluciones e historiales completos',
        'entradas exportadas intactas','flujos nulos de línea retirada','balances y potencia slack',
        'rangos de guía y top 5 reproducibles','MATPOWER base incluyendo pérdidas P/Q y slack P/Q'],
        'materials_checked':checked_materials,'question_before_answer_pairs_checked':3 if materials else 0,'sha256':{str(p.relative_to(ROOT)):fingerprint(p) for p in inputs},
        'human_pending':['Integrantes/nombres y distribución de voces','Grabación MP4 real continua,1080p,30–40min',
                         'Ensayo cronometrado y verificación de audio','Confirmación del escenario al profesor y entrega TEC Digital']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--materials',action='store_true')
    args = parser.parse_args()
    result = audit(args.materials)
    path = ROOT/'escenario1_assets/auditoria_evidencia.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evidencia verificada: único cambio, 6 soluciones, tablas de guía y validación MATPOWER.')
    if args.materials:
        print('Materiales MD/PPTX/PDF/DOCX sincronizados con la GUI, fuentes y hashes; grabación humana pendiente.')
    print(path)


if __name__ == '__main__':
    main()
