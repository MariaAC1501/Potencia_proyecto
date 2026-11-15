"""Download the pinned MATPOWER reference without modifying MATLAB's saved path.

Usage: python tools/setup_matpower.py [--destination C:/ruta/matpower8.1]
MATPOWER remains optional: main/app_flows never import it.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile

URL = "https://github.com/MATPOWER/matpower/releases/download/8.1/matpower8.1.zip"
SHA256 = "7f13b1441669a64e312d14a60e564cd91977ff1676ff77d25538e94ff313dd56"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=(
        Path(tempfile.gettempdir()) / "potencia-matpower8.1" / "matpower8.1"))
    args = parser.parse_args()
    destination = args.destination.resolve()
    # Do not merge or overwrite an existing installation.
    if destination.exists():
        version_file = destination / "lib" / "mpver.m"
        if not version_file.is_file() or "'8.1'" not in version_file.read_text(encoding="utf-8"):
            raise SystemExit(f"La carpeta existe y no parece MATPOWER 8.1: {destination}")
        print(f"MATPOWER 8.1 ya disponible: {destination.as_posix()}")
        return
    with tempfile.TemporaryDirectory(prefix="potencia-matpower-download-") as work:
        work = Path(work)
        archive = work / "matpower8.1.zip"
        request = urllib.request.Request(URL, headers={"User-Agent": "potencia-validation/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != SHA256:
            raise SystemExit(f"SHA-256 inesperado: {actual}; no se extrae la descarga.")
        extracted = work / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as package:
            for entry in package.infolist():
                target = (extracted / entry.filename).resolve()
                if not target.is_relative_to(extracted.resolve()):
                    raise SystemExit(f"Ruta insegura en el ZIP: {entry.filename}")
            package.extractall(extracted)
        source = extracted / "matpower8.1"
        if not (source / "install_matpower.m").is_file():
            raise SystemExit("El ZIP no contiene la estructura esperada de MATPOWER 8.1.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
    print(f"MATPOWER 8.1 instalado: {destination.as_posix()}")
    print(f"SHA-256 verificado: {SHA256}")
    print("MATLAB: addpath('matlab');")
    print(f"validate_against_matpower('{destination.as_posix()}');")


if __name__ == "__main__":
    main()
