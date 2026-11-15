"""Presentation content and restored-format regressions; evidence is read-only."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_video_materials import load_evidence
from presentation_story import (make_story, QUESTION_PROMPTS, SECTION_SECONDS,
                                PLANNED_SECONDS, EXPECTED_SLIDES)


class PresentationStoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = make_story(load_evidence(ROOT))

    def test_slide_count_and_guide_timing(self):
        self.assertEqual(len(self.story), EXPECTED_SLIDES)
        self.assertEqual(EXPECTED_SLIDES, 32)
        self.assertEqual(sum(s['seconds'] for s in self.story), PLANNED_SECONDS)
        self.assertEqual(PLANNED_SECONDS, 35*60+45)
        for section, (minimum, maximum) in enumerate(((60,120),(480,600),(180,240),(360,480),(600,720),(120,180))):
            seconds = sum(s['seconds'] for s in self.story if s['section_number']==section)
            self.assertEqual(seconds, SECTION_SECONDS[section])
            self.assertTrue(minimum <= seconds <= maximum)

    def test_question_immediately_before_each_answer(self):
        pairs = [(i,s) for i,s in enumerate(self.story) if s['kind']=='question']
        self.assertEqual([s['question_number'] for _,s in pairs],[1,2,3])
        expected = {1:'branch_changes',2:'voltage_change',3:'loss_change'}
        for i, question in pairs:
            number = question['question_number']
            self.assertEqual(self.story[i+1]['kind'],expected[number])
            self.assertEqual(self.story[i+1]['question_number'],number)
            self.assertEqual(question['speech'],[QUESTION_PROMPTS[number]])
            self.assertEqual(question['seconds'],15)

    def test_questions_match_teacher_guide_and_do_not_answer(self):
        guide = (ROOT/'Guía_para_el_video_de_exposición_—_Proyecto_de_Flujos_de_Potencia_IEEE_118_barra.md').read_text(encoding='utf-8')
        for slide in self.story:
            if slide['kind'] != 'question': continue
            self.assertIn(slide['question'],guide)
            for result in ('0,940040','165,897','240,61','757','909'):
                self.assertNotIn(result,slide['question'])

    def test_previous_white_navy_table_format_is_restored(self):
        import json
        from pptx import Presentation
        metadata = json.loads((ROOT/'presentacion_assets/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['checks']['presentation_style'],'classic')
        deck = Presentation(ROOT/'PRESENTACION.pptx')
        self.assertEqual(len(deck.slides),EXPECTED_SLIDES)
        for slide in deck.slides:
            self.assertEqual(str(slide.background.fill.fore_color.rgb),'FFFFFF')
        self.assertGreaterEqual(sum(any(shape.has_table for shape in slide.shapes) for slide in deck.slides),10)

    def test_detailed_notes_and_gui_workflow_are_retained(self):
        for kind in ('branch_changes','voltage_change','loss_change'):
            response = next(s for s in self.story if s['kind']==kind)
            self.assertGreaterEqual(len(response['speech']),3)
            self.assertGreater(len(' '.join(response['speech']).split()),80)
        notes = ' '.join(' '.join(s['speech']) for s in self.story)
        self.assertIn('Retirar línea 26–30',notes)
        self.assertIn('Volver al caso base',notes)
        self.assertIn('límites Q',notes)
        self.assertTrue(all(s['cue'] for s in self.story))


if __name__ == '__main__':
    unittest.main()
