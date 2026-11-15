"""Read-only integration check of the delivered numerical evidence."""
from pathlib import Path
import sys
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_video_evidence
from check_video_evidence import audit


class VideoEvidenceTests(unittest.TestCase):
    def test_delivered_evidence(self):
        result = audit(materials=False)
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['sha256']), 6)
        self.assertTrue(result['human_pending'])


class TamperedEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ('data/IEEE118.xlsx','data/IEEE118_escenario1.xlsx',
                     'resultados_IEEE118_matlab.xlsx','resultados_IEEE118_escenario1_matlab.xlsx',
                     'comparacion_escenario1.xlsx','validacion_MATPOWER.json','validacion_MATPOWER.xlsx',
                     'escenario1_assets/entrada_escenario1.json'):
            target = self.root/name; target.parent.mkdir(exist_ok=True,parents=True)
            shutil.copyfile(ROOT/name,target)
        override = patch.object(check_video_evidence,'ROOT',self.root)
        override.start(); self.addCleanup(override.stop)

    def modify(self, name, action):
        path = self.root/name
        book = load_workbook(path)
        try:
            action(book)
            book.save(path)
        finally:
            book.close()

    def test_rejects_wrong_difference(self):
        def corrupt(book):
            sheet = book['comparacion']
            for row in range(2,sheet.max_row+1):
                if sheet.cell(row,1).value == 'Pérdidas totales (MW)':
                    sheet.cell(row,4).value = -999
        self.modify('comparacion_escenario1.xlsx',corrupt)
        with self.assertRaises(AssertionError):
            audit()

    def test_rejects_wrong_angle(self):
        def corrupt(book):
            sheet = book['NR_bus']
            header = {c.value:c.column for c in sheet[1]}
            cell = sheet.cell(2,header['VA_deg']); cell.value += 90
        self.modify('resultados_IEEE118_matlab.xlsx',corrupt)
        with self.assertRaises(AssertionError):
            audit()

    def test_rejects_self_consistent_wrong_q_loss(self):
        def corrupt(book):
            for name,column in (('comparacion','Perdidas_Q_MVAr'),('NR_branch','Q_loss_MVAr')):
                sheet = book[name]; header = {c.value:c.column for c in sheet[1]}
                cell = sheet.cell(2,header[column]); cell.value += 100
        self.modify('resultados_IEEE118_matlab.xlsx',corrupt)
        with self.assertRaises(AssertionError):
            audit()

    def test_rejects_wrong_top_flow(self):
        def corrupt(book):
            book['base_top5_flujos']['A2'] = 999
        self.modify('comparacion_escenario1.xlsx',corrupt)
        with self.assertRaises(AssertionError):
            audit()


if __name__ == '__main__':
    unittest.main()
