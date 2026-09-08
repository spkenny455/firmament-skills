"""Check fixed geometry across content, computed counts, evidence, copy limits and escaping."""
from copy import deepcopy
import xml.etree.ElementTree as ET
from render_report import render, html_document, poster_words


def sample():
    return {'template_version': 3, 'agent': 'Test', 'agent_logo': '',
        'headline': 'Your agent had useful notes.', 'spotlight_label': 'Checks that helped', 'events': [], 'description': 'Those notes helped it choose the right test.',
        'findings': [{'id': 'a', 'topic': 'Testing', 'status': 'used', 'support': 'direct',
            'title': 'Keep <script> as text', 'happened': 'A & B were clear.', 'next_time': 'Use the same test.',
            'evidence': [{'source': 'message 1', 'quote': '<script>alert(1)</script>'}]}],
        'featured_ids': ['a']}


def check():
    data = sample(); svg = render(data); root = ET.fromstring(svg)
    assert '<script>alert' not in svg and '&lt;script&gt;' in svg
    assert poster_words(svg) <= 120
    assert 'fetch(' not in html_document(svg)
    def boxes(s):
        return [tuple(sorted(e.attrib.items())) for e in ET.fromstring(s).findall('{http://www.w3.org/2000/svg}rect') if e.attrib.get('rx') == '18']
    empty = sample(); empty.update(headline='There is not enough evidence.', description='This record is too thin to judge.', findings=[], featured_ids=[])
    assert boxes(svg) == boxes(render(empty))  # Empty results do not become a new design.
    assert 'No further example' in render(empty)
    unknown = deepcopy(data)
    unknown['findings'].append({'id': 'b', 'status': 'missed', 'support': 'summary_only'})
    assert render(unknown) == svg  # Unsupported findings never inflate numbers.
    different = sample(); different['headline'] = 'Your agent could use these notes.'
    different['findings'][0]['status'] = 'new'
    assert boxes(svg) == boxes(render(different))
    bars = {e.attrib['data-topic']: float(e.attrib['width']) for e in root.findall('{http://www.w3.org/2000/svg}rect') if 'data-topic' in e.attrib}
    assert bars == {'Testing': 164}
    events = deepcopy(data)
    events['events'] = [{'id': 'e1', 'label': 'Check passed', 'evidence': [{'source': 'tool result', 'quote': 'PASS'}]}]
    assert boxes(svg) == boxes(render(events))
    for case in ('duplicate', 'missing-evidence', 'long-copy', 'layout-override', 'unknown-feature', 'old-schema', 'event-no-evidence', 'duplicate-event'):
        bad = deepcopy(data)
        if case == 'duplicate': bad['findings'].append(deepcopy(bad['findings'][0]))
        if case == 'missing-evidence': bad['findings'][0]['evidence'] = []
        if case == 'long-copy': bad['headline'] = 'word '*10
        if case == 'layout-override': bad['layout'] = 'custom'
        if case == 'unknown-feature': bad['featured_ids'] = ['missing']
        if case == 'old-schema': bad['template_version'] = 1
        if case == 'event-no-evidence': bad['events'] = [{'id':'e','label':'Check passed','evidence':[]}]
        if case == 'duplicate-event': bad['events'] = events['events']*2
        try:
            render(bad)
            raise AssertionError('Accepted bad input: '+case)
        except ValueError:
            pass
    print('PASS: fixed geometry, derived counts, empty state, escaping and invalid input rejection')


if __name__ == '__main__':
    check()
