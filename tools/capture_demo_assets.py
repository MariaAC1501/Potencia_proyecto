"""Capture real MATLAB/Excel UI assets without modifying source workbooks.

Requires Windows, MATLAB R2025a, desktop Excel, pywin32 and Pillow.
Run: python tools/capture_demo_assets.py
Only this script, its MATLAB helper and presentacion_assets/capturas are outputs.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageGrab, ImageStat
import pythoncom
import win32com.client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentacion_assets' / 'capturas'
SOURCES = [ROOT / 'data' / 'IEEE118.xlsx', ROOT / 'resultados_IEEE118_matlab.xlsx']
EXPECTED = ['gui_caso.png', 'gui_ejecutado.png', 'gui_perfil.png',
            'gui_archivo.png', 'gui_parametros.png', 'gui_comparacion.png',
            'excel_barras.png', 'excel_comparacion.png', 'excel_tensiones.png']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matlab_quote(path):
    return str(path).replace('\\', '/').replace("'", "''")


def capture_matlab(manifest):
    matlab = shutil.which('matlab') or r'C:\Program Files\MATLAB\R2025a\bin\matlab.exe'
    command = (f"addpath('{matlab_quote(ROOT / 'tools')}'); "
               f"capture_presentation_gui('{matlab_quote(OUT)}','{matlab_quote(ROOT)}')")
    # MATLAB's working directory and transient files stay outside the repository.
    with tempfile.TemporaryDirectory(prefix='powerflow_matlab_capture_', ignore_cleanup_errors=True) as temp:
        result = subprocess.run([matlab, '-wait', '-batch', command], cwd=temp,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace', timeout=600)
        (OUT / 'capture_matlab.log').write_text(result.stdout, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'MATLAB exited {result.returncode}; see capture_matlab.log')
    meta = json.loads((OUT / 'capture_gui_metadata.json').read_text(encoding='utf-8-sig'))
    manifest['matlab'] = {'source': 'matlab/app_flows.m', 'engine': 'MATLAB R2025a exportapp',
                          'metadata': meta,
                          'styling': 'Window 2000x1100, light theme, larger fonts, row/column sizes only; no data edits.'}
    for name in ['gui_caso.png', 'gui_ejecutado.png', 'gui_perfil.png']:
        manifest['captures'][name] = {'source': 'Real app_flows uifigure / exportapp',
            'state': {'gui_caso.png': 'IEEE118 loaded by Cargar caso, before execution',
                      'gui_ejecutado.png': 'After original Ejecutar callback, Todos (three methods)',
                      'gui_perfil.png': 'Same results, real Perfil de tensión tab selected'}[name]}
    with Image.open(OUT / 'gui_ejecutado.png') as native:
        fw, fh = meta['figure_size']
        sx, sy = native.width / fw, native.height / fh
        for key, rect in meta['crops'].items():
            x, y, w, h = rect
            box = (max(0, round(x*sx)), max(0, round((fh-y-h)*sy)),
                   min(native.width, round((x+w)*sx)), min(native.height, round((fh-y)*sy)))
            native.crop(box).save(OUT / f'{key}.png')
            manifest['captures'][f'{key}.png'] = {
                'source': 'gui_ejecutado.png', 'operation': 'Native image crop only; no resampling or drawing',
                'pixel_box_left_top_right_bottom': box,
                'region': {'gui_archivo': 'Original first file-selection row',
                           'gui_parametros': 'Original method/tolerance/max iterations/relaxation and Execute controls',
                           'gui_comparacion': 'Original Comparación tab: table and convergence axes'}[key]}


def color(r, g, b):
    return r + 256*g + 65536*b


def format_range(ws, address, widths, scientific=()):
    """Presentation formatting only, on a temporary workbook copy."""
    rng = ws.Range(address)
    rng.Font.Name = 'Aptos'
    rng.Font.Size = 20
    rng.RowHeight = 36
    rng.Interior.Color = color(255, 255, 255)
    rng.Font.Color = color(20, 32, 48)
    rng.Borders.LineStyle = 1
    rng.Borders.Color = color(206, 214, 222)
    header = rng.Rows(1)
    header.Font.Bold = True
    header.Font.Color = color(255, 255, 255)
    header.Interior.Color = color(24, 59, 86)
    header.WrapText = True
    header.RowHeight = 58
    for i, width in enumerate(widths, 1):
        ws.Columns(i).ColumnWidth = width
    decimal = ws.Application.DecimalSeparator
    for column in scientific:
        ws.Range(f'{column}2:{column}{rng.Rows.Count}').NumberFormatLocal = f'0{decimal}000E+00'
    # Hide existing filter arrows on the discarded copy to expose the full headings.
    for index in range(1, ws.ListObjects.Count + 1):
        ws.ListObjects(index).ShowAutoFilter = False
    if ws.AutoFilterMode:
        ws.AutoFilterMode = False
    ws.Activate()
    ws.Application.ActiveWindow.DisplayGridlines = False
    ws.Application.ActiveWindow.Zoom = 80
    ws.Range('A1').Select()
    return rng


def checked_display(ws, addresses):
    """Reject locale-scaling mistakes or #### before capturing Excel's bitmap."""
    decimal = ws.Application.DecimalSeparator
    checked = {}
    for address in addresses:
        cell = ws.Range(address)
        value, text = cell.Value2, str(cell.Text)
        if '#' in text:
            raise RuntimeError(f'Unreadable Excel cell {address}: {text}')
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            displayed = float(text.replace(decimal, '.'))
            tolerance = abs(value) * 0.00051 if 'E' in text.upper() else 0.00000051
            if abs(displayed - value) > tolerance:
                raise RuntimeError(f'Excel display differs from source at {address}: {value} -> {text}')
        checked[address] = {'value': value, 'displayed_text': text}
    return checked


def copy_picture(rng, target):
    """Excel renders its own Range.CopyPicture; Pillow only saves its bitmap."""
    import win32clipboard
    for attempt in range(5):
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
        finally:
            win32clipboard.CloseClipboard()
        rng.CopyPicture(Appearance=1, Format=2)  # xlScreen, xlBitmap
        time.sleep(0.8 + attempt * 0.4)
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            image.convert('RGB').save(target)
            return
    raise RuntimeError(f'Excel did not provide a bitmap for {target.name}')


def capture_excel(manifest):
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx('Excel.Application')
        excel.Visible = True
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.EnableEvents = False
        excel.WindowState = -4137  # xlMaximized
        manifest['excel_version'] = str(excel.Version)
        with tempfile.TemporaryDirectory(prefix='powerflow_excel_capture_') as temp:
            for source in SOURCES:
                original = excel.Workbooks.Open(str(source), UpdateLinks=0, ReadOnly=True,
                                                 IgnoreReadOnlyRecommended=True, AddToMru=False)
                try:
                    if not original.ReadOnly:
                        raise RuntimeError('Source did not open read-only')
                    copy = Path(temp) / source.name
                    original.SaveCopyAs(str(copy))
                finally:
                    original.Close(SaveChanges=False)
                book = excel.Workbooks.Open(str(copy), UpdateLinks=0, ReadOnly=False, AddToMru=False)
                try:
                    if source.name == 'IEEE118.xlsx':
                        ws = book.Worksheets('bus')
                        rng = format_range(ws, 'A1:I7', [12, 11, 12, 12, 10, 10, 11, 13, 13])
                        copy_picture(rng, OUT / 'excel_barras.png')
                        manifest['captures']['excel_barras.png'] = {
                            'source': str(source.relative_to(ROOT)), 'sheet': 'bus', 'range': 'A1:I7',
                            'view': 'Native contiguous range; header plus first six actual buses (BUS_I through VA).'}
                    else:
                        ws = book.Worksheets('comparacion')
                        rng = format_range(ws, 'A1:G4', [36, 23, 21, 25, 20, 29, 30], scientific=('D',))
                        ws.Range('E2:G4').NumberFormatLocal = f'0{excel.DecimalSeparator}000000'
                        checked = checked_display(ws, ['B2', 'C2', 'D2', 'D3', 'D4', 'E2', 'F2', 'G2'])
                        copy_picture(rng, OUT / 'excel_comparacion.png')
                        manifest['captures']['excel_comparacion.png'] = {
                            'source': str(source.relative_to(ROOT)), 'sheet': 'comparacion', 'range': 'A1:G4',
                            'checked_display': checked,
                            'view': 'All seven exported columns, all three real methods; stored timing values, not recalc.'}
                        source_ws = book.Worksheets('NR_bus')
                        view = book.Worksheets.Add(After=book.Worksheets(book.Worksheets.Count))
                        view.Name = 'captura_tensiones'
                        # Explicit selection of existing exported columns, no computed/fabricated values.
                        for dest, src in [('A1:A7', 'A1:A7'), ('B1:B7', 'O1:O7'), ('C1:C7', 'P1:P7')]:
                            view.Range(dest).Value2 = source_ws.Range(src).Value2
                        assert view.Range('A1:C1').Value2 == (('BUS_I', 'VM_pu', 'VA_deg'),)
                        rng = format_range(view, 'A1:C7', [17, 23, 25])
                        view.Range('B2:C7').NumberFormatLocal = f'0{excel.DecimalSeparator}000000'
                        checked = checked_display(view, [f'{col}{row}' for col in 'ABC' for row in range(2, 8)])
                        copy_picture(rng, OUT / 'excel_tensiones.png')
                        manifest['captures']['excel_tensiones.png'] = {
                            'source': str(source.relative_to(ROOT)), 'sheet': 'NR_bus',
                            'source_ranges': ['A1:A7', 'O1:O7', 'P1:P7'],
                            'checked_display': checked,
                            'view': 'Temporary sheet captura_tensiones!A1:C7: BUS_I, VM_pu, VA_deg; '
                                    'header plus first six NR buses, copied unchanged with Value2; display rounded to six decimals.'}
                finally:
                    book.Close(SaveChanges=False)
        for name in ['excel_barras.png', 'excel_comparacion.png', 'excel_tensiones.png']:
            manifest['captures'][name]['rendering'] = ('Real Microsoft Excel COM, temporary SaveCopyAs copy, '
                'Range.CopyPicture(xlScreen,xlBitmap); native clipboard bitmap saved without drawing; '
                '20pt font, 36pt rows, 80% zoom, header styling and filter-arrow visibility only on discarded copy.')
    finally:
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Prevent stale images being reported as success on a failed rerun.
    for name in EXPECTED:
        (OUT / name).unlink(missing_ok=True)
    source_files = SOURCES + [ROOT / 'matlab' / 'app_flows.m']
    before = {str(p.relative_to(ROOT)): sha256(p) for p in source_files}
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
                'sources_sha256_before': before,
                'scripts_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in
                    [Path(__file__).resolve(), ROOT / 'tools' / 'capture_presentation_gui.m']},
                'captures': {}, 'errors': []}
    for stage in (capture_matlab, capture_excel):
        try:
            stage(manifest)
        except Exception as exc:
            manifest['errors'].append(f'{stage.__name__}: {type(exc).__name__}: {exc}')
    after = {str(p.relative_to(ROOT)): sha256(p) for p in source_files}
    manifest['sources_sha256_after'] = after
    manifest['originals_unchanged'] = before == after
    for name in EXPECTED:
        path = OUT / name
        if not path.exists():
            manifest['errors'].append(f'Missing capture: {name}')
            continue
        with Image.open(path) as image:
            image.load()
            extrema = ImageStat.Stat(image.convert('RGB')).stddev
            nonempty = image.width > 100 and image.height > 30 and max(extrema) > 5
            manifest['captures'].setdefault(name, {}).update({
                'width': image.width, 'height': image.height, 'bytes': path.stat().st_size,
                'sha256': sha256(path), 'nonempty_checked': nonempty})
            if not nonempty:
                manifest['errors'].append(f'Empty/invalid image: {name}')
    if not manifest['originals_unchanged']:
        manifest['errors'].append('ERROR: original workbook hashes changed')
    manifest['complete'] = not manifest['errors']
    (OUT / 'captura_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'complete': manifest['complete'], 'originals_unchanged': before == after,
                      'errors': manifest['errors'], 'output': str(OUT)}, ensure_ascii=False, indent=2))
    return 0 if manifest['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
