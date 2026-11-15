"""Validated local data and common plotting helpers for the presentation.

No numerical solver is replaced here. All plotted values come from MATLAB
workbooks and the independently generated MATPOWER comparison.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import unicodedata

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
NAVY, BLUE, TEAL, ORANGE = '10263F', '2563EB', '008878', 'CD6B22'
INK, MUTED, PALE, WHITE, LINE = '1B3049', '5C6B7C', 'F0F4F8', 'FFFFFF', 'D7E0EA'
METHODS = ('NR', 'GS', 'FDLF')
NAMES = {'NR': 'Newton-Raphson', 'GS': 'Gauss-Seidel', 'FDLF': 'Desacoplado rápido'}
COLORS = {'NR': BLUE, 'GS': ORANGE, 'FDLF': TEAL}


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value)).lower()
                   if c.isascii() and c.isalnum())


def method_code(value):
    key = normalized(value)
    for method, aliases in {'NR': ('nr', 'newtonraphson'), 'GS': ('gs', 'gaussseidel'),
                            'FDLF': ('fdlf', 'fd', 'desacopladorapido', 'desacopladorpido')}.items():
        if key in aliases:
            return method
    raise ValueError(f'Método desconocido: {value}')


def rows(book, sheet, required=()):
    if sheet not in book.sheetnames:
        raise ValueError(f'Falta la hoja {sheet}.')
    iterator = iter(book[sheet].values)
    header = next(iterator)
    if len(set(header)) != len(header) or not set(required).issubset(header):
        raise ValueError(f'Encabezados incorrectos en {sheet}.')
    return [dict(zip(header, row)) for row in iterator if any(v is not None for v in row)]


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Valor numérico inválido: {value!r}')
    return float(value)


def true(value):
    return value is True or (isinstance(value, (int, float)) and value == 1)


def fingerprint(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def case_metrics(case):
    voltage = case['voltage']['NR']
    generation = sum(finite(r['P_gen_calculada_MW']) for r in voltage)
    demand = sum(finite(r['P_load_MW']) for r in voltage)
    shunt = sum(finite(r['GS'])*r['VM_pu']**2 for r in voltage)
    loss = case['comparison']['NR']['Perdidas_P_MW']
    if not math.isclose(generation-demand, loss+shunt, abs_tol=1e-5):
        raise ValueError('Balance activo inconsistente; revisar pérdidas de ramas y shunts.')
    return {'generation': generation, 'demand': demand, 'loss': loss, 'shunt': shunt,
            'total_loss': loss+shunt, 'minimum': min(voltage, key=lambda r:r['VM_pu']),
            'maximum': max(voltage, key=lambda r:r['VM_pu'])}


def load_evidence(root):
    cases, files = {}, []
    for number in (14, 118, 300):
        path = root / f'resultados_IEEE{number}_matlab.xlsx'
        before = fingerprint(path)
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            case = {'bus': rows(book, 'entrada_bus', ('BUS_I','TYPE','VM','VMIN','VMAX')),
                    'gen': rows(book, 'entrada_gen', ('GEN_BUS','STATUS','VG')),
                    'branch': rows(book, 'entrada_branch', ('F_BUS','T_BUS','STATUS')),
                    'comparison': {}, 'voltage': {}, 'flows': {}, 'history': {}}
            ids = [r['BUS_I'] for r in case['bus']]
            if len(ids) != number or len(set(ids)) != number:
                raise ValueError(f'{path.name} no contiene {number} barras únicas.')
            for record in rows(book, 'comparacion', ('Metodo','Convergio','Iteraciones','Error_final_pu','Tiempo_s','Perdidas_P_MW')):
                method = method_code(record['Metodo'])
                if method in case['comparison'] or not true(record['Convergio']):
                    raise ValueError(f'Método repetido o no convergente: {number}/{method}.')
                if not 0 <= finite(record['Error_final_pu']) <= 1e-8:
                    raise ValueError('Error final fuera de tolerancia.')
                for column in ('Iteraciones','Tiempo_s','Perdidas_P_MW'):
                    if finite(record[column]) < 0:
                        raise ValueError(f'{column} negativa.')
                case['comparison'][method] = record
            if set(case['comparison']) != set(METHODS):
                raise ValueError('Se requieren los tres métodos.')
            for method in METHODS:
                voltage = sorted(rows(book, method+'_bus', ('BUS_I','VM_pu','VA_deg')), key=lambda r:r['BUS_I'])
                history = rows(book, method+'_conv', ('Iteracion','Error_max_pu'))
                flows = rows(book, method+'_branch', ('Rama','Desde','Hasta','P_loss_MW'))
                comp = case['comparison'][method]
                if [r['BUS_I'] for r in voltage] != sorted(ids):
                    raise ValueError('Identificadores de tensión incorrectos.')
                for row in voltage:
                    if finite(row['VM_pu']) <= 0:
                        raise ValueError('Tensión no positiva.')
                    finite(row['VA_deg'])
                for row in history:
                    if finite(row['Error_max_pu']) < 0:
                        raise ValueError('Desbalance negativo.')
                if [r['Iteracion'] for r in history] != list(range(int(comp['Iteraciones'])+1)):
                    raise ValueError('Historial incompleto.')
                if not math.isclose(history[-1]['Error_max_pu'], comp['Error_final_pu'], rel_tol=1e-8, abs_tol=1e-14):
                    raise ValueError('Error final inconsistente.')
                if len(flows) != len(case['branch']) or not math.isclose(
                        sum(finite(r['P_loss_MW']) for r in flows), comp['Perdidas_P_MW'], rel_tol=1e-8, abs_tol=1e-6):
                    raise ValueError('Pérdidas de ramas inconsistentes.')
                case['voltage'][method], case['history'][method], case['flows'][method] = voltage, history, flows
            case_metrics(case)
            cases[number] = case
        finally:
            book.close()
        if before != fingerprint(path):
            raise ValueError(f'{path.name} cambió durante la lectura.')
        files.append(before)
    path = root/'validacion_MATPOWER.xlsx'
    before = fingerprint(path)
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        validation = rows(book, 'resumen', ('Case','Method','MaxAbsVMError_pu','MaxAbsVAError_deg',
                                           'MaxAbsBranchPError_MW','MaxAbsBranchQError_MVAr','Passed'))
        pairs = {(int(normalized(r['Case']).replace('ieee','')), method_code(r['Method'])) for r in validation}
        if len(validation) != 9 or pairs != {(c,m) for c in cases for m in METHODS}:
            raise ValueError('Se requieren nueve comparaciones únicas.')
        for record in validation:
            if not true(record['Passed']):
                raise ValueError('Comparación MATPOWER no aprobada.')
            for key in ('MaxAbsVMError_pu','MaxAbsVAError_deg','MaxAbsBranchPError_MW','MaxAbsBranchQError_MVAr'):
                if finite(record[key]) < 0:
                    raise ValueError('Error de validación negativo.')
        for number, case in cases.items():
            case['reference'] = rows(book, f'IEEE{number}_NR_bus', ('BUS_I','Own_VM_pu','Reference_VM_pu','AbsVMError_pu'))
            case['reference'].sort(key=lambda r:r['BUS_I'])
            if [r['BUS_I'] for r in case['reference']] != [r['BUS_I'] for r in case['voltage']['NR']]:
                raise ValueError('La referencia no coincide con las barras de la solución.')
            if max(abs(a['Own_VM_pu']-b['VM_pu']) for a,b in zip(case['reference'],case['voltage']['NR'])) > 1e-10:
                raise ValueError('La validación corresponde a otra solución propia.')
    finally:
        book.close()
    if before != fingerprint(path):
        raise ValueError('La validación cambió durante la lectura.')
    files.append(before)
    meta_path = root/'validacion_MATPOWER.json'
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    if not metadata['allPassed'] or not metadata['officialIEEE118InputCheck']['matches']:
        raise ValueError('No se confirma el caso oficial IEEE118.')
    files.append(fingerprint(meta_path))
    return cases, validation, metadata, files


def plot_style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.labelsize':17,
        'xtick.labelsize':14,'ytick.labelsize':14,'axes.spines.top':False,'axes.spines.right':False,
        'axes.edgecolor':'#CBD5E1','text.color':'#'+INK,'axes.labelcolor':'#'+INK,
        'xtick.color':'#'+MUTED,'ytick.color':'#'+MUTED,'legend.frameon':False,
        'figure.facecolor':'white','savefig.facecolor':'white'})


def save_plot(figure, path, transparent=False):
    figure.savefig(path,dpi=180,bbox_inches='tight',pad_inches=.15,transparent=transparent,
                   facecolor='none' if transparent else figure.get_facecolor())
    plt.close(figure)
    return path


def topology(case,path,dark=False):
    ids=sorted(r['BUS_I'] for r in case['bus']); index={bus:i for i,bus in enumerate(ids)}
    edges=[(index[r['F_BUS']],index[r['T_BUS']]) for r in case['branch'] if r['STATUS']!=0]
    n=len(ids); adj=np.zeros((n,n))
    for i,j in edges: adj[i,j]=adj[j,i]=1
    pos=np.random.default_rng(5215).uniform(-1,1,(n,2)); spring=1/np.sqrt(n)
    for step in range(300):
        delta=pos[:,None,:]-pos[None,:,:]; dist=np.maximum(np.linalg.norm(delta,axis=2),.025)
        force=(delta*(spring**2/dist**2-adj*dist/spring)[:,:,None]).sum(axis=1)
        norm=np.maximum(np.linalg.norm(force,axis=1),1e-10)
        pos+=force/norm[:,None]*np.minimum(norm,.07*(1-step/300)+.001)[:,None]
        pos-=pos.mean(axis=0)
    _,axes=np.linalg.eigh(np.cov(pos,rowvar=False));pos=pos@axes[:,::-1]
    fig,ax=plt.subplots(figsize=(8,4.4)); bg='#'+NAVY if dark else 'white'
    fig.patch.set_facecolor(bg);ax.set_facecolor(bg)
    ax.add_collection(LineCollection([(pos[a],pos[b]) for a,b in edges],colors='#72ADC9' if dark else '#A6B6C7',lw=.9,alpha=.7))
    types={r['BUS_I']:r['TYPE'] for r in case['bus']}
    for kind,marker,color,size in ((1,'o','#AFC0D1' if dark else '#55748E',12),(2,'o','#4ED7C4' if dark else '#008878',26),(3,'D','#FFC667',75)):
        subset=[index[b] for b in ids if types[b]==kind]
        ax.scatter(pos[subset,0],pos[subset,1],s=size,color=color,marker=marker,zorder=3)
    ax.autoscale();ax.margins(.08);ax.set_aspect('equal');ax.axis('off')
    return save_plot(fig,path)
