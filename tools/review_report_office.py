"""Optional Windows/Word interoperability review of the generated report.

Requires Microsoft Word + pywin32 (not required to build the report).
Opens the DOCX read-only in a separate Word instance and exports a review PDF.
No document is saved and no existing desktop session is reused.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import py_compile
import re

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pdf(path, headings):
    with pymupdf.open(path) as pdf:
        all_text = '\n'.join(page.get_text() for page in pdf)
        compact = lambda text: re.sub(r'\s+', '', text.replace(chr(173),''))
        for heading in headings:
            assert compact(heading) in compact(all_text), f'Falta capítulo: {heading}'
        for number in ('165.897686','546.897686','0.940040','223.362016','224.004254'):
            assert number in all_text, f'Falta cifra: {number}'
        for page in pdf:
            assert len(page.get_text().strip()) > 15, 'Página vacía.'
            for block in page.get_text('blocks'):
                assert block[0] >= 0 and block[2] <= page.rect.width+1, 'Texto fuera del ancho.'
                assert block[1] >= 0 and block[3] <= page.rect.height+1, 'Texto fuera del alto.'
        return {'file':str(path.relative_to(ROOT)),'pages':len(pdf),
                'chapters_present':len(headings),'key_values_present':True,
                'no_blank_pages':True,'page_bounds_verified':True,'sha256':digest(path)}


def main():
    import pythoncom
    import win32com.client
    docx = ROOT/'INFORME_PROYECTO_MATLAB.docx'
    before = digest(docx)
    review_pdf = ROOT/'informe_assets/revision_word.pdf'
    pythoncom.CoInitialize()
    app = doc = None
    try:
        app = win32com.client.DispatchEx('Word.Application')
        app.Visible = False; app.DisplayAlerts = 0
        word_version = str(app.Version)
        doc = app.Documents.Open(str(docx),ConfirmConversions=False,ReadOnly=True,AddToRecentFiles=False)
        assert doc.Tables.Count >= 28 and doc.InlineShapes.Count >= 50
        doc.Repaginate()
        doc.ExportAsFixedFormat(str(review_pdf),17)
    finally:
        if doc is not None: doc.Close(False)
        if app is not None: app.Quit()
        pythoncom.CoUninitialize()
    assert digest(docx) == before, 'La revisión no debe modificar Word.'
    markdown = (ROOT/'INFORME_PROYECTO_MATLAB.md').read_text(encoding='utf-8')
    headings = re.findall(r'^## (\d+\. .+)$',markdown,re.M)
    assert len(headings) == 15
    checks = [check_pdf(ROOT/'INFORME_PROYECTO_MATLAB.pdf',headings),check_pdf(review_pdf,headings)]
    for name in ('build_video_report.py','build_report.py','review_report_office.py'):
        py_compile.compile(str(ROOT/'tools'/name),doraise=True)
    for pdf_name,prefix in (('INFORME_PROYECTO_MATLAB.pdf','revision_pdf'),('informe_assets/revision_word.pdf','revision_word')):
        with pymupdf.open(ROOT/pdf_name) as pdf:
            for number in (16,17,21):
                pdf[number-1].get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False).save(ROOT/f'informe_assets/{prefix}_{number}.png')
    report = {'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'word_application_version':word_version,
              'checks':checks,'py_compile':True,'word_open_export':True,
              'documents':{name:digest(ROOT/name) for name in ('INFORME_PROYECTO_MATLAB.docx','INFORME_PROYECTO_MATLAB.pdf')},
              'reviewer':'tools/review_report_office.py','not_a_video':True}
    (ROOT/'informe_assets/revision_documental.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Word abierto sin modificar; PDF principal y exportación Word verificados:',[r['pages'] for r in checks])


if __name__ == '__main__':
    main()
