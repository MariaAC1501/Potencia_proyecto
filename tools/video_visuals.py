"""Visual-only IEEE118 video materials; evidence and narrative remain external.

Charts are derived from the supplied evidence. PowerPoint diagrams and questions
are editable; long explanations live exclusively in the unchanged speaker notes.
No MATLAB, Office automation, or final-file writes occur in this module.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

NAVY, INK, TEAL, BLUE, ORANGE = '10263F', '20364C', '007E74', '2463A4', 'B34F16'
PALE, MUTED, LINE, WHITE = 'EFF4F8', '52667C', 'D6E1E9', 'FFFFFF'
METHODS = ['NR', 'GS', 'FDLF']


def f(value, places=3, signed=False):
    return format(value, ('+' if signed else '') + f'.{places}f').replace('.', ',').replace('-', '−')


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _finish(ax, xlabel=None):
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='both', length=0, pad=10, labelcolor='#'+MUTED)
    ax.grid(axis='x', color='#'+LINE, lw=.8, zorder=0)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel, color='#'+MUTED, labelpad=12)


def _topology(rows, buses):
    """Deterministic force layout from our branch endpoints, not geographic data."""
    ids = [int(r['BUS_I']) for r in buses]
    ix = {bus: i for i, bus in enumerate(ids)}
    adjacency = np.zeros((len(ids), len(ids)))
    for row in rows:
        if row['STATUS']:
            i, j = ix[int(row['F_BUS'])], ix[int(row['T_BUS'])]
            adjacency[i, j] = adjacency[j, i] = 1
    degree = adjacency.sum(axis=1)
    _, vec = np.linalg.eigh(np.diag(degree)-adjacency)
    pos = vec[:, 1:3].copy()
    # Fix eigenvector signs so repeated builds produce the same orientation.
    for col in range(2):
        if pos[np.argmax(abs(pos[:, col])), col] < 0:
            pos[:, col] *= -1
    pos /= max(np.max(abs(pos)), 1e-12)
    k = np.sqrt(4/len(ids))
    for step in range(240):
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.maximum(np.linalg.norm(delta, axis=2), .015)
        np.fill_diagonal(dist, 1.0)
        force = (delta*(k*k/dist**2-adjacency*dist/k)[:, :, None]).sum(axis=1)
        norm = np.maximum(np.linalg.norm(force, axis=1), 1e-12)
        pos += force/norm[:, None]*np.minimum(norm, .06*(1-step/240))[:, None]
        pos -= pos.mean(axis=0)
    return ids, ix, pos


def make_charts(e, assets, root):
    assets, root = Path(assets), Path(root)
    assets.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 19,
                         'axes.labelsize': 19, 'xtick.labelsize': 17, 'ytick.labelsize': 20,
                         'axes.edgecolor': '#'+LINE, 'text.color': '#'+INK,
                         'axes.labelcolor': '#'+MUTED, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.facecolor': 'white'})
    files = {'gui_base': root/'escenario1_assets/gui_caso_base.png',
             'gui_scenario': root/'escenario1_assets/gui_salida_26_30.png'}

    def save(fig, key):
        path = assets/f'video_{key}.png'
        fig.savefig(path, dpi=210)
        plt.close(fig)
        files[key] = path

    # Full range uses the guide's 0.95–1.05 pu, never the file's VMIN/VMAX.
    fig, ax = plt.subplots(figsize=(12, 3.65), layout='constrained')
    for key, label, color in [('base', 'Base · NR', BLUE), ('scenario', 'Sin 26–30 · NR', ORANGE)]:
        rows = e[key]['NR_bus']
        ax.plot([r['BUS_I'] for r in rows], [r['VM_pu'] for r in rows],
                label=label, color='#'+color, lw=2.2, ls='-' if key=='base' else '--')
    ax.axhspan(.95, 1.05, color='#'+TEAL, alpha=.065)
    for value in [.95, 1.05]:
        ax.axhline(value, color='#'+MUTED, ls=':', lw=1.5)
    low = min(e['scenario']['NR_bus'], key=lambda r: r['VM_pu'])
    ax.scatter([low['BUS_I']], [low['VM_pu']], color='#'+ORANGE, s=55, zorder=5)
    ax.set(xlim=(1, 118), ylim=(.933, 1.065), ylabel='|V| [pu]', xlabel='Barra')
    ax.set_yticks([.95, 1., 1.05]); ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f(x, 2)))
    ax.legend(loc='upper center', ncol=2, frameon=False, fontsize=17)
    ax.grid(axis='y', color='#'+LINE)
    save(fig, 'voltage')

    # Independent reference profiles: labels explicitly distinguish the solutions.
    reference = e['reference_voltage']
    fig, ax = plt.subplots(figsize=(12, 2.5), layout='constrained')
    ax.plot([r['BUS_I'] for r in reference], [r['Reference_VM_pu'] for r in reference],
            color='#'+TEAL, lw=3.3, label='MATPOWER · NR de referencia')
    ax.plot([r['BUS_I'] for r in reference], [r['Own_VM_pu'] for r in reference],
            color='#'+BLUE, lw=1.8, ls='--', label='NR propio · base')
    ax.set(xlim=(1, 118), ylim=(.933, 1.08), ylabel='|V| [pu]')
    ax.set_yticks([.95, 1., 1.05]); ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f(x, 2)))
    ax.legend(loc='upper center', ncol=2, frameon=False, fontsize=16)
    ax.grid(axis='y', color='#'+LINE)
    save(fig, 'reference_voltage')

    fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
    low_rows = e['comparison']['base_top5_bajas']
    for i, r in enumerate(low_rows):
        color = ORANGE if r['VM_pu'] < .95-1e-8 else TEAL
        ax.plot([.938, r['VM_pu']], [i, i], color='#'+LINE, lw=9, solid_capstyle='round')
        ax.scatter(r['VM_pu'], i, s=130, color='#'+color, zorder=3)
        ax.text(r['VM_pu']+.0005, i, f(r['VM_pu'], 6), va='center', fontsize=22, color='#'+color)
    ax.axvline(.95, color='#'+MUTED, ls='--', lw=1.5)
    ax.text(.9502, -.58, 'Umbral 0,95', fontsize=18, color='#'+MUTED)
    ax.set(yticks=range(5), yticklabels=[f"{int(r['BUS_I'])} · {r['TipoNombre']}" for r in low_rows],
           xlim=(.9375, .958), ylim=(4.55, -.8))
    ax.set_xticks([.94, .945, .95, .955]); ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f(x, 3)))
    _finish(ax, '|V| base [pu]'); save(fig, 'base_low')

    fig, ax = plt.subplots(figsize=(12, 4.35), layout='constrained')
    rows = e['comparison']['base_top5_flujos']
    y = np.arange(5)
    for field, offset, color, label in [('S_from_MVA', -.17, BLUE, 'Desde'),
                                       ('S_to_MVA', .17, TEAL, 'Hasta')]:
        values = [r[field] for r in rows]
        ax.barh(y+offset, values, height=.28, color='#'+color, label=label)
        for yi, value in zip(y+offset, values):
            ax.text(value+5, yi, f(value), va='center', fontsize=17, color='#'+color)
    ax.set(yticks=y, yticklabels=[f"{int(r['Desde'])}–{int(r['Hasta'])}" for r in rows],
           xlim=(0, 540), ylim=(4.6, -.75))
    ax.legend(ncol=2, loc='lower right', frameon=False, fontsize=18)
    _finish(ax, '|S| por extremo [MVA] · orden: máximo de ambos'); save(fig, 'base_flows')

    fig, ax = plt.subplots(figsize=(12, 4.6), layout='constrained')
    rows = e['comparison']['cambios_top5_total']
    for i, r in enumerate(rows):
        delta = r['Delta_MVA']; color = ORANGE if delta>0 else BLUE
        if not r['Activa_escenario']:
            color = NAVY
        ax.barh(i, delta, height=.48, color='#'+color)
        ax.text(delta+(8 if delta>=0 else -8), i,
                f"{f(delta, 3, True)} MVA\n{f(r['Delta_pct'], 2, True)} %",
                ha='left' if delta>=0 else 'right', va='center', fontsize=20, color='#'+color)
    ax.axvline(0, color='#'+MUTED, lw=1)
    ax.set(yticks=range(5), yticklabels=[f"{int(r['Desde'])}–{int(r['Hasta'])}"+
           (' · retirada' if not r['Activa_escenario'] else '') for r in rows],
           xlim=(-420, 420), ylim=(4.6, -.6), xticks=[-200, 0, 200])
    _finish(ax, 'Δ S máx = escenario − base [MVA]'); save(fig, 'branch_changes')

    base, scenario = e['base_methods'][0], e['scenario_methods'][0]
    lb, ls = base['Perdidas_P_MW'], scenario['Perdidas_P_MW']
    removed = e['comparison']['linea_retirada'][0]['P_loss_MW']
    other = ls-lb+removed
    fig, ax = plt.subplots(figsize=(12, 3.65), layout='constrained')
    starts, heights = [0, lb-removed, lb-removed, 0], [lb, removed, other, ls]
    colors = [BLUE, TEAL, ORANGE, NAVY]
    for i, (start, height, color) in enumerate(zip(starts, heights, colors)):
        ax.bar(i, height, bottom=start, width=.6, color='#'+color)
        value = [lb, -removed, other, ls][i]
        ax.text(i, start+height+6, f(value, 6, i in (1, 2)), ha='center', fontsize=22, color='#'+color)
    for i, value in enumerate([lb, lb-removed, ls]):
        ax.plot([i+.3, i+.7], [value, value], color='#'+MUTED, ls=':', lw=1.5)
    ax.set(xticks=range(4), xticklabels=['Base', 'Rama retirada', 'Otras ramas', 'Escenario'],
           ylabel='Pérdidas P [MW]', ylim=(0, 205), yticks=[0, 50, 100, 150])
    ax.tick_params(length=0); ax.grid(axis='y', color='#'+LINE); ax.set_axisbelow(True)
    ax.spines[['left', 'bottom']].set_visible(False)
    save(fig, 'loss_waterfall')

    fig, ax = plt.subplots(figsize=(7.5, 4.2), layout='constrained')
    for i, (b, s) in enumerate(zip(e['base_methods'], e['scenario_methods'])):
        ax.plot([b['Iteraciones'], s['Iteraciones']], [i, i], lw=5, color='#'+LINE)
        ax.scatter(b['Iteraciones'], i, color='#'+BLUE, s=180, zorder=3, label='Base' if i==0 else None)
        ax.scatter(s['Iteraciones'], i, color='#'+ORANGE, s=150, marker='D', zorder=4,
                   label='Escenario' if i==0 else None)
        ax.text(np.sqrt(b['Iteraciones']*s['Iteraciones']), i-.25,
                f"{b['Iteraciones']} → {s['Iteraciones']}", ha='center', fontsize=24)
    ax.set_xscale('log'); ax.set(xlim=(1.5, 2000), ylim=(2.55, -.65), yticks=range(3),
                                yticklabels=METHODS, xticks=[3, 10, 100, 1000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: str(int(x))))
    ax.legend(loc='lower right', frameon=False, fontsize=17)
    _finish(ax, 'Iteraciones · escala logarítmica'); save(fig, 'method_iterations')

    # Retain the convergence diagnostic for technical traceability, not a text slide.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout='constrained')
    for ax, key, title in zip(axes, ['base', 'scenario'], ['Base', 'Sin 26–30']):
        for method, color in zip(METHODS, [BLUE, ORANGE, TEAL]):
            rows = e[key][method+'_conv']
            ax.semilogy([r['Iteracion'] for r in rows], [r['Error_max_pu'] for r in rows],
                        color='#'+color, label=method, lw=2)
        ax.axhline(1e-8, color='#'+MUTED, ls=':')
        ax.set_xscale('symlog', linthresh=1); ax.set(title=title, xlabel='Iteración', ylabel='Mismatch [pu]')
        ax.legend(fontsize=14, frameon=False); ax.grid(alpha=.15)
    save(fig, 'convergence')

    ids, ix, pos = _topology(e['base_input']['branch'], e['base_input']['bus'])
    fig, ax = plt.subplots(figsize=(7.6, 5.0), layout='constrained')
    for r in e['base_input']['branch']:
        if r['STATUS']:
            i, j = ix[r['F_BUS']], ix[r['T_BUS']]
            ax.plot(pos[[i, j], 0], pos[[i, j], 1], color='#B9C9D5', lw=1.2, zorder=1)
    sizes = [24 if r['BASE_KV']<300 else 66 for r in e['base_input']['bus']]
    ax.scatter(pos[:, 0], pos[:, 1], s=sizes, color='#'+BLUE, edgecolors='white', linewidth=.35, zorder=2)
    for bus, offset in [(26, (-.5, -.45)), (30, (.35, .35)), (69, (.35, -.3))]:
        i = ix[bus]; color = TEAL if bus==69 else ORANGE
        ax.scatter(*pos[i], color='#'+color, s=130, edgecolors='white', linewidth=1.5, zorder=3)
        ax.annotate(str(bus), pos[i], pos[i]+offset, color='#'+color, fontsize=20,
                    bbox=dict(facecolor='white', edgecolor='none', pad=2),
                    arrowprops=dict(arrowstyle='-', color='#'+color), zorder=5)
    ax.set_aspect('equal'); ax.axis('off'); save(fig, 'topology')

    # A genuine GUI crop, never described as an Excel screenshot.
    with Image.open(files['gui_scenario']) as image:
        assert image.size == (1600, 1000)
        path = assets/'video_gui_status_row.png'
        image.crop((17, 288, 1328, 347)).save(path)
        files['gui_status_row'] = path
        zoom = assets/'video_gui_status_zoom.png'
        image.crop((1205, 288, 1327, 347)).save(zoom)
        files['gui_status_zoom'] = zoom

    # Copy only the corrected, independently identified UW crop.
    original = root/'escenario1_assets/unifilar_region_26_30.png'
    annotated = root/'escenario1_assets/unifilar_region_26_30_anotado.png'
    assert 'Tanners Creek' in e['published_source']['bus26']
    assert 'Sorenson' in e['published_source']['bus30']
    path = assets/'video_unifilar_region_anotada.png'
    path.write_bytes(annotated.read_bytes()); files['crop'] = path
    (assets/'video_unifilar_anotaciones.json').write_text(json.dumps({
        'source': str(original.relative_to(root)), 'source_sha256': _hash(original),
        'annotated_source': str(annotated.relative_to(root)), 'annotated_source_sha256': _hash(annotated),
        'operation': 'Copia sin cambios del recorte verificado. 26=Tanners Creek; 30=Sorenson, 345 kV.',
        'publication_attribution': e['published_source']['citation'],
        'annotations_attribution': 'Equipo del proyecto; etiquetas y resaltado propios, no originales UW.',
        'output_sha256': _hash(path)}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return files


TITLES = {
    'cover': 'IEEE118', 'architecture': 'Excel → modelo → solución → Excel',
    'inputs': 'Dos entradas. Cuatro hojas por libro.', 'bus_types': 'Qué conocemos → qué resolvemos',
    'ybus': 'Una rama → cuatro entradas en Ybus', 'newton': 'Newton-Raphson · corrección conjunta',
    'gauss': 'Gauss-Seidel · usar el valor nuevo', 'decoupled': 'Desacoplado rápido · dos pasos secuenciales',
    'options': 'Mismos parámetros. Mismo arranque.', 'result_math': 'De las tensiones a los resultados',
    'small_run': 'El tamaño lo definen los datos', 'network_data': 'IEEE118 · nuestra topología de datos',
    'published_diagram': 'Unifilar publicado · ubicar 26–30', 'base_run': 'Caso base · ejecutar y grabar',
    'base_output': 'Excel base · seguir la trazabilidad', 'base_methods': 'Caso base · tres métodos, una solución',
    'validation': 'Caso base · contraste independiente', 'base_low': 'Las cinco tensiones más bajas · base',
    'base_flows': 'Las cinco ramas de mayor |S| · base', 'outage_diagram': '26–30 · antes de abrir la línea',
    'edit_input': 'Un único cambio · STATUS 1 → 0', 'scenario_run': 'Escenario · conservar la base y resolver',
    'scenario_comparison': 'Base frente a escenario · tabla guía', 'branch_changes': 'Respuesta 1 · las cinco mayores variaciones',
    'voltage_change': 'Respuesta 2 · tres bajas nuevas', 'loss_change': 'Respuesta 3 · aumentan las pérdidas',
    'scenario_methods': 'Más iteraciones en los tres métodos', 'conclusions': 'Convergente ≠ operación aceptable',
    'closing': 'Entregables y toma real pendiente',
}


class VisualDeck:
    def __init__(self, assets, count):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(13.333333), Inches(7.5)
        self.prs.core_properties.title = 'IEEE118 — Escenario 1: salida de línea 26–30'
        self.prs.core_properties.author = 'MI-5215 · Integrantes pendientes de completar'
        self.assets, self.count = Path(assets), count

    def text(self, slide, text, x, y, w, h, size=24, color=INK, bold=False, font='Aptos', align=None):
        obj = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = obj.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(.015)
        tf.margin_top = tf.margin_bottom = Inches(.015)
        for i, line in enumerate(str(text).split('\n')):
            p = tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text = line
            p.font.name, p.font.size, p.font.bold = font, Pt(size), bold
            p.font.color.rgb = RGBColor.from_string(color)
            p.space_after = Pt(0); p.space_before = Pt(0)
            if align is not None:
                p.alignment = align
        return obj

    def box(self, slide, x, y, w, h, fill=PALE, line=None, radius=False):
        obj = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                     Inches(x), Inches(y), Inches(w), Inches(h))
        obj.fill.solid(); obj.fill.fore_color.rgb = RGBColor.from_string(fill)
        if line:
            obj.line.color.rgb = RGBColor.from_string(line)
        else:
            obj.line.fill.background()
        if radius:
            obj.adjustments[0] = .08
        return obj

    def line(self, slide, x1, y1, x2, y2, color=MUTED, width=2):
        obj = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        obj.line.color.rgb = RGBColor.from_string(color); obj.line.width = Pt(width)
        return obj

    def arrow(self, slide, x, y, w=.55, h=.25, color=TEAL, down=False, left=False):
        shape = MSO_SHAPE.DOWN_ARROW if down else MSO_SHAPE.LEFT_ARROW if left else MSO_SHAPE.RIGHT_ARROW
        obj = slide.shapes.add_shape(shape,
                                     Inches(x), Inches(y), Inches(w), Inches(h))
        obj.fill.solid(); obj.fill.fore_color.rgb = RGBColor.from_string(color); obj.line.fill.background()
        return obj

    def node(self, slide, label, x, y, diameter=.7, color=BLUE, size=24):
        obj = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(diameter), Inches(diameter))
        obj.fill.solid(); obj.fill.fore_color.rgb = RGBColor.from_string(color); obj.line.fill.background()
        label_box = self.text(slide, label, x, y, diameter, diameter, size, WHITE, True,
                              align=PP_ALIGN.CENTER)
        label_box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        return obj

    def card(self, slide, value, label, x, y, w, h=1.65, color=TEAL, size=40):
        self.box(slide, x, y, w, h)
        self.box(slide, x, y, .055, h, color)
        self.text(slide, value, x+.18, y+.16, w-.35, max(.75, size/72*1.25), size, color, True)
        label_y, label_h = (h-.64, .55) if h>=1.6 else (h-.48, .4)
        label_size = 22 if w<3 else 23 if h>=1.6 else 21
        self.text(slide, label, x+.18, y+label_y, w-.35, label_h, label_size, INK)

    def file(self, slide, label, x, y, w=1.8, h=2, color=TEAL, detail=''):
        self.box(slide, x, y, w, h, WHITE, LINE)
        fold = .3
        self.box(slide, x+w-fold, y, fold, fold, LINE)
        self.box(slide, x, y, .065, h, color)
        self.text(slide, label, x+.17, y+.28, w-.32, .7, 26, color, True)
        if detail:
            self.text(slide, detail, x+.17, y+1.0, w-.32, h-1.1, 20, INK)

    def new(self, spec, index):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        dark = spec['kind'] in ('cover', 'question')
        s.background.fill.solid(); s.background.fill.fore_color.rgb = RGBColor.from_string(NAVY if dark else WHITE)
        self.box(s, .55, .33, .1, .25, ORANGE if dark else TEAL)
        self.text(s, spec['section'].upper(), .8, .28, 11.7, .35, 13, 'A7C5D5' if dark else TEAL, True)
        if spec['kind'] not in ('cover', 'question'):
            self.text(s, TITLES.get(spec['kind'], spec['title']), .65, .85, 12.05, .85, 30, NAVY, True)
        footer = 'MI-5215 / IEEE118' if not dark else 'MI-5215 · Apoyo estático / MP4 pendiente'
        self.text(s, footer, .65, 7.12, 10.6, .22, 10, 'A7C5D5' if dark else MUTED)
        self.text(s, f'{index:02d}/{self.count}', 11.93, 7.08, .75, .3, 12,
                  'A7C5D5' if dark else MUTED, align=PP_ALIGN.RIGHT)
        for section in range(6):
            self.box(s, .65+section*2.015, 7.43, 1.94, .035,
                     ORANGE if section==spec['section_number'] else ('27425A' if dark else LINE))
        return s

    def caption(self, slide, text):
        self.text(slide, text, .65, 6.65, 12.0, .38, 12, MUTED)

    def code(self, slide, text, x=.8, y=2, w=11.7, h=1.5, size=19):
        self.box(slide, x, y, w, h, NAVY, radius=True)
        self.text(slide, text, x+.2, y+.14, w-.4, h-.2, size, WHITE, font='Consolas')

    def image(self, slide, path, x, y, w, h):
        with Image.open(path) as image:
            ratio = image.width/image.height
        width = min(w, h*ratio); height = width/ratio
        return slide.shapes.add_picture(str(path), Inches(x+(w-width)/2), Inches(y+(h-height)/2),
                                        width=Inches(width), height=Inches(height))

    def table(self, slide, headers, rows, widths, y=2, size=22, row_h=.7, x=.65):
        obj = slide.shapes.add_table(len(rows)+1, len(headers), Inches(x), Inches(y),
                                     Inches(sum(widths)), Inches(row_h*(len(rows)+1)))
        for col, width in enumerate(widths):
            obj.table.columns[col].width = Inches(width)
        for i, row in enumerate([headers]+rows):
            obj.table.rows[i].height = Inches(row_h)
            for j, value in enumerate(row):
                cell = obj.table.cell(i, j); cell.text = str(value); cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = cell.margin_right = Inches(.09)
                cell.margin_top = cell.margin_bottom = Inches(.025)
                cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string(NAVY if i==0 else PALE if i%2 else WHITE)
                for p in cell.text_frame.paragraphs:
                    p.font.name = 'Aptos'; p.font.size = Pt(size-2 if i==0 else size)
                    p.font.bold = i==0 or j==0
                    p.font.color.rgb = RGBColor.from_string(WHITE if i==0 else TEAL if j==0 else INK)
        return obj

    def steps(self, slide, items, x=9.65, y=2.15, w=3.0, step=1.28):
        for i, text in enumerate(items, 1):
            self.node(slide, str(i), x, y+(i-1)*step, .43, TEAL, 17)
            self.text(slide, text, x+.6, y+(i-1)*step-.01, w-.6, 1.05, 24)


def _method_table(d, s, rows):
    body = [[m, str(r['Iteraciones']), f(r['Tiempo_s'], 4), f"{r['Error_final_pu']:.2e}",
             f(r['P_slack_MW']), f(r['Perdidas_P_MW']), f(r['Perdidas_Q_MVAr'])]
            for m, r in zip(METHODS, rows)]
    d.table(s, ['Método', 'Iter.', 'Tiempo\n[s]', 'Mismatch\n[pu]', 'P slack\n[MW]',
                'Pérdidas P\n[MW]', 'Pérdidas Q\n[MVAr]'], body,
            [1.15, .75, 1.4, 1.85, 2.05, 2.35, 2.35], y=2.05, size=23, row_h=.83)
    d.text(s, 'NR · Newton-Raphson     GS · Gauss-Seidel     FDLF · desacoplado rápido', .7, 5.65, 12, .48, 20, TEAL)
    d.text(s, 'Tiempo: solución + ensamblado + consola. Sin Excel ni gráficas.', .7, 6.12, 12, .4, 18, MUTED)


def build_deck(e, story, charts, root, assets):
    d = VisualDeck(assets, len(story)); root = Path(root)
    comp = e['comparison']; b = e['base_methods'][0]; sc = e['scenario_methods'][0]
    for index, spec in enumerate(story, 1):
        s = d.new(spec, index); kind = spec['kind']
        if kind=='question':
            number = spec['question_number']
            d.text(s, f'PREGUNTA {number} / 3', .85, 1.45, 10, .55, 22, '7BCAC1', True)
            d.text(s, spec['question'], .85, 2.35, 10.95, 3.4, 39, WHITE, True)
            d.box(s, .85, 6.05, 1.1, .055, ORANGE)
        elif kind=='cover':
            d.text(s, 'IEEE', .8, 1.16, 5.7, .8, 42, '7BCAC1', True)
            d.text(s, '118', .7, 1.85, 5.6, 2.0, 115, WHITE, True)
            d.text(s, 'Flujos de potencia', .85, 3.8, 6.1, .65, 34, WHITE, True)
            d.text(s, 'Escenario 1 · salida de línea', .85, 4.6, 6.5, .6, 26, '7BCAC1')
            d.line(s, 8.1, 3.25, 11.8, 3.25, ORANGE, 8)
            d.node(s, '26', 7.5, 2.65, 1.2, TEAL, 38); d.node(s, '30', 11.1, 2.65, 1.2, BLUE, 38)
            d.text(s, '345 kV', 8.55, 3.75, 2.9, .6, 28, WHITE, align=PP_ALIGN.CENTER)
            d.text(s, 'TEC · MI-5215 · II semestre 2026', .85, 5.6, 11.5, .5, 23, WHITE)
            d.text(s, 'Integrantes: [COMPLETAR NOMBRES REALES]', .85, 6.25, 11.5, .4, 20, 'E9AB80')
        elif kind=='architecture':
            for x, label, sub, color in [( .75, 'Excel', 'Cargar + validar', TEAL),
                    (3.85, 'Ybus', 'Modelo eléctrico', BLUE), (9.95, 'Excel', 'Resultados', TEAL)]:
                d.file(s, label, x, 2.6, 2.35, 2.3, color, sub)
            for x in [3.25, 6.3, 9.3]: d.arrow(s, x, 3.5, .45, .3)
            for y, label, color in [(2.38, 'NR', BLUE), (3.4, 'GS', ORANGE), (4.42, 'FDLF', TEAL)]:
                d.box(s, 6.95, y, 2.15, .8, color, radius=True)
                d.text(s, label, 7.1, y+.13, 1.85, .5, 28, WHITE, True, align=PP_ALIGN.CENTER)
            d.text(s, 'GUI / main.m', .8, 5.65, 3.1, .5, 24, TEAL, True)
            d.text(s, 'solve_power_flow.m', 6.55, 5.65, 3.9, .5, 20, BLUE)
            d.caption(s, 'Métodos propios. MATPOWER: referencia externa, no solucionador del programa.')
        elif kind=='inputs':
            d.file(s, 'Base', .75, 1.95, 2.45, 1.6, TEAL, 'IEEE118.xlsx')
            d.file(s, 'Sin 26–30', .75, 3.85, 2.45, 1.6, ORANGE, 'Copia')
            d.arrow(s, 3.5, 3.45, .6, .35)
            for x, y, name, fields in [(4.45, 1.95, 'config', '100 MVA'),
                    (8.65, 1.95, 'bus', 'PD/QD · VM/VA\nGS/BS'),
                    (4.45, 3.85, 'gen', 'PG/QG · VG\nQMIN/QMAX'),
                    (8.65, 3.85, 'branch', 'R/X/B · TAP\nSHIFT · STATUS')]:
                d.box(s, x, y, 3.9, 1.6)
                d.text(s, name, x+.18, y+.12, 3.5, .5, 27, TEAL, True)
                d.text(s, fields, x+.18, y+.65, 3.5, .85, 23)
            d.text(s, '2 entradas + 3 salidas = 5 Excel', 3.5, 5.85, 9, .6, 29, BLUE, True)
            d.caption(s, 'Potencias: MW/MVAr · VM, R/X/B: pu · VA/SHIFT: grados · GS/BS en bus.')
        elif kind=='bus_types':
            counts = {t: sum(r['TYPE']==t for r in e['base_input']['bus']) for t in [1, 2, 3]}
            for x, t, name, known, unknown, color in [( .75, 1, 'PQ', 'P · Q', '|V| · θ', BLUE),
                    (4.9, 2, 'PV', 'P · |V|', 'Q · θ', TEAL), (9.05, 3, 'Slack', '|V| · θ', 'P · Q', ORANGE)]:
                d.box(s, x, 2.0, 3.55, 3.8)
                d.text(s, name, x+.2, 2.2, 3.1, .6, 34, color, True)
                d.text(s, str(counts[t]), x+2.45, 2.2, .8, .6, 30, color, True)
                d.text(s, known, x+.2, 3.15, 3.1, .6, 30)
                d.arrow(s, x+1.38, 3.95, .35, .5, color, down=True)
                d.text(s, unknown, x+.2, 4.75, 3.1, .6, 30, color, True)
            d.text(s, 'Estado: 117 ángulos + 64 magnitudes PQ', .8, 6.0, 11.8, .55, 28, TEAL, True)
            d.caption(s, 'Conocidas → calculadas · Slack 69 · TYPE 1/2/3 desde Excel.')
        elif kind=='ybus':
            d.node(s, 'i', .85, 2.5, .55); d.node(s, 'j', 5.45, 2.5, .55)
            d.line(s, 1.4, 2.78, 2.65, 2.78, BLUE, 3); d.line(s, 4.3, 2.78, 5.45, 2.78, BLUE, 3)
            d.box(s, 2.65, 2.43, 1.65, .7, PALE, BLUE)
            d.text(s, 'y = 1/z', 2.75, 2.55, 1.5, .5, 24, BLUE)
            d.text(s, 't = a·exp(jφ)', 1.25, 1.85, 3.5, .5, 25, TEAL, True)
            for x in [1.75, 4.95]:
                d.line(s, x, 2.78, x, 3.5, BLUE, 2)
                d.line(s, x-.22, 3.5, x+.22, 3.5, BLUE, 2)
                d.line(s, x-.22, 3.67, x+.22, 3.67, BLUE, 2)
                d.line(s, x, 3.67, x, 4.15, BLUE, 2)
                d.line(s, x-.25, 4.15, x+.25, 4.15, BLUE, 2)
                d.text(s, 'jB/2', x-.55, 4.4, 1.3, .5, 24, BLUE)
            for x, y, label, formula in [(6.65, 2.05, 'Yff', '(y+jB/2)/|t|²'),
                    (9.75, 2.05, 'Yft', '−y/conj(t)'), (6.65, 3.95, 'Ytf', '−y/t'),
                    (9.75, 3.95, 'Ytt', 'y+jB/2')]:
                d.box(s, x, y, 2.9, 1.55)
                d.text(s, label, x+.15, y+.1, 2.6, .45, 25, TEAL, True)
                d.text(s, formula, x+.15, y+.75, 2.65, .55, 22, BLUE)
            d.text(s, 'Diagonal += (GS+jBS)/baseMVA', .8, 5.85, 8.3, .55, 26, TEAL, True)
            d.caption(s, 'build_ybus.m · z=R+jX · φ=SHIFT · TAP=0: a=1 · STATUS=0: omitir rama.')
        elif kind=='newton':
            d.box(s, .8, 2.55, 2.6, 2.15)
            d.text(s, 'ΔS', 1.0, 2.8, 2.2, .83, 42, BLUE, True, align=PP_ALIGN.CENTER)
            d.text(s, '[ΔP; ΔQ]', 1.0, 3.75, 2.2, .5, 24, align=PP_ALIGN.CENTER)
            d.arrow(s, 3.6, 3.45, .55, .3)
            for x, y, label in [(4.4, 2.55, 'H'), (5.75, 2.55, 'N'), (4.4, 3.65, 'M'), (5.75, 3.65, 'L')]:
                d.box(s, x, y, 1.2, .95, BLUE if label in ['H', 'L'] else TEAL)
                d.text(s, label, x, y+.17, 1.2, .6, 31, WHITE, True, align=PP_ALIGN.CENTER)
            d.arrow(s, 7.2, 3.45, .55, .3)
            d.card(s, 'Δx', 'J·Δx = ΔS', 8.0, 2.55, 2.0, 2.15, BLUE, 39)
            d.arrow(s, 10.2, 3.45, .55, .3)
            d.card(s, 'x + Δx', 'Nuevo x', 10.95, 2.55, 1.7, 2.15, TEAL, 25)
            d.line(s, 11.8, 5.05, 2.1, 5.05, TEAL, 2)
            d.text(s, 'Recalcular S(V) = V ⊙ conj(Ybus·V)', 2.7, 5.35, 8.3, .6, 28, BLUE, True)
            d.caption(s, 'J\\mis, no inv(J) · Mismatch AC ≤10⁻⁸ pu · máximo 1000 iteraciones.')
        elif kind=='gauss':
            for i, (label, color) in enumerate([('V(i−1) nuevo', TEAL), ('V(i) nuevo', TEAL), ('V(i+1) previo', BLUE), ('…', BLUE)]):
                x = .85+i*3.1
                d.box(s, x, 2.12, 2.7, 1.1, color, radius=True)
                d.text(s, label, x+.1, 2.38, 2.5, .6, 25, WHITE, True, align=PP_ALIGN.CENTER)
                if i<3: d.arrow(s, x+2.8, 2.55, .25, .2)
            d.text(s, 'V candidato = [(P−jQ)/conj(V) − Σ Yim·Vm] / Yii', .85, 3.65, 11.8, .75, 28, BLUE)
            d.box(s, .85, 4.65, 11.65, .95, PALE)
            d.text(s, 'V nuevo = V previo + 1,5·(V candidato − V previo)', 1.05, 4.88, 11.2, .6, 28, TEAL, True)
            d.text(s, 'PV: estimar Q → restaurar |V|=VG     Slack: fija', .85, 5.95, 11.7, .55, 25)
            d.caption(s, 'Mismatch AC ≤10⁻⁸ pu tras cada barrido; no solo cambio de V.')
        elif kind=='decoupled':
            for y, first, matrix, last, color in [(2.05, 'ΔP / |V|', 'B′', 'Δθ', BLUE),
                                                  (4.65, 'ΔQ / |V|', 'B″', 'Δ|V|', TEAL)]:
                for x, label in [(1.0, first), (5.0, matrix), (9.0, last)]:
                    d.box(s, x, y, 3.15, 1.05, color, radius=True)
                    d.text(s, label, x+.12, y+.22, 2.9, .65, 31, WHITE, True, align=PP_ALIGN.CENTER)
                d.arrow(s, 4.35, y+.4, .45, .25, color); d.arrow(s, 8.35, y+.4, .45, .25, color)
            d.arrow(s, 10.35, 3.32, .35, .8, ORANGE, down=True)
            d.text(s, 'Reevaluar Q con el ángulo nuevo', 2.4, 3.65, 7.8, .65, 27, ORANGE, True)
            d.caption(s, 'Matrices antes del bucle · aceptar con mismatch AC completo ≤10⁻⁸ pu.')
        elif kind=='options':
            for x, value, label, color in [( .8, '10⁻⁸', 'Tolerancia [pu]', BLUE), (3.9, '1000', 'Iteraciones máx.', TEAL),
                    (7.0, '1,5', 'Relajación GS', BLUE), (10.1, 'Q off', 'Límites inactivos', ORANGE)]:
                d.card(s, value, label, x, 2.25, 2.75, 2.0, color, 38 if value!='Q off' else 32)
            d.box(s, .85, 4.85, 11.65, 1.2, NAVY)
            d.text(s, 'Arranque: VM/VA del Excel + VG en PV y slack', 1.05, 5.16, 11.25, .65, 28, WHITE, True)
            d.caption(s, 'No plano · verbose=true · conversión PV→PQ implementada, desactivada aquí.')
        elif kind=='result_math':
            d.node(s, 'i', 1.0, 2.15, .8, BLUE, 30); d.node(s, 'j', 11.5, 2.15, .8, BLUE, 30)
            d.line(s, 1.8, 2.55, 11.5, 2.55, BLUE, 3)
            d.arrow(s, 3.0, 2.37, 1.2, .35, TEAL)
            d.arrow(s, 9.1, 2.37, 1.2, .35, TEAL, left=True)
            d.text(s, 'Sᵢ → rama', 2.25, 3.1, 3.2, .6, 28, TEAL, True)
            d.text(s, 'Sⱼ → rama', 8.35, 3.1, 3.2, .6, 28, TEAL, True)
            d.text(s, 'S = V·conj(I)·baseMVA', 3.2, 1.8, 7.2, .55, 28, BLUE, True)
            d.card(s, 'Sᵢ + Sⱼ', 'Pérdida de rama', .85, 4.2, 3.55, 1.7, BLUE, 34)
            d.card(s, 'Σ ramas', 'Pérdidas totales', 4.9, 4.2, 3.55, 1.7, TEAL, 34)
            d.card(s, 'Pcalc + PD', 'Generación slack', 8.95, 4.2, 3.55, 1.7, BLUE, 28)
            d.caption(s, 'Análogo Qcalc+QD · Q neta puede ser negativa por capacitancia.')
        elif kind=='small_run':
            d.text(s, '14', .85, 1.85, 3.4, 1.8, 103, BLUE, True)
            d.text(s, 'barras', 1.0, 3.65, 3.1, .65, 30, TEAL, True)
            d.code(s, "addpath('matlab');\noptions = struct('verbose',true);\nr14 = main('data/IEEE14.xlsx', ...\n 'resultados_IEEE14_matlab.xlsx',false,options);", 4.2, 2.15, 8.35, 2.4, 18)
            for i, (x, label) in enumerate([(1.0, 'Ejecutar'), (5.0, 'Iteraciones'), (9.0, 'Abrir Excel')], 1):
                d.node(s, str(i), x, 5.3, .5, TEAL, 19)
                d.text(s, label, x+.7, 5.32, 2.8, .6, 27)
                if i<3:
                    d.arrow(s, x+3.25, 5.46, .45, .25)
            d.caption(s, 'nBus desde datos · toma real <1 min, sin cortes ni acelerado.')
        elif kind=='network_data':
            d.image(s, charts['topology'], .65, 1.65, 7.5, 4.8)
            for x, value, label in [(8.45, len(e['base_input']['bus']), 'barras'),
                    (10.7, len(e['base_input']['branch']), 'ramas')]:
                d.card(s, str(value), label, x, 1.95, 1.95, 1.65, BLUE, 38)
            active_gen = sum(bool(r['STATUS']) for r in e['base_input']['gen'])
            d.card(s, str(active_gen), 'gen. activos', 8.45, 3.85, 4.2, 1.45, TEAL, 38)
            pd = sum(r['PD'] for r in e['base_input']['bus']); qd = sum(r['QD'] for r in e['base_input']['bus'])
            d.text(s, f'{f(pd, 0)} MW\n{f(qd, 0)} MVAr', 8.55, 5.55, 4.1, .95, 27, ORANGE, True)
            d.caption(s, 'Topología propia desde branch; no geográfica. MATPOWER 8.1 / case118 v2.')
        elif kind=='published_diagram':
            d.image(s, root/'escenario1_assets/IEEE118_unifilar_UW.png', .7, 1.75, 7.1, 4.65)
            d.arrow(s, 7.8, 3.65, .6, .3, ORANGE)
            d.image(s, charts['crop'], 8.15, 1.75, 2.85, 4.65)
            d.text(s, '30\nSorenson', 11.1, 2.05, 1.8, 1.2, 24, ORANGE, True)
            d.text(s, '26\nTanners\nCreek', 11.1, 5.0, 1.8, 1.5, 24, ORANGE, True)
            d.caption(s, 'Christie/UW 1993 · AEP 1962 · 345 kV · recorte y resaltado propios.')
        elif kind in ('base_run', 'scenario_run'):
            base = kind=='base_run'
            d.image(s, charts['gui_base' if base else 'gui_scenario'], .65, 1.75, 8.75, 4.7)
            d.steps(s, ['IEEE-118 / Todos', 'Ejecutar métodos', 'Exportar + revisar'] if base else
                    ['Retirar línea\n26–30', 'NR → GS → FDLF', 'Exportar + comparar'], x=9.65, y=2.1, w=3.0)
            if base:
                d.text(s, 'app_flows', 9.65, 6.08, 3, .45, 23, TEAL, True, font='Consolas')
            else:
                d.box(s, 9.65, 6.0, 3.0, .55, PALE, radius=True)
                d.text(s, 'Volver al caso base', 9.75, 6.1, 2.8, .35, 17, TEAL, True)
            d.caption(s, 'GUI: captura temporal, no video; tiempos distintos a tablas. Grabar hasta exportar.')
        elif kind=='base_output':
            for x, label, detail in [( .8, 'comparacion', 'Métodos\n+ parametros'), (4.85, 'NR_bus', 'Barra 69\nP / Q slack'),
                                     (8.9, 'NR_branch', 'Rama 38\nAmbos extremos')]:
                d.file(s, label, x, 2.05, 3.65, 2.2, TEAL, detail)
            d.card(s, f(b['P_slack_MW']), 'P slack [MW]', .85, 4.65, 5.6, 1.55, BLUE, 36)
            d.card(s, f(b['Q_slack_MVAr']), 'Q slack [MVAr] · absorbe', 6.85, 4.65, 5.6, 1.55, TEAL, 36)
            d.caption(s, 'resultados_IEEE118_matlab.xlsx · NR/GS/FDLF: barras, ramas, historial (iteración cero incluida).')
        elif kind=='base_methods':
            _method_table(d, s, e['base_methods'])
            d.caption(s, 'resultados_IEEE118_matlab.xlsx / comparacion · Q neta incluye capacitancia.')
        elif kind=='validation':
            d.image(s, charts['reference_voltage'], .65, 1.68, 12.0, 2.45)
            body = [[m, f"{r['MaxAbsVMError_pu']:.1e}", f"{r['MaxAbsVAError_deg']:.1e}",
                     f"{r['AbsPLossError_MW']:.1e}", f"{r['AbsSlackPError_MW']:.1e}", f"{r['AbsSlackQError_MVAr']:.1e}"]
                    for m, r in zip(METHODS, e['validation'])]
            error_table = d.table(s, ['Método', 'Máx |ΔV|\n[pu]', 'Máx |Δθ|\n[°]', '|Δ pérdidas P|\n[MW]',
                        '|Δ P slack|\n[MW]', '|Δ Q slack|\n[MVAr]'], body,
                    [1.1, 2.1, 2.1, 2.3, 2.2, 2.1], y=4.12, size=19, row_h=.44)
            error_table.table.rows[0].height = Inches(.65)
            d.text(s, f"Slack de referencia: P {f(e['reference_slack_p'], 9)} MW · Q {f(e['reference_slack_q'], 9)} MVAr", .7, 6.16, 12, .38, 17, TEAL, True)
            d.caption(s, 'validacion_MATPOWER.xlsx · solo base · referencia NR 10⁻¹⁰, Q off · perfiles superpuestos.')
        elif kind=='base_low':
            d.image(s, charts['base_low'], .65, 1.85, 9.2, 4.65)
            d.card(s, str(len(comp['fuera_base'])), '<0,95 pu', 10.1, 2.35, 2.5, 2.1, ORANGE, 62)
            d.text(s, '53 · 76 · 118', 10.1, 5.0, 2.55, 1, 27, ORANGE, True)
            d.caption(s, 'base_top5_bajas · guía 0,95–1,05 pu (margen 10⁻⁸), no VMIN/VMAX.')
        elif kind=='base_flows':
            d.image(s, charts['base_flows'], .65, 1.75, 12.0, 4.6)
            d.caption(s, 'S máx=max(|S desde|,|S hasta|) · base_top5_flujos · RATE_A=0: sin diagnóstico térmico.')
        elif kind=='outage_diagram':
            r = comp['linea_retirada'][0]
            d.node(s, '26', 1.15, 2.05, 1.05, TEAL, 34); d.node(s, '30', 11.1, 2.05, 1.05, BLUE, 34)
            d.line(s, 2.2, 2.58, 11.1, 2.58, ORANGE, 6)
            d.text(s, 'Tanners Creek', .8, 3.25, 4.1, .6, 26, TEAL, True)
            d.text(s, 'Sorenson', 8.9, 3.25, 3.5, .6, 26, BLUE, True, align=PP_ALIGN.RIGHT)
            d.text(s, f"P {f(r['P_from_MW'])} MW\nQ {f(r['Q_from_MVAr'])} MVAr\n|S| {f(r['S_from_MVA'])} MVA", .85, 4.12, 4.65, 1.6, 26)
            d.text(s, f"P {f(r['P_to_MW'])} MW\nQ {f(r['Q_to_MVAr'])} MVAr\n|S| {f(r['S_to_MVA'])} MVA", 8.0, 4.12, 4.65, 1.6, 26)
            d.text(s, 'Rama 38\n345 kV', 5.4, 3.6, 2.55, 1.25, 28, ORANGE, True, align=PP_ALIGN.CENTER)
            d.text(s, f"Pérdida base: {f(r['P_loss_MW'], 6)} MW", 3.4, 5.95, 7.4, .6, 28, ORANGE, True)
            d.caption(s, 'linea_retirada · inyección hacia la rama · un solo retiro; recalcular toda la red.')
        elif kind=='edit_input':
            d.card(s, '1', 'Base · STATUS', 1.0, 2.1, 3.0, 2.0, BLUE, 64)
            d.arrow(s, 4.6, 2.9, 2.0, .5, ORANGE)
            d.card(s, '0', 'Copia · STATUS', 7.1, 2.1, 3.0, 2.0, ORANGE, 64)
            d.text(s, 'branch!K39', 10.45, 2.45, 2.2, .55, 23, ORANGE, True)
            d.image(s, charts['gui_status_zoom'], 10.45, 3.15, 2.15, 1.05)
            d.text(s, 'GUI real · fila resaltada de la rama 26–30', .85, 4.62, 11.7, .55, 26, TEAL, True)
            d.image(s, charts['gui_status_row'], .8, 5.4, 11.8, .55)
            d.text(s, 'Rama 38 · sin otros cambios de entrada', .85, 6.08, 11.7, .45, 24)
            d.caption(s, 'Recorte GUI, no Excel. En la toma: IEEE118_escenario1.xlsx / branch!K39.')
        elif kind=='scenario_comparison':
            source = comp['comparacion']; rows = []
            for name, value_index, id_index in [('V mínima [pu] · barra', 0, 1), ('V máxima [pu] · barra', 2, 3)]:
                r, ids = source[value_index], source[id_index]
                rows.append([name, f"{f(r['Caso_base'], 6)} · b{int(ids['Caso_base'])}",
                             f"{f(r['Escenario'], 6)} · b{int(ids['Escenario'])}", f(r['Diferencia'], 6, True)])
            for name, row_index, places in [('Fuera de 0,95–1,05 pu', 4, 0), ('P slack 69 [MW]', 5, 3),
                    ('Q slack 69 [MVAr]', 6, 3), ('Pérdidas P [MW]', 7, 3), ('Iteraciones NR', 8, 0), ('Iteraciones GS', 9, 0)]:
                r = source[row_index]
                rows.append([name, f(r['Caso_base'], places), f(r['Escenario'], places), f(r['Diferencia'], places, True)])
            d.table(s, ['Variable', 'Base', 'Escenario', 'Δ esc.−base'], rows,
                    [4.5, 2.7, 2.7, 2.1], y=1.9, size=21, row_h=.5)
            d.caption(s, 'comparacion_escenario1.xlsx · magnitudes NR · b=barra; Δ nunca resta identificadores.')
        elif kind=='branch_changes':
            d.image(s, charts['branch_changes'], .65, 1.75, 12.0, 4.65)
            d.caption(s, 'cambios_top5_total: GLOBAL, incluye retirada · Δ%=100·ΔS/Sbase · S=max módulos de extremos.')
        elif kind=='voltage_change':
            d.image(s, charts['voltage'], .65, 1.75, 12.0, 3.8)
            d.text(s, f"{len(comp['fuera_base'])} → {len(comp['fuera_escenario'])}", .85, 5.55, 1.7, .75, 34, ORANGE, True)
            d.text(s, 'barras fuera\nde rango', 2.65, 5.65, 2.15, .85, 23)
            d.text(s, 'Nuevas: 20 · 21 · 22', 4.95, 5.72, 4.0, .65, 26, ORANGE, True)
            low = min(e['scenario']['NR_bus'], key=lambda r: r['VM_pu'])
            d.text(s, f"{f(low['VM_pu'], 6)} pu\nBarra {int(low['BUS_I'])}", 9.3, 5.6, 3.1, .95, 25, ORANGE, True)
            d.caption(s, 'Guía 0,95–1,05 pu ±10⁻⁸ · previas: 53/76/118 · seis bajas.')
        elif kind=='loss_change':
            d.image(s, charts['loss_waterfall'], .65, 1.75, 12.0, 3.9)
            delta = sc['Perdidas_P_MW']-b['Perdidas_P_MW']
            d.text(s, f"+{f(100*delta/b['Perdidas_P_MW'], 3)} %", .85, 5.78, 4.0, .65, 33, ORANGE, True)
            d.text(s, f"Δ P slack = +{f(delta)} MW", 5.0, 5.88, 7.2, .55, 27, TEAL, True)
            d.caption(s, 'Descomposición CONTABLE, no corridas intermedias · pérdidas R|I|² · cargas/PG no slack constantes.')
        elif kind=='scenario_methods':
            d.image(s, charts['method_iterations'], .65, 1.95, 7.45, 4.25)
            rows = [[m, f(bb['Tiempo_s'], 4), f(ss['Tiempo_s'], 4)] for m, bb, ss in
                    zip(METHODS, e['base_methods'], e['scenario_methods'])]
            d.table(s, ['Tiempo [s]', 'Base', 'Esc.'], rows, [1.65, 1.3, 1.3], x=8.35, y=2.25, size=20, row_h=.72)
            d.text(s, 'Tres métodos ≤10⁻⁸ pu', 8.4, 5.5, 4.1, .7, 26, TEAL, True)
            d.caption(s, 'Una corrida, no benchmark · solución+ensamblado+consola; sin Excel/gráficas.')
        elif kind=='conclusions':
            delta = sc['Perdidas_P_MW']-b['Perdidas_P_MW']
            d.card(s, f"+{f(100*delta/b['Perdidas_P_MW'], 3)} %", 'Pérdidas activas', .85, 2.1, 3.65, 2.0, ORANGE, 37)
            d.card(s, f"{len(comp['fuera_base'])} → {len(comp['fuera_escenario'])}", 'Barras bajas', 4.85, 2.1, 3.65, 2.0, ORANGE, 43)
            d.card(s, f(sc['P_slack_MW']), 'P slack [MW]', 8.85, 2.1, 3.65, 2.0, BLUE, 36)
            d.box(s, .85, 4.7, 11.65, 1.42, NAVY)
            d.text(s, 'Revisar soporte Q + redespacho', 1.1, 4.93, 11.1, .65, 30, WHITE, True)
            d.text(s, 'y repetir con límites Q y capacidades térmicas verificadas', 1.1, 5.6, 11.1, .4, 22, 'A7C5D5')
            d.caption(s, 'Seis bajas · Q límites off · RATE_A=0: sin factibilidad térmica/N−1 acreditada.')
        elif kind=='closing':
            for x, label, detail, color in [( .85, '5 Excel', '2 entradas\n3 salidas', TEAL),
                    (3.32, 'Word', 'Informe', BLUE), (5.79, 'PPTX', 'Con notas', BLUE),
                    (8.26, '.m', 'Código', TEAL), (10.73, 'MP4', 'PENDIENTE', ORANGE)]:
                d.file(s, label, x, 2.15, 1.8, 2.25, color, detail)
            d.text(s, '1080p · voces de todos · corridas sin cortes', .85, 5.1, 11.7, .65, 29, TEAL, True)
            duration = sum(scene['seconds'] for scene in story)
            d.text(s, f'Plan {duration//60:02d}:{duration%60:02d} · ensayar 30–40 min · completar nombres reales', .85, 5.93, 11.7, .55, 23)
            d.caption(s, 'Entregar un día antes · acceso al profesor · PDF/logs no sustituyen MP4.')
        else:
            raise ValueError(f'Escena sin diseño: {kind}')
        # EXACT legacy note contract: do not abridge, rephrase, or normalize.
        s.notes_slide.notes_text_frame.text = (f"{index}. {spec['title']}\n{spec['section']}\nVoz: {spec['voice']}\n"
            f"Presupuesto: {spec['seconds']} s (incluye acciones en pantalla; no duración ensayada).\n\nQUÉ DECIR\n"+
            '\n\n'.join(spec['speech'])+'\n\nAPOYO — NO LEER\n'+spec['cue']+
            ('\n\nCOMANDOS REALES\n'+spec['code'] if spec['code'] else ''))
    return d.prs
