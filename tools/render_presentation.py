"""Export and inspect the deck using Microsoft PowerPoint on Windows.

Requires PowerPoint and pywin32. Preview images additionally use pymupdf/Pillow.
Usage: python tools/build_presentation.py && python tools/render_presentation.py
This is a static render check, not a timed oral rehearsal or projector test.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import pythoncom
    import win32com.client

    source = ROOT / "PRESENTACION.pptx"
    output = ROOT / "PRESENTACION.pdf"
    assets = ROOT / "presentacion_assets"
    if not source.is_file():
        raise FileNotFoundError("Construya PRESENTACION.pptx antes de exportarla.")
    assets.mkdir(exist_ok=True)
    metadata = json.loads((assets / 'manifest.json').read_text(encoding='utf-8'))
    if metadata.get('project') != 'IEEE118_escenario1_video':
        raise ValueError('Construya la versión de la guía: python tools/build_presentation.py')
    expected = next(item['sha256'] for item in metadata['outputs'] if item['path'] == 'PRESENTACION.pptx')
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('PPTX cambió desde el builder. Reconstruir antes de verificar/exportar.')
    overflows = []
    app = presentation = None
    pythoncom.CoInitialize()

    def inspect(shape, slide, label):
        if shape.HasTextFrame and shape.TextFrame.HasText:
            frame = shape.TextFrame
            text = frame.TextRange
            excess = text.BoundTop + text.BoundHeight - (
                shape.Top + shape.Height - frame.MarginBottom)
            if excess > 1.0:
                overflows.append({"slide": slide, "shape": label,
                                  "overflow_pt": round(excess, 2), "text": text.Text[:100]})

    try:
        app = win32com.client.DispatchEx("PowerPoint.Application")
        presentation = app.Presentations.Open(str(source), ReadOnly=True,
                                              Untitled=False, WithWindow=False)
        count = presentation.Slides.Count
        if count != metadata['checks']['slides']:
            raise ValueError('Cantidad de diapositivas no coincide con la guía generada.')
        for index in range(1, count + 1):
            slide = presentation.Slides(index)
            for number in range(1, slide.Shapes.Count + 1):
                shape = slide.Shapes(number)
                inspect(shape, index, shape.Name)
                if shape.HasTable:
                    for row in range(1, shape.Table.Rows.Count + 1):
                        for col in range(1, shape.Table.Columns.Count + 1):
                            inspect(shape.Table.Cell(row, col).Shape, index,
                                    f"{shape.Name}[{row},{col}]")
        presentation.SaveAs(str(output), 32)  # ppSaveAsPDF
    finally:
        if presentation is not None:
            presentation.Close()
        if app is not None:
            app.Quit()
        pythoncom.CoUninitialize()

    review = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "pptx_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "rendered_slides": count, "powerpoint_readonly_render": "OK",
              "text_overflows": overflows,
              "pdf_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
              "project": "IEEE118_escenario1_video",
              "note": "Render técnico estático, NO video real ni ensayo oral cronometrado. " 
                      "La revisión corresponde a estos SHA-256."}
    (assets / "revision_powerpoint.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    make_previews(output, assets)
    print(f"PowerPoint: {count} diapositivas exportadas; desbordamientos: {len(overflows)}.")
    print(f"PDF: {output}")
    return 1 if overflows else 0


def make_previews(pdf: Path, assets: Path) -> None:
    try:
        import pymupdf
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        print("Vista general omitida: instale pymupdf y Pillow si la necesita.")
        return
    with pymupdf.open(pdf) as document:
        previews = []
        for index, page in enumerate(document, 1):
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            image = ImageOps.expand(image, border=(3, 21, 3, 3), fill="#dde3e9")
            ImageDraw.Draw(image).text((8, 4), f"{index:02d}", fill="black")
            previews.append(image)
        width = max(image.width for image in previews)
        height = max(image.height for image in previews)
        columns = 4
        sheet = Image.new("RGB", (columns * width,
                          ((len(previews) + columns - 1) // columns) * height), "#bfc8d2")
        for index, image in enumerate(previews):
            sheet.paste(image, ((index % columns) * width, (index // columns) * height))
        sheet.save(assets / "vista_general.png")
        metadata = json.loads((assets/'manifest.json').read_text(encoding='utf-8'))
        conclusion_index = next((i for i,s in enumerate(metadata['slides']) if s['kind']=='conclusions'),None)
        if conclusion_index is not None:
            document[conclusion_index].get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2), alpha=False).save(
                assets / "detalle_conclusiones.png")


if __name__ == "__main__":
    raise SystemExit(main())
