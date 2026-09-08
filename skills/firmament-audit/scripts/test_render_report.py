"""Check truthful counts, escaping, empty findings and invalid input handling."""
from copy import deepcopy
import xml.etree.ElementTree as ET
from render_report import render, html_document


def check():
    data = {"agent": "Test agent", "card": {"scope": "One conversation", "starting_note": "Keep the demonstrated constraint.", "coverage_note": "Selected findings only"}, "findings": [{"id": "f1", "kind": "correction", "support": "direct", "title": "Keep <script> as text", "card_summary": "A & B must remain readable.", "established_evidence": [{"source": "message 1", "quote": "<script>alert(1)</script>"}]}, {"id": "f2", "kind": "decision", "support": "unverified"}], "issues": [{"id": "i1"}]}
    svg = render(data)
    ET.fromstring(svg)
    assert '1 supported lessons, 1 issues, 1 corrections' in svg
    assert '<script>alert' not in svg and '&lt;script&gt;' in svg
    assert 'fetch(' not in html_document(svg)
    empty = deepcopy(data); empty['findings'] = []; empty['issues'] = []
    assert 'No supported lessons' in render(empty)
    for bad in ('duplicate', 'unsupported-feature', 'overflow', 'missing-evidence'):
        changed = deepcopy(data)
        if bad == 'duplicate': changed['findings'].append(deepcopy(changed['findings'][0]))
        if bad == 'unsupported-feature': changed['card']['featured_ids'] = ['f2']
        if bad == 'overflow': changed['findings'][0]['card_summary'] = 'x' * 221
        if bad == 'missing-evidence': changed['findings'][0]['established_evidence'] = []
        try:
            render(changed)
            raise AssertionError('Invalid input accepted: ' + bad)
        except ValueError:
            pass
    print('PASS: evidence-filtered counts, escaped source text, empty state, invalid input refusal')


if __name__ == '__main__':
    check()
