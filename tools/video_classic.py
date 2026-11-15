"""Previous white/navy presentation format, with current content and questions.

The layout is deliberately the earlier title/table/list format. Evidence is
read-only, and every speaker note remains identical to the shared story.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

NAVY, INK, TEAL, BLUE, ORANGE, PALE, MUTED = ('10263F','20364C','007E74','2463A4','B34F16','EFF4F8','52667C')
METHODS = ('NR','GS','FDLF')


def f(value, places=3):
    return f'{value:.{places}f}'.replace('.',',')


def make_charts(e, assets, root):
    assets, root = Path(assets), Path(root)
    assets.mkdir(exist_ok=True,parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig, ax = plt.subplots(figsize=(11,3.65),layout='constrained')
    for key,label,color in (('base','Caso base',BLUE),('scenario','Sin 26–30',ORANGE)):
        rows=e[key]['NR_bus']
        ax.plot([r['BUS_I'] for r in rows],[r['VM_pu'] for r in rows],
                label=label,color='#'+color,lw=1.8,ls='-' if key=='base' else '--')
    ax.axhspan(.95,1.05,color='#'+TEAL,alpha=.07)
    ax.axhline(.95,ls='--',color='#'+MUTED);ax.axhline(1.05,ls='--',color='#'+MUTED)
    low=min(e['scenario']['NR_bus'],key=lambda r:r['VM_pu'])
    ax.scatter([low['BUS_I']],[low['VM_pu']],color='#'+ORANGE,s=45,zorder=5)
    ax.annotate(f"Barra {low['BUS_I']}: {f(low['VM_pu'],6)} pu",(low['BUS_I'],low['VM_pu']),
                xytext=(27,.925),arrowprops={'arrowstyle':'->'},fontsize=11)
    ax.set(xlabel='Número de barra',ylabel='Tensión [pu]',xlim=(1,118),ylim=(.917,1.06))
    ax.legend(loc='upper center',ncol=2);ax.grid(axis='y',alpha=.15)
    voltage=assets/'video_perfil_base_escenario.png';fig.savefig(voltage,dpi=180);plt.close(fig)
    crop=root/'escenario1_assets/unifilar_region_26_30_anotado.png'
    return {'voltage':voltage,'crop':crop,
            'gui_base':root/'escenario1_assets/gui_caso_base.png',
            'gui_scenario':root/'escenario1_assets/gui_salida_26_30.png'}


class ClassicDeck:
    def __init__(self,assets,count):
        self.prs=Presentation();self.prs.slide_width=Inches(13.333333);self.prs.slide_height=Inches(7.5)
        self.prs.core_properties.title='IEEE118 — Video escenario 1, salida línea 26–30'
        self.prs.core_properties.author='MI-5215 · Integrantes pendientes de completar'
        self.assets,self.count=Path(assets),count

    def text(self,s,text,x,y,w,h,size=23,color=INK,bold=False,font='Aptos'):
        obj=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        frame=obj.text_frame;frame.word_wrap=True
        frame.margin_left=frame.margin_right=Inches(.02)
        frame.margin_top=frame.margin_bottom=Inches(.01)
        for i,line in enumerate(str(text).split('\n')):
            p=frame.paragraphs[0] if i==0 else frame.add_paragraph();p.text=line
            p.font.name=font;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color)
            p.space_after=Pt(5)
        return obj

    def new(self,spec,index):
        s=self.prs.slides.add_slide(self.prs.slide_layouts[6])
        s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor(255,255,255)
        self.text(s,spec['section'].upper(),.55,.25,11.9,.35,13,TEAL,True)
        self.text(s,spec['title'],.55,.82,12.2,.85,29,NAVY,True)
        self.text(s,'MI-5215 · IEEE118 · Escenario 1 · Apoyo estático; video real pendiente',.55,7.12,11,.25,10,MUTED)
        self.text(s,f'{index:02d}/{self.count}',12,7.1,.8,.3,11,MUTED)
        return s

    def bullets(self,s,items,x=.7,y=1.92,w=11.9,step=1.12,size=25):
        for i,item in enumerate(items):self.text(s,'• '+item,x,y+i*step,w,step-.10,size)

    def caption(self,s,text):self.text(s,text,.65,6.65,12,.38,12,MUTED)

    def code(self,s,text,x=.75,y=2,w=11.9,h=2.4,size=18):
        self.text(s,text,x,y,w,h,size,BLUE,False,'Consolas')

    def image(self,s,path,x,y,w,h):
        with Image.open(path) as image:ratio=image.width/image.height
        width=min(w,h*ratio);height=width/ratio
        s.shapes.add_picture(str(path),Inches(x+(w-width)/2),Inches(y+(h-height)/2),width=Inches(width),height=Inches(height))

    def table(self,s,headers,rows,widths,y=2,size=20,row_h=.68,x=.65):
        shape=s.shapes.add_table(len(rows)+1,len(headers),Inches(x),Inches(y),Inches(sum(widths)),Inches(row_h*(len(rows)+1)))
        for col,width in enumerate(widths):shape.table.columns[col].width=Inches(width)
        for i,row in enumerate([headers]+rows):
            shape.table.rows[i].height=Inches(row_h)
            for j,value in enumerate(row):
                cell=shape.table.cell(i,j);cell.text=str(value);cell.vertical_anchor=MSO_ANCHOR.MIDDLE
                cell.margin_left=cell.margin_right=Inches(.08);cell.margin_top=cell.margin_bottom=Inches(.025)
                cell.fill.solid();cell.fill.fore_color.rgb=RGBColor.from_string(NAVY if i==0 else PALE if i%2 else 'FFFFFF')
                for p in cell.text_frame.paragraphs:
                    p.font.name='Aptos';p.font.size=Pt(size-1 if i==0 else size);p.font.bold=i==0
                    p.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else INK)
        return shape


def _methods(d,s,records):
    rows=[[m,str(r['Iteraciones']),f(r['Tiempo_s'],4),f"{r['Error_final_pu']:.2e}",
           f(r['P_slack_MW']),f(r['Perdidas_P_MW']),f(r['Perdidas_Q_MVAr'])] for m,r in zip(METHODS,records)]
    d.table(s,['Método','Iter.','Tiempo\n[s]','Mismatch\n[pu]','P slack\n[MW]','Pérdidas P\n[MW]','Pérdidas Q\n[MVAr]'],
            rows,[1.3,.8,1.5,1.7,2.,2.25,2.4],size=20,row_h=.8)
    d.text(s,'NR: Newton-Raphson · GS: Gauss-Seidel · FDLF: desacoplado rápido',.75,5.43,11.9,.45,18,TEAL,True)
    d.text(s,'Una corrida. Tiempo: solución + ensamblado + consola; sin Excel ni gráficas.',.75,6,11.9,.5,18,MUTED)


def build_deck(e,story,charts,root,assets):
    root=Path(root);d=ClassicDeck(assets,len(story));comp=e['comparison']
    b=e['base_methods'][0];sc=e['scenario_methods'][0]
    for index,spec in enumerate(story,1):
        s=d.new(spec,index);kind=spec['kind']
        if kind=='question':
            d.text(s,spec['question'],.85,2.1,11.65,3.35,36,NAVY,True)
            d.caption(s,'Pregunta del escenario 1. La respuesta se presenta en la siguiente diapositiva.')
        elif kind=='cover':
            d.text(s,'Programación y análisis de flujos de potencia',.75,2,11.9,.75,33,TEAL,True)
            d.text(s,'Instituto Tecnológico de Costa Rica · MI-5215\nII semestre 2026 · MATLAB + Excel',.75,3.02,11.9,1.,25)
            d.text(s,'Integrantes: [COMPLETAR TODOS LOS NOMBRES REALES]',.75,4.35,11.9,.7,24,ORANGE,True)
            d.text(s,'Voces por sección: asignar antes de grabar; cada integrante se identifica.',.75,5.25,11.9,.6,23)
            total=sum(item['seconds'] for item in story)
            d.caption(s,f'Plan: {total//60:02d}:{total%60:02d} · 0 Presentación → 1 Configuración → 2 Red → 3 Base → 4 Escenario → 5 Cierre')
        elif kind=='architecture':
            d.bullets(s,['app_flows.m / main.m → cargar y validar los datos',
                         'solve_power_flow.m → NR / GS / desacoplado rápido',
                         'build_ybus.m + assemble_result.m + calculate_branch_flows.m',
                         'export_results_excel.m → comparación, barras, ramas e historiales'],size=24,step=1.05)
            d.caption(s,'GUI: Ejecutar métodos → Retirar línea 26–30 → comparar → Volver al caso base. MATPOWER solo valida.')
        elif kind=='inputs':
            d.table(s,['Hoja','Columnas para mostrar','Unidades / significado'],[
                ['config','baseMVA','100 MVA'],['bus','BUS_I, TYPE, PD/QD, VM/VA, GS/BS','MW / MVAr; pu / grados; shunts a 1 pu'],
                ['gen','GEN_BUS, PG/QG, VG, QMIN/QMAX, STATUS','MW / MVAr; consigna VG en pu'],
                ['branch','F_BUS/T_BUS, BR_R/X/B, TAP, SHIFT, STATUS','R/X/B en pu; SHIFT en grados']],
                [1.2,5.4,5.35],row_h=.83,size=18)
            d.caption(s,'Dos libros de entrada, cuatro hojas cada uno. Salidas: base, escenario y comparación (cinco Excel principales).')
        elif kind=='bus_types':
            d.table(s,['Tipo','Conocido','Calculado','Cantidad'],[
                ['PQ (TYPE 1)','P, Q','|V|, ángulo','64'],['PV (TYPE 2)','P, |V|','Q, ángulo','53'],
                ['Slack (TYPE 3)','|V|, ángulo','P, Q','1 · barra69']], [2.7,3.,3.,3.25],row_h=.9,size=24)
            d.text(s,'Estado: 117 ángulos no slack + 64 magnitudes PQ',.75,6,11.8,.55,26,TEAL,True)
            d.caption(s,'Código: matlab/bus_sets.m, voltage_setpoints.m y specified_power.m')
        elif kind=='ybus':
            d.text(s,'Modelo π: y = 1/(R+jX)\nCarga capacitiva: jB/2 por extremo\nTap complejo: t = a·exp(j·SHIFT)\nShunts: (GS+jBS)/baseMVA\nSTATUS=0 → omitir rama',.75,2,5.6,3.9,23)
            lines=(root/'matlab/build_ybus.m').read_text(encoding='utf-8').splitlines()
            d.code(s,'\n'.join(lines[20:32]),x=6.3,y=1.96,w=6.3,h=4.4,size=16)
            d.caption(s,'Fragmento real de build_ybus.m; mostrar también n=numel(ids), shunts y salto por STATUS==0.')
        elif kind=='newton':
            d.text(s,'S(V) = V ⊙ conj(Ybus·V)\nΔS = [ΔP no slack ; ΔQ PQ]\nJ·Δx = ΔS → x nuevo = x + Δx',.8,2.02,11.8,2.1,30,BLUE,True)
            d.bullets(s,['Jacobiano H, N, M, L; resolver con J\\mis, no inv(J).',
                         'Aceptar: max|ΔS| ≤ 10⁻⁸ pu · máximo 1000 iteraciones.'],y=4.65,step=.9,size=25)
            d.caption(s,'Código para abrir: matlab/solve_newton_raphson.m y power_mismatch.m')
        elif kind=='gauss':
            d.text(s,'V candidato = [(P−jQ)/conj(V) − Σ Yim·Vm] / Yii\nV nuevo = V anterior + 1,5·(V candidato − V anterior)',.75,2,11.9,1.8,25,BLUE,True)
            d.bullets(s,['Usar valores recién calculados durante el barrido.',
                         'PV: estimar Q y restaurar |V|=VG; slack fija.',
                         'Evaluar mismatch AC tras cada barrido; tolerancia 10⁻⁸.'],y=4,step=.78,size=24)
            d.caption(s,'Código: matlab/solve_gauss_seidel.m · máximo 1000 barridos · α=1,5')
        elif kind=='decoupled':
            d.text(s,'B′·Δθ = ΔP / |V|\nReevaluar Q con el nuevo ángulo\nB″·Δ|V| = ΔQ / |V|',.8,2,11.8,2.6,29,BLUE,True)
            d.bullets(s,['Matrices formadas antes del bucle; dos correcciones secuenciales.',
                         'Aceptar con mismatch AC completo ≤ 10⁻⁸ pu.'],y=4.95,step=.7,size=23)
            d.caption(s,'Código: matlab/fast_decoupled_matrices.m y solve_fast_decoupled.m')
        elif kind=='options':
            d.table(s,['Parámetro','Valor en ambos casos'],[
                ['Tolerancia / máximo','10⁻⁸ pu / 1000'],['Relajación GS / consola','1,5 / verbose=true'],
                ['Inicio','VM/VA Excel; VG activa en PV y slack'],['Límites Q','enforceQLimits=false; conversión PV→PQ implementada, no activada']],
                [3.25,8.7],row_h=.82,size=21)
            d.caption(s,'Mostrar main.m, initial_voltage.m, apply_q_limits.m y hoja parametros. No se acredita cumplimiento Q.')
        elif kind=='result_math':
            d.bullets(s,['Flujo de extremo: S = V·conj(I)·baseMVA',
                         'Pérdida de rama: S desde + S hasta; sumar todas las ramas.',
                         'Slack: P generación = P calculada + PD; análogo para Q.',
                         'Excel: entradas, parametros, comparacion, NR/GS/FDLF_bus/branch/conv.'],step=1.,size=24)
            d.caption(s,'calculate_branch_flows.m · assemble_result.m · result_comparison.m · export_results_excel.m')
        elif kind=='small_run':
            d.code(s,spec['code'],y=2,h=2.2,size=19)
            d.bullets(s,['Corrida real <1 min: ejecutar → iteraciones → exportación.',
                         'Confirmar 14 barras; no es otra exposición de resultados.',
                         'Sin cortes ni acelerado. Duración real pendiente de comprobar.'],y=4.4,step=.72,size=23)
            d.caption(s,'nBus se obtiene de los datos. PDF y logs no sustituyen la demostración.')
        elif kind=='network_data':
            d.table(s,['Dato','Valor del archivo'],[
                ['Barras / ramas / registros gen activos','118 / 186 / 54'],['Transformadores / otras ramas','11 TAP≠0 / 175 TAP=0'],
                ['Barras con PD o QD no nulas','99'],['Demanda total','4242 MW + j1438 MVAr'],
                ['Generación P programada / slack','4377,4 MW / barra69'],['Tensión nominal','106×138 kV; 11×345 kV; barra87: 161 kV']],
                [5.2,6.75],row_h=.61,size=20)
            d.caption(s,'MATPOWER 8.1 case118, formato v2; CDF 15-Oct-2014, corrección taps 2019. Fuente: data/case118.m')
        elif kind=='published_diagram':
            d.image(s,root/'escenario1_assets/IEEE118_unifilar_UW.png',.65,1.75,7.,4.65)
            d.image(s,charts['crop'],8.,1.75,4.65,4.65)
            d.caption(s,'UW/Christie1993, AEP1962. 26=Tanners Creek; 30=Sorenson (345kV). Recorte, etiquetas y resaltado propios.')
        elif kind in ('base_run','scenario_run'):
            base=kind=='base_run'
            d.image(s,charts['gui_base' if base else 'gui_scenario'],.65,1.8,8.,4.65)
            if base:
                d.code(s,spec['code'],x=8.85,y=1.98,w=3.8,h=.95,size=17)
                d.bullets(s,['IEEE-118 · Todos','Tolerancia 10⁻⁸ · Q off','Pulsar Ejecutar métodos','Tres métodos → Excel base'],x=8.8,y=3.1,w=3.9,step=.67,size=20)
                d.text(s,'Al terminar se habilita\nRetirar línea 26–30.',8.85,5.8,3.8,.8,19,TEAL,True)
            else:
                d.text(s,'Retirar línea 26–30',8.85,2,3.8,.75,22,TEAL,True)
                d.bullets(s,['NR → GS → FDLF','Mismos parámetros','Base conservada','Comparación automática'],x=8.8,y=3,w=3.9,step=.67,size=20)
                d.text(s,'Volver al caso base\nrestaura sin recalcular.',8.85,5.8,3.8,.8,19,BLUE,True)
            d.caption(s,'Captura estática de apoyo. Grabar la toma real sin cortes: botón → solver → exportación y apertura del Excel.')
        elif kind=='base_output':
            d.table(s,['Hoja / selección','Qué verificar'],[
                ['comparacion + parametros','Convergencia, tolerancia, iteraciones y P/Q slack'],
                ['NR_bus → BUS_I=69','VM_pu, VA_deg; Pgen=513,863 MW; Qgen=−82,424 MVAr'],
                ['NR_branch → Rama=38','P/Q en ambos extremos y pérdidas por rama'],
                ['GS_bus/branch/conv y FDLF_*','Resultados e historial, incluida iteración cero']],
                [4.1,7.85],row_h=.87,size=21)
            d.caption(s,'Fuente: resultados_IEEE118_matlab.xlsx. Mostrar el Excel recién exportado, no una captura como corrida.')
        elif kind in ('base_methods','scenario_methods'):
            _methods(d,s,e['base_methods' if kind=='base_methods' else 'scenario_methods'])
            d.caption(s,'Fuente: comparacion de los resultados Excel. Q neta puede ser negativa por capacitancia; no es pérdida activa negativa.')
        elif kind=='validation':
            rows=[[m,f"{r['MaxAbsVMError_pu']:.2e}",f"{r['MaxAbsVAError_deg']:.2e}",f"{r['AbsPLossError_MW']:.2e}"] for m,r in zip(METHODS,e['validation'])]
            d.table(s,['Método','Máx |ΔV| [pu]','Máx |Δθ| [°]','|Δ pérdidas P| [MW]'],rows,[1.3,3.4,3.4,3.85],row_h=.68,size=20)
            dp=abs(b['P_slack_MW']-e['reference_slack_p']);dq=abs(b['Q_slack_MVAr']-e['reference_slack_q'])
            d.text(s,f"P slack ref: {f(e['reference_slack_p'],9)} MW; |ΔP NR|={dp:.3e} MW\nQ slack ref: {f(e['reference_slack_q'],9)} MVAr; |ΔQ NR|={dq:.3e} MVAr\nReconstrucción: flujos incidentes + carga de barra69 (sin shunts).",.75,5.02,11.8,1.25,18,TEAL,True)
            d.caption(s,'MATPOWER 8.1 NR tol1e−10, Q límites off. Fuente: validacion_MATPOWER.xlsx; base, no escenario.')
        elif kind=='base_low':
            rows=[[str(r['BUS_I']),r['TipoNombre'],f(r['VM_pu'],6),f(r['VA_deg'],4)] for r in comp['base_top5_bajas']]
            d.table(s,['Barra','Tipo','|V| [pu]','Ángulo [°]'],rows,[2.,2.,4.,3.95],row_h=.62,size=23)
            d.text(s,'Fuera del intervalo guía: 53, 76 y 118 (3 barras).',.75,6.05,11.8,.5,24,ORANGE,True)
            d.caption(s,'Fuente: base_top5_bajas. Rango guía 0,95–1,05 ≠ archivo 0,94–1,06 pu.')
        elif kind=='base_flows':
            rows=[[str(r['Rama']),f"{r['Desde']}–{r['Hasta']}",f(r['S_from_MVA']),f(r['S_to_MVA']),f(r['S_max_MVA'])] for r in comp['base_top5_flujos']]
            d.table(s,['Rama','Extremos','S desde [MVA]','S hasta [MVA]','S máx [MVA]'],rows,[1.,2.,3.,3.,2.95],row_h=.62,size=21)
            d.text(s,'S máx = max(|S desde|, |S hasta|). No es % de capacidad.',.75,6.08,11.8,.48,23,TEAL,True)
            d.caption(s,'Fuente: base_top5_flujos. RATE_A=0 en todas las ramas: no es un diagnóstico térmico.')
        elif kind=='outage_diagram':
            d.image(s,charts['crop'],.65,1.82,4.1,4.55);r=comp['linea_retirada'][0]
            d.table(s,['Extremo','P [MW]','Q [MVAr]','|S| [MVA]'],[
                ['26 → línea',f(r['P_from_MW']),f(r['Q_from_MVAr']),f(r['S_from_MVA'])],
                ['30 → línea',f(r['P_to_MW']),f(r['Q_to_MVAr']),f(r['S_to_MVA'])]],
                [2.1,1.8,2.05,2.],x=4.85,y=2,row_h=.8,size=20)
            d.text(s,'26 Tanners Creek → 30 Sorenson\nRama38 · 345 kV · pérdida base 3,978115 MW\nAl retirar: flujo=0; recalcular TODA la red.',4.98,4.75,7.6,1.6,23,TEAL,True)
            d.caption(s,'Fuente: linea_retirada. Unifilar publicado UW con resaltado propio; ver cita en PRESENTACION.md.')
        elif kind=='edit_input':
            d.table(s,['Libro','Celda','Desde','Hasta','STATUS'],[
                ['data/IEEE118.xlsx','branch!K39','26','30','1'],
                ['data/IEEE118_escenario1.xlsx','branch!K39','26','30','0 (resaltado)']],
                [5.5,2.1,1.1,1.1,2.15],size=18,row_h=.9)
            d.bullets(s,['Único cambio verificado: rama38, fila Excel39, columnaK.',
                         'Sin cambios en cargas, generadores, taps ni compensación.',
                         'La red permanece conectada; STATUS=0 elimina aporte a Ybus.'],y=4.95,step=.5,size=20)
            d.caption(s,'Mostrar la celda real en Excel, no solo esta tabla. El archivo base permanece intacto.')
        elif kind=='scenario_comparison':
            labels=['Tensión mínima [pu]','Barra mínima','Tensión máxima [pu]','Barra máxima','Barras fuera 0,95–1,05',
                    'P slack69 [MW]','Q slack69 [MVAr]','Pérdidas P [MW]','Iteraciones NR','Iteraciones GS','Q neta ramas [MVAr]']
            rows=[]
            for i,(label,r) in enumerate(zip(labels,comp['comparacion'])):
                decimals=6 if i in (0,2) else 3 if i in (5,6,7,10) else 0
                rows.append([label,f(r['Caso_base'],decimals),f(r['Escenario'],decimals),
                             '— (identificador)' if r['Diferencia'] is None else f(r['Diferencia'],decimals)])
            d.table(s,['Variable','Base','Escenario','Diferencia'],rows,[4.65,2.45,2.45,2.4],y=1.78,size=17,row_h=.385)
            d.caption(s,'Fuente: comparacion_escenario1.xlsx / comparacion. Diferencia=escenario−base. No restar identificadores.')
        elif kind=='branch_changes':
            rows=[[f"{r['Desde']}–{r['Hasta']}",f(r['S_base_MVA']),f(r['S_escenario_MVA']),f(r['Delta_MVA']),f(r['Delta_pct'],2)+' %'] for r in comp['cambios_top5_total']]
            d.table(s,['Rama','Base [MVA]','Esc. [MVA]','Δ [MVA]','Δ [%]'],rows,[2.2,2.45,2.45,2.6,2.25],row_h=.64,size=22)
            d.text(s,'Ranking global: incluye retirada. Redistribución activa: otra hoja.',.75,6.06,11.8,.5,21,TEAL,True)
            d.caption(s,'Fuente: cambios_top5_total; complemento cambios_top5. S=max extremos; Δ%=100·ΔS/Sbase. No sumar Δ MVA como MW.')
        elif kind=='voltage_change':
            d.image(s,charts['voltage'],.6,1.8,12.1,3.9)
            d.text(s,'Base: 53,76,118 → Escenario: 20,21,22,53,76,118\nTres bajas nuevas. Mínima escenario: 0,940040 pu en barra21.',.75,5.72,11.8,.85,23,ORANGE,True)
            d.caption(s,'Criterio guía inclusivo 0,95–1,05 pu, margen1e−8. Las tablas completas están en fuera_base / fuera_escenario.')
        elif kind=='loss_change':
            delta=sc['Perdidas_P_MW']-b['Perdidas_P_MW'];removed=comp['linea_retirada'][0]['P_loss_MW']
            d.text(s,f"{f(b['Perdidas_P_MW'])} → {f(sc['Perdidas_P_MW'])} MW",.75,1.98,11.8,.85,39,ORANGE,True)
            d.text(s,f"Δ pérdidas = +{f(delta)} MW (+{f(100*delta/b['Perdidas_P_MW'],2)} %)\nΔ P slack = +{f(sc['P_slack_MW']-b['P_slack_MW'])} MW",.75,3.12,11.8,1.15,29,TEAL,True)
            d.bullets(s,[f'Línea retirada: {f(removed)} MW; otras ramas: +{f(delta+removed)} MW.',
                         'Redistribución de corrientes y tensiones; pérdidas resistivas ∝ R|I|².',
                         'Q neta negativa: efecto capacitivo, no pérdida activa negativa.'],y=4.83,step=.55,size=21)
            d.caption(s,'Cargas/PG no slack iguales; GS=0. El aumento de pérdidas explica el aumento de P slack.')
        elif kind=='conclusions':
            d.bullets(s,['Métodos: NR 3→4; GS 757→909; FDLF 9→11. Todos ≤10⁻⁸ pu.',
                         'Pérdidas +33,035 MW (+24,86 %); P slack escenario 546,898 MW.',
                         '26–25: +223,362 MVA (+240,61 %). Fuera de tensión: 3→6 barras.',
                         'Convergente, no aceptable por tensión; RATE_A=0 impide certificar térmica.',
                         'Revisar soporte Q y redespacho; verificar límites Q/térmicos con nuevas corridas.'],step=.86,size=23)
            d.caption(s,'Diagnóstico limitado al flujo estático ensayado. No afirmar colapso, estabilidad dinámica o seguridad N−1.')
        elif kind=='closing':
            total=sum(item['seconds'] for item in story)
            d.bullets(s,['Pendiente: nombres reales, reparto de TODAS las voces y ensayo.',
                         f'MP4 real 1080p, audio claro, 30–40min; plan {total//60:02d}:{total%60:02d}.',
                         'Corridas sin cortes ni acelerado: desde ejecutar hasta exportar.',
                         'Entregar programa, informe Word, PPTX y cinco Excel principales.',
                         'Subir un día antes; si usa enlace, probar acceso del profesor.'],step=.83,size=24)
            d.caption(s,'Fuentes: MATPOWER8.1; Christie/UW1993; Tinney–Hart1967; Stott–Alsac1974. Referencias en PRESENTACION.md.')
        else:
            raise ValueError(f'Escena sin formato anterior: {kind}')
        s.notes_slide.notes_text_frame.text=(f"{index}. {spec['title']}\n{spec['section']}\nVoz: {spec['voice']}\n"
            f"Presupuesto: {spec['seconds']} s (incluye acciones en pantalla; no duración ensayada).\n\nQUÉ DECIR\n"+
            '\n\n'.join(spec['speech'])+'\n\nAPOYO — NO LEER\n'+spec['cue']+
            ('\n\nCOMANDOS REALES\n'+spec['code'] if spec['code'] else ''))
    return d.prs
