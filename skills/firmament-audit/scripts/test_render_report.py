"""Synthetic scenarios: storage evidence, derived counts, fixed layout and offline export."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from render_report import checked, render, html_document, poster_words


def sample():
    # Keep the documented fixture executable: schema and instructions must agree.
    doc = (Path(__file__).parent.parent / 'references/report-data.md').read_text()
    return json.loads(doc.split('```json\n')[1].split('\n```')[0])


def set_state(d, state):
    r = d['findings'][0]['retention']
    r['status'] = state
    if state == 'saved':
        r['rationale_saved'] = True
        r['evidence'] = [{'source': 'A2', 'quote': 'Keep retries at one until idempotency keys prevent duplicate charges.'}]
        r['reason'] = 'The handoff stores both the limit and why it must remain.'
        r.pop('missing', None)
    elif state == 'unknown':
        r['artifact_ids'] = []
        r['reason'] = 'Cannot access the task output files.'
        r.pop('evidence', None)
        r.pop('missing', None)
        d['artifacts'] = []
    elif state == 'chat_only':
        r['reason'] = 'The checked function and full handoff omit retry limits and guidance.'
        r['missing'] = 'The retry limit and its reason.'
        r.pop('evidence', None)


def panels(svg):
    return [tuple(sorted(e.attrib.items())) for e in ET.fromstring(svg)
            if 'data-panel' in e.attrib]


class ReportTests(unittest.TestCase):
    def test_partial_decision(self):
        d = sample()
        _, counts, _ = checked(d)
        self.assertEqual(counts, {'partial': 1})
        self.assertNotIn('saved', counts)
        self.assertLessEqual(poster_words(render(d)), 165)

    def test_all_saved_and_chat_only_and_unknown(self):
        for state in ('saved', 'chat_only', 'unknown'):
            with self.subTest(state=state):
                d = sample(); set_state(d, state)
                self.assertEqual(checked(d)[1], {state: 1})
                self.assertEqual(panels(render(sample())), panels(render(d)))

    def test_unknown_does_not_disappear(self):
        d = sample(); set_state(d, 'unknown')
        self.assertIn('data-state="unknown" data-count="1"', render(d))

    def test_empty_and_summary_only_do_not_claim_retention(self):
        d = sample(); d.update(findings=[], featured_ids=[], insight_ids=[])
        d['headline'] = 'I could not check what was kept.'
        d['insight'] = 'The earlier work is not in the available record. I cannot count its lessons or check which ones were saved.'
        svg = render(d)
        self.assertIn('Not enough evidence to count', svg)
        self.assertEqual(panels(svg), panels(render(sample())))
        candidate = sample(); set_state(candidate, 'unknown')
        candidate['findings'][0]['support'] = 'summary_only'
        d['findings'] = candidate['findings']
        self.assertEqual(render(d), svg)

    def test_graph_has_exact_shared_denominator(self):
        d = sample()
        for i, state in enumerate(('saved', 'chat_only', 'unknown'), 2):
            variant = sample(); set_state(variant, state)
            f = variant['findings'][0]
            f['id'] = f'K{i}'; f['knowledge'] += f' Distinct synthetic item {i}.'
            d['findings'].append(f)
        root = ET.fromstring(render(d))
        bars = {e.attrib['data-state']: float(e.attrib['width']) for e in root if 'data-state' in e.attrib}
        self.assertEqual(bars, dict.fromkeys(('saved', 'partial', 'chat_only', 'unknown'), 174))
        self.assertEqual(sum(checked(d)[1].values()), 4)

    def test_reject_bad_data(self):
        cases = ['no-source', 'no-storage-quote', 'no-inspection', 'wrong-artifact',
                 'new-artifact', 'decision-without-why', 'duplicate', 'duplicate-knowledge',
                 'summary-storage', 'summary-feature', 'ungrounded-insight', 'old-schema',
                 'layout', 'long-copy', 'unsupported-logo', 'no-impact', 'no-impact-basis']
        for case in cases:
            with self.subTest(case=case):
                d = sample(); f = d['findings'][0]; r = f['retention']
                if case == 'no-source': f['evidence'] = []
                if case == 'no-storage-quote': r['evidence'] = []
                if case == 'no-inspection': set_state(d, 'chat_only'); r['artifact_ids'] = []
                if case == 'wrong-artifact': r['evidence'][0]['source'] = 'not-checked'
                if case == 'new-artifact': d['artifacts'][0]['existed_before_audit'] = False
                if case == 'decision-without-why': r['status'] = 'saved'
                if case == 'duplicate': d['findings'].append(deepcopy(f))
                if case == 'duplicate-knowledge':
                    second = deepcopy(f); second['id'] = 'other'; d['findings'].append(second)
                if case == 'summary-storage': f['support'] = 'summary_only'
                if case == 'summary-feature': set_state(d, 'unknown'); f['support'] = 'summary_only'
                if case == 'ungrounded-insight': d['insight_ids'] = ['imaginary']
                if case == 'old-schema': d['template_version'] = 3
                if case == 'layout': d['layout'] = 'my-style'
                if case == 'long-copy': d['headline'] = 'word '*20
                if case == 'unsupported-logo': d['agent_logo'] = 'invented'
                if case == 'no-impact': f.pop('impact')
                if case == 'no-impact-basis': f.pop('impact_basis')
                with self.assertRaises(ValueError): render(d)

    def test_escaping_and_embedded_assets(self):
        d = sample(); d['agent_logo'] = 'codex'
        d['findings'][0]['title'] = 'Keep <script> as text'
        svg = render(d)
        self.assertIn('&lt;script&gt;', svg)
        root = ET.fromstring(svg)
        images = root.findall('{http://www.w3.org/2000/svg}image')
        self.assertEqual(len(images), 2)
        self.assertTrue(all(e.attrib['href'].startswith('data:image/') for e in images))
        self.assertNotIn('fetch(', html_document(svg))
        self.assertIn('canvas.width=2480;canvas.height=3508', html_document(svg))

    def test_text_slots_keep_vertical_padding(self):
        root = ET.fromstring(render(sample()))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        for slot in root.findall('s:g', ns):
            for row in slot.findall('s:text', ns):
                # Reserve descent below the last baseline, not just line count.
                self.assertLessEqual(float(row.attrib['y'])+float(row.attrib['font-size'])*.3,
                                     float(slot.attrib['data-bottom']))
        boxes = [e for e in root if e.attrib.get('data-panel') == 'example']
        for box in boxes:
            edge = float(box.attrib['y'])+float(box.attrib['height'])
            self.assertGreaterEqual(edge-1070, 24)

    def test_unrelated_task_same_template(self):
        d = sample()
        d.update(headline='The launch plan lost a key reason.',
                 insight='I kept the launch date but left out why we chose it. The next agent could move it before support is ready.')
        f = d['findings'][0]
        f.update(knowledge='Launch after support training.', why='Support needs to handle new customers.',
                 title='Why launch waits until Monday', detail='The plan has the date. The reason for waiting is only in this chat.')
        f['evidence'] = [{'source': 'user message', 'quote': 'Wait until Monday so support can finish training.'}]
        f['retention'].update(evidence=[{'source':'A1','quote':'Launch: Monday'}], missing='Support readiness is the reason for the date.')
        self.assertEqual(panels(render(d)), panels(render(sample())))


if __name__ == '__main__':
    unittest.main()
