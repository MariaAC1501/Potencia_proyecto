"""Compile the spoken script, with one reference slide per page.

Canonical story: tools/presentation_story.py (also generates PPT speaker notes).
Run build_presentation.py, render_presentation.py, then build_oral_script.py.
GUION_PARA_EXPONER.md is generated; do not silently diverge it from PPT notes.
Run from any directory: python tools/build_oral_script.py
Requires Typst, pymupdf and Pillow. Does not modify the presentation or Excel.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_speeches(source: str) -> list[dict]:
    headings = list(re.finditer(r"^## (\d+)\. (.+)$", source, re.MULTILINE))
    slides = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(source)
        body = source[match.end():end]
        sections = re.split(r"^### (.+)\n", body, flags=re.MULTILINE)
        if sections[0].strip():
            raise ValueError(f"Contenido sin etiqueta en la diapositiva {match[1]}.")
        fields = {}
        for position in range(1, len(sections), 2):
            label, content = sections[position].strip(), sections[position + 1].strip()
            if label in fields or label not in {"Discurso", "Apoyo visual", "Comandos"}:
                raise ValueError(f"Sección inválida o duplicada: {label}.")
            fields[label] = content
        speech = [p.strip() for p in fields.get("Discurso", "").split("\n\n") if p.strip()]
        if not speech:
            raise ValueError(f"Falta el discurso de la diapositiva {match[1]}.")
        if any(re.match(r"^(Presentar|Comparar|Leer primero|Mencionar|Cerrar con)\b", p) for p in speech):
            raise ValueError("El discurso debe estar escrito para decirse, no como una instrucción.")
        code = ""
        if "Comandos" in fields:
            code_match = re.fullmatch(r"```matlab\n(.*?)\n```", fields["Comandos"], re.DOTALL)
            if code_match is None:
                raise ValueError("Los comandos deben estar en un bloque matlab.")
            code = code_match[1]
        slides.append({"number": int(match[1]), "title": match[2].strip(),
                       "speech": speech, "cues": [p for p in fields.get("Apoyo visual", "").split("\n\n") if p],
                       "code": code, "speech_words": len(re.findall(r"\S+", " ".join(speech)))})
    return slides


def verify_pdf(path: Path, slides: list[dict]) -> None:
    with pymupdf.open(path) as document:
        if len(document) != len(slides) + 1:
            raise ValueError(f"Se esperaban {len(slides)+1} páginas (portada + una por diapositiva), "
                             f"pero se generaron {len(document)}. Revisar saltos o desbordamientos.")
        for index, slide in enumerate(slides, 1):
            page = document[index]
            text = page.get_text()
            if f"DIAPOSITIVA {slide['number']}" not in text:
                raise ValueError(f"La página {index+1} no corresponde a la diapositiva {slide['number']}.")
            compact = lambda value: re.sub(r"\s+", "", value.replace("\u00ad", ""))
            if compact(slide["title"]) not in compact(text):
                raise ValueError(f"Falta el título de la diapositiva {slide['number']}.")
            for paragraph in slide["speech"]:
                if compact(paragraph) not in compact(text):
                    raise ValueError(f"Falta texto del discurso de la diapositiva {slide['number']}.")
            if len(page.get_images()) == 0:
                raise ValueError(f"Falta la imagen de referencia en la diapositiva {slide['number']}.")
            for block in page.get_text("blocks"):
                if block[0] < 35 or block[2] > page.rect.width - 35:
                    raise ValueError(f"Desbordamiento horizontal en la página {index+1}.")
        print(f"PDF comprobado: {len(document)} páginas; {len(slides)} discursos completos e imágenes de referencia.")


def main() -> None:
    source = ROOT / "GUION_PARA_EXPONER.md"
    presentation = ROOT / "PRESENTACION.pptx"
    presentation_pdf = ROOT / "PRESENTACION.pdf"
    metadata = json.loads((ROOT / "presentacion_assets/manifest.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "presentacion_assets/revision_powerpoint.json").read_text(encoding="utf-8"))
    if metadata.get('project') != 'IEEE118_escenario1_video' or review.get('project') != 'IEEE118_escenario1_video':
        raise ValueError('Se requiere la presentación de escenario1, no la antigua de varias redes.')
    if review["pptx_sha256"] != digest(presentation) or review["pdf_sha256"] != digest(presentation_pdf):
        raise ValueError("La revisión no coincide con el PowerPoint/PDF actual. Regenerar la presentación primero.")
    if review["text_overflows"]:
        raise ValueError("La presentación contiene desbordamientos de texto.")
    slides = parse_speeches(source.read_text(encoding="utf-8"))
    if len(slides) != len(metadata["slides"]):
        raise ValueError("El número de discursos no coincide con la presentación.")
    elapsed = 0
    for spoken, shown in zip(slides, metadata["slides"]):
        if (spoken["number"] != shown["number"] or spoken["title"] != shown["title"]
                or spoken['speech'] != shown['speech'] or spoken['code'] != shown['code']):
            raise ValueError(f"Guion y notas desincronizados: {spoken['number']}. {spoken['title']}. Regenerar desde presentation_story.py.")
        spoken.update(seconds=shown["seconds"], start_seconds=elapsed, appendix=shown.get("appendix", False))
        elapsed += shown["seconds"]
        spoken["end_seconds"] = elapsed
        spoken['voice'] = shown['voice']
        spoken['section'] = shown['section']
        spoken["image"] = f"diapositiva_{spoken['number']:02d}.png"
    assets = ROOT / "guion_assets"
    assets.mkdir(exist_ok=True)
    expected_images = {slide['image'] for slide in slides}
    for image in assets.glob('diapositiva_*.png'):
        if re.fullmatch(r'diapositiva_\d+\.png',image.name) and image.name not in expected_images:
            image.unlink()  # Solo miniaturas generadas que ya no pertenecen al guion.
    with pymupdf.open(presentation_pdf) as document:
        if len(document) != len(slides):
            raise ValueError("El PDF de diapositivas tiene otra cantidad de páginas.")
        for page, slide in zip(document, slides):
            page.get_pixmap(matrix=pymupdf.Matrix(0.9, 0.9), alpha=False).save(assets / slide["image"])
    content = {"project": "IEEE118_escenario1_video", "recording_status": "Video real con voces pendiente", "total_seconds": elapsed, "slides": slides,
               "main_slides": sum(not slide["appendix"] for slide in slides),
               "backup_slides": sum(slide["appendix"] for slide in slides)}
    (assets / "guion.json").write_text(json.dumps(content, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    typst = shutil.which("typst")
    if not typst:
        raise RuntimeError("Typst no está disponible en el PATH.")
    output = ROOT / "GUION_PARA_EXPONER.pdf"
    subprocess.run([typst, "compile", str(ROOT / "GUION_PARA_EXPONER.typ"), str(output)],
                   cwd=ROOT, check=True)
    verify_pdf(output, slides)
    manifest = {"built_at_utc": datetime.now(timezone.utc).isoformat(),
                "presentation_sha256": digest(presentation), "presentation_pdf_sha256": digest(presentation_pdf),
                "speech_source_sha256": digest(source), "pdf_sha256": digest(output),
                "slides": len(slides), "main_slides": content["main_slides"],
                "backup_slides": content["backup_slides"], "planned_seconds": elapsed,
                "speech_words": sum(slide["speech_words"] for slide in slides),
                "pages": len(slides)+1, "layout": "Portada + una página por diapositiva"}
    (assets / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Guion oral: {output}")
    print(f"Texto editable: {source}")
    print(f"Palabras del discurso: {manifest['speech_words']}; tiempo de presentación previsto: {elapsed//60}:{elapsed%60:02d}.")


if __name__ == "__main__":
    main()
