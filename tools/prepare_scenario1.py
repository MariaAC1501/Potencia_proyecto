"""Create the video scenario: copy IEEE118 and set only branch 26--30 STATUS=0.

Requires openpyxl. Preserves every other cell value, including the base workbook.
The modified row and STATUS cell are highlighted for the continuous recording.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill, Font

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cell_differences(base, scenario):
    if base.sheetnames != scenario.sheetnames:
        raise ValueError('Las hojas del caso modificado no coinciden con el caso base.')
    changes = []
    for name in base.sheetnames:
        left, right = base[name], scenario[name]
        for row in range(1, max(left.max_row, right.max_row) + 1):
            for col in range(1, max(left.max_column, right.max_column) + 1):
                a, b = left.cell(row, col), right.cell(row, col)
                if a.value != b.value:
                    changes.append((name, a.coordinate, a.value, b.value))
    return changes


def prepare(source=ROOT / 'data/IEEE118.xlsx', output=ROOT / 'data/IEEE118_escenario1.xlsx', force=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('El destino no puede ser el caso base.')
    source_hash = fingerprint(source)
    base = load_workbook(source)
    try:
        branch = base['branch']
        header = {cell.value: cell.column for cell in branch[1]}
        required = {'F_BUS', 'T_BUS', 'STATUS'}
        if not required.issubset(header):
            raise ValueError('Faltan columnas de ramas: F_BUS, T_BUS o STATUS.')
        matches = [row for row in range(2, branch.max_row + 1)
                   if {branch.cell(row, header['F_BUS']).value,
                       branch.cell(row, header['T_BUS']).value} == {26, 30}]
        if len(matches) != 1:
            raise ValueError(f'Se esperaba una sola rama 26–30; se encontraron {len(matches)}.')
        row = matches[0]
        cell = branch.cell(row, header['STATUS'])
        if cell.value != 1:
            raise ValueError('La línea 26–30 debe estar activa (STATUS=1) en el caso base.')
        expected = [('branch', cell.coordinate, 1, 0)]
        if output.exists() and not force:
            previous = load_workbook(output)
            try:
                if cell_differences(base, previous) != expected:
                    raise ValueError('El destino tiene cambios adicionales. Revíselo o use --force explícitamente.')
                if previous['branch'][cell.coordinate].fill.fill_type != 'solid':
                    raise ValueError('El dato modificado no está resaltado. Regenere con --force.')
            finally:
                previous.close()
        else:
            for value in branch[row]:
                value.fill = PatternFill('solid', fgColor='FFF2CC')
            cell.value = 0
            cell.fill = PatternFill('solid', fgColor='FFC000')
            cell.font = Font(bold=True, color='9C0006')
            cell.comment = Comment('Escenario 1: salida de la línea 26–30. Único cambio numérico: STATUS de 1 a 0. No eliminar la fila.', 'Proyecto MI-5215')
            output.parent.mkdir(parents=True, exist_ok=True)
            base.save(output)
    finally:
        base.close()
    original, modified = load_workbook(source), load_workbook(output)
    try:
        actual = cell_differences(original, modified)
        if actual != expected:
            raise ValueError(f'Cambios inesperados: {actual!r}')
    finally:
        original.close()
        modified.close()
    assert fingerprint(source) == source_hash, 'El archivo original cambió.'
    return {'scenario': '1: salida de línea 26–30', 'source': str(source), 'output': str(output),
            'source_sha256': source_hash, 'output_sha256': fingerprint(output),
            'changed_sheet': 'branch', 'changed_cell': expected[0][1],
            'branch_index_1based': row - 1, 'old_status': 1, 'new_status': 0,
            'changes': actual, 'definition': 'Se conserva la rama, con STATUS=0 y flujos nulos.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'data/IEEE118.xlsx')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/IEEE118_escenario1.xlsx')
    parser.add_argument('--force', action='store_true', help='Recrear un destino existente; nunca modifica el original.')
    args = parser.parse_args()
    record = prepare(args.source, args.output, args.force)
    assets = ROOT / 'escenario1_assets'
    assets.mkdir(exist_ok=True)
    (assets / 'entrada_escenario1.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Escenario verificado: {record['changed_sheet']}!{record['changed_cell']}, STATUS 1 -> 0; demás valores idénticos.")
    print(args.output)


if __name__ == '__main__':
    main()
