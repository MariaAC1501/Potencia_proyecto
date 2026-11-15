"""Refresh the expanded report from existing, read-only numerical evidence.

python tools/build_report.py
Updates the full technical report plus the video scenario, builds report figures,
and produces Markdown, PDF (Typst) and real Word (.docx). The compatible entry
point delegates to build_video_report.py. Never starts MATLAB,
changes workbooks or modifies an already-open desktop session.
"""
from __future__ import annotations

from datetime import datetime,timezone
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pymupdf
from openpyxl import load_workbook

from presentation_data import (ROOT,METHODS,NAMES,COLORS,NAVY,INK,MUTED,TEAL,BLUE,ORANGE,
                                load_evidence,case_metrics,fingerprint,plot_style,save_plot)

BLOCKS=('inventario','tipos_barras','parametros','resultados_14','resultados_118','resultados_300',
        'tensiones','balance_activo','balance_reactivo','acuerdo_interno','validacion_tensiones',
        'validacion_flujos','diagnosticos','archivos_evidencia')


def table(header,body,left=(0,)):
    def row(values):
        values=[str(v) for v in values]
        if any('|' in v or '\n' in v for v in values):
            raise ValueError('No se admiten barras o saltos en una celda Markdown.')
        return '| '+' | '.join(values)+' |'
    return '\n'.join([row(header),row(['---' if i in left else '---:' for i in range(len(header))])]
                     +[row(values) for values in body])


def number(value,default=0):
    return default if value is None else float(value)


def study(case):
    result=case_metrics(case);voltage=case['voltage']['NR']
    result['q_generation']=sum(r['Q_gen_calculada_MVAr'] for r in voltage)
    result['q_demand']=sum(r['Q_load_MVAr'] for r in voltage)
    result['q_branch']=sum(r['Q_loss_MVAr'] for r in case['flows']['NR'])
    result['q_shunt']=-sum(r['BS']*r['VM_pu']**2 for r in voltage)
    result['p_residual']=result['generation']-result['demand']-result['loss']-result['shunt']
    result['q_residual']=result['q_generation']-result['q_demand']-result['q_branch']-result['q_shunt']
    if abs(result['q_residual'])>1e-6:
        raise ValueError('El balance reactivo no cierra.')
    active={g['GEN_BUS'] for g in case['gen'] if g['STATUS']!=0}
    result['pv']=sum(r['TYPE']==2 and r['BUS_I'] in active for r in case['bus'])
    result['pq']=sum(r['TYPE']==1 or (r['TYPE']==2 and r['BUS_I'] not in active) for r in case['bus'])
    result['slack']=next(r['BUS_I'] for r in case['bus'] if r['TYPE']==3)
    result['unknowns']=len(case['bus'])-1+result['pq']
    result['voltage_violations']=sum(r['VM_pu']<r['VMIN']-1e-8 or r['VM_pu']>r['VMAX']+1e-8 for r in voltage)
    q_violations=[]
    for row in voltage:
        if row['TYPE']!=2:continue
        units=[g for g in case['gen'] if g['GEN_BUS']==row['BUS_I'] and g['STATUS']!=0]
        if not units:continue
        lower=sum(number(g.get('QMIN'),-math.inf) for g in units)
        upper=sum(number(g.get('QMAX'),math.inf) for g in units)
        if row['Q_gen_calculada_MVAr']<lower-1e-6 or row['Q_gen_calculada_MVAr']>upper+1e-6:
            q_violations.append(row['BUS_I'])
    result['q_violations']=q_violations
    result['rated_branches']=sum(number(r.get('RATE_A'))>0 and r['STATUS']!=0 for r in case['branch'])
    reference=case['voltage']['NR'];vm=[];va=[];loss=[]
    for method in METHODS:
        other=case['voltage'][method]
        vm.append(max(abs(a['VM_pu']-b['VM_pu']) for a,b in zip(other,reference)))
        va.append(max(abs((a['VA_deg']-b['VA_deg']+180)%360-180) for a,b in zip(other,reference)))
        loss.append(abs(case['comparison'][method]['Perdidas_P_MW']-result['loss']))
    result['internal_vm']=max(vm);result['internal_va']=max(va);result['internal_loss']=max(loss)
    return result


def base_mva(path):
    book=load_workbook(path,read_only=True,data_only=True)
    try:
        if 'config' not in book.sheetnames:return 100
        values=[value for row in book['config'].iter_rows(min_row=2,values_only=True) for value in row
                if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)]
        if not values or values[0]<=0:raise ValueError('Base MVA inválida en el Excel.')
        return values[0]
    finally:book.close()


def generated_tables(cases,validation,metadata,metrics,files,root):
    output={}
    output['inventario']=table(['Caso','Barras','Ramas','Registros gen.','Base MVA'],[
        [f'IEEE-{n}',n,len(c['branch']),len(c['gen']),f"{base_mva(root/'data'/f'IEEE{n}.xlsx'):g}"] for n,c in cases.items()])
    output['tipos_barras']=table(['Caso','Slack (BUS_I)','PV efectivas','PQ efectivas','Incógnitas'],[
        [f'IEEE-{n}',m['slack'],m['pv'],m['pq'],m['unknowns']] for n,m in metrics.items()])
    output['parametros']=table(['Parámetro','Solución propia','Referencia'],[
        ['Método','NR, GS y FD','NR de MATPOWER'],['Tolerancia de potencia','1e-8 pu','1e-10 pu'],
        ['Máximo IEEE-14 / IEEE-118','1000','30'],['Máximo IEEE-300','30000','30'],
        ['Relajación GS','1.5','No aplica'],['Aplicar límites Q','No','No'],
        ['Inicialización','VM/VA y VG activa','Datos equivalentes'],['MATPOWER','No requerido por main',metadata['matpowerVersion']]],left=(0,1,2))
    for n,case in cases.items():
        output[f'resultados_{n}']=table(['Método','Iter.','Error final (pu)','P ramas (MW)','Tiempo (s)'],[
            [NAMES[m],r['Iteraciones'],f"`{r['Error_final_pu']:.4e}`",f"{r['Perdidas_P_MW']:.6f}",f"{r['Tiempo_s']:.6f}"]
            for m in METHODS for r in [case['comparison'][m]]])
    output['tensiones']=table(['Caso','VM mínima (pu)','BUS_I mín.','VM máxima (pu)','BUS_I máx.'],[
        [f'IEEE-{n}',f"{m['minimum']['VM_pu']:.6f}",m['minimum']['BUS_I'],f"{m['maximum']['VM_pu']:.6f}",m['maximum']['BUS_I']]
        for n,m in metrics.items()])
    output['balance_activo']=table(['Caso','P generación','P demanda','P ramas','P shunts'],[
        [f'IEEE-{n}']+[f'{m[k]:.6f}' for k in ('generation','demand','loss','shunt')] for n,m in metrics.items()])
    output['balance_activo']+='\n\nTodas las potencias están en MW. Máximo residuo de balance activo: '
    output['balance_activo']+=f"`{max(abs(m['p_residual']) for m in metrics.values()):.3e} MW`. Las conductancias shunt de IEEE-300 se evalúan a la tensión resuelta."
    output['balance_reactivo']=table(['Caso','Q generación','Q demanda','Q ramas','Q shunts'],[
        [f'IEEE-{n}']+[f'{m[k]:.6f}' for k in ('q_generation','q_demand','q_branch','q_shunt')] for n,m in metrics.items()])
    output['balance_reactivo']+='\n\nPotencias en MVAr; Q shunts es absorción neta, negativa si hay aporte capacitivo. Máximo residuo reactivo: '
    output['balance_reactivo']+=f"`{max(abs(m['q_residual']) for m in metrics.values()):.3e} MVAr`."
    output['acuerdo_interno']=table(['Caso','Máx. diferencia VM (pu)','Máx. diferencia VA (°)','Diferencia P ramas (MW)'],[
        [f'IEEE-{n}']+[f'`{m[k]:.3e}`' for k in ('internal_vm','internal_va','internal_loss')] for n,m in metrics.items()])
    short={'Newton-Raphson':'NR','Gauss-Seidel':'GS','Desacoplado rápido':'FD'}
    output['validacion_tensiones']=table(['Caso','Método','Error VM (pu)','Error VA (°)','Aceptación'],[
        [r['Case'],short.get(r['Method'],r['Method']),f"`{r['MaxAbsVMError_pu']:.3e}`",f"`{r['MaxAbsVAError_deg']:.3e}`",'Sí' if r['Passed'] else 'No']
        for r in validation],left=(0,1,4))
    output['validacion_flujos']=table(['Caso','Método','Error P rama (MW)','Error Q rama (MVAr)','Error P total (MW)'],[
        [r['Case'],short.get(r['Method'],r['Method']),f"`{r['MaxAbsBranchPError_MW']:.3e}`",f"`{r['MaxAbsBranchQError_MVAr']:.3e}`",f"`{r['AbsPLossError_MW']:.3e}`"]
        for r in validation],left=(0,1))
    output['diagnosticos']=table(['Caso','Barras fuera de VMIN/VMAX','PV fuera de Q agregado','Ramas activas con RATE_A'],[
        [f'IEEE-{n}',m['voltage_violations'],len(m['q_violations']),f"{m['rated_branches']} / {len(cases[n]['branch'])}"] for n,m in metrics.items()])
    output['diagnosticos']+='\n\nDiagnóstico posterior sobre Newton-Raphson, con tolerancia 1e-8 pu para tensión y 1e-6 MVAr para límites Q. '
    output['diagnosticos']+='Una PV se cuenta si la Q total requerida excede la suma de los límites de sus generadores activos. Esto no es una nueva corrida con límites Q aplicados. '
    for n,m in metrics.items():
        if m['q_violations']:
            ids=', '.join(str(bus) for bus in m['q_violations'])
            output['diagnosticos']+=f"\n\nEn IEEE-{n} se detectan {len(m['q_violations'])} barras PV fuera del intervalo Q agregado: BUS_I = {ids}. "
            output['diagnosticos']+='El resultado sigue siendo una solución de las ecuaciones sin aplicar límites Q, pero no acredita factibilidad reactiva. La Slack no está incluida en este recuento.'
    if all(m['rated_branches']==0 for m in metrics.values()):
        output['diagnosticos']+='\n\nNinguno de los tres libros dispone de RATE_A positivo en las ramas activas; no puede concluirse ausencia de sobrecargas térmicas.'
    descriptions=[]
    for record in files:
        path=Path(record['path']);stamp=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        descriptions.append([f'`{path.name}`',stamp,f"`{record['sha256'][:12]}`"])
    output['archivos_evidencia']=table(['Archivo','Modificado (UTC)','SHA-256, prefijo'],descriptions,left=(0,1,2))
    output['archivos_evidencia']+='\n\nLos hashes completos y la fecha de compilación están en `informe_assets/datos_informe.json`. Las fechas anteriores son de modificación de archivos, no una certificación de cuándo comenzó cada cálculo.'
    return output


def refresh_tables(path,blocks):
    text=path.read_text(encoding='utf-8')
    for name,body in blocks.items():
        start=f'<!-- BEGIN:{name} -->';end=f'<!-- END:{name} -->'
        if text.count(start)!=1 or text.count(end)!=1:
            raise ValueError(f'El informe debe contener una sola pareja de marcadores para {name}.')
        pattern=re.compile(re.escape(start)+r'.*?'+re.escape(end),re.DOTALL)
        text=pattern.sub(lambda _:start+'\n\n'+body+'\n\n'+end,text)
    path.write_text(text,encoding='utf-8')


def diagram_box(ax,text,x,y,w,h,fill='#EFF4F9',color='#1B3049',size=13):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.02,rounding_size=.04',fc=fill,ec='#CCD7E4',lw=1.1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size,color=color)


def arrow(ax,a,b,color='#008878',dashed=False):
    ax.annotate('',b,a,arrowprops={'arrowstyle':'->','lw':1.8,'color':color,'linestyle':'--' if dashed else '-'})


def diagram_figures(assets):
    fig,ax=plt.subplots(figsize=(11.5,4.5));ax.set(xlim=(0,12),ylim=(0,4.5));ax.axis('off')
    for x,text in [(0.1,'Excel de entrada\nbus · gen · branch'),(3.2,'Importar y validar\nload_case_excel'),(6.3,'Solución propia\nNR · GS · FD'),(9.4,'Resultados\nExcel + gráficas')]:
        diagram_box(ax,text,x,2.5,2.45,1.1)
    for x in (2.55,5.65,8.75):arrow(ax,(x,3.05),(x+.65,3.05))
    diagram_box(ax,'GUI: cargar, editar y ejecutar',3.2,.45,3.0,.8,fill='#E4F5F0')
    diagram_box(ax,'MATPOWER 8.1\nValidación separada',8.1,.35,3.7,1.0,fill='#FFF0E4')
    arrow(ax,(4.7,1.25),(4.7,2.5));arrow(ax,(10,1.35),(10.6,2.5),dashed=True)
    save_plot(fig,assets/'arquitectura.png')
    fig,ax=plt.subplots(figsize=(11.5,4.0));ax.set(xlim=(0,12),ylim=(0,4));ax.axis('off')
    headings=[('Newton-Raphson',BLUE,'Desbalances → Jacobiano\n→ corrección conjunta'),
              ('Gauss-Seidel',ORANGE,'Barrido de barras\n→ reutilizar tensiones nuevas'),
              ('Desacoplado rápido',TEAL,'P–ángulo → reevaluar Q\n→ Q–magnitud')]
    for j,(title,color,body) in enumerate(headings):
        x=.15+j*4.0;ax.text(x+1.75,3.55,title,ha='center',fontsize=15,weight='bold',color='#'+color)
        diagram_box(ax,body,x,1.65,3.5,1.1,size=12)
        arrow(ax,(x+1.75,1.65),(x+1.75,.95),'#'+color)
        ax.text(x+1.75,.55,'Evaluar el desbalance AC',ha='center',fontsize=12,color='#'+MUTED)
    save_plot(fig,assets/'metodos.png')
    capture=ROOT/'escenario1_assets/gui_caso_base.png'
    if not capture.is_file():
        capture=ROOT/'presentacion_assets/capturas/gui_ejecutado.png'
    if not capture.is_file():raise FileNotFoundError('Falta la captura real de la interfaz.')
    shutil.copyfile(capture,assets/'interfaz.png')


def result_figures(cases,validation,assets):
    for n,case in cases.items():
        fig,ax=plt.subplots(figsize=(11.5,4.1),layout='constrained')
        for method in METHODS:
            h=[r for r in case['history'][method] if r['Iteracion']>0 and r['Error_max_pu']>0]
            ax.plot([r['Iteracion'] for r in h],[r['Error_max_pu'] for r in h],lw=2.4,color='#'+COLORS[method],label=NAMES[method])
        ax.axhline(1e-8,ls='--',color='#64748B',lw=1.4,label='Tolerancia 10⁻⁸ pu')
        ax.set(xscale='log',yscale='log',xlabel='Iteración (sin el estado inicial)',ylabel='Desbalance máximo [pu]')
        ax.grid(alpha=.18);ax.legend(fontsize=12,ncol=4,loc='lower center',bbox_to_anchor=(.5,1.02))
        save_plot(fig,assets/f'convergencia_IEEE{n}.png')
        fig,axes=plt.subplots(1,2,figsize=(11.5,4.1),layout='constrained')
        bus=sorted(case['bus'],key=lambda r:r['BUS_I']);ids=[r['BUS_I'] for r in bus]
        contiguous=ids==list(range(ids[0],ids[0]+len(ids)));x=ids if contiguous else list(range(1,len(ids)+1))
        axes[0].fill_between(x,[r['VMIN'] for r in bus],[r['VMAX'] for r in bus],color='#EEF3F8')
        for method,style in zip(METHODS,('-','--',':')):
            for ax,column in zip(axes,('VM_pu','VA_deg')):
                ax.plot(x,[r[column] for r in case['voltage'][method]],lw=2.0,ls=style,color='#'+COLORS[method],label=method)
        for ax,label in zip(axes,('Magnitud [pu]','Ángulo [°]')):
            ax.set(xlabel='BUS_I' if contiguous else 'Posición ordenada por BUS_I',ylabel=label,xlim=(x[0],x[-1]));ax.grid(alpha=.18)
        axes[0].legend(fontsize=12,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.15))
        save_plot(fig,assets/f'estado_IEEE{n}.png')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.3),layout='constrained');centers=np.arange(3)
    for ax,key,ylabel in zip(axes,('Iteraciones','Tiempo_s'),('Iteraciones','Tiempo registrado [s]')):
        for j,method in enumerate(METHODS):
            values=[cases[n]['comparison'][method][key] for n in (14,118,300)]
            bars=ax.bar(centers+(j-1)*.25,values,.22,color='#'+COLORS[method],label=method)
            for bar,value in zip(bars,values):
                text=str(int(value)) if key=='Iteraciones' else f'{value:.3g}'
                ax.annotate(text,(bar.get_x()+bar.get_width()/2,value),xytext=(0,5),textcoords='offset points',ha='center',fontsize=11)
        ax.set(yscale='log',ylabel=ylabel);ax.set_xticks(centers,['IEEE-14','IEEE-118','IEEE-300']);ax.margins(y=.25)
        ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].legend(ncol=3,fontsize=12,loc='lower center',bbox_to_anchor=(.5,1.02))
    save_plot(fig,assets/'comparacion_metodos.png')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.1),layout='constrained')
    for ax,key,label,limit in zip(axes,('MaxAbsVMError_pu','MaxAbsVAError_deg'),('Error VM [pu]','Error VA [°]'),(1e-7,1e-5)):
        for j,method in enumerate(METHODS):
            values=[]
            for n in (14,118,300):
                record=next(r for r in validation if int(str(r['Case']).replace('IEEE',''))==n and
                            (r['Method']==NAMES[method] or (method=='FDLF' and str(r['Method']).startswith('Desacoplado'))))
                values.append(record[key])
            ax.bar(centers+(j-1)*.25,values,.22,color='#'+COLORS[method],label=method)
        ax.axhline(limit,color='#64748B',ls='--',label='Umbral');ax.set(yscale='log',ylabel=label)
        ax.set_xticks(centers,['IEEE-14','IEEE-118','IEEE-300']);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].legend(ncol=4,fontsize=11,loc='lower center',bbox_to_anchor=(.5,1.02))
    save_plot(fig,assets/'validacion_tensiones.png')


def refresh_legacy_report():
    """Preserve and refresh the complete original technical report and figures."""
    assets=ROOT/'informe_assets';assets.mkdir(exist_ok=True)
    cases,validation,metadata,files=load_evidence(ROOT)
    metrics={n:study(case) for n,case in cases.items()}
    for n in cases:files.append(fingerprint(ROOT/'data'/f'IEEE{n}.xlsx'))
    tables=generated_tables(cases,validation,metadata,metrics,files,ROOT)
    if set(tables)!=set(BLOCKS):raise ValueError('Bloques numéricos incompletos.')
    refresh_tables(ROOT/'INFORME_PROYECTO_MATLAB.md',tables)
    plot_style();diagram_figures(assets);result_figures(cases,validation,assets)
    code_files=[fingerprint(path) for path in sorted((ROOT/'matlab').glob('*.m'))]
    verification_logs=[fingerprint(path) for path in [ROOT/'verificacion_MATLAB.log',
        ROOT/'escenario1_assets/pruebas_GUI_escenario1.log', ROOT/'escenario1_assets/pruebas_escenario1.log'] if path.is_file()]
    gui_sources=[fingerprint(path) for path in [ROOT/'escenario1_assets/gui_caso_base.png',
        ROOT/'escenario1_assets/gui_salida_26_30.png', ROOT/'escenario1_assets/captura_GUI_escenario1.json'] if path.is_file()]
    data={'compiled_at_utc':datetime.now(timezone.utc).isoformat(),
          'description':'Lectura de resultados guardados; no se ejecutaron nuevamente los solucionadores.',
          'files':files,'code_files':code_files,'verification_logs':verification_logs,'gui_capture_inputs':gui_sources,
          'reference_metadata':metadata,'case_analysis':metrics,
          'document_source':fingerprint(ROOT/'INFORME_PROYECTO_MATLAB.md'),
          'document_template':fingerprint(ROOT/'INFORME_PROYECTO_MATLAB.typ'),
          'figures':[fingerprint(path) for path in sorted(assets.glob('*.png'))],
          'comparison_tables':{n:case['comparison'] for n,case in cases.items()}}
    (assets/'datos_informe.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    typst=shutil.which('typst')
    if not typst:raise RuntimeError('Typst no está disponible.')
    pdf=ROOT/'INFORME_PROYECTO_MATLAB.pdf'
    subprocess.run([typst,'compile',str(ROOT/'INFORME_PROYECTO_MATLAB.typ'),str(pdf)],cwd=ROOT,check=True)
    with pymupdf.open(pdf) as document:
        text='\n'.join(page.get_text() for page in document)
        for marker in ('IEEE-14','IEEE-118','IEEE-300','132.862872','408.985541'):
            if marker not in text:raise ValueError(f'Falta contenido en PDF: {marker}')
        if len(document)<12:raise ValueError('El documento no parece contener la ampliación completa.')
        compact=lambda value:re.sub(r'\s+','',value.replace('\u00ad',''))
        headings=re.findall(r'^## (.+)$',(ROOT/'INFORME_PROYECTO_MATLAB.md').read_text(encoding='utf-8'),re.MULTILINE)
        for heading in headings:
            if compact(heading) not in compact(text):raise ValueError(f'Falta una sección: {heading}')
        for index,page in enumerate(document,1):
            if len(page.get_text().strip())<20:raise ValueError(f'Página vacía: {index}')
            for block in page.get_text('blocks'):
                if block[0]<42 or block[2]>page.rect.width-42:
                    raise ValueError(f'Desbordamiento horizontal en página {index}')
        page_count=len(document);bookmark_count=len(document.get_toc())
        print(f'Informe ampliado: {page_count} páginas, {bookmark_count} entradas de índice.')
    manifest={'built_at_utc':data['compiled_at_utc'],'inputs':files,'code_files':code_files,
              'outputs':[fingerprint(path) for path in [ROOT/'INFORME_PROYECTO_MATLAB.md',ROOT/'INFORME_PROYECTO_MATLAB.typ',assets/'datos_informe.json',pdf]],
              'pages':page_count,'bookmarks':bookmark_count,'chapters':len(headings),'figures':len(data['figures']),
              'verification':'Sections present, numerical evidence consistent, no horizontal overflow'}
    (assets/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'PDF: {pdf}\nDatos y tablas: {assets}')
    for n,m in metrics.items():print(f"IEEE-{n}: PV con Q fuera de límites={len(m['q_violations'])}; P shunt={m['shunt']:.6f} MW")


def main():
    # Both entry points now preserve the scenario and produce the required Word.
    from build_video_report import main as build_video_report
    build_video_report()


if __name__=='__main__':main()
