"""Run with: python -m unittest discover -s tests -v"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_scenario1 import prepare, cell_differences, fingerprint


class PrepareScenarioTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'scenario.xlsx'
        self.source = ROOT / 'data/IEEE118.xlsx'

    def test_unique_change_and_idempotence(self):
        before = fingerprint(self.source)
        record = prepare(self.source, self.output)
        self.assertEqual(record['changes'], [('branch', 'K39', 1, 0)])
        self.assertEqual(before, fingerprint(self.source))
        scenario_hash = fingerprint(self.output)
        prepare(self.source, self.output)
        self.assertEqual(scenario_hash, fingerprint(self.output))
        book = load_workbook(self.output)
        try:
            self.assertEqual(book['branch']['K39'].fill.fgColor.rgb, '00FFC000')
            self.assertIsNotNone(book['branch']['K39'].comment)
        finally:
            book.close()

    def test_refuses_overwriting_base(self):
        with self.assertRaisesRegex(ValueError, 'destino'):
            prepare(self.source, self.source)

    def test_refuses_other_edits(self):
        prepare(self.source, self.output)
        book = load_workbook(self.output)
        book['bus']['C2'] = book['bus']['C2'].value + 1
        book.save(self.output)
        book.close()
        with self.assertRaisesRegex(ValueError, 'cambios adicionales'):
            prepare(self.source, self.output)
        prepare(self.source, self.output, force=True)
        left, right = load_workbook(self.source), load_workbook(self.output)
        try:
            self.assertEqual(cell_differences(left, right), [('branch', 'K39', 1, 0)])
        finally:
            left.close()
            right.close()

    def test_refuses_ambiguous_line(self):
        source = Path(self.temp.name) / 'duplicate.xlsx'
        book = load_workbook(self.source)
        book['branch'].append([c.value for c in book['branch'][39]])
        book.save(source)
        book.close()
        with self.assertRaisesRegex(ValueError, 'una sola rama'):
            prepare(source, self.output)

    def test_accepts_reverse_orientation(self):
        source = Path(self.temp.name) / 'reverse.xlsx'
        book = load_workbook(self.source)
        book['branch']['A39'], book['branch']['B39'] = 30, 26
        book.save(source)
        book.close()
        self.assertEqual(prepare(source, self.output)['changes'], [('branch', 'K39', 1, 0)])


if __name__ == '__main__':
    unittest.main()
